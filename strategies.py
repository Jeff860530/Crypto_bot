import pandas_ta as ta
import config

class RuleBasedStrategy:
    def __init__(self, short_window=config.SMA_SHORT, long_window=config.SMA_LONG):
        self.short_window = short_window
        self.long_window = long_window

    def analyze(self, df):
        """
        傳入 DataFrame，回傳訊號與詳細資訊
        """
        if df is None or len(df) < self.long_window:
            return {"action": "DATA_ERROR", "info": "數據不足"}

        # 計算指標
        df['ma_short'] = ta.sma(df['close'], length=self.short_window)
        df['ma_long'] = ta.sma(df['close'], length=self.long_window)

        # 取得最後一根 (最新) 與 倒數第二根 (確認交叉用)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        signal = "HOLD"
        info = f"S:{last_row['ma_short']:.2f} | L:{last_row['ma_long']:.2f}"

        # 邏輯：黃金交叉 (短期向上突破長期) -> 做多
        if prev_row['ma_short'] <= prev_row['ma_long'] and last_row['ma_short'] > last_row['ma_long']:
            signal = "LONG"
        
        # 邏輯：死亡交叉 (短期向下突破長期) -> 做空
        elif prev_row['ma_short'] >= prev_row['ma_long'] and last_row['ma_short'] < last_row['ma_long']:
            signal = "SHORT"
        
        # 目前狀態檢查 (若不是交叉點，但處於多頭/空頭排列)
        elif last_row['ma_short'] > last_row['ma_long']:
            info += " (多頭排列中)"
        elif last_row['ma_short'] < last_row['ma_long']:
            info += " (空頭排列中)"

        return {"action": signal, "info": info, "price": last_row['close'], "time": last_row['timestamp']}