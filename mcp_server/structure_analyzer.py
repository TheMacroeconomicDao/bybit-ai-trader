"""
Structure Analyzer - Market Structure Detection
Анализ BOS (Break of Structure) и ChoCh (Change of Character)
"""

import pandas as pd
from typing import Dict, List, Any
from loguru import logger


class StructureAnalyzer:
    """Анализ рыночной структуры - BOS & ChoCh"""
    
    def detect_structure_breaks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Break of Structure (BOS) vs Change of Character (ChoCh)
        
        BOS = Продолжение тренда (пробой previous high в uptrend)
        ChoCh = Разворот тренда (пробой previous low в uptrend)
        
        Args:
            df: DataFrame с OHLCV данными
        
        Returns:
            Dict с BOS/ChoCh событиями и текущей структурой
        """
        if len(df) < 10:
            return {"bos": [], "choch": [], "current_structure": "neutral"}
        
        # Находим swing highs/lows
        swing_highs = self._find_swing_highs(df)
        swing_lows = self._find_swing_lows(df)
        
        # Определяем текущий тренд
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            last_high = swing_highs[-1]
            prev_high = swing_highs[-2]
            last_low = swing_lows[-1]
            prev_low = swing_lows[-2]
            
            # Uptrend: Higher Highs + Higher Lows
            if last_high['price'] > prev_high['price'] and last_low['price'] > prev_low['price']:
                current_structure = "bullish"
            # Downtrend: Lower Highs + Lower Lows
            elif last_high['price'] < prev_high['price'] and last_low['price'] < prev_low['price']:
                current_structure = "bearish"
            else:
                current_structure = "neutral"
        else:
            current_structure = "neutral"
        
        # Детект BOS и ChoCh
        bos_events = []
        choch_events = []
        current_price = df['close'].iloc[-1]
        
        # BOS: В uptrend пробой previous high
        if current_structure == "bullish" and len(swing_highs) >= 2:
            prev_high = swing_highs[-2]
            if current_price > prev_high['price']:
                bos_events.append({
                    "type": "bullish_bos",
                    "level": prev_high['price'],
                    "strength": "strong",
                    "description": "Break of Structure - continuation confirmed"
                })
        
        # ChoCh: В uptrend пробой previous low (reversal!)
        elif current_structure == "bullish" and len(swing_lows) >= 2:
            prev_low = swing_lows[-2]
            if current_price < prev_low['price']:
                choch_events.append({
                    "type": "bearish_choch",
                    "level": prev_low['price'],
                    "strength": "strong",
                    "description": "Change of Character - potential reversal"
                })
        
        # BOS: В downtrend пробой previous low
        if current_structure == "bearish" and len(swing_lows) >= 2:
            prev_low = swing_lows[-2]
            if current_price < prev_low['price']:
                bos_events.append({
                    "type": "bearish_bos",
                    "level": prev_low['price'],
                    "strength": "strong",
                    "description": "Break of Structure - continuation confirmed"
                })
        
        # ChoCh: В downtrend пробой previous high (reversal!)
        elif current_structure == "bearish" and len(swing_highs) >= 2:
            prev_high = swing_highs[-2]
            if current_price > prev_high['price']:
                choch_events.append({
                    "type": "bullish_choch",
                    "level": prev_high['price'],
                    "strength": "strong",
                    "description": "Change of Character - potential reversal"
                })
        
        return {
            "bos": bos_events,
            "choch": choch_events,
            "current_structure": current_structure,
            "swing_highs_count": len(swing_highs),
            "swing_lows_count": len(swing_lows)
        }
    
    def _find_swing_highs(self, df: pd.DataFrame, window: int = 5) -> List[Dict]:
        """Найти swing highs (локальные максимумы)"""
        swing_highs = []
        
        for i in range(window, len(df) - window):
            high = df['high'].iloc[i]
            is_swing_high = True
            
            # Проверяем что это локальный максимум
            for j in range(i - window, i + window + 1):
                if j != i and df['high'].iloc[j] >= high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    "index": i,
                    "price": high,
                    "timestamp": df.index[i]
                })
        
        return swing_highs
    
    def _find_swing_lows(self, df: pd.DataFrame, window: int = 5) -> List[Dict]:
        """Найти swing lows (локальные минимумы)"""
        swing_lows = []
        
        for i in range(window, len(df) - window):
            low = df['low'].iloc[i]
            is_swing_low = True
            
            for j in range(i - window, i + window + 1):
                if j != i and df['low'].iloc[j] <= low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    "index": i,
                    "price": low,
                    "timestamp": df.index[i]
                })
        
        return swing_lows