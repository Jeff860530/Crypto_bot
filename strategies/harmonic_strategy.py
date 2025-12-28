# strategies/harmonic_strategy.py
from .base_strategy import BaseStrategy

class HarmonicStrategy(BaseStrategy):
    def __init__(self):
        # 誤差容忍度 (例如 0.1 代表允許 10% 的誤差)
        self.tolerance = 0.1

    def analyze(self, df, context) -> dict:
        """
        諧波策略：分析 ZigZag 轉折點是否符合 Gartley 等型態
        """
        # 1. 取得由 MarketDataService 算好的轉折點
        pivots = context.get('pivots', [])
        
        # 諧波型態至少需要 5 個點 (X, A, B, C, D)
        if len(pivots) < 5:
            return {
                "signal": "NEUTRAL",
                "reason": "轉折點不足 (需5點)",
                "stop_loss": None,
                "take_profit": None
            }

        # 2. 取出最近的 5 個點 (注意：pivots 列表是 舊 -> 新)
        # 我們定義: X(0), A(1), B(2), C(3), D(4) 為最近的點 (D是最新價格附近)
        # 所以要倒著取
        P_D = pivots[-1] # 最新
        P_C = pivots[-2]
        P_B = pivots[-3]
        P_A = pivots[-4]
        P_X = pivots[-5] # 最舊

        # 3. 取出價格與方向
        price_X, type_X = P_X['price'], P_X['type']
        price_A, type_A = P_A['price'], P_A['type']
        price_B, type_B = P_B['price'], P_B['type']
        price_C, type_C = P_C['price'], P_C['type']
        # D點通常是「現在價格」或「剛形成的轉折」，這裡假設 D 點是最新轉折
        price_D, type_D = P_D['price'], P_D['type']

        signal = "NEUTRAL"
        reason = ""

        # ==========================================
        # 4. 判斷型態：Bullish Gartley (看漲)
        # 結構: X(低) -> A(高) -> B(低) -> C(高) -> D(低)
        # ==========================================
        if type_X == "LOW" and type_A == "HIGH" and type_B == "LOW" and type_C == "HIGH" and type_D == "LOW":
            
            # --- 計算斐波那契比例 ---
            XA_len = abs(price_X - price_A)
            AB_len = abs(price_A - price_B)
            BC_len = abs(price_B - price_C)
            CD_len = abs(price_C - price_D)
            XD_len = abs(price_X - price_D)

            # B點回撤: AB / XA (Gartley 標準 0.618)
            ratio_B = AB_len / XA_len
            
            # D點回撤: XD / XA (Gartley 標準 0.786)
            ratio_D = XD_len / XA_len

            # 檢查誤差 (Tolerance)
            is_B_valid = abs(ratio_B - 0.618) <= self.tolerance
            is_D_valid = abs(ratio_D - 0.786) <= self.tolerance
            
            if is_B_valid and is_D_valid:
                signal = "LONG"
                reason = f"Bullish Gartley (B={ratio_B:.2f}, D={ratio_D:.2f})"
                
                # 建議止損: X 點下方
                stop_loss = price_X * 0.995 
                # 建議止盈: AD 的 0.618 回調處
                take_profit = price_D + (abs(price_A - price_D) * 0.618)
                
                return {
                    "signal": signal,
                    "reason": reason,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }

        # ==========================================
        # 5. 判斷型態：Bearish Gartley (看跌)
        # 結構: X(高) -> A(低) -> B(高) -> C(低) -> D(高)
        # ==========================================
        elif type_X == "HIGH" and type_A == "LOW" and type_B == "HIGH" and type_C == "LOW" and type_D == "HIGH":
            
            XA_len = abs(price_X - price_A)
            AB_len = abs(price_A - price_B)
            XD_len = abs(price_X - price_D)

            ratio_B = AB_len / XA_len
            ratio_D = XD_len / XA_len

            is_B_valid = abs(ratio_B - 0.618) <= self.tolerance
            is_D_valid = abs(ratio_D - 0.786) <= self.tolerance
            
            if is_B_valid and is_D_valid:
                signal = "SHORT"
                reason = f"Bearish Gartley (B={ratio_B:.2f}, D={ratio_D:.2f})"
                
                # 建議止損: X 點上方
                stop_loss = price_X * 1.005
                take_profit = price_D - (abs(price_A - price_D) * 0.618)

                return {
                    "signal": signal,
                    "reason": reason,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }

        # 若都不符合
        return {
            "signal": "NEUTRAL",
            "reason": "未偵測到諧波型態",
            "stop_loss": None,
            "take_profit": None
        }