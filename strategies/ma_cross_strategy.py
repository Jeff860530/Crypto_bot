# strategies/ma_cross_strategy.py
from .base_strategy import BaseStrategy

class MACrossStrategy(BaseStrategy):
    def analyze(self, df, context):
        # 從 context 取得已經算好的指標 (由 MarketDataService 提供)
        # 🔥 修改：使用 .get() 的第二個參數給予預設值，防止 None
        trend = context.get('trend_signal', 'NEUTRAL') # LONG / SHORT
        ma_fast = context.get('ma_fast', 0.0)
        ma_slow = context.get('ma_slow', 0.0)
        
        # 再次確保如果是 None 還是要轉成 float (雙重保險)
        if ma_fast is None: ma_fast = 0.0
        if ma_slow is None: ma_slow = 0.0

        signal = "NEUTRAL"
        reason = ""
        
        # 簡單的黃金交叉/死亡交叉邏輯
        if trend == "LONG":
            signal = "LONG"
            reason = f"MA金叉 (Fast: {ma_fast:.2f} > Slow: {ma_slow:.2f})"
        elif trend == "SHORT":
            signal = "SHORT"
            reason = f"MA死叉 (Fast: {ma_fast:.2f} < Slow: {ma_slow:.2f})"
            
        return {
            "signal": signal,
            "reason": reason,
            "stop_loss": None,   # 可在此加入 ATR 止損邏輯
            "take_profit": None
        }