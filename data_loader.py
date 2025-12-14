import ccxt
import pandas as pd
import config
import time

class BingXLoader:
    def __init__(self):
        try:
            # 初始化 BingX 交易所實例
            self.exchange = ccxt.bingx({
                'apiKey': config.API_KEY,
                'secret': config.SECRET_KEY,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',  # 設定為永續合約 (Swap)
                }
            })
        except Exception as e:
            print(f"❌ 初始化交易所失敗: {e}")

    def fetch_data(self, timeframe, limit=100):
        """
        抓取 K 線資料
        :param timeframe: '15m', '4h', '1d'
        :param limit: 要抓幾根 K 線
        """
        try:
            print(f"📡 正在抓取 {config.SYMBOL} [{timeframe}] 數據...")
            # 抓取 OHLCV (Open, High, Low, Close, Volume)
            ohlcv = self.exchange.fetch_ohlcv(config.SYMBOL, timeframe, limit=limit)
            
            if not ohlcv:
                print("⚠️ 未抓取到數據，請檢查交易對名稱或網路")
                return None

            # 轉成 DataFrame 方便處理
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 處理時間格式 (轉為 UTC+8 或人類可讀格式)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            print(f"❌ 抓取數據失敗 ({timeframe}): {e}")
            return None