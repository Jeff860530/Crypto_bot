#services/market_data_service.py
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from typing import Dict, Any

class MarketDataService:
    def __init__(self):
        # 這裡可以放一些全域的指標設定參數
        self.rsi_length = 14
        self.ma_fast = 7
        self.ma_slow = 25
        self.bb_length = 20

    def analyze_technicals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        計算技術指標並返回結構化數據與文字描述
        :param df: 包含 Open, High, Low, Close 的 DataFrame
        :return: 包含數值與文字摘要的字典
        """
        if df is None or df.empty:
            print("⚠️ 警告: 傳入的 DataFrame 為空")
            return {}

        # 複製一份以免修改到原始資料
        df = df.copy()

        # 1. 計算指標 (使用 pandas_ta)
        # RSI
        df['rsi'] = ta.rsi(df['close'], length=self.rsi_length)
        
        # MA (移動平均)
        df['ma_fast'] = ta.sma(df['close'], length=self.ma_fast)
        df['ma_slow'] = ta.sma(df['close'], length=self.ma_slow)
        
        # Bollinger Bands (布林通道)
        bbands = ta.bbands(df['close'], length=self.bb_length)
        # pandas_ta 的 bbands 欄位名稱通常是 BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
        # 為了方便，我們重新命名或直接取值
        df['bb_upper'] = bbands.iloc[:, 2] # 上軌
        df['bb_lower'] = bbands.iloc[:, 0] # 下軌

        # 2. 取得最新一筆數據 (Latest Row)
        row = df.iloc[-1]

        # 3. 邏輯判斷 (Rule-based Logic)
        
        # 趨勢判斷
        if row['ma_fast'] > row['ma_slow']:
            trend = "多頭排列 (Bullish)"
            trend_signal = "LONG"
        else:
            trend = "空頭排列 (Bearish)"
            trend_signal = "SHORT"

        # 布林位置判斷
        bb_pos = "中軸震盪"
        if row['close'] >= row['bb_upper']:
            bb_pos = "觸及上軌 (壓力區/超買)"
        elif row['close'] <= row['bb_lower']:
            bb_pos = "觸及下軌 (支撐區/超賣)"

        # 4. 生成給 AI 看的摘要文字 (Prompt Material)
        # 這裡的格式越清楚，AI 寫出來的報告越精準
        ta_text = f"""
        【最新價格數據】
        - 現價: {row['close']:.2f}
        
        【趨勢指標】
        - MA狀態: {trend}
        - 短期MA({self.ma_fast}): {row['ma_fast']:.2f}
        - 長期MA({self.ma_slow}): {row['ma_slow']:.2f}
        
        【動能與波動】
        - RSI({self.rsi_length}): {row['rsi']:.2f}
        - 布林帶狀態: {bb_pos}
          (上軌: {row['bb_upper']:.2f} / 下軌: {row['bb_lower']:.2f})
        """

        # 5. 返回完整字典
        return {
            "close": row['close'],
            "rsi": row['rsi'],
            "ma_fast": row['ma_fast'],
            "ma_slow": row['ma_slow'],
            "bb_upper": row['bb_upper'],
            "bb_lower": row['bb_lower'],
            "trend": trend,
            "trend_signal": trend_signal, # 方便程式邏輯做 if/else
            "bb_pos": bb_pos,
            "technical_analysis_text": ta_text, # 這是專門餵給 AI 的
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# 用法測試
if __name__ == "__main__":
    # 造一個假的 DataFrame 測試
    data = {
        'close': [3000, 3010, 3020, 3050, 3040, 3060, 3080, 3100, 3120, 3110, 3150, 3200, 3180, 3190, 3210, 3250, 3300, 3280, 3290, 3310, 3350, 3400, 3380, 3360, 3390, 3410]
    }
    df_test = pd.DataFrame(data)
    
    service = MarketDataService()
    result = service.analyze_technicals(df_test)
    
    print("--- AI 會看到的文字 ---")
    print(result['technical_analysis_text'])