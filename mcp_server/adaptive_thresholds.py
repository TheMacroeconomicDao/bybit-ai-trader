# ═══════════════════════════════════════════════════════════
# FILE: mcp_server/adaptive_thresholds.py
# PURPOSE: Adaptive Thresholds - Dynamic threshold calculation
# VERSION: 3.0 INSTITUTIONAL
# ═══════════════════════════════════════════════════════════

"""
Adaptive Thresholds - Dynamic threshold calculation
Adjusts score thresholds based on market regime for optimal filtering

BASE THRESHOLDS:
• LONG: 7.0/10
• SHORT: 7.0/10

ADJUSTMENTS BY REGIME:

Strong Bull:
  • LONG: -1.0 (easier, trend is friend) → 6.0
  • SHORT: +1.5 (harder, against trend) → 8.5
  
Strong Bear:
  • LONG: +1.5 (harder, against trend) → 8.5
  • SHORT: -1.0 (easier, trend is friend) → 6.0
  
Sideways:
  • LONG: 7.0 (moderate)
  • SHORT: 7.0 (moderate)
  
High Volatility:
  • Both: +0.5 (more risk, higher bar)
  
Very Low Volatility:
  • Both: -0.25 (less risk, can relax)
"""

from typing import Dict, Any
from loguru import logger


class AdaptiveThresholds:
    """
    Динамические пороги на основе рыночного режима
    
    Адаптирует требования к качеству сигналов в зависимости от
    текущего состояния рынка для оптимальной фильтрации
    """
    
    @staticmethod
    def calculate(market_regime: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate adaptive thresholds for LONG and SHORT
        
        Args:
            market_regime: Market regime data from RegimeDetector
            
        Returns:
            {
                "long": float,
                "short": float,
                "regime_type": str,
                "volatility": str,
                "reasoning": str,
                "adjustments": {...}
            }
        """
        regime_type = market_regime.get("type", "sideways")
        metrics = market_regime.get("metrics", {})
        volatility = metrics.get("volatility", "normal")
        adx = metrics.get("adx", 20)
        
        # Base thresholds
        base_long = 7.0
        base_short = 7.0
        adjustments = {}
        
        # ═══════════════════════════════════════════════════
        # REGIME-BASED ADJUSTMENTS
        # ═══════════════════════════════════════════════════
        
        if regime_type == "strong_bull":
            # В сильном бычьем рынке
            base_long -= 1.0  # LONG easier (6.0)
            base_short += 1.5  # SHORT harder (8.5)
            adjustments["regime"] = "LONG -1.0, SHORT +1.5 (strong bull)"
            logger.info("🐂 Strong Bull: LONG threshold 6.0, SHORT threshold 8.5")
        
        elif regime_type == "strong_bear":
            # В сильном медвежьем рынке
            base_long += 1.5  # LONG harder (8.5)
            base_short -= 1.0  # SHORT easier (6.0)
            adjustments["regime"] = "LONG +1.5, SHORT -1.0 (strong bear)"
            logger.info("🐻 Strong Bear: LONG threshold 8.5, SHORT threshold 6.0")
        
        elif regime_type == "sideways":
            # В боковом рынке
            # Keep moderate thresholds
            adjustments["regime"] = "No adjustment (sideways)"
            logger.info("➡️ Sideways: Both thresholds 7.0")
        
        else:  # uncertain
            # При неопределенности - строгие пороги
            base_long += 0.5
            base_short += 0.5
            adjustments["regime"] = "LONG +0.5, SHORT +0.5 (uncertain, be cautious)"
            logger.info("❓ Uncertain: Both thresholds increased to 7.5")
        
        # ═══════════════════════════════════════════════════
        # VOLATILITY ADJUSTMENTS
        # ═══════════════════════════════════════════════════
        
        if volatility == "high":
            # Высокая волатильность = больше риск
            base_long += 0.5
            base_short += 0.5
            adjustments["volatility"] = "Both +0.5 (high volatility)"
            logger.info("⚡ High volatility: Both thresholds +0.5")
        
        elif volatility == "very_low":
            # Очень низкая волатильность = меньше риск
            base_long -= 0.25
            base_short -= 0.25
            adjustments["volatility"] = "Both -0.25 (very low volatility)"
            logger.info("😴 Very low volatility: Both thresholds -0.25")
        
        else:
            adjustments["volatility"] = "No adjustment (normal volatility)"
        
        # ═══════════════════════════════════════════════════
        # TREND STRENGTH ADJUSTMENTS (ADX)
        # ═══════════════════════════════════════════════════
        
        if adx > 35:
            # Очень сильный тренд - направление тренда еще легче
            if regime_type == "strong_bull":
                base_long -= 0.25
                adjustments["trend_strength"] = "LONG -0.25 (very strong uptrend)"
                logger.info(f"💪 Very strong uptrend (ADX {adx:.1f}): LONG threshold -0.25")
            elif regime_type == "strong_bear":
                base_short -= 0.25
                adjustments["trend_strength"] = "SHORT -0.25 (very strong downtrend)"
                logger.info(f"💪 Very strong downtrend (ADX {adx:.1f}): SHORT threshold -0.25")
        
        # ═══════════════════════════════════════════════════
        # CAP THRESHOLDS (reasonable limits)
        # ═══════════════════════════════════════════════════
        
        base_long = max(5.0, min(9.0, base_long))
        base_short = max(5.0, min(9.0, base_short))
        
        # ═══════════════════════════════════════════════════
        # ASSEMBLE RESULT
        # ═══════════════════════════════════════════════════
        
        return {
            "long": round(base_long, 1),
            "short": round(base_short, 1),
            "regime_type": regime_type,
            "volatility": volatility,
            "adx": adx,
            "adjustments": adjustments,
            "reasoning": (
                f"Regime: {regime_type}, Vol: {volatility}, ADX: {adx:.1f} → "
                f"LONG {base_long:.1f}, SHORT {base_short:.1f}"
            )
        }
    
    @staticmethod
    def get_threshold_explanation(regime_type: str, direction: str) -> str:
        """
        Get explanation for why threshold is set at current level
        
        Args:
            regime_type: Market regime type
            direction: "long" or "short"
            
        Returns:
            Human-readable explanation
        """
        if regime_type == "strong_bull":
            if direction == "long":
                return "Threshold снижен до 6.0 - бычий тренд поддерживает LONG позиции"
            else:
                return "Threshold повышен до 8.5 - SHORT против тренда требует высокой уверенности"
        
        elif regime_type == "strong_bear":
            if direction == "long":
                return "Threshold повышен до 8.5 - LONG против тренда требует высокой уверенности"
            else:
                return "Threshold снижен до 6.0 - медвежий тренд поддерживает SHORT позиции"
        
        elif regime_type == "sideways":
            return "Threshold 7.0 - боковой рынок, нейтральные критерии"
        
        else:  # uncertain
            return "Threshold 7.5 - неопределенность требует осторожности"