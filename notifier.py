import requests
import json
import config

class LineNotifier:
    def __init__(self):
        self.enabled = config.ENABLE_LINE_NOTIFY
        self.token = config.LINE_CHANNEL_ACCESS_TOKEN
        self.user_id = config.LINE_USER_ID
        # Messaging API 的 Push 訊息接口
        self.api_url = "https://api.line.me/v2/bot/message/push"

    def send(self, message):
        """
        發送 Push Message 給指定 User ID
        """
        if not self.enabled or not self.token or not self.user_id:
            return

        try:
            # 設定 Header
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }
            
            # 設定 Body (Payload)
            payload = {
                "to": self.user_id,
                "messages": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
            
            # 發送請求
            response = requests.post(
                self.api_url, 
                headers=headers, 
                data=json.dumps(payload) # 轉成 JSON 格式
            )
            
            # 檢查回應
            if response.status_code != 200:
                print(f"⚠️ LINE API 發送失敗: {response.status_code} | {response.text}")
            # else:
            #     print("✅ LINE 通知發送成功") # 測試時可打開，正式跑建議關閉避免洗版

        except Exception as e:
            print(f"⚠️ LINE 通知發生錯誤: {e}")

# 測試用
if __name__ == "__main__":
    bot = LineNotifier()
    bot.send("🔔 測試：這是來自 Messaging API 的通知！")