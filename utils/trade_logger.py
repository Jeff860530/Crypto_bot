import json
import os
from datetime import datetime
import config

class TradeLogger:
    def __init__(self, filename="logs/trade_history.json"):
        self.filename = filename
        
        # 確保 log 目錄存在
        log_dir = os.path.dirname(self.filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def log(self, action, price, amount, tag, pnl=0.0, balance=0.0, symbol=None):
        """
        記錄交易到 JSON 檔案
        :param symbol: 交易幣種 (例如 'BTC-USDT') 🔥 新增這個參數
        """
        
        # 如果呼叫時沒傳 symbol，嘗試用 config 裡的預設值 (兼容舊程式碼)
        if symbol is None:
            if hasattr(config, 'SYMBOL'):
                symbol = config.SYMBOL
            elif hasattr(config, 'COIN_LIST') and config.COIN_LIST:
                symbol = config.COIN_LIST[0]
            else:
                symbol = "UNKNOWN"

        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,  # 🔥 寫入幣種
            "action": action,
            "price": float(price),
            "amount": float(amount),
            "tag": tag,
            "realized_pnl": float(pnl),
            "balance": float(balance)
        }

        # 讀取現有紀錄
        history = []
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        # 加入新紀錄
        history.append(record)

        # 寫回檔案
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            print(f"📝 [Log] {symbol} 交易紀錄已更新: {action} @ {price}")
        except Exception as e:
            print(f"❌ [Log] 寫入失敗: {e}")

# 測試用
if __name__ == "__main__":
    logger = TradeLogger()
    logger.log("TEST_ENTRY", 50000, 0.001, "測試寫入", symbol="BTC-USDT")