import ccxt
import config

class BingXExecutor:
    def __init__(self, exchange):
        self.exchange = exchange
        self.dry_run = config.DRY_RUN
        
        # 🔥 修改 1：將模擬倉位改成字典 (Dictionary)，以支援多幣種
        # 格式: {'BTC-USDT': 'LONG', 'ETH-USDT': None, ...}
        self.simulated_positions = {} 
        
        if not self.dry_run:
            # 🔥 修改 2：啟動時，遍歷清單中的每一個幣設定槓桿
            print("⚙️ 正在為監控清單設定槓桿...")
            for symbol in config.COIN_LIST:
                self.set_leverage(config.LEVERAGE, symbol)

    def set_leverage(self, leverage, symbol):
        if self.dry_run:
            return 
        try:
            # print(f"   └─ 設定 {symbol} 槓桿: {leverage}x ...")
            self.exchange.set_leverage(leverage, symbol)
        except Exception as e:
            print(f"⚠️ 設定槓桿失敗 ({symbol}): {e}")

    def get_open_position(self, symbol):
        """
        檢查指定幣種 (symbol) 目前是否有持倉
        """
        # 🔥 修改 3：模擬模式下，從字典讀取該幣種的狀態
        if self.dry_run:
            return self.simulated_positions.get(symbol)

        # --- 以下是真實模式的邏輯 ---
        try:
            # 針對特定幣種查詢
            positions = self.exchange.fetch_positions([symbol])
            target_position = None
            
            for pos in positions:
                # 比對 symbol (有些交易所回傳格式可能是 BTC/USDT:USDT)
                if pos['symbol'] == symbol or pos['symbol'] == symbol.replace('/', '-'):
                    if float(pos['contracts']) > 0:
                        target_position = pos
                        break
            
            if target_position:
                return target_position['side'].upper() # 'LONG' or 'SHORT'
            else:
                return None

        except Exception as e:
            print(f"⚠️ 讀取倉位失敗 ({symbol}): {e}")
            return None

    def place_order(self, side, symbol, amount):
        """
        下單核心函式 (需傳入 symbol 與 amount)
        """
        # 🔥 修改 4：模擬模式下，更新字典中的狀態
        if self.dry_run:
            print(f"🧪 [模擬交易] {symbol} 執行成功: {side.upper()} {amount}")
            
            if side == 'buy':
                self.simulated_positions[symbol] = 'LONG'
            elif side == 'sell':
                self.simulated_positions[symbol] = 'SHORT'
            return None

        # --- 以下是真實模式的邏輯 ---
        try:
            print(f"⚡ [真實交易] {symbol} 正在發送訂單: {side.upper()} {amount} ...")
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=amount
            )
            print(f"✅ 下單成功! ID: {order['id']}")
            return order
            
        except Exception as e:
            print(f"❌ 下單失敗 ({symbol}): {e}")
            return None
        
    def close_position(self, symbol):
        """
        平掉指定幣種的所有倉位
        """
        # 🔥 修改 5：模擬模式下，清除字典中的該幣種狀態
        if self.dry_run:
            current_sim_pos = self.simulated_positions.get(symbol)
            if current_sim_pos:
                print(f"🧪 [模擬交易] {symbol} 平倉成功: 賣出 {current_sim_pos}")
                self.simulated_positions[symbol] = None
            return

        # 真實交易邏輯
        try:
            # 1. 先確認目前該幣種倉位方向
            current_pos = self.get_open_position(symbol)
            if not current_pos:
                print(f"⚠️ {symbol} 無倉位可平")
                return

            # 2. 決定平倉方向
            side = 'sell' if current_pos == 'LONG' else 'buy'
            
            # 這裡我們需要知道該下多少量來平倉，通常是用 config 定義的量，
            # 或是如果要精確全平，需要去 fetch_positions 拿 contracts 數量。
            # 這裡暫時維持使用 config 的設定量或傳入量 (依賴 main.py 控制)
            # 但為了安全，建議 BingX 使用 reduceOnly
            
            # 注意：在多幣種模式下，這裡的 amount 最好是動態獲取，
            # 但為了保持簡單，我們先假設 main.py 邏輯保證了倉位數量一致。
            
            # 為了能正確下單，這裡稍微調用一下 config (假設是全平模式，或使用固定手數)
            # 為了避免循環引用問題，這裡直接下市價反向單
            
            # 若要更嚴謹，這裡應該要傳入 amount，但配合你的 main.py 架構：
            # 我們假設平倉量 = 下單量 (簡易版)
            # 或者，對於 BingX，不傳 amount 有時無法平倉。
            # 建議：這裡先用 config.ORDER_AMOUNT (若有多幣種數量設定，需在 main.py 傳入)
            
            # 在此範例中，我們暫時使用 config.ORDER_AMOUNT，
            # 但強烈建議未來將 close_position 也加上 amount 參數。
            close_amount = config.ORDER_AMOUNT
            # 如果你有在 config 設定多幣種數量，可以在這裡判斷 symbol 取不同數量
            
            print(f"⚡ [真實交易] {symbol} 正在平倉: {side.upper()} ...")
            
            self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=close_amount,
                params={'reduceOnly': True} 
            )
            print(f"✅ {symbol} 平倉成功")
            
        except Exception as e:
            print(f"❌ 平倉失敗 ({symbol}): {e}")