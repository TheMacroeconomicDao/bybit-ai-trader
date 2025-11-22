"""Volume Profile Analysis"""
from typing import Dict, List, Any
import pandas as pd
import numpy as np
from loguru import logger
from datetime import datetime


class VolumeProfileAnalyzer:
    def __init__(self, bybit_client):
        self.client = bybit_client
        logger.info("Volume Profile Analyzer initialized")
    
    async def calculate_volume_profile(self, symbol: str, timeframe: str = "1h", lookback: int = 100) -> Dict[str, Any]:
        try:
            ohlcv = await self.client.get_ohlcv(symbol, timeframe, limit=lookback)
            if not ohlcv or len(ohlcv) < 10:
                return {"error": "Insufficient data"}
            
            # Конвертируем в DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            price_range = df['high'].max() - df['low'].min()
            if price_range == 0:
                return {"error": "Zero price range"}
            
            num_bins = 50
            bin_size = price_range / num_bins
            min_price = df['low'].min()
            
            volume_by_level = {}
            for idx, row in df.iterrows():
                for i in range(num_bins):
                    bin_mid = min_price + (i + 0.5) * bin_size
                    if row['low'] <= bin_mid <= row['high']:
                        if bin_mid not in volume_by_level:
                            volume_by_level[bin_mid] = 0
                        volume_by_level[bin_mid] += row['volume']
            
            if not volume_by_level:
                return {"error": "Could not calculate volume profile"}
            
            # POC (Point of Control) - уровень с максимальным объемом
            poc = max(volume_by_level.items(), key=lambda x: x[1])[0]
            
            # Value Area (70% объема)
            sorted_levels = sorted(volume_by_level.items(), key=lambda x: x[1], reverse=True)
            total_vol = sum(v for p, v in sorted_levels)
            va_vol = 0
            va_levels = []
            for price, vol in sorted_levels:
                va_vol += vol
                va_levels.append(price)
                if va_vol >= total_vol * 0.70:
                    break
            
            va_high = max(va_levels)
            va_low = min(va_levels)
            current = float(df['close'].iloc[-1])
            
            position = "above_va" if current > va_high else "below_va" if current < va_low else "in_va"
            
            # ✅ FIX: Явно конвертируем в JSON-совместимый bool
            confluence_with_poc = bool(abs(current - poc) / current < 0.02) if current > 0 else False
            
            return {
                "poc": round(float(poc), 4),
                "value_area_high": round(float(va_high), 4),
                "value_area_low": round(float(va_low), 4),
                "current_position": position,
                "confluence_with_poc": bool(confluence_with_poc),  # Явно конвертируем в bool
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return {"error": str(e)}
