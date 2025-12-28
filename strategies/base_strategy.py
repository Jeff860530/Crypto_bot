# strategies/base_strategy.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    @abstractmethod
    def analyze(self, df: pd.DataFrame, context: dict) -> dict:
        """
        所有策略都必須實作這個方法
        :param df: K線資料
        :param context: 市場指標 (RSI, ZigZag 等)
        :return: {
            "signal": "LONG" | "SHORT" | "NEUTRAL",
            "reason": "策略觸發原因",
            "stop_loss": 建議止損價,
            "take_profit": 建議止盈價
        }
        """
        pass