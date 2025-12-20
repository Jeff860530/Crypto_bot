#services/email_service.py
import sys
import os

# 取得目前檔案所在的資料夾 (services)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 取得上一層資料夾 (crypto_bot 根目錄)
parent_dir = os.path.dirname(current_dir)
# 將根目錄加入 Python 搜尋路徑
sys.path.append(parent_dir)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import config

class EmailService:
    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.username = config.SMTP_USERNAME
        self.password = config.SMTP_PASSWORD
        self.to_addr = config.SMTP_TO_EMAIL  # 預設收件人

    def send_report(self, subject: str, html_content: str, to_email: str = None) -> bool:
        """
        發送 HTML 格式的郵件
        :param subject: 郵件標題
        :param html_content: HTML 內容
        :param to_email: 收件人 (若未指定則使用 config 預設值)
        :return: 是否發送成功
        """
        # 如果 config 沒設定開啟郵件，直接跳過 (方便測試)
        if not getattr(config, 'ENABLE_EMAIL', True):
            print(f"🔕 Email 功能已關閉，跳過發送: {subject}")
            return True

        target_email = to_email if to_email else self.to_addr

        # 建立郵件物件
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = target_email
        msg['Subject'] = Header(subject, 'utf-8')

        # 加入 HTML 內文
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        try:
            # 建立 SMTP 連線
            # 如果是 Gmail 或是使用 SSL (Port 465)
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                # 如果是 TLS (Port 587)
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            print(f"📨 Email 發送成功: {subject} -> {target_email}")
            return True

        except Exception as e:
            print(f"❌ Email 發送失敗: {e}")
            return False

# 用法測試
if __name__ == "__main__":
    email_service = EmailService()
    email_service.send_report("測試郵件", "<h1>這是測試</h1><p>系統運作正常。</p>")