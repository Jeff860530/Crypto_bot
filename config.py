# config.py
from gitIgnoreFile.MyKey import myApiKey, mySecretKey
from gitIgnoreFile.MyMail import EmailSender, EmailPassword, EmailReceiver
from gitIgnoreFile.MyGeminiKey import MyGeminiApiKey, MyGeminiAiName

# --- BingX API 設定 ---
API_KEY = myApiKey
SECRET_KEY = mySecretKey

# --- 交易標的與資金管理 ---
COIN_LIST = [
    "BTC-USDT",
    "ETH-USDT"
]

DRY_RUN = True  # True: 模擬交易 | False: 真實下單
LEVERAGE = 5
TRADING_FEE_RATE = 0.0005

# 預設下單數量 (當找不到 ORDER_SIZES 時使用)
ORDER_AMOUNT = 0.001 

# 個別幣種下單量 (建議約 10~100 USDT)
ORDER_SIZES = {
    "BTC-USDT": 0.001,   # 約 90 U
    "ETH-USDT": 0.01,    # 約 25 U
    "SOL-USDT": 0.5,     # 約 50 U
    "DOGE-USDT": 100,    # 約 30 U
    "BNB-USDT": 0.1      # 約 60 U
}

# --- 策略與指標參數 ---
TRADE_TIMEFRAME = '15m'  # 交易用 K 線
SMA_SHORT = 7
SMA_LONG = 25

# 風控 (0.02 = 2%)
STOP_LOSS_PCT = 0.02      
TAKE_PROFIT_PCT = 0.04    

# --- 系統服務設定 ---
# 1. Email (SMTP)
ENABLE_EMAIL = True
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = EmailSender
SMTP_PASSWORD = EmailPassword
SMTP_TO_EMAIL = EmailReceiver

# 2. Gemini AI
GEMINI_API_KEY = MyGeminiApiKey
GEMINI_MODEL_NAME = MyGeminiAiName

# 3. 報告與 QA
ENABLE_QA_SYSTEM = True
ENABLE_PERIODIC_REPORT = True
REPORT_INTERVAL_MINUTES = 60
QA_CHECK_INTERVAL = 5