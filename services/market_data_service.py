# services/market_data_service.py
import sys
import os
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from typing import Dict, Any, Optional

# 🔥 取得目前檔案的路徑，並將「上一層目錄」加入 Python 搜尋路徑
# 這樣才能正確引入 config 和 utils
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import config
from utils.zigzag import ZigZagIdentifier  # 🔥 引入 ZigZag 工具

class MarketDataService:
    def __init__(self):
        # --- 1. 基礎設定參數 (從 config 讀取) ---
        
        # A. 趨勢 (Trend)
        self.ma_fast = getattr(config, 'SMA_SHORT', 7)
        self.ma_slow = getattr(config, 'SMA_LONG', 25)
        self.bb_length = 20
        self.bb_std = 2.0
        
        # MACD
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # B. 動能 (Momentum)
        self.rsi_length = 14
        self.kdj_length = getattr(config, 'KDJ_LENGTH', 9)
        self.kdj_signal = getattr(config, 'KDJ_SIGNAL', 3)
        
        # C. 波動率 (Volatility)
        self.atr_length = 14
        
        # D. 成交量 (Volume)
        self.mfi_length = 14
        
        # E. 🔥 結構 (Structure / ZigZag)
        self.zigzag_order = getattr(config, 'ZIGZAG_ORDER', 5)
        # 初始化 ZigZag 識別器
        self.zigzag = ZigZagIdentifier(order=self.zigzag_order)

    def analyze_technicals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        計算技術指標並返回結構化數據與文字描述
        :param df: 包含 Open, High, Low, Close, Volume 的 DataFrame
        :return: 包含數值與文字摘要的字典
        """
        # 1. 基礎資料檢查
        if df is None or df.empty:
            print("⚠️ 警告: 傳入的 DataFrame 為空")
            return {}
        
        # 確保資料長度足夠計算長天期指標 (至少要比 ma_slow 長)
        min_required_len = max(self.ma_slow, self.macd_slow, 30)
        if len(df) < min_required_len:
            print(f"⚠️ 警告: 數據長度不足 ({len(df)} < {min_required_len})，指標可能不準確")

        # 複製並處理索引 (VWAP 需要時間索引)
        df = df.copy()
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

        # ==========================================
        # 2. 計算指標 (使用 pandas_ta 擴充方法)
        # ==========================================
        try:
            # --- A. 趨勢與波段 ---
            df['ma_fast'] = ta.sma(df['close'], length=self.ma_fast)
            df['ma_slow'] = ta.sma(df['close'], length=self.ma_slow)
            
            # BBands
            bbands = ta.bbands(df['close'], length=self.bb_length, std=self.bb_std)
            if bbands is not None:
                df['bb_lower'] = bbands.iloc[:, 0]
                df['bb_upper'] = bbands.iloc[:, 2]
            else:
                df['bb_lower'], df['bb_upper'] = df['close'], df['close']

            # MACD
            macd = ta.macd(df['close'], fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
            if macd is not None:
                df['macd_line'] = macd.iloc[:, 0]   # DIF
                df['macd_hist'] = macd.iloc[:, 1]   # Histogram
                df['macd_signal'] = macd.iloc[:, 2] # Signal
            else:
                df['macd_line'], df['macd_hist'], df['macd_signal'] = 0, 0, 0

            # --- B. 動能 ---
            df['rsi'] = ta.rsi(df['close'], length=self.rsi_length)
            
            # KDJ
            kdj = ta.kdj(df['high'], df['low'], df['close'], length=self.kdj_length, signal=self.kdj_signal)
            if kdj is not None:
                df['kdj_k'] = kdj.iloc[:, 0]
                df['kdj_d'] = kdj.iloc[:, 1]
                df['kdj_j'] = kdj.iloc[:, 2]
            else:
                df['kdj_k'], df['kdj_d'], df['kdj_j'] = 50, 50, 50

            # --- C. 波動率 ---
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=self.atr_length)

            # --- D. 成交量指標 ---
            df['obv'] = ta.obv(df['close'], df['volume'])
            df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=self.mfi_length)
            
            # VWAP (需要 Exception Handling 因為依賴時間索引)
            try:
                vwap = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
                df['vwap'] = vwap if vwap is not None else df['ma_slow']
            except Exception:
                # 若計算失敗 (例如 index 不是 datetime)，降級使用 MA 或 Close
                df['vwap'] = df['ma_slow'] if 'ma_slow' in df else df['close']

        except Exception as e:
            print(f"❌ 指標計算發生錯誤: {e}")
            # 發生嚴重錯誤時，直接回傳空字典或進行降級處理
            return {}

        # ==========================================
        # 3. 數據清理與取值
        # ==========================================
        # 使用 ffill 填補 NaN (前端計算指標常有 NaN)
        df = df.ffill().fillna(0)
        
        # 取得最後一筆數據
        row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else row
        
        # 取值 Helper (轉為 float 避免 numpy type 問題)
        close = float(row['close'])
        ma_fast = float(row['ma_fast'])
        ma_slow = float(row['ma_slow'])
        
        # --- 趨勢判斷 ---
        if ma_fast > ma_slow:
            trend = "多頭排列 (Bullish)"
            trend_signal = "LONG"
        else:
            trend = "空頭排列 (Bearish)"
            trend_signal = "SHORT"

        # --- BBands ---
        bb_upper = float(row['bb_upper'])
        bb_lower = float(row['bb_lower'])
        bb_pos = "中軸震盪"
        if close >= bb_upper: bb_pos = "觸及上軌 (壓力/超買)"
        elif close <= bb_lower: bb_pos = "觸及下軌 (支撐/超賣)"

        # --- KDJ ---
        k_val = float(row['kdj_k'])
        d_val = float(row['kdj_d'])
        j_val = float(row['kdj_j'])
        
        kdj_cross = "K>D (金叉傾向)" if k_val > d_val else "K<D (死叉傾向)"
        kdj_status = "正常"
        if j_val > 100: kdj_status = "J線超買 (>100)"
        elif j_val < 0: kdj_status = "J線超賣 (<0)"

        # --- 風控 (ATR) ---
        atr_val = float(row['atr'])
        if atr_val <= 0: atr_val = close * 0.01 # 防呆
        
        atr_stop_loss = atr_val * 2
        sl_long = close - atr_stop_loss
        sl_short = close + atr_stop_loss
        risk_pct = (atr_stop_loss / close) * 100

        # --- 成交量 (VWAP/MFI/OBV) ---
        vwap_val = float(row['vwap'])
        if vwap_val == 0: vwap_val = close
        
        vwap_status = "價格 > VWAP (強勢)" if close > vwap_val else "價格 < VWAP (弱勢)"
        
        mfi_val = float(row['mfi'])
        mfi_status = "中性"
        if mfi_val > 80: mfi_status = "資金過熱 (超買 >80)"
        elif mfi_val < 20: mfi_status = "資金冷卻 (超賣 <20)"
        
        obv_val = float(row['obv'])
        prev_obv = float(prev_row['obv'])
        obv_trend = "OBV上升 (資金流入)" if obv_val > prev_obv else "OBV下降 (資金流出)"

        # ==========================================
        # 🔥 4. ZigZag 結構分析
        # ==========================================
        # 取得最近 5 個轉折點 (用來判斷 XABCD)
        try:
            last_pivots = self.zigzag.get_last_n_pivots(df, n=5)
        except Exception as e:
            print(f"⚠️ ZigZag 計算失敗: {e}")
            last_pivots = []
        
        # 轉成文字描述給 AI
        zigzag_text = "尚無足夠轉折點"
        if len(last_pivots) >= 3:
            zigzag_text = "最近轉折點 (舊->新):\n"
            for p in last_pivots:
                # 簡單取時間 HH:MM
                p_time = str(p['time']).split(' ')[-1][:5] if ' ' in str(p['time']) else str(p['time'])
                zigzag_text += f"        - {p['type']} @ {p['price']:.2f} ({p_time})\n"

        # ==========================================
        # 5. 生成 Prompt
        # ==========================================
        ta_text = f"""
        【最新價格數據】
        - 現價: {close:.2f}
        
        【趨勢指標 (Trend)】
        - MA均線: {trend} | MA{self.ma_fast}={ma_fast:.2f}, MA{self.ma_slow}={ma_slow:.2f}
        - MACD指標: DIF={row['macd_line']:.2f}, DEM={row['macd_signal']:.2f}, 柱狀圖={row['macd_hist']:.4f}
        
        【市場結構 (Structure / ZigZag)】
        {zigzag_text}
        (註: 可用於判斷諧波型態 X-A-B-C-D 或支撐壓力位)

        【成交量分析 (Volume)】
        - VWAP (機構成本): {vwap_val:.2f} | 狀態: {vwap_status}
          (註: 日內交易重要支撐壓力，價格在 VWAP 之上偏多，之下偏空)
        - OBV (能量潮): {obv_val:.0f} | 趨勢: {obv_trend}
        - MFI (資金流向): {mfi_val:.1f} | 狀態: {mfi_status} (含量的RSI，>80超買 <20超賣)
        
        【動能與震盪 (Momentum)】
        - RSI({self.rsi_length}): {row['rsi']:.1f}
        - KDJ指標: K={k_val:.1f}, D={d_val:.1f}, J={j_val:.1f} | {kdj_status}
        - 布林帶: {bb_pos} (上軌:{bb_upper:.2f} / 下軌:{bb_lower:.2f})
        
        【波動率與風控 (Volatility)】
        - ATR({self.atr_length}): {atr_val:.4f}
        - [多單] 止損價: {sl_long:.2f} | 價差: -{atr_stop_loss:.2f} (風險: -{risk_pct:.2f}%)
        - [空單] 止損價: {sl_short:.2f} | 價差: +{atr_stop_loss:.2f} (風險: -{risk_pct:.2f}%)
        """

        # ==========================================
        # 6. 返回結果
        # ==========================================
        return {
            "close": close,
            "rsi": float(row['rsi']),
            "kdj_k": k_val,
            "kdj_j": j_val,

            "ma_fast": float(row['ma_fast']),
            "ma_slow": float(row['ma_slow']),
            
            "macd_hist": float(row['macd_hist']),
            "atr": atr_val,
            "obv": obv_val,
            "mfi": mfi_val,
            "vwap": vwap_val,
            "trend": trend,
            "trend_signal": trend_signal,
            "pivots": last_pivots, 
            "technical_analysis_text": ta_text, 
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

if __name__ == "__main__":
    # ... (測試區塊保持不變) ...
    import numpy as np
    print("🤖 啟動 MarketDataService 測試程序...")
    periods = 200 # 增加數據長度以便 ZigZag 計算
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='15min')
    np.random.seed(42)
    price_changes = np.random.randn(periods) * 10 
    close_prices = np.cumsum(price_changes) + 3000
    data = {
        'timestamp': dates,
        'open': close_prices + np.random.randint(-5, 5, periods),
        'high': close_prices + np.random.randint(5, 15, periods),
        'low': close_prices - np.random.randint(5, 15, periods),
        'close': close_prices,
        'volume': np.abs(np.random.randn(periods) * 100) + 50
    }
    df_test = pd.DataFrame(data)
    service = MarketDataService()
    try:
        print("🔍 正在計算技術指標...")
        result = service.analyze_technicals(df_test)
        if result:
            print("\n✅ 計算成功！")
            pivots = result.get('pivots', [])
            print(f"📊 抓到 {len(pivots)} 個轉折點")
            print(f"🛠️ 數值檢查: VWAP={result['vwap']:.2f}")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")