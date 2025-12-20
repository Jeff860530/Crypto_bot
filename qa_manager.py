import json
import os
import config
from datetime import datetime

class QAManager:
    def __init__(self, filename="questions.json"):
        self.filename = filename

    def load_questions(self):
        if not os.path.exists(self.filename):
            # 如果檔案不存在，建立一個範本
            default_data = [{"id": "question000", "question": "範例問題", "answered": True}]
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
            return default_data
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 讀取問題檔失敗: {e}")
            return []

    def mark_as_answered(self, question_id):
        """將問題標記為已回答"""
        questions = self.load_questions()
        updated = False
        for q in questions:
            if q['id'] == question_id:
                q['answered'] = True
                q['answered_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated = True
                break
        
        if updated:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=4)
            # print(f"✅ 問題 {question_id} 已標記為完成")

    def process_pending_questions(self, ai_reporter, mailer):
        """檢查並處理所有未回答的問題"""
        if not config.ENABLE_QA_SYSTEM:
            return

        questions = self.load_questions()
        pending_count = 0

        for q in questions:
            # 找到 answered 為 False 的問題
            if not q.get('answered', False):
                q_id = q.get('id', 'unknown')
                q_text = q.get('question', '')
                
                print(f"\n💡 發現新問題 ({q_id}): {q_text}")
                print("🤖 AI 正在思考答案...")

                try:
                    # 1. AI 生成答案
                    answer_html = ai_reporter.generate_free_qa(q_text)
                    
                    # 2. 組合 Email 內容 (🔥 修改這裡：調整排版)
                    email_subject = f"🧠 AI 問答回覆: {q_id}"
                    
                    email_body = f"""
                    <div style="background-color: #f8f9fa; padding: 15px; border-left: 5px solid #0d6efd; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: #0d6efd;">📌 提問編號: {q_id}</h3>
                        <p style="font-size: 16px; font-weight: bold; margin: 0; line-height: 1.5;">
                            {q_text}
                        </p>
                    </div>
                    
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    
                    <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                        {answer_html}
                    </div>
                    """

                    # 3. 發送郵件
                    mailer.send_report(email_subject, email_body)
                    print(f"📨 回覆已寄出: {q_id}")

                    # 4. 標記為已回答 (寫回檔案)
                    self.mark_as_answered(q_id)
                    pending_count += 1

                except Exception as e:
                    print(f"❌ 處理問題 {q_id} 時發生錯誤: {e}")

        if pending_count == 0:
            pass