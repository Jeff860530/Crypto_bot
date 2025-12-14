import time
import json
import os
from data_loader import BingXLoader
from strategies import RuleBasedStrategy
from executor import BingXExecutor
from trade_logger import TradeLogger
import config

# --- 全域變數 (統計數據) ---
entry_price = 0.0
initial_balance = 1000.0
accumulated_pnl = 0.0     # 淨累積損益
total_win_amount = 0.0    # 總獲利金額
total_loss_amount = 0.0   # 總虧損金額
win_count = 0             # 獲利次數
loss_count = 0            # 虧損次數

# 🔥 設定 Log 檔案路徑
LOG_FILE = "logs/trade_history.json"

def run_bot():
    global entry_price, initial_balance, accumulated_pnl
    global total_win_amount, total_loss_amount, win_count, loss_count
    
    print(f"🤖 Crypto Bot 啟動中... (模式: {'🧪 模擬' if config.DRY_RUN else '⚡ 真實'})")
    print(f"💼 預設初始本金: {initial_balance} USDT")
    
    loader = BingXLoader()
    executor = BingXExecutor(loader.exchange)
    strategy = RuleBasedStrategy()
    
    # 🔥 傳入新的路徑給 Logger
    logger = TradeLogger(filename=LOG_FILE)
    
    target_tf = '15m' 
    
    # 解析幣種名稱 (例如從 BTC-USDT 取得 BTC)
    try:
        coin_name = config.SYMBOL.split('-')[0] if '-' in config.SYMBOL else config.SYMBOL.split('/')[0]
    except:
        coin_name = "COIN"

    # ==========================================
    # 🔥 啟動時讀取 logs/trade_history.json 回補戰績
    # ==========================================
    # 確保資料夾存在
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    if os.path.exists(LOG_FILE):
        try:
            print(f"📖 正在讀取歷史交易紀錄 ({LOG_FILE})...")
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                for trade in history:
                    # 讀取每筆交易的已實現損益
                    pnl = trade.get("realized_pnl", 0.0)
                    if pnl != 0:
                        accumulated_pnl += pnl
                        if pnl > 0:
                            win_count += 1
                            total_win_amount += pnl
                        else:
                            loss_count += 1
                            total_loss_amount += abs(pnl)
            print(f"✅ 歷史戰績回補完成！(累積損益: {accumulated_pnl:.4f} U)")
        except Exception as e:
            print(f"⚠️ 讀取歷史紀錄失敗: {e}")
    else:
        print("ℹ️ 尚無歷史紀錄，將建立新檔案。")
    # ==========================================

    if not config.DRY_RUN:
        try:
            balance = loader.exchange.fetch_balance()
            initial_balance = float(balance['USDT']['total'])
            print(f"💼 偵測到真實帳戶餘額: {initial_balance} USDT")
        except Exception as e:
            print(f"⚠️ 無法讀取真實餘額 (使用預設值): {e}")

    # 內部函式：更新統計 (當下平倉時用)
    def update_trade_stats(pnl):
        global total_win_amount, total_loss_amount, win_count, loss_count
        if pnl > 0:
            win_count += 1
            total_win_amount += pnl
        elif pnl < 0:
            loss_count += 1
            total_loss_amount += abs(pnl)

    while True:
        try:
            print(f"\n--- 正在分析 {target_tf} ---")
            
            # 1. 獲取數據
            df = loader.fetch_data(timeframe=target_tf)
            if df is None:
                time.sleep(5)
                continue

            # 2. 獲取狀態
            current_pos = executor.get_open_position()
            current_price = df.iloc[-1]['close'] 
            
            # 3. 策略分析
            result = strategy.analyze(df)
            signal = result['action']
            
            if signal == "HOLD":
                if "多頭" in result['info']: signal = "LONG"
                elif "空頭" in result['info']: signal = "SHORT"

            # ==============================
            # 🧮 損益與資產計算核心
            # ==============================
            net_pnl_usdt = 0.0
            net_pnl_pct = 0.0
            estimated_fee = 0.0

            if current_pos is not None and entry_price > 0:
                # 價差毛利
                diff = (current_price - entry_price) if current_pos == "LONG" else (entry_price - current_price)
                gross_pnl = diff * config.ORDER_AMOUNT
                
                # 手續費
                entry_fee = entry_price * config.ORDER_AMOUNT * config.TRADING_FEE_RATE
                exit_fee = current_price * config.ORDER_AMOUNT * config.TRADING_FEE_RATE
                estimated_fee = entry_fee + exit_fee
                
                # 淨利
                net_pnl_usdt = gross_pnl - estimated_fee
                net_pnl_pct = net_pnl_usdt / (entry_price * config.ORDER_AMOUNT)
                
                # 🔥 修改點：文字改為「目前艙位損益」
                print(f"📉 目前倉位損益: {net_pnl_pct*100:.4f}% ({net_pnl_usdt:+.4f} U) | 手續費預估: {estimated_fee:.4f} U")
                print(f"   (進場: {entry_price} -> 現價: {current_price})")

            # 計算當前總權益
            current_equity = initial_balance + accumulated_pnl + net_pnl_usdt
            nav_pct = (current_equity / initial_balance) * 100
            acc_pnl_pct = (accumulated_pnl / initial_balance) * 100

            # 計算盈虧比
            pf_ratio = 0.0
            if total_loss_amount > 0:
                pf_ratio = total_win_amount / total_loss_amount
            elif total_win_amount > 0: 
                pf_ratio = 999.0

            # ---------------- 印出 Dashboard ----------------
            pos_info = "空手"
            if current_pos:
                pos_value = current_price * config.ORDER_AMOUNT
                pos_info = f"{current_pos} ({config.ORDER_AMOUNT} {coin_name} / {pos_value:.4f} U)"
            
            print(f"💰 現價: {current_price} | 🛡️  持倉: {pos_info}")
            print(f"💼 初始投資({initial_balance:.4f} U) / 累積損益({acc_pnl_pct:.4f}% | {accumulated_pnl:+.4f} U) / 資產資訊({nav_pct:.4f}% | {current_equity:.4f} U)")
            print(f"📊 統計: 盈虧金額(盈:{total_win_amount:.4f}U / 虧:{total_loss_amount:.4f}U) | 盈虧比({total_win_amount:.2f}:{total_loss_amount:.2f} / {pf_ratio:.3f}) | 次數(盈:{win_count} / 虧:{loss_count})")
            print(f"⚙️  風控參數: 槓桿 {config.LEVERAGE}x | 止損 {config.STOP_LOSS_PCT*100:.4f}% | 止盈 {config.TAKE_PROFIT_PCT*100:.4f}% | 手續費率 {config.TRADING_FEE_RATE*100:.2f}%")
            # ------------------------------------------------

            # ==============================
            # ⚖️ 風控檢查 (SL/TP)
            # ==============================
            if current_pos is not None and entry_price > 0:
                current_pnl_ratio = net_pnl_pct 
                
                if current_pnl_ratio <= -config.STOP_LOSS_PCT:
                    print(f"🛑 觸發止損！(淨虧損 {current_pnl_ratio*100:.4f}%)")
                    executor.close_position()
                    
                    accumulated_pnl += net_pnl_usdt
                    update_trade_stats(net_pnl_usdt)
                    current_equity = initial_balance + accumulated_pnl
                    
                    logger.log(action=f"CLOSE_{current_pos} (SL)", price=current_price, amount=config.ORDER_AMOUNT, tag="止損觸發", pnl=net_pnl_usdt, balance=current_equity)
                    
                    entry_price = 0.0
                    time.sleep(5)
                    continue

                elif current_pnl_ratio >= config.TAKE_PROFIT_PCT:
                    print(f"🎉 觸發止盈！(淨獲利 {current_pnl_ratio*100:.4f}%)")
                    executor.close_position()
                    
                    accumulated_pnl += net_pnl_usdt
                    update_trade_stats(net_pnl_usdt)
                    current_equity = initial_balance + accumulated_pnl
                    
                    logger.log(action=f"CLOSE_{current_pos} (TP)", price=current_price, amount=config.ORDER_AMOUNT, tag="止盈觸發", pnl=net_pnl_usdt, balance=current_equity)
                    
                    entry_price = 0.0
                    time.sleep(5)
                    continue

            # ==============================
            # 🚀 策略進出場邏輯
            # ==============================
            if signal == "LONG":
                if current_pos == "SHORT":
                    print("🔄 反手：平空開多")
                    accumulated_pnl += net_pnl_usdt
                    update_trade_stats(net_pnl_usdt)
                    executor.close_position()
                    logger.log(action="CLOSE_SHORT", price=current_price, amount=config.ORDER_AMOUNT, tag="策略反轉", pnl=net_pnl_usdt, balance=initial_balance + accumulated_pnl)
                    
                    executor.place_order('buy')
                    entry_price = current_price
                    logger.log(action="OPEN_LONG", price=current_price, amount=config.ORDER_AMOUNT, tag="策略訊號", pnl=0, balance=initial_balance + accumulated_pnl)

                elif current_pos is None:
                    print("🚀 進場做多")
                    executor.place_order('buy')
                    entry_price = current_price
                    logger.log(action="OPEN_LONG", price=current_price, amount=config.ORDER_AMOUNT, tag="策略訊號", pnl=0, balance=initial_balance + accumulated_pnl)
                else:
                    print("✅ 持有多單續抱")

            elif signal == "SHORT":
                if current_pos == "LONG":
                    print("🔄 反手：平多開空")
                    accumulated_pnl += net_pnl_usdt
                    update_trade_stats(net_pnl_usdt)
                    executor.close_position()
                    logger.log(action="CLOSE_LONG", price=current_price, amount=config.ORDER_AMOUNT, tag="策略反轉", pnl=net_pnl_usdt, balance=initial_balance + accumulated_pnl)
                    
                    executor.place_order('sell')
                    entry_price = current_price
                    logger.log(action="OPEN_SHORT", price=current_price, amount=config.ORDER_AMOUNT, tag="策略訊號", pnl=0, balance=initial_balance + accumulated_pnl)

                elif current_pos is None:
                    print("📉 進場做空")
                    executor.place_order('sell')
                    entry_price = current_price
                    logger.log(action="OPEN_SHORT", price=current_price, amount=config.ORDER_AMOUNT, tag="策略訊號", pnl=0, balance=initial_balance + accumulated_pnl)
                else:
                    print("✅ 持有空單續抱")

            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n🛑 程式手動停止")
            break
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()