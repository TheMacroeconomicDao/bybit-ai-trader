# ═══════════════════════════════════════════════════════════
# FILE: mcp_server/smart_display.py
# PURPOSE: Smart Display Logic - Intelligent opportunity presentation
# VERSION: 3.0.1 INSTITUTIONAL (English Localization)
# ═══════════════════════════════════════════════════════════

"""
Smart Display Logic - Intelligent opportunity presentation
ALWAYS shows opportunities, never returns empty

GOLDEN RULES:
1. NEVER return empty (always show TOP-3 each direction)
2. Add clear warnings for sub-optimal setups
3. Provide educational context
4. Explain WHY opportunities limited if applicable
"""

from typing import List, Dict, Any
from loguru import logger


class SmartDisplay:
    """
    Smart display logic for opportunities.
    
    Ensures the user ALWAYS receives information,
    even if all opportunities are of low quality.
    """
    
    @staticmethod
    def select_top_3_with_warnings(
        opportunities: List[Dict[str, Any]],
        threshold: float,
        market_regime: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Select top 3 opportunities with appropriate warnings (English).
        
        Args:
            opportunities: List of opportunities (sorted by score DESC)
            threshold: Adaptive threshold for this direction
            market_regime: Current market regime
            
        Returns:
            Top 3 opportunities with enhanced metadata in English.
        """
        result = []
        regime_type = market_regime.get("type", "uncertain")
        
        # ═══════════════════════════════════════════════════
        # SELECT TOP 3 (or less if fewer available)
        # ═══════════════════════════════════════════════════
        
        for idx, opp in enumerate(opportunities[:3], start=1):
            score = opp.get("score", 0.0)
            tier = opp.get("tier", "not_recommended")
            side = opp.get("side", "long")
            
            # Clone opportunity to avoid mutation
            enhanced_opp = opp.copy()
            enhanced_opp["rank"] = idx
            
            # ═══════════════════════════════════════════════
            # THRESHOLD-BASED WARNINGS (English)
            # ═══════════════════════════════════════════════
            
            if score >= threshold and tier == "elite":
                # ✅ EXCELLENT - meets/exceeds threshold, elite tier
                enhanced_opp["warning"] = None
                enhanced_opp["display_recommendation_en"] = (
                    "✅ EXCELLENT SETUP - Recommended for execution"
                )
                enhanced_opp["recommendation_level"] = "strong_buy"
                
            elif score >= threshold and tier == "professional":
                # ✅ GOOD - meets threshold, professional tier
                enhanced_opp["warning"] = "⚠️ Professional tier - consider reducing position size"
                enhanced_opp["display_recommendation_en"] = (
                    "✅ GOOD SETUP - Cautiously recommended"
                )
                enhanced_opp["recommendation_level"] = "cautious_buy"
                
            elif score >= threshold - 0.5 and tier not in ["not_recommended", "high_risk"]:
                # ⚠️ CLOSE TO THRESHOLD - acceptable with extra caution
                enhanced_opp["warning"] = (
                    f"⚠️ Score {score:.1f} is close to threshold {threshold:.1f} - "
                    "extra caution advised"
                )
                enhanced_opp["display_recommendation_en"] = (
                    "⚠️ ACCEPTABLE - For experienced traders, minimum size"
                )
                enhanced_opp["recommendation_level"] = "speculative"
                
            elif score >= 4.0:
                # 🔴 BELOW THRESHOLD - show but discourage
                enhanced_opp["warning"] = (
                    f"⚠️⚠️ Score {score:.1f} BELOW threshold {threshold:.1f} - "
                    "High Risk"
                )
                enhanced_opp["display_recommendation_en"] = (
                    "🔴 HIGH RISK - Not recommended or for paper trading only"
                )
                enhanced_opp["recommendation_level"] = "avoid"
                
            else:
                # ⛔ VERY LOW SCORE - show for educational purposes only
                enhanced_opp["warning"] = (
                    f"⛔ Score {score:.1f} is VERY LOW - "
                    "shown for educational purposes only"
                )
                enhanced_opp["display_recommendation_en"] = (
                    "⛔ SKIP - Setup is too weak"
                )
                enhanced_opp["recommendation_level"] = "skip"
            
            # ═══════════════════════════════════════════════
            # REGIME-SPECIFIC WARNINGS (English)
            # ═══════════════════════════════════════════════
            
            if regime_type == "strong_bull" and side == "short":
                enhanced_opp["regime_warning"] = (
                    "🔴 AGAINST THE TREND: BTC is in a strong uptrend, SHORT is extremely risky"
                )
                # Increase warning level
                if enhanced_opp.get("recommendation_level") not in ["avoid", "skip"]:
                    enhanced_opp["recommendation_level"] = "speculative"
                    
            elif regime_type == "strong_bear" and side == "long":
                enhanced_opp["regime_warning"] = (
                    "🔴 AGAINST THE TREND: BTC is in a strong downtrend, LONG is extremely risky"
                )
                if enhanced_opp.get("recommendation_level") not in ["avoid", "skip"]:
                    enhanced_opp["recommendation_level"] = "speculative"
            
            else:
                enhanced_opp["regime_warning"] = None
            
            # ═══════════════════════════════════════════════
            # ADD EDUCATIONAL CONTEXT
            # ═══════════════════════════════════════════════
            
            enhanced_opp["threshold_used"] = threshold
            enhanced_opp["meets_threshold"] = score >= threshold
            enhanced_opp["score_vs_threshold"] = round(score - threshold, 2)
            
            result.append(enhanced_opp)
        
        # ═══════════════════════════════════════════════════
        # HANDLE INSUFFICIENT OPPORTUNITIES
        # ═══════════════════════════════════════════════════
        
        if len(result) < 3:
            logger.warning(
                f"Only {len(result)} opportunities available for display, "
                f"target was 3"
            )
            # This is OK - just show what we have with explanation
        
        return result
    
    @staticmethod
    def format_no_opportunities_message(
        direction: str,
        market_regime: Dict[str, Any],
        total_scanned: int
    ) -> Dict[str, Any]:
        """
        Format informative message when NO opportunities found (English).
        
        Args:
            direction: "long" or "short"
            market_regime: Current market regime
            total_scanned: Number of assets scanned
            
        Returns:
            Informative message with context in English.
        """
        regime_type = market_regime.get("type", "uncertain")
        
        # Explain WHY no opportunities
        explanation = SmartDisplay._explain_empty_direction(direction, regime_type)
        
        # What to wait for
        what_to_wait = SmartDisplay._what_to_wait_for(direction, regime_type)
        
        return {
            "direction": direction,
            "count": 0,
            "message": f"No {direction.upper()} opportunities found after scanning {total_scanned} assets",
            "explanation": explanation,
            "what_we_wait_for": what_to_wait,
            "is_normal": SmartDisplay._is_empty_normal(direction, regime_type)
        }
    
    @staticmethod
    def _explain_empty_direction(direction: str, regime_type: str) -> str:
        """Explain why direction is empty (English)"""
        if direction == "long" and regime_type == "strong_bear":
            return (
                "In a strong bear market, LONG opportunities are extremely rare and dangerous. "
                "Most assets are following BTC down. This is a NORMAL situation."
            )
        elif direction == "short" and regime_type == "strong_bull":
            return (
                "In a strong bull market, SHORT opportunities are extremely rare and risky. "
                "Attempting to short an uptrend is a low-probability strategy. "
                "This is a NORMAL situation."
            )
        elif direction == "long":
            return (
                "There are currently no quality LONG setups matching our strict criteria. "
                "It's better to wait for clearer signals."
            )
        else:  # short
            return (
                "There are currently no quality SHORT setups matching our strict criteria. "
                "It's better to wait for clearer signals."
            )
    
    @staticmethod
    def _what_to_wait_for(direction: str, regime_type: str) -> str:
        """What conditions to wait for (English)"""
        if direction == "long":
            return (
                "Waiting for: \n"
                "• BTC stabilization or upward reversal\n"
                "• Oversold conditions on multiple timeframes\n"
                "• Volume spike with bullish candles\n"
                "• Reversal pattern formation\n"
                "• Reaching a strong support level"
            )
        else:  # short
            return (
                "Waiting for: \n"
                "• BTC weakness or downward reversal\n"
                "• Overbought conditions on multiple timeframes\n"
                "• Distribution volume with bearish candles\n"
                "• Topping pattern formation\n"
                "• Reaching a strong resistance level"
            )
    
    @staticmethod
    def _is_empty_normal(direction: str, regime_type: str) -> bool:
        """Is it normal to have empty direction in this regime?"""
        if direction == "long" and regime_type == "strong_bear":
            return True
        elif direction == "short" and regime_type == "strong_bull":
            return True
        return False