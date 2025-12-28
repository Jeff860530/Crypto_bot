# strategies/__init__.py
from .base_strategy import BaseStrategy
from .ma_cross_strategy import MACrossStrategy
from .harmonic_strategy import HarmonicStrategy
# from .rsi_reversal_strategy import RsiReversalStrategy (如果有的話)

# 🔥 建立一個對照表，方便字串轉物件
STRATEGY_MAP = {
    "MACrossStrategy": MACrossStrategy,
    "HarmonicStrategy": HarmonicStrategy,
    # "RsiReversalStrategy": RsiReversalStrategy
}