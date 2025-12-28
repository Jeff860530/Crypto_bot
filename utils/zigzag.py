import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

class ZigZagIdentifier:
    def __init__(self, order: int = 5):
        self.order = order

    def find_pivots(self, df: pd.DataFrame) -> dict:
        if df is None or df.empty: return {}
        highs = df['high'].values
        lows = df['low'].values
        timestamps = df.index.values

        high_idx = argrelextrema(highs, np.greater, order=self.order)[0]
        low_idx = argrelextrema(lows, np.less, order=self.order)[0]
        
        high_points = [{'index': int(i), 'price': float(highs[i]), 'type': 'HIGH', 'time': str(timestamps[i])} for i in high_idx]
        low_points = [{'index': int(i), 'price': float(lows[i]), 'type': 'LOW', 'time': str(timestamps[i])} for i in low_idx]
            
        return {'highs': high_points, 'lows': low_points}
    
    def get_last_n_pivots(self, df: pd.DataFrame, n: int = 5) -> list:
        pivots = self.find_pivots(df)
        if not pivots: return []
        all_pivots = pivots['highs'] + pivots['lows']
        all_pivots.sort(key=lambda x: x['index'])
        return all_pivots[-n:]