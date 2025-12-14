import ccxt
import config

class BingXExecutor:
    def __init__(self, exchange):
        self.exchange = exchange
        self.symbol = config.SYMBOL
        self.dry_run = config.DRY_RUN
        
        # 🔥 新增：用來記憶模擬模式下的倉位狀態
        self.simulated_position = None 
        
        if not self.dry_run:
            self.set_leverage(config.LEVERAGE)

    def set_leverage(self, leverage):
        if self.dry_run:
            return # 模擬模式不需要真的設槓桿
        try:
            print(f"⚙️ 正在設定槓桿: {leverage}x ...")
            self.exchange.set_leverage(leverage, self.symbol)
        except Exception as e:
            print(f"⚠️ 設定槓桿失敗: {e}")

    def get_open_position(self):
        """
        檢查目前是否有持倉
        """
        # 🔥 修改點：如果是模擬模式，直接回傳記憶體中的變數
        if self.dry_run:
            return self.simulated_position

        # --- 以下是真實模式的邏輯 (不變) ---
        try:
            positions = self.exchange.fetch_positions([self.symbol])
            target_position = None
            
            for pos in positions:
                if pos['symbol'] == self.symbol or pos['symbol'] == self.symbol.replace('/', '-'):
                    if float(pos['contracts']) > 0:
                        target_position = pos
                        break
            
            if target_position:
                return target_position['side'].upper() # 'LONG' or 'SHORT'
            else:
                return None

        except Exception as e:
            print(f"⚠️ 讀取倉位失敗: {e}")
            return None

    def place_order(self, side, amount=config.ORDER_AMOUNT):
        """
        下單核心函式
        """
        # 🔥 修改點：模擬模式下，更新本地狀態
        if self.dry_run:
            print(f"🧪 [模擬交易] 執行成功: {side.upper()} {amount} {self.symbol}")
            
            # 更新模擬狀態
            # 邏輯：如果做多(buy)，狀態變 LONG；如果做空(sell)，狀態變 SHORT
            # (這裡簡化處理，假設每次下單都是開倉或反手)
            if side == 'buy':
                self.simulated_position = 'LONG'
            elif side == 'sell':
                self.simulated_position = 'SHORT'
            return None

        # --- 以下是真實模式的邏輯 (不變) ---
        try:
            print(f"⚡ [真實交易] 正在發送訂單: {side.upper()} {amount} ...")
            order = self.exchange.create_market_order(
                symbol=self.symbol,
                side=side,
                amount=amount
            )
            print(f"✅ 下單成功! ID: {order['id']}")
            return order
            
        except Exception as e:
            print(f"❌ 下單失敗: {e}")
            return None
        
    def close_position(self):
        """
        平掉目前所有倉位
        """
        if self.dry_run:
            if self.simulated_position:
                print(f"🧪 [模擬交易] 平倉成功: 賣出 {self.simulated_position}")
                self.simulated_position = None
            return

        # 真實交易邏輯
        try:
            # 1. 先確認目前倉位方向
            current_pos = self.get_open_position()
            if not current_pos:
                print("⚠️ 無倉位可平")
                return

            # 2. 決定平倉方向 (持有 LONG 就要 sell, 持有 SHORT 就要 buy)
            side = 'sell' if current_pos == 'LONG' else 'buy'
            
            print(f"⚡ [真實交易] 正在平倉: {side.upper()} {config.ORDER_AMOUNT} ...")
            
            # BingX 平倉通常只需發送反向市價單
            # 注意: 某些交易所需要設定 reduceOnly=True，但在這裡簡單反向操作通常可行
            self.exchange.create_market_order(
                symbol=self.symbol,
                side=side,
                amount=config.ORDER_AMOUNT,
                params={'reduceOnly': True} # 建議加上，確保只平倉不開新倉
            )
            print("✅ 平倉成功")
            
        except Exception as e:
            print(f"❌ 平倉失敗: {e}")