import google.generativeai as genai
import pandas_ta as ta
import config
from datetime import datetime

class AIReportGenerator:
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # 讀取 config 中的模型設定
        # print(f"🧠 AI Reporter 使用模型: {config.GEMINI_MODEL_NAME}")
        self.model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)

    def _prepare_data(self, df):
        """共用的數據處理函式"""
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['ma7'] = ta.sma(df['close'], length=7)
        df['ma25'] = ta.sma(df['close'], length=25)
        upper, middle, lower = ta.bbands(df['close'], length=20).iloc[:, 0], ta.bbands(df['close'], length=20).iloc[:, 1], ta.bbands(df['close'], length=20).iloc[:, 2]
        
        row = df.iloc[-1]
        trend = "多頭排列 (Bullish)" if row['ma7'] > row['ma25'] else "空頭排列 (Bearish)"
        
        bb_pos = "中軸附近"
        if row['close'] >= upper.iloc[-1]: bb_pos = "觸及上軌 (壓力)"
        elif row['close'] <= lower.iloc[-1]: bb_pos = "觸及下軌 (支撐)"

        return row, trend, bb_pos, upper.iloc[-1], lower.iloc[-1]

    # 🔥 修正 1: 這裡必須接收 symbol 參數
    def generate_entry_report(self, df, action, price, symbol):
        """交易進場報告 (Event-based)"""
        row, trend, bb_pos, up, low = self._prepare_data(df)
        
        market_context = f"""
        時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        交易對: {symbol} 
        動作: {action} (價格 {price})
        
        【技術數據 ({config.TRADE_TIMEFRAME})】
        - RSI(14): {row['rsi']:.1f}
        - MA狀態: {trend}
        - 布林位置: {bb_pos}
        """
        
        prompt = f"""
        請撰寫一份 **HTML 格式** 的「交易進場快訊」。
        背景色: {'#e6f4ea' if 'LONG' in action else '#fce8e6'}。
        
        數據:
        {market_context}
        
        內容要求:
        1. 標題: 交易訊號通知 ({symbol} {action})
        2. 表格: 顯示 RSI, MA, 布林數據。
        3. 分析: 簡述為何觸發此策略。
        4. 建議: 止損與止盈參考價。
        
        只輸出 HTML。
        """
        return self._generate(prompt)

    # 🔥 修正 2: 這裡必須接收 symbol 參數
    def generate_market_report(self, df, symbol):
        """定期市場分析報告 (Time-based)"""
        row, trend, bb_pos, up, low = self._prepare_data(df)
        
        market_context = f"""
        報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        交易對: {symbol}
        分析週期: {config.REPORT_TIMEFRAME} (大時框分析)
        
        【技術數據】
        - 收盤價: {row['close']}
        - RSI(14): {row['rsi']:.1f}
        - MA(7): {row['ma7']:.4f} | MA(25): {row['ma25']:.4f}
        - 趨勢: {trend}
        - 布林帶: 上{up:.2f} / 下{low:.2f}
        - 位置: {bb_pos}
        """
        
        prompt = f"""
        請撰寫一份 **HTML 格式** 的「定期市場趨勢週報」。
        
        數據:
        {market_context}
        
        內容要求:
        1. **標題**: 市場趨勢掃描 ({symbol})
        2. **市場解讀**: 
           - 目前是大趨勢多頭、空頭，還是盤整？
           - AI 對於未來 4-12 小時的走勢預判。
        3. **關鍵點位**:
           - 指出下一個關鍵支撐位與壓力位在哪裡。
        4. **操作建議**:
           - 空手者建議觀望還是進場？
           - 持倉者建議續抱還是減碼？
        
        風格要求: 像一份專業的投顧日報，使用藍色/灰色系 (#e8f0fe) 作為標題背景。
        只輸出 HTML。
        """
        return self._generate(prompt)

    def _generate(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            return response.text.replace("```html", "").replace("```", "").strip()
        except Exception as e:
            print(f"❌ AI 報告生成失敗: {e}")
            raise e # 拋出錯誤讓外層知道，方便重試或記錄

# ==========================================
# 🔥 這裡就是你要的查詢功能
# ==========================================
if __name__ == "__main__":
    print("\n🔍 正在連線 Google Gemini API 查詢可用模型...")
    print(f"🔑 使用 Key: {config.GEMINI_API_KEY[:5]}...{config.GEMINI_API_KEY[-5:]}")
    print(f"🎯 目前 Config 設定: {config.GEMINI_MODEL_NAME}")
    print("-" * 50)

    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        models = list(genai.list_models())
        
        count = 0
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                # 簡單的清理名稱，把 'models/' 去掉方便閱讀
                clean_name = m.name.replace("models/", "")
                
                # 如果是目前設定的模型，加上星號 ⭐
                if clean_name == config.GEMINI_MODEL_NAME:
                    print(f"⭐ {m.name} (使用中)")
                else:
                    print(f"   {m.name}")
                count += 1
        
        print("-" * 50)
        print(f"✅ 查詢完成，共找到 {count} 個可用模型。")
        print("💡 提示: 若要更換模型，請將名稱(不含 models/) 複製到 config.py")

    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
        print("⚠️ 請檢查 config.py 裡的 API Key 是否正確。")