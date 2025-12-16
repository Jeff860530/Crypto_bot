# config.py
from gitIgnoreFile.MyKey import myApiKey, mySecretKey
from gitIgnoreFile.MyMail import EmailSender, EmailPassword, EmailReceiver
from gitIgnoreFile.MyGeminiKey import MyGeminiApiKey, MyGeminiAiName

# BingX API 設定
API_KEY = myApiKey
SECRET_KEY = mySecretKey

# --- 交易標的設定 ---
# ✅ 多幣種清單 (取代原本的 SYMBOL)
COIN_LIST = [
    # "SOL-USDT",
    # "DOGE-USDT",
    # "BNB-USDT",
    "BTC-USDT",
    "ETH-USDT"
]

# --- 交易設定 ---
DRY_RUN = True  # True: 模擬交易 (只印Log) | False: 真實下單

# 槓桿倍數
LEVERAGE = 5

# ✅ 預設下單數量 (當找不到個別設定時使用)
ORDER_AMOUNT = 0.001 

# 🔥 [強烈建議新增] 個別幣種下單量 (避免不同幣價導致下單金額差距過大)
# 建議換算成大約 10~100 USDT 的等值數量
ORDER_SIZES = {
    "BTC-USDT": 0.001,   # 約 90 U
    "ETH-USDT": 0.01,    # 約 25 U
    "SOL-USDT": 0.5,     # 約 50 U
    "DOGE-USDT": 100,    # 約 30 U
    "BNB-USDT": 0.1      # 約 60 U
}

# 交易費率 (BingX Taker 約 0.05%)
TRADING_FEE_RATE = 0.0005

# --- 策略參數 ---
SMA_SHORT = 7
SMA_LONG = 25

# --- 風控設定 (數值修正) ---
# 0.02 代表 2%, 0.04 代表 4%
STOP_LOSS_PCT = 0.02      # 止損 2%
TAKE_PROFIT_PCT = 0.04    # 止盈 4%

# --- 頻率與時框設定 ---
# 1. 交易機器人運作頻率 (決定進出場的 K 線)
TRADE_TIMEFRAME = '15m'  

# 2. AI 報告設定
ENABLE_PERIODIC_REPORT = True     # 是否開啟定期發送 AI 報告
REPORT_TIMEFRAME = '1h'           # AI 寫報告時要看的 K 線
REPORT_INTERVAL_MINUTES = 60      # 每隔幾分鐘發送一次報告

# --- Email 設定 ---
ENABLE_EMAIL_NOTIFY = True
EMAIL_SENDER = EmailSender
EMAIL_PASSWORD = EmailPassword
EMAIL_RECEIVER = EmailReceiver

# --- Google Gemini AI 設定 ---
GEMINI_API_KEY = MyGeminiApiKey
GEMINI_MODEL_NAME = MyGeminiAiName