# ═══════════════════════════════════════════════════════════
# FILE: mcp_server/regime_detector.py
# PURPOSE: Market Regime Detector - Automatic market state detection
# VERSION: 3.0 INSTITUTIONAL
# ═══════════════════════════════════════════════════════════

"""
Market Regime Detector - Automatic market state detection
Detects: Strong Bull, Strong Bear, Sideways, Uncertain

REGIMES:

Strong Bull:
  • BTC weekly change: >+5%
  • ADX: >25 (strong trend)
  • Signal: STRONG_BUY/BUY
  • Confidence: >60%
  
Strong Bear:
  • BTC weekly change: <-5%
  • ADX: >25
  • Signal: STRONG_SELL/SELL
  • Confidence: >60%
  
Sideways:
  • BTC weekly change: ±2%
  • ADX: <20 (weak trend)
  
Uncertain:
  • Mixed signals
  • Moderate ADX
"""

from typing import Dict, Any, Literal
from loguru import logger

RegimeType = Literal["strong_bull", "strong_bear", "sideways", "uncertain"]


class RegimeDetector:
    """
    Автоматическое определение рыночного режима
    
    Анализирует BTC для определения общего состояния рынка
    и адаптации торговых стратегий
    """
    
    @staticmethod
    def detect(btc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect current market regime from BTC analysis
        
        Args:
            btc_analysis: Full BTC technical analysis from analyze_asset()
            
        Returns:
            {
                "type": RegimeType,
                "confidence": float (0-1),
                "metrics": {...},
                "description": str,
                "trading_implications": str
            }
        """
        try:
            # Extract metrics from BTC analysis
            composite = btc_analysis.get("composite_signal", {})
            timeframes = btc_analysis.get("timeframes", {})
            h4_data = timeframes.get("4h", {})
            d1_data = timeframes.get("1d", {})
            
            # ═══════════════════════════════════════════════
            # METRIC EXTRACTION
            # ═══════════════════════════════════════════════
            
            # Price change (approximate weekly from daily)
            price_change_week = RegimeDetector._calculate_weekly_change(btc_analysis)
            
            # ADX (trend strength) from 4h
            adx = h4_data.get("indicators", {}).get("adx", {}).get("adx", 20)
            
            # Volatility (ATR-based)
            atr = h4_data.get("indicators", {}).get("atr", {}).get("atr_14", 0)
            avg_atr = RegimeDetector._estimate_avg_atr(h4_data)
            volatility = RegimeDetector._classify_volatility(atr, avg_atr)
            
            # Signal & confidence
            signal = composite.get("signal", "HOLD")
            signal_confidence = composite.get("confidence", 0.5)
            
            # ═══════════════════════════════════════════════
            # REGIME DETECTION LOGIC
            # ═══════════════════════════════════════════════
            
            regime_type: RegimeType
            regime_confidence: float
            
            # STRONG BULL
            if (price_change_week > 5.0 and 
                adx > 25 and 
                signal in ["STRONG_BUY", "BUY"] and 
                signal_confidence > 0.6):
                
                regime_type = "strong_bull"
                regime_confidence = min(0.95, 0.75 + (adx / 100) + (signal_confidence * 0.2))
                logger.info(f"Detected STRONG BULL: BTC +{price_change_week:.1f}%, ADX={adx:.1f}")
            
            # STRONG BEAR
            elif (price_change_week < -5.0 and 
                  adx > 25 and 
                  signal in ["STRONG_SELL", "SELL"] and 
                  signal_confidence > 0.6):
                
                regime_type = "strong_bear"
                regime_confidence = min(0.95, 0.75 + (adx / 100) + (signal_confidence * 0.2))
                logger.info(f"Detected STRONG BEAR: BTC {price_change_week:.1f}%, ADX={adx:.1f}")
            
            # SIDEWAYS
            elif abs(price_change_week) < 2.0 and adx < 20:
                regime_type = "sideways"
                regime_confidence = 0.70
                logger.info(f"Detected SIDEWAYS: BTC {price_change_week:.1f}%, ADX={adx:.1f}")
            
            # UNCERTAIN
            else:
                regime_type = "uncertain"
                regime_confidence = 0.50
                logger.info(f"Detected UNCERTAIN: Mixed signals, BTC {price_change_week:.1f}%, ADX={adx:.1f}")
            
            # ═══════════════════════════════════════════════
            # ASSEMBLE RESULT
            # ═══════════════════════════════════════════════
            
            return {
                "type": regime_type,
                "confidence": round(regime_confidence, 2),
                "metrics": {
                    "btc_weekly_change_pct": round(price_change_week, 2),
                    "adx": round(adx, 1),
                    "signal": signal,
                    "signal_confidence": round(signal_confidence, 2),
                    "volatility": volatility,
                    "atr_14": round(atr, 2)
                },
                "description": RegimeDetector._get_description(regime_type),
                "trading_implications": RegimeDetector._get_implications(regime_type)
            }
            
        except Exception as e:
            logger.error(f"Regime detection failed: {e}", exc_info=True)
            # Fallback to uncertain
            return {
                "type": "uncertain",
                "confidence": 0.30,
                "error": str(e),
                "description": "Unable to detect regime",
                "trading_implications": "Use strict thresholds for safety"
            }
    
    @staticmethod
    def _calculate_weekly_change(btc_analysis: Dict) -> float:
        """
        Calculate BTC weekly price change %
        
        NOTE: This is approximate. In production, fetch actual 1w data.
        """
        try:
            # Method 1: From composite signal score (rough estimate)
            composite = btc_analysis.get("composite_signal", {})
            signal_score = composite.get("score", 0)
            
            # Signal score roughly correlates to momentum
            # Positive score = upward momentum, negative = downward
            # Scale to approximate weekly %
            weekly_estimate = signal_score * 0.5  # Rough heuristic
            
            # Method 2: From 1d trend strength
            d1_data = btc_analysis.get("timeframes", {}).get("1d", {})
            trend = d1_data.get("trend", {})
            direction = trend.get("direction", "sideways")
            strength = trend.get("strength", "weak")
            
            # Enhance estimate based on trend
            if direction == "uptrend":
                if strength == "very_strong":
                    weekly_estimate = max(weekly_estimate, 7.0)
                elif strength == "strong":
                    weekly_estimate = max(weekly_estimate, 5.0)
                elif strength == "moderate":
                    weekly_estimate = max(weekly_estimate, 3.0)
            elif direction == "downtrend":
                if strength == "very_strong":
                    weekly_estimate = min(weekly_estimate, -7.0)
                elif strength == "strong":
                    weekly_estimate = min(weekly_estimate, -5.0)
                elif strength == "moderate":
                    weekly_estimate = min(weekly_estimate, -3.0)
            
            return round(weekly_estimate, 2)
            
        except Exception as e:
            logger.warning(f"Failed to calculate weekly change: {e}")
            return 0.0
    
    @staticmethod
    def _estimate_avg_atr(h4_data: Dict) -> float:
        """Estimate average ATR for volatility comparison"""
        try:
            atr_14 = h4_data.get("indicators", {}).get("atr", {}).get("atr_14", 0)
            # Assume current ATR represents baseline
            # In production, calculate actual average from historical data
            return atr_14 * 1.1  # Slight buffer
        except:
            return 1.0
    
    @staticmethod
    def _classify_volatility(current_atr: float, avg_atr: float) -> str:
        """Classify volatility level"""
        if avg_atr == 0 or current_atr == 0:
            return "normal"
        
        ratio = current_atr / avg_atr
        
        if ratio > 1.5:
            return "high"
        elif ratio > 1.2:
            return "elevated"
        elif ratio < 0.7:
            return "very_low"
        elif ratio < 0.9:
            return "low"
        else:
            return "normal"
    
    @staticmethod
    def _get_description(regime_type: RegimeType) -> str:
        """Get human-readable regime description"""
        descriptions = {
            "strong_bull": "Сильный бычий тренд - импульс вверх, фокус на LONG позиции",
            "strong_bear": "Сильный медвежий тренд - импульс вниз, фокус на SHORT позиции",
            "sideways": "Боковое движение - нет четкого тренда, range trading",
            "uncertain": "Смешанные сигналы - нет четкого режима, осторожность"
        }
        return descriptions.get(regime_type, "Неизвестный режим")
    
    @staticmethod
    def _get_implications(regime_type: RegimeType) -> str:
        """Get trading implications for regime"""
        implications = {
            "strong_bull": "Смягчить LONG пороги, ужесточить SHORT пороги. Следовать тренду.",
            "strong_bear": "Ужесточить LONG пороги, смягчить SHORT пороги. Шортить отскоки.",
            "sideways": "Умеренные пороги в обе стороны. Торговать от границ диапазона.",
            "uncertain": "Строгие пороги в обе стороны. Ждать ясности."
        }
        return implications.get(regime_type, "Требуется дополнительный анализ")