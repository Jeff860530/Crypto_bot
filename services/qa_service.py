import json
import os
import config
from datetime import datetime
from typing import List, Dict, Any

class QAService:
    def __init__(self, filename: str = "questions.json"):
        self.filename = filename

    def _load_questions(self) -> List[Dict[str, Any]]:
        """讀取問題列表 (內部方法)"""
        if not os.path.exists(self.filename):
            # 如果檔案不存在，建立一個範本
            default_data = [{"id": "question000", "question": "範例問題", "answered": True}]
            self._save_questions(default_data)
            return default_data
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 讀取問題檔失敗: {e}")
            return []

    def _save_questions(self, data: List[Dict[str, Any]]) -> None:
        """儲存問題列表 (內部方法)"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _format_email_content(self, q_id: str, question: str, answer_html: str) -> str:
        """生成 Email 的 HTML 內容"""
        return f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-left: 5px solid #0d6efd; margin-bottom: 20px;">
            <h3 style="margin: 0 0 10px 0; color: #0d6efd;">📌 提問編號: {q_id}</h3>
            <p style="font-size: 16px; font-weight: bold; margin: 0; line-height: 1.5;">
                {question}
            </p>
        </div>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
            {answer_html}
        </div>
        """

    def mark_as_answered(self, question_id: str) -> None:
        """將問題標記為已回答"""
        questions = self._load_questions()
        updated = False
        
        for q in questions:
            if q.get('id') == question_id:
                q['answered'] = True
                q['answered_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated = True
                break
        
        if updated:
            self._save_questions(questions)

    def process_pending_questions(self, ai_reporter, mailer) -> None:
        """
        核心業務邏輯：檢查並處理所有未回答的問題
        :param ai_reporter: 負責生成回答的物件
        :param mailer: 負責發送郵件的物件
        """
        if not getattr(config, 'ENABLE_QA_SYSTEM', False):
            return

        questions = self._load_questions()
        pending_count = 0

        # 篩選出未回答的問題
        pending_questions = [q for q in questions if not q.get('answered', False)]

        if not pending_questions:
            return

        for q in pending_questions:
            q_id = q.get('id', 'unknown')
            q_text = q.get('question', '')
            
            print(f"\n💡 發現新問題 ({q_id}): {q_text}")
            print("🤖 AI 正在思考答案...")

            try:
                # 1. AI 生成答案
                # 假設 ai_reporter 有 generate_free_qa 方法
                answer_html = ai_reporter.generate_free_qa(q_text)
                
                # 2. 組合 Email 內容
                email_subject = f"🧠 AI 問答回覆: {q_id}"
                email_body = self._format_email_content(q_id, q_text, answer_html)

                # 3. 發送郵件
                mailer.send_report(email_subject, email_body)
                print(f"📨 回覆已寄出: {q_id}")

                # 4. 標記為已回答 (更新狀態)
                # 這裡直接呼叫 mark_as_answered 會重新讀寫一次檔案，雖然 IO 多一點但比較安全
                self.mark_as_answered(q_id)
                pending_count += 1

            except Exception as e:
                print(f"❌ 處理問題 {q_id} 時發生錯誤: {e}")
                # 可以在這裡加入錯誤 logging 或通知管理員

        if pending_count > 0:
            print(f"✅ 本次共處理了 {pending_count} 個問題")