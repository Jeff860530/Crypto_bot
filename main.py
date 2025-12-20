import time
from datetime import datetime, timedelta
import config

# 引入服務模組
from services.trading_service import TradingService
from services.report_service import ReportService
from services.qa_service import QAService
from services.email_service import EmailService
from services.market_data_service import MarketDataService

def main():
    print(f"🤖 Crypto Bot 架構重構版啟動...")

    # 1. 初始化服務 (指揮官組裝工具)
    mailer = EmailService()           
    reporter = ReportService()        
    market_data = MarketDataService() 
    qa_service = QAService("questions.json")
    
    # 將 reporter 和 mailer 注入給 trader (如果未來需要)
    trader = TradingService(report_service=reporter, email_service=mailer) 

    # 2. 設定時間鎖
    timers = {
        'trade': datetime.now(),         # 馬上執行一次
        'report': datetime.now(),        # 馬上執行一次
        'qa': datetime.now()             # 馬上執行一次
    }

    print("🚀 系統進入極速監聽模式...")

    while True:
        try:
            now = datetime.now()

            # --- 任務 1: QA 問答 (優先級最高，每 5 秒) ---
            if config.ENABLE_QA_SYSTEM and now >= timers['qa']:
                # 將 reporter 和 mailer "注入" 給 qa_service
                qa_service.process_pending_questions(ai_reporter=reporter, mailer=mailer)
                timers['qa'] = now + timedelta(seconds=5)

            # --- 任務 2: 交易 (每 15 分鐘) ---
            if now >= timers['trade']:
                print(f"💰 執行交易策略檢查... {now.strftime('%H:%M')}")
                trader.run_cycle() 
                timers['trade'] = now + timedelta(minutes=15)

            # --- 任務 3: 定期報告 (每 60 分鐘) ---
            if config.ENABLE_PERIODIC_REPORT and now >= timers['report']:
                print(f"📊 執行定期市場報告... {now.strftime('%H:%M')}")
                
                # 範例邏輯 (你可以之後再解除註解並修改)
                # target_symbol = "ETHUSDT"
                # df = get_klines(target_symbol) # 需自行實作獲取資料
                # if not df.empty:
                #     context = market_data.analyze_technicals(df)
                #     context['symbol'] = target_symbol
                #     html = reporter.generate_market_report(context)
                #     mailer.send_report(f"📅 市場週報: {target_symbol}", html)
                
                timers['report'] = now + timedelta(minutes=config.REPORT_INTERVAL_MINUTES)

            # 極速迴圈休息
            time.sleep(3)

        # 🔥 重點在這裡：try 區塊結束後，一定要接 except
        except KeyboardInterrupt:
            print("\n🛑 程式手動停止")
            break
        except Exception as e:
            print(f"❌ 主迴圈發生錯誤: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()