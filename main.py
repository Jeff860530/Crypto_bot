import time
from datetime import datetime, timedelta
import config

# 引入服務模組
from services.trading_service import TradingService
from services.report_service import ReportService
from services.qa_service import QAService
from services.email_service import EmailService
from services.market_data_service import MarketDataService
from utils.data_loader import BingXLoader

def main():
    print(f"🤖 Crypto Bot 架構重構版啟動...")

    # 1. 初始化服務
    mailer = EmailService()            
    reporter = ReportService()        
    market_data = MarketDataService() 
    qa_service = QAService("questions.json")

    loader = BingXLoader()
    trader = TradingService(report_service=reporter, email_service=mailer) 

    # 2. 設定時間鎖 (Time Locks)
    timers = {
        'trade': datetime.now(),         # 馬上執行一次
        'report': datetime.now(),        # 馬上執行一次
        'qa': datetime.now()             # 馬上執行一次
    }

    # 顯示目前的頻率設定
    print("🚀 系統進入極速監聽模式...")
    print(f"   ⏱️ QA檢查: 每 {config.INTERVAL_QA_CHECK} 秒")
    print(f"   ⏱️ 交易檢查: 每 {config.INTERVAL_TRADING_CHECK / 60:.0f} 分鐘")
    print(f"   ⏱️ 定期報告: 每 {config.INTERVAL_PERIODIC_REPORT / 60:.0f} 分鐘")
    print("-" * 50) # 初始分隔線

    while True:
        try:
            now = datetime.now()

            # --- 任務 1: QA 問答 ---
            if config.ENABLE_QA_SYSTEM and now >= timers['qa']:
                # 執行 QA 邏輯
                qa_service.process_pending_questions(ai_reporter=reporter, mailer=mailer)
                
                # 重設計時器
                timers['qa'] = now + timedelta(seconds=config.INTERVAL_QA_CHECK)
                
                # 🔥 優化：任務結束後多印一行空行，方便閱讀
                # (因為 QA 比較頻繁，如果不希望它一直刷空行，可以只在有處理問題時印，
                # 但為了保持程式碼簡單一致，這裡先統一印出)
                # print() 

            # --- 任務 2: 交易檢查 ---
            if config.ENABLE_TRADING_SYSTEM and now >= timers['trade']:
                print(f"💰 執行交易策略檢查... {now.strftime('%H:%M')}")
                trader.run_cycle() 
                
                # 重設計時器
                timers['trade'] = now + timedelta(seconds=config.INTERVAL_TRADING_CHECK)
                
                # 🔥 優化：任務結束後多印一行空行
                print("-" * 30 + "\n") 

            # --- 任務 3: 定期報告 ---
            if config.ENABLE_PERIODIC_REPORT and now >= timers['report']:
                print(f"📊 執行定期市場報告... {now.strftime('%H:%M')}")
                
                # 針對監控清單中的每一個幣種生成報告
                for symbol in config.COIN_LIST:
                    try:
                        # 1. 抓資料 (抓 1 小時線來看大趨勢)
                        df = loader.fetch_data(timeframe='1h', symbol=symbol, limit=50)
                        
                        if df is not None and not df.empty:
                            # 2. 算指標
                            context = market_data.analyze_technicals(df)
                            context['symbol'] = symbol
                            
                            # 3. 生成 HTML
                            html = reporter.generate_market_report(context)
                            
                            # 4. 寄信
                            subject = f"📅 市場趨勢報告: {symbol}"
                            mailer.send_report(subject, html)
                            print(f"   ✅ {symbol} 報告已寄出")
                        else:
                            print(f"   ⚠️ {symbol} 無法獲取數據，跳過報告")
                            
                    except Exception as e:
                        print(f"   ❌ {symbol} 報告生成錯誤: {e}")

                # 重設計時器
                timers['report'] = now + timedelta(seconds=config.INTERVAL_PERIODIC_REPORT)
                
                # 🔥 優化：任務結束後多印一行空行
                print("-" * 30 + "\n")

            # 極速迴圈休息
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 程式手動停止")
            break
        except Exception as e:
            print(f"❌ 主迴圈發生錯誤: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()