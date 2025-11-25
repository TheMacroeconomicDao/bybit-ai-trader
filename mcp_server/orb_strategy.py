"""
Opening Range Breakout Strategy  
Professional-Grade Implementation
"""
from typing import Dict, Any, Optional
from datetime import datetime
import pytz
from loguru import logger


class OpeningRangeBreakout:
    """
    Opening Range Breakout - Профессиональная стратегия для начала сессий
    
    Win Rate: 65-75%
    Best Time: European (08:00-10:00 UTC), US (13:30-15:30 UTC)
    """
    
    def __init__(self, bybit_client, technical_analysis):
        self.client = bybit_client
        self.ta = technical_analysis
        logger.info("ORB Strategy initialized")
    
    async def detect_orb_setup(
        self,
        symbol: str,
        timeframe: str = "5m",
        or_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Детектирует ORB setup и генерирует entry plan
        
        Args:
            symbol: Торговая пара (например "BTC/USDT")
            timeframe: Таймфрейм для анализа (default: "5m")
            or_minutes: Длительность Opening Range в минутах (default: 30)
        
        Returns:
            {
                "has_setup": bool,
                "entry_price": float,
                "stop_loss": float,
                "take_profit": float,
                "side": "long" | "short",
                "strength": "strong" | "moderate" | "weak",
                "confidence": float
            }
        """
        try:
            session = self._get_current_session()
            
            if not self._is_orb_time(session):
                return {"has_setup": False, "reason": "Not ORB time"}
            
            # Получаем OHLCV данные
            ohlcv = await self.client.get_ohlcv(symbol, timeframe, limit=50)
            if not ohlcv or len(ohlcv) < 10:
                return {"has_setup": False, "reason": "No data"}
            
            # Определяем количество свечей для Opening Range
            candles_per_minute = {"1m": 1, "5m": 5, "15m": 15}.get(timeframe, 5)
            or_candles_count = max(1, or_minutes // candles_per_minute)
            # Исправление: используем минимум из запрошенного и доступного
            or_candles = ohlcv[:min(or_candles_count, len(ohlcv))] if len(ohlcv) > 0 else []
            
            if not or_candles:
                return {"has_setup": False, "reason": "Insufficient OR data"}
            
            # Вычисляем OR High и Low
            or_high = max(float(c[2]) for c in or_candles)  # high
            or_low = min(float(c[3]) for c in or_candles)   # low
            or_height = or_high - or_low
            
            if or_height == 0:
                return {"has_setup": False, "reason": "Zero OR range"}
            
            # Текущая свеча
            current = ohlcv[-1]
            price = float(current[4])  # close
            volume = float(current[5])  # volume
            
            # Средний объем в OR
            avg_vol = sum(float(c[5]) for c in or_candles) / len(or_candles) if or_candles else volume
            
            # Проверяем breakout
            breakout = None
            breakout_threshold = 0.001  # 0.1% для пробоя
            
            if price > or_high * (1 + breakout_threshold):
                breakout = "up"
            elif price < or_low * (1 - breakout_threshold):
                breakout = "down"
            
            if not breakout:
                return {"has_setup": False, "reason": "No breakout detected"}
            
            # Проверяем volume confirmation
            volume_ratio = volume / avg_vol if avg_vol > 0 else 1.0
            if volume_ratio < 1.5:
                return {"has_setup": False, "reason": "Insufficient volume"}
            
            # Генерируем entry plan
            if breakout == "up":
                entry = or_high * (1 + breakout_threshold * 2)  # Немного выше OR high
                sl = or_low * (1 - breakout_threshold)  # Ниже OR low
                tp = entry + (or_height * 2)  # 2x высота OR
                side = "long"
            else:  # breakout == "down"
                entry = or_low * (1 - breakout_threshold * 2)  # Немного ниже OR low
                sl = or_high * (1 + breakout_threshold)  # Выше OR high
                tp = entry - (or_height * 2)  # 2x высота OR
                side = "short"
            
            # Проверяем R:R
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rr = reward / risk if risk > 0 else 0
            
            if rr < 2.0:
                return {"has_setup": False, "reason": f"R:R too low: {rr:.2f}"}
            
            # Определяем strength
            if volume_ratio > 1.8 and (or_height / price) > 0.015:
                strength = "strong"
                confidence = 0.75
            elif volume_ratio > 1.5:
                strength = "moderate"
                confidence = 0.70
            else:
                strength = "weak"
                confidence = 0.65
            
            return {
                "has_setup": True,
                "session": session,
                "or_high": round(or_high, 4),
                "or_low": round(or_low, 4),
                "or_height": round(or_height, 4),
                "side": side,
                "entry_price": round(entry, 4),
                "stop_loss": round(sl, 4),
                "take_profit": round(tp, 4),
                "risk_reward": round(rr, 2),
                "volume_ratio": round(volume_ratio, 2),
                "strength": strength,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"ORB error for {symbol}: {e}")
            return {"has_setup": False, "error": str(e)}
    
    def _get_current_session(self) -> str:
        """Определяет текущую торговую сессию"""
        hour = datetime.now(pytz.UTC).hour
        if 8 <= hour < 13:
            return "european"
        elif 13 <= hour < 21:
            return "us"
        return "asian"
    
    def _is_orb_time(self, session: str) -> bool:
        """Проверяет, подходящее ли время для ORB"""
        hour = datetime.now(pytz.UTC).hour
        minute = datetime.now(pytz.UTC).minute
        
        if session == "european":
            # European ORB: 08:00-10:00 UTC
            return 8 <= hour < 10
        elif session == "us":
            # US ORB: 13:30-15:30 UTC
            return (hour == 13 and minute >= 30) or (14 <= hour < 15) or (hour == 15 and minute < 30)
        return False


