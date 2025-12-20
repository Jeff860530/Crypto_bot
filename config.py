# config.py
from gitIgnoreFile.MyKey import myApiKey, mySecretKey
from gitIgnoreFile.MyMail import EmailSender, EmailPassword, EmailReceiver
from gitIgnoreFile.MyGeminiKey import MyGeminiApiKey, MyGeminiAiName

# --- BingX API 設定 ---
API_KEY = myApiKey
SECRET_KEY = mySecretKey

# --- 交易標的與資金管理 ---
COIN_LIST = [
    # "BTC-USDT",
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

# True: 真實呼叫 Gemini (消耗額度)
# False: 使用模擬假資料 (快速測試用)
ENABLE_AI_GENERATION = True

# 3. 系統功能開關
# (True: 開啟 | False: 暫停)
ENABLE_QA_SYSTEM = False        # 是否開啟問答系統
ENABLE_TRADING_SYSTEM = True   # 是否開啟交易策略檢查
ENABLE_PERIODIC_REPORT = False  # 是否開啟定期報告

# --------------------------------------------------------
# ⏱️ 服務執行頻率設定 (單位: 秒)
# --------------------------------------------------------
# 說明: 支援數學運算，例如 15 * 60 代表 15 分鐘
# --------------------------------------------------------

# QA 問答檢查頻率 (建議 5~10 秒)
INTERVAL_QA_CHECK = 5 

# 交易策略檢查頻率 (建議配合 K 線時框，例如 15 分鐘)
# INTERVAL_TRADING_CHECK = 15 * 60
INTERVAL_TRADING_CHECK = 1 * 60 * 60

# 定期市場報告頻率 (例如每 60 分鐘發一次)
# INTERVAL_PERIODIC_REPORT = 60 * 60
INTERVAL_PERIODIC_REPORT = 1 * 60 * 60