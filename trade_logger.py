import json
import os
from datetime import datetime

class TradeLogger:
    # 預設改為 logs/trade_history.json
    def __init__(self, filename="logs/trade_history.json"):
        self.filename = filename
        
        # 🔥 新增：自動建立資料夾 (例如 logs/)
        folder = os.path.dirname(self.filename)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            
        self.history = self._load()

    def _load(self):
        """讀取現有的 JSON 紀錄"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def log(self, action, price, amount, tag, pnl=0.0, balance=0.0):
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "price": float(price),
            "amount": float(amount),
            "tag": tag,
            "realized_pnl": float(f"{pnl:.4f}"),
            "account_equity": float(f"{balance:.2f}")
        }
        
        self.history.append(record)
        self._save()
        # print(f"📝 交易紀錄已保存至 {self.filename}") # 這行可以註解掉，保持畫面乾淨

    def _save(self):
        """寫入 JSON 檔案"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)