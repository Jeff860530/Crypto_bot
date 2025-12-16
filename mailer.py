import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import config

class GmailNotifier:
    def __init__(self):
        self.enabled = config.ENABLE_EMAIL_NOTIFY
        self.sender = config.EMAIL_SENDER
        self.password = config.EMAIL_PASSWORD
        self.receiver = config.EMAIL_RECEIVER
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587 # Gmail 使用 TLS 的端口

    def send_report(self, subject, content):
        """
        發送 Email 報告
        :param subject: 信件標題
        :param content: 信件內容 (支援 HTML 或純文字)
        """
        if not self.enabled:
            return

        try:
            # 1. 建立郵件物件
            msg = MIMEMultipart()
            msg['From'] = formataddr(("Crypto Bot", self.sender))
            msg['To'] = self.receiver
            msg['Subject'] = f"📊 {subject}" # 加個圖示比較好辨識

            # 2. 加入內容 (使用 HTML 格式可以讓排版更漂亮)
            # 將 \n 換行符號轉成 HTML 的 <br>
            html_content = content.replace("\n", "<br>")
            
            body = f"""
            <html>
                <body>
                    <h2>🤖 Crypto Bot 交易分析報告</h2>
                    <hr>
                    <p style="font-size: 14px; line-height: 1.6;">
                        {html_content}
                    </p>
                    <hr>
                    <p style="color: gray; font-size: 12px;">此郵件由 Python 自動發送，請勿回覆。</p>
                </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html', 'utf-8'))

            # 3. 連線並寄送
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls() # 啟動傳輸加密
            server.login(self.sender, self.password)
            server.sendmail(self.sender, [self.receiver], msg.as_string())
            server.quit()
            
            print(f"📧 Email 報告已發送至 {self.receiver}")

        except Exception as e:
            print(f"❌ Email 發送失敗: {e}")

# 測試用
if __name__ == "__main__":
    mailer = GmailNotifier()
    mailer.send_report("CryptoBot", "這是一封測試郵件。\n換行測試。\nAI 分析結果：看漲！")