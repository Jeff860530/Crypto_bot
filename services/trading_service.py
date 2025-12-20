import config
from datetime import datetime
import time

# 引入核心工具
from services.market_data_service import MarketDataService
from utils.data_loader import BingXLoader
from utils.executor import BingXExecutor
from utils.trade_logger import TradeLogger

class TradingService:
    def __init__(self, report_service=None, email_service=None):
        """
        整合所有交易相關的元件
        """
        self.report_service = report_service
        self.email_service = email_service
        
        # 1. 數據服務 (計算指標)
        self.market_data_service = MarketDataService()
        
        # 2. 交易所連線 (BingX)
        self.loader = BingXLoader()
        self.executor = BingXExecutor(self.loader.exchange)
        
        # 3. 日誌記錄
        self.logger = TradeLogger()

        self.symbols = config.COIN_LIST

    def run_cycle(self):
        """
        執行一次完整的交易循環
        """
        print(f"🔨 TradingService: 開始掃描市場 ({config.TRADE_TIMEFRAME})...")

        for symbol in self.symbols:
            try:
                # ----------------------------------------
                # Step 1: 獲取真實數據
                # ----------------------------------------
                df = self.loader.fetch_data(
                    timeframe=config.TRADE_TIMEFRAME, 
                    symbol=symbol, 
                    limit=50 # 只需要足夠計算 MA25 即可
                )
                
                if df is None or df.empty:
                    print(f"   ⚠️ 跳過 {symbol}: 無法獲取數據")
                    continue

                # ----------------------------------------
                # Step 2: 計算技術指標 (AIContext)
                # ----------------------------------------
                context = self.market_data_service.analyze_technicals(df)
                context['symbol'] = symbol
                
                # ----------------------------------------
                # Step 3: 檢查當前倉位
                # ----------------------------------------
                # 模擬模式下，executor 會從記憶體讀取；真實模式會打 API
                current_position = self.executor.get_open_position(symbol)
                
                # ----------------------------------------
                # Step 4: 策略邏輯 (Golden Cross / Death Cross)
                # ----------------------------------------
                signal = context.get('trend_signal') # LONG / SHORT
                close_price = context.get('close')
                
                # 取得該幣種設定的下單量
                order_amount = config.ORDER_SIZES.get(symbol, config.ORDER_AMOUNT)

                # 印出簡易狀態
                pos_status = current_position if current_position else "EMPTY"
                print(f"   [{symbol}] ${close_price:.2f} | 訊號:{signal} | 持倉:{pos_status} | RSI:{context['rsi']:.1f}")

                # --- 進場邏輯 ---
                if current_position is None:
                    if signal == "LONG":
                        self._execute_trade("buy", symbol, order_amount, close_price, "MA金叉做多", context)
                    elif signal == "SHORT":
                        self._execute_trade("sell", symbol, order_amount, close_price, "MA死叉做空", context)
                
                # --- 出場邏輯 (簡單反向平倉) ---
                # 如果持多單，但訊號轉空 -> 平倉
                elif current_position == "LONG" and signal == "SHORT":
                    self._close_trade(symbol, close_price, "訊號反轉平多")
                
                # 如果持空單，但訊號轉多 -> 平倉
                elif current_position == "SHORT" and signal == "LONG":
                    self._close_trade(symbol, close_price, "訊號反轉平空")

            except Exception as e:
                print(f"   ❌ 處理 {symbol} 時發生錯誤: {e}")

    def _execute_trade(self, side, symbol, amount, price, tag, context):
        """執行下單並發送通知"""
        print(f"   🚀 觸發下單: {symbol} {side} ({tag})")
        
        # 1. 執行下單
        order = self.executor.place_order(side, symbol, amount)
        
        if order or config.DRY_RUN:
            # 2. 寫入 Log
            self.logger.log(side.upper(), price, amount, tag, symbol=symbol)
            
            # 3. 發送 AI 報告與 Email
            if self.report_service and self.email_service:
                # 補充 context 資訊
                context['action'] = side.upper()
                context['price'] = price
                
                html_report = self.report_service.generate_entry_report(context)
                subject = f"🚀 交易快訊: {symbol} {side.upper()} ({tag})"
                self.email_service.send_report(subject, html_report)

    def _close_trade(self, symbol, price, tag):
        """執行平倉"""
        print(f"   👋 觸發平倉: {symbol} ({tag})")
        
        # 1. 執行平倉
        self.executor.close_position(symbol)
        
        # 2. 寫入 Log (平倉暫時記錄 amount=0 或依據邏輯調整)
        self.logger.log("CLOSE", price, 0, tag, symbol=symbol)