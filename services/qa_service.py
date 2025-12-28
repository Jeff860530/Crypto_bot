# services/qa_service.py
import json
import os
import config
from datetime import datetime
from typing import List, Dict, Any

class QAService:
    def __init__(self, filename: str = "questions.json"):
        self.filename = filename

    def _load_questions(self) -> List[Dict[str, Any]]:
        """讀取問題列表"""
        if not os.path.exists(self.filename):
            default_data = [{"id": "example01", "question": "範例: ETH走勢分析", "answered": False, "frequency": 3600}]
            self._save_questions(default_data)
            return default_data
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 讀取問題檔失敗: {e}")
            return []

    def _save_questions(self, data: List[Dict[str, Any]]) -> None:
        """儲存問題列表"""
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
        """更新問題狀態 (更新最後回答時間)"""
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
        核心邏輯：處理未回答 或 週期性需重問 的問題
        """
        if not getattr(config, 'ENABLE_QA_SYSTEM', False):
            return

        questions = self._load_questions()
        pending_count = 0

        for q in questions:
            q_id = q.get('id', 'unknown')
            q_text = q.get('question', '')
            is_answered = q.get('answered', False)
            frequency = q.get('frequency', 0) # 預設 0 (不重複)
            
            should_process = False

            # --- 判斷邏輯 ---
            # 情況 1: 從未回答過 -> 執行
            if not is_answered:
                should_process = True
            
            # 情況 2: 是週期性問題 (frequency > 0) -> 檢查時間差
            elif frequency > 0:
                last_time_str = q.get('answered_at')
                if last_time_str:
                    try:
                        last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
                        # 計算距離上次回答過了好幾秒
                        seconds_diff = (datetime.now() - last_time).total_seconds()
                        
                        if seconds_diff >= frequency:
                            print(f"⏰ 週期性問題 {q_id} 時間到 (距上次 {int(seconds_diff)} 秒) -> 準備執行")
                            should_process = True
                    except Exception as e:
                        print(f"⚠️ 時間格式解析錯誤 ({q_id}): {e}，將重置為可執行")
                        should_process = True
            
            # --- 執行問答 ---
            if should_process:
                print(f"\n💡 處理問題 ({q_id}): {q_text}")
                print("🤖 AI 正在思考答案...")

                try:
                    # 1. AI 生成答案
                    answer_html = ai_reporter.generate_free_qa(q_text)
                    
                    # 2. 組合 Email
                    # 如果是週期性問題，標題可以加註時間，方便區分
                    title_prefix = "🔄 [定期] " if frequency > 0 else "🧠 "
                    email_subject = f"{title_prefix}AI 問答回覆: {q_id}"
                    
                    email_body = self._format_email_content(q_id, q_text, answer_html)

                    # 3. 發送郵件
                    mailer.send_report(email_subject, email_body)
                    print(f"📨 回覆已寄出: {q_id}")

                    # 4. 更新狀態 (寫入回答時間)
                    self.mark_as_answered(q_id)
                    pending_count += 1

                except Exception as e:
                    print(f"❌ 處理問題 {q_id} 時發生錯誤: {e}")

        if pending_count > 0:
            print(f"✅ 本次共處理了 {pending_count} 個問題")