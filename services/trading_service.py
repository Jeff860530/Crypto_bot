import sys
import os

# 🔥 取得目前檔案的路徑，並將「上一層目錄」加入 Python 搜尋路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 接著才是原本的 import
import config
from datetime import datetime
import time

# 引入核心工具
from services.market_data_service import MarketDataService
from utils.data_loader import BingXLoader
from utils.executor import BingXExecutor
from utils.trade_logger import TradeLogger

# 引入策略對照表
from strategies import STRATEGY_MAP

class TradingService:
    def __init__(self, report_service=None, email_service=None):
        """
        整合所有交易相關的元件 (支援多策略)
        """
        self.report_service = report_service
        self.email_service = email_service
        
        self.market_data_service = MarketDataService()
        self.loader = BingXLoader()
        self.executor = BingXExecutor(self.loader.exchange)
        self.logger = TradeLogger()

        # 初始化多策略系統
        self.strategies = []
        print(f"⚙️ 正在載入策略: {config.ACTIVE_STRATEGIES}")
        
        for strategy_name in config.ACTIVE_STRATEGIES:
            strategy_class = STRATEGY_MAP.get(strategy_name)
            if strategy_class:
                self.strategies.append(strategy_class()) # 實例化策略物件
            else:
                print(f"⚠️ 警告: 找不到策略 {strategy_name}，請檢查拼字或 __init__.py")

        self.symbols = config.COIN_LIST

    def _get_combined_signal(self, df, context):
        """
        🔥 核心：整合所有策略的投票結果
        回傳: (final_signal, concise_reason, detailed_logs)
        """
        final_signal = "NEUTRAL"
        final_reasons = [] # 給下單紀錄用的簡潔理由
        detailed_logs = [] # 🔥 給 Log 顯示用的詳細清單
        
        long_votes = 0
        short_votes = 0
        
        for strategy in self.strategies:
            try:
                result = strategy.analyze(df, context)
                sig = result['signal']
                reason = result['reason']
                name = strategy.__class__.__name__
                
                # 1. 收集詳細 Log
                # 格式: [策略名] 訊號: 理由
                detailed_logs.append(f"[{name}] {sig}: {reason}")

                # 2. 統計投票
                if sig == "LONG":
                    long_votes += 1
                    final_reasons.append(f"[{name}] {reason}")
                elif sig == "SHORT":
                    short_votes += 1
                    final_reasons.append(f"[{name}] {reason}")
            except Exception as e:
                print(f"❌ 策略 {strategy} 執行錯誤: {e}")
                detailed_logs.append(f"[{strategy.__class__.__name__}] ERROR: {e}")
        
        # --- 決策邏輯 ---
        if long_votes > 0 and short_votes > 0:
            final_signal = "NEUTRAL"
            final_reasons = ["⚠️ 策略衝突 (多空互斥)，系統選擇觀望"]
        elif long_votes > 0:
            final_signal = "LONG"
        elif short_votes > 0:
            final_signal = "SHORT"
            
        return final_signal, " | ".join(final_reasons), detailed_logs

    def run_cycle(self):
        """
        執行一次完整的交易循環
        """
        print(f"🔨 TradingService: 開始掃描市場 ({config.TRADE_TIMEFRAME})...")

        for symbol in self.symbols:
            try:
                # Step 1: 獲取數據
                df = self.loader.fetch_data(
                    timeframe=config.TRADE_TIMEFRAME, 
                    symbol=symbol, 
                    limit=200
                )
                
                if df is None or df.empty:
                    print(f"   ⚠️ 跳過 {symbol}: 無法獲取數據")
                    continue

                # Step 2: 計算指標
                context = self.market_data_service.analyze_technicals(df)
                
                # 防呆：如果計算失敗回傳空字典，直接跳過
                if not context:
                    print(f"   ⚠️ 跳過 {symbol}: 技術指標計算失敗 (可能數據不足)")
                    continue
                    
                context['symbol'] = symbol
                
                # Step 3: 檢查倉位
                current_position = self.executor.get_open_position(symbol)
                
                # Step 4: 呼叫多策略整合邏輯
                # 🔥 這裡接收 3 個回傳值
                signal, reason, detailed_logs = self._get_combined_signal(df, context)
                
                close_price = context.get('close', 0.0)
                order_amount = config.ORDER_SIZES.get(symbol, config.ORDER_AMOUNT)

                # 解析 ZigZag 資訊 (結構)
                pivots = context.get('pivots', [])
                pivot_status = "無結構"
                if pivots and len(pivots) > 0:
                    last_p = pivots[-1]
                    pivot_status = f"{last_p.get('type')}@{last_p.get('price'):.1f}"

                pos_status = current_position if current_position else "EMPTY"
                
                # 🔥 優化顯示：第一行顯示總結，下面列出所有策略詳情
                print(f"   [{symbol}] ${close_price:.2f} | 總訊號:{signal} | 持倉:{pos_status} | 結構:{pivot_status}")
                for log in detailed_logs:
                    print(f"        👉 {log}")

                # --- 進場邏輯 ---
                if current_position is None:
                    if signal == "LONG":
                        self._execute_trade("buy", symbol, order_amount, close_price, reason, context)
                    elif signal == "SHORT":
                        self._execute_trade("sell", symbol, order_amount, close_price, reason, context)
                
                # --- 出場邏輯 ---
                elif current_position == "LONG" and signal == "SHORT":
                    self._close_trade(symbol, close_price, "訊號反轉平多")
                
                elif current_position == "SHORT" and signal == "LONG":
                    self._close_trade(symbol, close_price, "訊號反轉平空")

            except Exception as e:
                print(f"   ❌ 處理 {symbol} 時發生錯誤: {e}")
                import traceback
                traceback.print_exc()

    def _execute_trade(self, side, symbol, amount, price, tag, context):
        """執行下單"""
        print(f"   🚀 觸發下單: {symbol} {side} ({tag})")
        order = self.executor.place_order(side, symbol, amount)
        
        if order or config.DRY_RUN:
            self.logger.log(side.upper(), price, amount, tag, symbol=symbol)
            if self.report_service and self.email_service:
                context['action'] = side.upper()
                context['price'] = price
                html_report = self.report_service.generate_entry_report(context)
                subject = f"🚀 交易快訊: {symbol} {side.upper()}"
                self.email_service.send_report(subject, html_report)

    def _close_trade(self, symbol, price, tag):
        """執行平倉"""
        print(f"   👋 觸發平倉: {symbol} ({tag})")
        self.executor.close_position(symbol)
        self.logger.log("CLOSE", price, 0, tag, symbol=symbol)