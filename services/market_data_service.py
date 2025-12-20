import pandas as pd
import pandas_ta as ta
from datetime import datetime
from typing import Dict, Any

class MarketDataService:
    def __init__(self):
        # --- 1. 基礎設定參數 ---
        # 趨勢與動能
        self.rsi_length = 14
        self.ma_fast = 7
        self.ma_slow = 25
        self.bb_length = 20
        self.bb_std = 2.0
        
        # MACD 設定 (標準參數 12, 26, 9)
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # 🔥 KDJ 設定 (標準參數 9, 3, 3)
        # 通常設定為 (9, 3) 即可，pandas_ta 會自動處理
        self.kdj_length = 9
        self.kdj_signal = 3
        
        # ATR (波動率) 設定
        self.atr_length = 14

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

        # ==========================================
        # 1. 計算指標 (使用 pandas_ta)
        # ==========================================
        
        # --- A. 基礎趨勢 (MA & BB & RSI) ---
        df['rsi'] = ta.rsi(df['close'], length=self.rsi_length)
        df['ma_fast'] = ta.sma(df['close'], length=self.ma_fast)
        df['ma_slow'] = ta.sma(df['close'], length=self.ma_slow)
        
        bbands = ta.bbands(df['close'], length=self.bb_length, std=self.bb_std)
        df['bb_upper'] = bbands.iloc[:, 2] 
        df['bb_lower'] = bbands.iloc[:, 0] 

        # --- B. 進階趨勢 (MACD) ---
        macd = ta.macd(df['close'], fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
        df['macd_line'] = macd.iloc[:, 0]   # DIF
        df['macd_hist'] = macd.iloc[:, 1]   # OSC
        df['macd_signal'] = macd.iloc[:, 2] # DEM

        # --- C. 🔥 動能震盪 (KDJ) ---
        # 使用 pandas_ta 的 kdj 方法
        # 回傳順序通常是 K, D, J (需注意 pandas_ta 版本，通常 K在0, D在1, J在2)
        kdj = ta.kdj(df['high'], df['low'], df['close'], length=self.kdj_length, signal=self.kdj_signal)
        df['kdj_k'] = kdj.iloc[:, 0]
        df['kdj_d'] = kdj.iloc[:, 1]
        df['kdj_j'] = kdj.iloc[:, 2] # 🔥 新增 J 線

        # --- D. 波動率 (ATR) ---
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=self.atr_length)

        # ==========================================
        # 2. 取得最新數據與邏輯判斷
        # ==========================================
        row = df.iloc[-1]
        
        # --- MA 趨勢判斷 ---
        if row['ma_fast'] > row['ma_slow']:
            trend = "多頭排列 (Bullish)"
            trend_signal = "LONG"
        else:
            trend = "空頭排列 (Bearish)"
            trend_signal = "SHORT"

        # --- 布林位置判斷 ---
        bb_pos = "中軸震盪"
        if row['close'] >= row['bb_upper']: bb_pos = "觸及上軌 (壓力/超買)"
        elif row['close'] <= row['bb_lower']: bb_pos = "觸及下軌 (支撐/超賣)"

        # --- MACD 狀態 ---
        macd_status = "多頭動能增強" if row['macd_hist'] > 0 else "空頭動能增強"
        if row['macd_line'] > row['macd_signal']: macd_cross = "黃金交叉 (看漲)"
        else: macd_cross = "死亡交叉 (看跌)"

        # --- 🔥 KDJ 狀態 ---
        k_val, d_val, j_val = row['kdj_k'], row['kdj_d'], row['kdj_j']
        
        # 1. 判斷金叉死叉
        kdj_cross = "K大於D (金叉傾向)" if k_val > d_val else "K小於D (死叉傾向)"
        
        # 2. 判斷 J 線異常區 (敏感度最高)
        kdj_status = "正常區間"
        if j_val > 100: kdj_status = "J線超買 (>100) 隨時回調"
        elif j_val < 0: kdj_status = "J線超賣 (<0) 隨時反彈"
        elif k_val > 80: kdj_status = "KD超買區"
        elif k_val < 20: kdj_status = "KD超賣區"

        # --- ATR 止損建議 ---
        atr_stop_loss_distance = row['atr'] * 2
        stop_loss_long = row['close'] - atr_stop_loss_distance
        stop_loss_short = row['close'] + atr_stop_loss_distance
        
        # 計算風險百分比
        risk_pct = (atr_stop_loss_distance / row['close']) * 100

        # ==========================================
        # 3. 生成給 AI 看的摘要文字 (Prompt Material)
        # ==========================================
        ta_text = f"""
        【最新價格數據】
        - 現價: {row['close']:.2f}
        
        【趨勢指標 (Trend)】
        - MA均線: {trend} | MA{self.ma_fast}={row['ma_fast']:.2f}, MA{self.ma_slow}={row['ma_slow']:.2f}
        - MACD指標: {macd_cross} | 柱狀圖: {row['macd_hist']:.4f} ({macd_status})
        
        【動能與震盪 (Momentum)】
        - RSI({self.rsi_length}): {row['rsi']:.1f} (強弱分界 50)
        - KDJ指標: K={k_val:.1f}, D={d_val:.1f}, J={j_val:.1f}
          狀態: {kdj_status} | 訊號: {kdj_cross}
          (註: J>100 為鈍化超買，J<0 為鈍化超賣，反應比KD更快)
        - 布林帶: {bb_pos} (上軌:{row['bb_upper']:.2f} / 下軌:{row['bb_lower']:.2f})
        
        【波動率與風控 (Volatility)】
        - ATR({self.atr_length}): {row['atr']:.4f}
        - [多單] 止損參考: {stop_loss_long:.2f} (風險: -{risk_pct:.2f}%)
        - [空單] 止損參考: {stop_loss_short:.2f} (風險: -{risk_pct:.2f}%)
        """

        # ==========================================
        # 4. 返回完整字典
        # ==========================================
        return {
            "close": row['close'],
            "rsi": row['rsi'],
            "ma_fast": row['ma_fast'],
            "ma_slow": row['ma_slow'],
            "bb_upper": row['bb_upper'],
            "bb_lower": row['bb_lower'],
            "macd_line": row['macd_line'],
            "macd_signal": row['macd_signal'],
            "macd_hist": row['macd_hist'],
            "kdj_k": row['kdj_k'],
            "kdj_d": row['kdj_d'],
            "kdj_j": row['kdj_j'],
            "atr": row['atr'],
            "trend": trend,
            "trend_signal": trend_signal,
            "bb_pos": bb_pos,
            "technical_analysis_text": ta_text, 
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

if __name__ == "__main__":
    # 測試代碼略... (同上)
    pass