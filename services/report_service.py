import google.generativeai as genai
import config
from typing import Dict, Any

class ReportService:
    def __init__(self):
        # 設定 Gemini API
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)

    def _generate_html(self, prompt: str) -> str:
        """內部方法：呼叫 AI 並清理輸出"""
        try:
            response = self.model.generate_content(prompt)
            # 清理可能出現的 markdown 標記
            return response.text.replace("```html", "").replace("```", "").strip()
        except Exception as e:
            print(f"❌ AI 報告生成失敗: {e}")
            return "<p>⚠️ 報告生成發生錯誤，請稍後再試。</p>"

    def generate_entry_report(self, context: Dict[str, Any]) -> str:
        """
        生成交易進場報告
        """
        # 動態決定背景色
        bg_color = '#e6f4ea' if 'LONG' in context.get('trend_signal', '') else '#fce8e6'
        
        prompt = f"""
        你是一個專業的量化交易助理。請根據以下數據寫一份 **HTML 交易快訊**。
        
        【交易資訊】
        - 標的: {context.get('symbol')}
        - 訊號: {context.get('trend_signal')}
        - 現價: {context.get('close')}
        - 時間: {context.get('time')}
        
        【技術指標數據】
        {context.get('technical_analysis_text')}
        
        【輸出要求】
        1. HTML 格式，背景色使用 {bg_color}。
        2. 標題: 交易訊號 ({context.get('symbol')} {context.get('trend_signal')})。
        3. 用表格呈現技術指標數據。
        4. 根據數據簡短分析進場理由。
        5. 給出止損/止盈建議。
        6. 只輸出 HTML 代碼，不要有 Markdown。
        """
        return self._generate_html(prompt)

    def generate_market_report(self, context: Dict[str, Any]) -> str:
        """
        生成定期市場週報
        """
        prompt = f"""
        你是一個資深的加密貨幣分析師。請根據以下數據寫一份 **HTML 市場趨勢日報**。
        
        【市場資訊】
        - 標的: {context.get('symbol')}
        - 報告時間: {context.get('time')}
        
        【技術分析摘要】
        {context.get('technical_analysis_text')}
        
        【輸出要求】
        1. 風格專業、客觀，標題背景色使用 #e8f0fe。
        2. **市場解讀**: 判斷目前是大趨勢多頭、空頭還是盤整。
        3. **關鍵點位**: 分析支撐與壓力。
        4. **操作建議**: 針對空手者與持倉者給予建議。
        5. 只輸出 HTML 代碼。
        """
        return self._generate_html(prompt)

    def generate_free_qa(self, user_question: str) -> str:
        """
        QA 系統專用介面 (配合 qa_service.py)
        """
        prompt = f"""
        使用者問題: {user_question}
        
        請以「加密貨幣與金融交易顧問」的身分回答：
        1. 使用 HTML 格式 (不含 ``` 標記)。
        2. 重點加粗。
        3. 語氣專業親切。
        """
        return self._generate_html(prompt)