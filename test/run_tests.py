# tests/run_tests.py
import unittest
import sys
import os
import pandas as pd
import warnings

# 忽略 FutureWarning 讓輸出乾淨點
warnings.simplefilter(action='ignore', category=FutureWarning)

# 🔥 設定路徑：讓測試腳本能找到上一層的模組
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 引入要測試的模組
import config
from utils.data_loader import BingXLoader
from services.market_data_service import MarketDataService
from strategies.ma_cross_strategy import MACrossStrategy
from strategies.harmonic_strategy import HarmonicStrategy
from utils.executor import BingXExecutor
import ccxt

class TestCryptoBot(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """所有測試開始前執行一次，建立共用物件"""
        print("\n🤖 === 開始 Crypto Bot 單元測試 ===\n")
        cls.symbol = "ETH-USDT" # 測試用幣種
        cls.timeframe = "15m"
        
        # 1. 測試 Loader
        cls.loader = BingXLoader()
        
        # 2. 測試 MarketDataService
        cls.market_service = MarketDataService()

    def test_01_data_loader(self):
        """測試：從交易所抓取 K 線數據"""
        print("🧪 [1/5] 測試 Data Loader...")
        df = self.loader.fetch_data(self.timeframe, self.symbol, limit=100)
        
        # 驗證數據是否正確
        self.assertIsNotNone(df, "數據不應為 None")
        self.assertFalse(df.empty, "數據不應為空")
        self.assertIn('close', df.columns, "必須包含 close 欄位")
        self.assertIn('volume', df.columns, "必須包含 volume 欄位")
        
        print(f"   ✅ 成功獲取 {len(df)} 筆 K 線數據")
        
        # 存起來給後面的測試用，避免重複打 API
        TestCryptoBot.shared_df = df

    def test_02_market_data_calculation(self):
        """測試：計算技術指標 (MA, RSI, ZigZag)"""
        print("🧪 [2/5] 測試 技術指標計算...")
        df = TestCryptoBot.shared_df
        
        context = self.market_service.analyze_technicals(df)
        
        # 驗證關鍵指標是否存在
        self.assertIn('rsi', context, "缺少 RSI")
        self.assertIn('ma_fast', context, "缺少 MA Fast")
        self.assertIn('pivots', context, "缺少 ZigZag Pivots")
        
        # 驗證數值是否合理
        rsi = context['rsi']
        self.assertTrue(0 <= rsi <= 100, f"RSI 數值異常: {rsi}")
        
        pivots = context.get('pivots', [])
        print(f"   ✅ 指標計算完成 (RSI={rsi:.1f}, 轉折點數={len(pivots)})")
        
        # 存起來給策略測試用
        TestCryptoBot.shared_context = context

    def test_03_zigzag_logic(self):
        """測試：ZigZag 轉折點邏輯"""
        print("🧪 [3/5] 測試 ZigZag 結構...")
        pivots = TestCryptoBot.shared_context.get('pivots', [])
        
        if len(pivots) > 0:
            last_p = pivots[-1]
            self.assertIn('price', last_p)
            self.assertIn('type', last_p)
            self.assertIn(last_p['type'], ['HIGH', 'LOW'])
            print(f"   ✅ ZigZag 格式正確: {last_p['type']} @ {last_p['price']}")
        else:
            print("   ⚠️ 警告: 樣本數據過短，未抓到轉折點 (這在短 K 線中可能發生)")

    def test_04_strategies(self):
        """測試：策略分析邏輯 (MA交叉 & 諧波)"""
        print("🧪 [4/5] 測試 策略模組...")
        df = TestCryptoBot.shared_df
        context = TestCryptoBot.shared_context
        
        # A. 測試 MA 策略
        ma_strategy = MACrossStrategy()
        res_ma = ma_strategy.analyze(df, context)
        self.assertIn(res_ma['signal'], ['LONG', 'SHORT', 'NEUTRAL'])
        print(f"   ✅ MA策略回傳: {res_ma['signal']} ({res_ma['reason']})")
        
        # B. 測試 諧波策略
        harmonic_strategy = HarmonicStrategy()
        res_har = harmonic_strategy.analyze(df, context)
        self.assertIn(res_har['signal'], ['LONG', 'SHORT', 'NEUTRAL'])
        print(f"   ✅ 諧波策略回傳: {res_har['signal']} ({res_har['reason']})")

    def test_05_executor_simulation(self):
        """測試：模擬下單功能"""
        print("🧪 [5/5] 測試 Executor (模擬模式)...")
        
        # 強制開啟 DRY_RUN 以免真的下單
        original_dry_run = config.DRY_RUN
        config.DRY_RUN = True 
        
        executor = BingXExecutor(None) # 傳入 None 因為模擬模式不需要真實 exchange 物件
        
        # 1. 測試下單
        order = executor.place_order('buy', self.symbol, 0.01)
        self.assertIsNotNone(order, "下單回傳不應為 None")
        
        # 2. 測試查詢倉位 (模擬記憶體)
        pos = executor.get_open_position(self.symbol)
        self.assertEqual(pos, 'LONG', "模擬倉位應該是 LONG")
        
        # 3. 測試平倉
        executor.close_position(self.symbol)
        pos_after = executor.get_open_position(self.symbol)
        self.assertIsNone(pos_after, "平倉後倉位應為 None")
        
        print("   ✅ 模擬下單/平倉流程通過")
        
        # 還原設定
        config.DRY_RUN = original_dry_run

if __name__ == '__main__':
    unittest.main()