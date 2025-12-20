import time
import json
import os
import pandas_ta as ta
from datetime import datetime, timedelta
from data_loader import BingXLoader
from strategies import RuleBasedStrategy
from executor import BingXExecutor
from trade_logger import TradeLogger
from mailer import GmailNotifier
from ai_reporter import AIReportGenerator
from qa_manager import QAManager
import config

# --- 全域變數 ---
initial_balance = 1000.0
accumulated_pnl = 0.0
total_win_amount = 0.0
total_loss_amount = 0.0
win_count = 0
loss_count = 0

# --- 多幣種狀態管理 ---
coin_states = {}

LOG_FILE = "logs/trade_history.json"

def run_bot():
    global initial_balance, accumulated_pnl
    global total_win_amount, total_loss_amount, win_count, loss_count
    global coin_states
    
    print(f"🤖 Crypto Bot 多幣種軍團啟動... (模式: {'🧪 模擬' if config.DRY_RUN else '⚡ 真實'})")
    print(f"📋 監控清單: {config.COIN_LIST}")
    
    loader = BingXLoader()
    executor = BingXExecutor(loader.exchange)
    strategy = RuleBasedStrategy()
    
    logger = TradeLogger(filename=LOG_FILE)
    mailer = GmailNotifier()
    ai_reporter = AIReportGenerator()
    qa_manager = QAManager("questions.json")
    
    target_tf = '15m' 

    # 初始化狀態
    for symbol in config.COIN_LIST:
        coin_states[symbol] = {'entry_price': 0.0, 'pos': None}

    # ==========================================
    # 歷史回補
    # ==========================================
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir): os.makedirs(log_dir, exist_ok=True)
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                for trade in history:
                    pnl = trade.get("realized_pnl", 0.0)
                    if pnl != 0:
                        accumulated_pnl += pnl
                        if pnl > 0: win_count += 1; total_win_amount += pnl
                        else: loss_count += 1; total_loss_amount += abs(pnl)
            print(f"✅ 歷史戰績回補完成！(累積損益: {accumulated_pnl:.4f} U)")
        except Exception: pass

    if not config.DRY_RUN:
        try:
            balance = loader.exchange.fetch_balance()
            initial_balance = float(balance['USDT']['total'])
        except Exception: pass

    def update_trade_stats(pnl):
        global total_win_amount, total_loss_amount, win_count, loss_count
        if pnl > 0: win_count += 1; total_win_amount += pnl
        elif pnl < 0: loss_count += 1; total_loss_amount += abs(pnl)

    # 🔥🔥 修正後的發信函式：改用 iloc 抓取布林帶，避免 KeyError 🔥🔥
    def send_trade_signal_email(symbol, df, action, price):
        try:
            # 1. 本地快速計算關鍵指標
            rsi = ta.rsi(df['close'], length=14).iloc[-1]
            ma7 = ta.sma(df['close'], length=7).iloc[-1]
            ma25 = ta.sma(df['close'], length=25).iloc[-1]
            
            # 🔥 修正重點：一次算出 DataFrame，然後用位置抓取
            # pandas_ta.bbands 回傳順序通常是: [Lower, Mid, Upper, Bandwidth, Percent]
            # 所以 0 是下軌，2 是上軌
            bb_df = ta.bbands(df['close'], length=20, std=2)
            
            if bb_df is not None and not bb_df.empty:
                lower = bb_df.iloc[-1, 0] # 取第一欄 (下軌)
                upper = bb_df.iloc[-1, 2] # 取第三欄 (上軌)
            else:
                lower = 0.0
                upper = 0.0
            
            trend_str = "多頭排列 🐂" if ma7 > ma25 else "空頭排列 🐻"
            color = "#e6f4ea" if "LONG" in action else "#fce8e6"
            
            # 2. 組建 HTML 內容
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="background-color: {color}; padding: 10px; border-radius: 5px; text-align: center;">
                    ⚡ 交易訊號: {action}
                </h2>
                
                <ul style="list-style: none; padding: 0; font-size: 16px;">
                    <li>🎯 <b>交易對象:</b> {symbol}</li>
                    <li>💰 <b>觸發價格:</b> {price}</li>
                    <li>⏰ <b>時間:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
                
                <hr>
                
                <h3>📊 技術指標狀態 ({target_tf})</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ddd;">指標</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">數值 / 狀態</th>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">RSI (14)</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{rsi:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">趨勢 (MA7/25)</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{trend_str}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;">布林帶</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">上 {upper:.2f} / 下 {lower:.2f}</td>
                    </tr>
                </table>
                
                <br>
                <p style="color: gray; font-size: 12px;">*此信件由 Python 策略自動觸發，不含 AI 分析。</p>
            </div>
            """
            
            mailer.send_report(f"⚡ 交易訊號 ({symbol}) - {action}", html_content)
            
        except Exception as e:
            print(f"⚠️ 發送交易信件失敗: {e}")

    def get_order_amount(symbol):
        if hasattr(config, 'ORDER_SIZES') and isinstance(config.ORDER_SIZES, dict):
            return config.ORDER_SIZES.get(symbol, config.ORDER_AMOUNT)
        return config.ORDER_AMOUNT

    # 🔥🔥 時間鎖設定 🔥🔥
    next_qa_time = datetime.now()
    next_trade_time = datetime.now()
    next_report_time = datetime.now()
    next_report_time = next_report_time + timedelta(minutes=15)

    print("🚀 系統進入極速監聽模式 (QA優先 | 交易信件改用本地生成)...")

    while True:
        try:
            now = datetime.now()

            # ======================================
            # ❓ 0. 自訂問答 (維持使用 AI)
            # ======================================
            if config.ENABLE_QA_SYSTEM and now >= next_qa_time:
                qa_manager.process_pending_questions(ai_reporter, mailer)
                next_qa_time = now + timedelta(seconds=5)

            # ======================================
            # 🕒 1. 定期報告 (維持使用 AI)
            # ======================================
            if config.ENABLE_PERIODIC_REPORT and now >= next_report_time:
                print(f"\n⏰ 定期報告時間到...")
                for symbol in config.COIN_LIST:
                    print(f"📡 [報告] 抓取 {symbol}...")
                    report_df = loader.fetch_data(symbol=symbol, timeframe=config.REPORT_TIMEFRAME)
                    if report_df is not None:
                        try:
                            report_content = ai_reporter.generate_market_report(report_df, symbol)
                            mailer.send_report(f"📅 市場趨勢報告 ({symbol})", report_content)
                            print(f"📨 {symbol} 定期報告已寄出")
                        except Exception as e:
                            print(f"❌ {symbol} AI 報告失敗: {e}")
                    
                    time.sleep(15) # 休息一下給 AI 喘口氣

                print(f"✅ 定期報告完成")
                next_report_time = now + timedelta(minutes=config.REPORT_INTERVAL_MINUTES)

            # ======================================
            # 📈 2. 交易邏輯 (不使用 AI，改用本地發信)
            # ======================================
            if now >= next_trade_time:
                print(f"\n======== 🔄 開始交易掃描 ({target_tf}) ========")
                
                for symbol in config.COIN_LIST:
                    print(f"\n🔍 分析: {symbol}")
                    
                    # 1. 獲取數據
                    df = loader.fetch_data(symbol=symbol, timeframe=target_tf)
                    if df is None: time.sleep(1); continue

                    current_pos = executor.get_open_position(symbol=symbol)
                    current_price = df.iloc[-1]['close'] 
                    
                    if current_pos is not None and coin_states[symbol]['entry_price'] == 0:
                        coin_states[symbol]['entry_price'] = current_price
                        coin_states[symbol]['pos'] = current_pos

                    result = strategy.analyze(df)
                    signal = result['action']
                    
                    if signal == "HOLD":
                        if "多頭" in result['info']: signal = "LONG"
                        elif "空頭" in result['info']: signal = "SHORT"

                    entry_price = coin_states[symbol]['entry_price']
                    order_amount = get_order_amount(symbol)

                    try: coin_name_short = symbol.split('-')[0]
                    except: coin_name_short = symbol

                    # 損益計算
                    net_pnl_usdt = 0.0
                    net_pnl_pct = 0.0
                    if current_pos is not None and entry_price > 0:
                        diff = (current_price - entry_price) if current_pos == "LONG" else (entry_price - current_price)
                        gross_pnl = diff * order_amount
                        estimated_fee = (entry_price + current_price) * order_amount * config.TRADING_FEE_RATE
                        net_pnl_usdt = gross_pnl - estimated_fee
                        net_pnl_pct = net_pnl_usdt / (entry_price * order_amount)
                        print(f"📉 損益: {net_pnl_pct*100:.2f}% ({net_pnl_usdt:+.2f} U)")

                    # 顯示資訊
                    current_equity = initial_balance + accumulated_pnl + net_pnl_usdt
                    pos_info = f"{current_pos}" if current_pos else "空手"
                    print(f"💰 {current_price} | {pos_info} | 權益 {current_equity:.1f}")

                    # SL/TP 檢查
                    if current_pos is not None and entry_price > 0:
                        if net_pnl_pct <= -config.STOP_LOSS_PCT:
                            print(f"🛑 {symbol} 止損")
                            executor.close_position(symbol=symbol)
                            accumulated_pnl += net_pnl_usdt; update_trade_stats(net_pnl_usdt)
                            logger.log(action=f"CLOSE_{current_pos} (SL)", symbol=symbol, price=current_price, amount=order_amount, tag="止損", pnl=net_pnl_usdt, balance=initial_balance+accumulated_pnl)
                            coin_states[symbol]['entry_price'] = 0.0; coin_states[symbol]['pos'] = None
                            continue
                        elif net_pnl_pct >= config.TAKE_PROFIT_PCT:
                            print(f"🎉 {symbol} 止盈")
                            executor.close_position(symbol=symbol)
                            accumulated_pnl += net_pnl_usdt; update_trade_stats(net_pnl_usdt)
                            logger.log(action=f"CLOSE_{current_pos} (TP)", symbol=symbol, price=current_price, amount=order_amount, tag="止盈", pnl=net_pnl_usdt, balance=initial_balance+accumulated_pnl)
                            coin_states[symbol]['entry_price'] = 0.0; coin_states[symbol]['pos'] = None
                            continue

                    # 進出場策略
                    if signal == "LONG":
                        if current_pos == "SHORT":
                            print(f"🔄 反手做多")
                            accumulated_pnl += net_pnl_usdt; update_trade_stats(net_pnl_usdt)
                            executor.close_position(symbol=symbol)
                            logger.log(action="CLOSE_SHORT", symbol=symbol, price=current_price, amount=order_amount, tag="反手", pnl=net_pnl_usdt, balance=initial_balance+accumulated_pnl)
                            executor.place_order('buy', symbol=symbol, amount=order_amount)
                            coin_states[symbol]['entry_price'] = current_price; coin_states[symbol]['pos'] = "LONG"
                            logger.log(action="OPEN_LONG", symbol=symbol, price=current_price, amount=order_amount, tag="訊號", pnl=0, balance=initial_balance+accumulated_pnl)
                            
                            send_trade_signal_email(symbol, df, "OPEN LONG (反手)", current_price)

                        elif current_pos is None:
                            print(f"🚀 進場做多")
                            executor.place_order('buy', symbol=symbol, amount=order_amount)
                            coin_states[symbol]['entry_price'] = current_price; coin_states[symbol]['pos'] = "LONG"
                            logger.log(action="OPEN_LONG", symbol=symbol, price=current_price, amount=order_amount, tag="訊號", pnl=0, balance=initial_balance+accumulated_pnl)
                            
                            send_trade_signal_email(symbol, df, "OPEN LONG", current_price)

                    elif signal == "SHORT":
                        if current_pos == "LONG":
                            print(f"🔄 反手做空")
                            accumulated_pnl += net_pnl_usdt; update_trade_stats(net_pnl_usdt)
                            executor.close_position(symbol=symbol)
                            logger.log(action="CLOSE_LONG", symbol=symbol, price=current_price, amount=order_amount, tag="反手", pnl=net_pnl_usdt, balance=initial_balance+accumulated_pnl)
                            executor.place_order('sell', symbol=symbol, amount=order_amount)
                            coin_states[symbol]['entry_price'] = current_price; coin_states[symbol]['pos'] = "SHORT"
                            logger.log(action="OPEN_SHORT", symbol=symbol, price=current_price, amount=order_amount, tag="訊號", pnl=0, balance=initial_balance+accumulated_pnl)
                            
                            send_trade_signal_email(symbol, df, "OPEN SHORT (反手)", current_price)

                        elif current_pos is None:
                            print(f"📉 進場做空")
                            executor.place_order('sell', symbol=symbol, amount=order_amount)
                            coin_states[symbol]['entry_price'] = current_price; coin_states[symbol]['pos'] = "SHORT"
                            logger.log(action="OPEN_SHORT", symbol=symbol, price=current_price, amount=order_amount, tag="訊號", pnl=0, balance=initial_balance+accumulated_pnl)
                            
                            send_trade_signal_email(symbol, df, "OPEN SHORT", current_price)

                    time.sleep(1)

                print(f"\n💤 交易掃描完成，系統待機中...")
                next_trade_time = now + timedelta(minutes=15)

            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n🛑 程式手動停止"); break
        except Exception as e:
            print(f"❌ 發生錯誤: {e}"); time.sleep(5)

if __name__ == "__main__":
    run_bot()