import time
import json
import os
from datetime import datetime, timedelta
from data_loader import BingXLoader
from strategies import RuleBasedStrategy
from executor import BingXExecutor
from trade_logger import TradeLogger
from mailer import GmailNotifier
from ai_reporter import AIReportGenerator
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
    
    target_tf = '15m' 

    # 初始化狀態
    for symbol in config.COIN_LIST:
        coin_states[symbol] = {'entry_price': 0.0, 'pos': None}

    # ==========================================
    # 歷史回補 (略)
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

    # 🔥 發信函式修正：將 symbol 傳給 ai_reporter
    def send_ai_entry_report(symbol, df, action, price):
        try:
            # 🔥 修改點：這裡傳入 symbol
            ai_content = ai_reporter.generate_entry_report(df, action, price, symbol)
            mailer.send_report(f"進場通知 ({symbol}) - {action}", ai_content)
        except Exception as e:
            print(f"⚠️ 發送進場報告失敗: {e}")

    def get_order_amount(symbol):
        if hasattr(config, 'ORDER_SIZES') and isinstance(config.ORDER_SIZES, dict):
            return config.ORDER_SIZES.get(symbol, config.ORDER_AMOUNT)
        return config.ORDER_AMOUNT

    next_report_time = datetime.now()
    next_trade_time = datetime.now()

    while True:
        try:
            now = datetime.now()

            # ======================================
            # 🕒 1. 定期報告
            # ======================================
            if config.ENABLE_PERIODIC_REPORT and now >= next_report_time:
                print(f"\n⏰ 定期報告時間到 (每 {config.REPORT_INTERVAL_MINUTES} 分鐘)...")
                
                for symbol in config.COIN_LIST:
                    print(f"\n📡 [報告] 正在抓取 {symbol} 數據...")
                    report_df = loader.fetch_data(symbol=symbol, timeframe=config.REPORT_TIMEFRAME)
                    
                    if report_df is not None:
                        print(f"🤖 AI 正在撰寫 {symbol} 市場趨勢報告...")
                        try:
                            # 🔥 修改點：這裡傳入 symbol
                            report_content = ai_reporter.generate_market_report(report_df, symbol)
                            mailer.send_report(f"📅 市場趨勢報告 ({symbol})", report_content)
                            print(f"📨 {symbol} 報告已寄出")
                        except Exception as e:
                            print(f"❌ {symbol} AI 報告失敗: {e}")
                    
                    print("⏳ 休息 15 秒避免 AI 額度超標...")
                    time.sleep(15)

                print(f"✅ 所有定期報告發送完成")
                next_report_time = now + timedelta(minutes=config.REPORT_INTERVAL_MINUTES)

            # ======================================
            # 📈 2. 交易邏輯
            # ======================================
            if now >= next_trade_time:
                print(f"\n======== 🔄 開始新一輪掃描 ({target_tf}) ========")
                
                for symbol in config.COIN_LIST:
                    print(f"\n🔍 正在分析: {symbol}")
                    
                    df = loader.fetch_data(symbol=symbol, timeframe=target_tf)
                    if df is None:
                        time.sleep(1)
                        continue

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

                    net_pnl_usdt = 0.0
                    net_pnl_pct = 0.0
                    estimated_fee = 0.0

                    if current_pos is not None and entry_price > 0:
                        diff = (current_price - entry_price) if current_pos == "LONG" else (entry_price - current_price)
                        gross_pnl = diff * order_amount
                        estimated_fee = (entry_price + current_price) * order_amount * config.TRADING_FEE_RATE
                        net_pnl_usdt = gross_pnl - estimated_fee
                        net_pnl_pct = net_pnl_usdt / (entry_price * order_amount)
                        
                        print(f"📉 目前艙位損益: {net_pnl_pct*100:.4f}% ({net_pnl_usdt:+.4f} U)")
                        print(f"   (進場: {entry_price} -> 現價: {current_price})")

                    current_equity = initial_balance + accumulated_pnl + net_pnl_usdt
                    nav_pct = (current_equity / initial_balance - 1) * 100
                    acc_pnl_pct = (accumulated_pnl / initial_balance) * 100
                    
                    pos_info = "空手"
                    if current_pos:
                        pos_value = current_price * order_amount
                        pos_info = f"{current_pos} ({order_amount} {coin_name_short} / {pos_value:.4f} U)"
                    
                    print(f"💰 現價: {current_price} | 🛡️  持倉: {pos_info}")
                    print(f"💼 資金: 初始{initial_balance:.1f} / 權益{current_equity:.1f} ({nav_pct:.2f}%) / 累損益{accumulated_pnl:.1f}")

                    # SL/TP
                    if current_pos is not None and entry_price > 0:
                        if net_pnl_pct <= -config.STOP_LOSS_PCT:
                            print(f"🛑 {symbol} 觸發止損！")
                            executor.close_position(symbol=symbol)
                            accumulated_pnl += net_pnl_usdt
                            update_trade_stats(net_pnl_usdt)
                            logger.log(action=f"CLOSE_{current_pos} (SL)", symbol=symbol, price=current_price, amount=order_amount, tag="止損", pnl=net_pnl_usdt, balance=initial_balance+accumulated_pnl)
                            coin_states[symbol]['entry_price'] = 0.0; coin_states[symbol]['pos'] = None
                            time.sleep(1); continue 
                        elif net_pnl_pct >= config.TAKE_PROFIT_PCT:
                            print(f"🎉 {symbol} 觸發止盈！")
                            executor.close_position(symbol=symbol)
                            accumulated_pnl += net_pnl_usdt
                            update_trade_stats(net_pnl_usdt)
                            logger.log(action=f"CLOSE_{current_pos} (TP)", symbol=symbol, price=current_price, amount=order_amount, tag="止盈", pnl=net_pnl_usdt, balance=initial_balance+accumulated_pnl)
                            coin_states[symbol]['entry_price'] = 0.0; coin_states[symbol]['pos'] = None
                            time.sleep(1); continue

                    # 進出場
                    if signal == "LONG":
                        if current_pos == "SHORT":
                            print(f"🔄 {symbol} 反手：平空開多")
                            accumulated_pnl += net_pnl_usdt
                            update_trade_stats(net_pnl_usdt)
                            executor.close_position(symbol=symbol)
                            logger.log(action="CLOSE_SHORT", symbol=symbol, price=current_price, amount=order_amount, tag="反手", pnl=net_pnl_usdt, balance=initial_balance+accumulated_pnl)
                            
                            executor.place_order('buy', symbol=symbol, amount=order_amount)
                            coin_states[symbol]['entry_price'] = current_price; coin_states[symbol]['pos'] = "LONG"
                            logger.log(action="OPEN_LONG", symbol=symbol, price=current_price, amount=order_amount, tag="訊號", pnl=0, balance=initial_balance+accumulated_pnl)
                            send_ai_entry_report(symbol, df, "OPEN LONG (反手)", current_price)

                        elif current_pos is None:
                            print(f"🚀 {symbol} 進場做多")
                            executor.place_order('buy', symbol=symbol, amount=order_amount)
                            coin_states[symbol]['entry_price'] = current_price; coin_states[symbol]['pos'] = "LONG"
                            logger.log(action="OPEN_LONG", symbol=symbol, price=current_price, amount=order_amount, tag="訊號", pnl=0, balance=initial_balance+accumulated_pnl)
                            send_ai_entry_report(symbol, df, "OPEN LONG", current_price)

                    elif signal == "SHORT":
                        if current_pos == "LONG":
                            print(f"🔄 {symbol} 反手：平多開空")
                            accumulated_pnl += net_pnl_usdt
                            update_trade_stats(net_pnl_usdt)
                            executor.close_position(symbol=symbol)
                            logger.log(action="CLOSE_LONG", symbol=symbol, price=current_price, amount=order_amount, tag="反手", pnl=net_pnl_usdt, balance=initial_balance+accumulated_pnl)
                            
                            executor.place_order('sell', symbol=symbol, amount=order_amount)
                            coin_states[symbol]['entry_price'] = current_price; coin_states[symbol]['pos'] = "SHORT"
                            logger.log(action="OPEN_SHORT", symbol=symbol, price=current_price, amount=order_amount, tag="訊號", pnl=0, balance=initial_balance+accumulated_pnl)
                            send_ai_entry_report(symbol, df, "OPEN SHORT (反手)", current_price)

                        elif current_pos is None:
                            print(f"📉 {symbol} 進場做空")
                            executor.place_order('sell', symbol=symbol, amount=order_amount)
                            coin_states[symbol]['entry_price'] = current_price; coin_states[symbol]['pos'] = "SHORT"
                            logger.log(action="OPEN_SHORT", symbol=symbol, price=current_price, amount=order_amount, tag="訊號", pnl=0, balance=initial_balance+accumulated_pnl)
                            send_ai_entry_report(symbol, df, "OPEN SHORT", current_price)

                    time.sleep(1)

                print(f"\n💤 掃描完成，等待 15 分鐘...")
                next_trade_time = now + timedelta(minutes=15)

            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n🛑 程式手動停止"); break
        except Exception as e:
            print(f"❌ 發生錯誤: {e}"); time.sleep(10)

if __name__ == "__main__":
    run_bot()