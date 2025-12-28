import ccxt
import pandas as pd
import config

class BingXLoader:
    def __init__(self):
        # 初始化交易所物件
        self.exchange = ccxt.bingx({
            'enableRateLimit': True, # 啟用速率限制，避免被鎖 IP
        })

    def fetch_data(self, timeframe, symbol=None, limit=100):
        """
        從 BingX 獲取 K 線數據
        :param timeframe: 時框 (例如 '15m', '1h')
        :param symbol: 交易對 (例如 'BTC-USDT')，如果為 None 則嘗試讀取 config
        :param limit: 獲取 K 線的數量
        """
        # 1. 處理 Symbol (優先使用傳入的參數，否則使用 config 預設)
        if symbol is None:
            if hasattr(config, 'SYMBOL'):
                symbol = config.SYMBOL
            elif hasattr(config, 'COIN_LIST') and config.COIN_LIST:
                symbol = config.COIN_LIST[0]
            else:
                print("❌ 錯誤: 未指定 Symbol 且 Config 中找不到設定")
                return None

        # CCXT 通常需要 'BTC/USDT' 格式，而我們 config 可能寫 'BTC-USDT'
        formatted_symbol = symbol.replace('-', '/')

        try:
            # print(f"📥 正在獲取 {formatted_symbol} 的 {timeframe} K 線數據...")
            
            # 2. 呼叫 CCXT API
            ohlcv = self.exchange.fetch_ohlcv(formatted_symbol, timeframe, limit=limit)
            
            if not ohlcv:
                print(f"⚠️ {symbol} 獲取數據為空")
                return None

            # 3. 轉換為 DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 處理時間戳 (轉為人類可讀時間，方便除錯)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 確保數據是 float 格式
            df = df.astype({
                'open': 'float',
                'high': 'float',
                'low': 'float',
                'close': 'float',
                'volume': 'float'
            })
            
            return df

        except Exception as e:
            print(f"❌ {symbol} 數據獲取失敗: {e}")
            return None

# 簡單測試用
if __name__ == "__main__":
    loader = BingXLoader()
    # 測試多幣種傳參
    df = loader.fetch_data(timeframe='15m', symbol='BTC-USDT')
    if df is not None:
        print(f"✅ BTC-USDT 測試成功:\n{df.tail(2)}")