# config.py
from gitIgnoreFile.MyKey import myApiKey,mySecretKey
from gitIgnoreFile.MyLineToken import myLineChannelToken, myLineUserID


# BingX API 設定 (去 BingX 官網申請)
API_KEY = myApiKey
SECRET_KEY = mySecretKey

# 交易對設定
SYMBOL = "BTC/USDT:USDT"  # BingX 的合約通常格式是這樣，或是 "BTC-USDT" 視 ccxt 版本而定

# 參數設定
TIMEFRAMES = {
    'short': '15m',  # 15 分鐘
    'mid': '4h',     # 4 小時
    'long': '1d'     # 日線
}

# 策略參數 (雙均線)
SMA_SHORT = 7
SMA_LONG = 25

# --- 交易設定 ---
DRY_RUN = True  # True: 只印 Log 不下單 | False: 真槍實彈 (小心！)

# 槓桿倍數
LEVERAGE = 10000

# 每次交易數量 (單位: BTC)
# ⚠️ 注意: BingX 最小下單單位限制，BTC 通常要 0.0001 以上
ORDER_AMOUNT = 0.1

# --- 風控設定 ---
STOP_LOSS_PCT = 0.002   # 止損 2%
TAKE_PROFIT_PCT = 0.004 # 止盈 4%

# 交易費率 (BingX Taker 約 0.05%)
TRADING_FEE_RATE = 0.0005

# --- LINE Messaging API 設定 ---
ENABLE_LINE_NOTIFY = True
# 填入 Messaging API 分頁最下方的 Channel Access Token
LINE_CHANNEL_ACCESS_TOKEN = myLineChannelToken

# 填入 Basic settings 分頁最下方的 Your User ID (U開頭的那串)
LINE_USER_ID = myLineUserID