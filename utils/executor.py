import ccxt
import config

class BingXExecutor:
    def __init__(self, exchange):
        self.exchange = exchange
        self.dry_run = config.DRY_RUN
        
        # 模擬倉位儲存: {'BTC-USDT': 'LONG', ...}
        self.simulated_positions = {} 
        
        if not self.dry_run:
            print("⚙️ [Executor] 正在為監控清單設定槓桿...")
            for symbol in config.COIN_LIST:
                self.set_leverage(config.LEVERAGE, symbol)

    def set_leverage(self, leverage, symbol):
        if self.dry_run: return 
        try:
            self.exchange.set_leverage(leverage, symbol)
        except Exception as e:
            print(f"⚠️ 設定槓桿失敗 ({symbol}): {e}")

    def get_open_position(self, symbol):
        """回傳 'LONG', 'SHORT' 或 None"""
        if self.dry_run:
            return self.simulated_positions.get(symbol)

        try:
            # 針對特定幣種查詢真實倉位
            # 注意: CCXT BingX fetch_positions 可能需要 symbol 格式轉換
            positions = self.exchange.fetch_positions([symbol.replace('-', '/')])
            for pos in positions:
                # 檢查合約數量 > 0
                if float(pos['contracts']) > 0:
                    return pos['side'].upper() # LONG / SHORT
            return None
        except Exception as e:
            print(f"⚠️ 讀取倉位失敗 ({symbol}): {e}")
            return None

    def place_order(self, side, symbol, amount):
        if self.dry_run:
            print(f"🧪 [模擬] {symbol} 下單: {side.upper()} {amount}")
            # 更新模擬狀態
            pos_type = 'LONG' if side == 'buy' else 'SHORT'
            self.simulated_positions[symbol] = pos_type
            return {'id': 'sim_order_id'}

        try:
            print(f"⚡ [真實] {symbol} 下單: {side.upper()} {amount} ...")
            order = self.exchange.create_market_order(symbol.replace('-', '/'), side, amount)
            print(f"✅ 下單成功! ID: {order['id']}")
            return order
        except Exception as e:
            print(f"❌ 下單失敗 ({symbol}): {e}")
            return None
        
    def close_position(self, symbol):
        if self.dry_run:
            if self.simulated_positions.get(symbol):
                print(f"🧪 [模擬] {symbol} 平倉成功")
                self.simulated_positions[symbol] = None
            return

        try:
            # 真實平倉：通常使用 reduceOnly 或查詢當前持倉量後反向操作
            # 這裡簡單示範：先查方向，再反向市價全平
            current_pos = self.get_open_position(symbol)
            if not current_pos:
                return

            side = 'sell' if current_pos == 'LONG' else 'buy'
            # 注意：BingX 平倉最好傳入 reduceOnly: True
            # Amount 這裡暫時用 config 的設定，理想情況是讀取當前持倉數量
            amount = config.ORDER_SIZES.get(symbol, config.ORDER_AMOUNT)

            print(f"⚡ [真實] {symbol} 平倉: {side.upper()} ...")
            self.exchange.create_market_order(
                symbol.replace('-', '/'), 
                side, 
                amount, 
                params={'reduceOnly': True} 
            )
            print(f"✅ {symbol} 平倉指令已發送")
            
        except Exception as e:
            print(f"❌ 平倉失敗 ({symbol}): {e}")