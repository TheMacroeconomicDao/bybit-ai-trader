# ═══════════════════════════════════════════════════════════
# FILE: mcp_server/smart_display.py
# PURPOSE: Smart Display Logic - Intelligent opportunity presentation
# VERSION: 3.0 INSTITUTIONAL
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
    Умная логика отображения возможностей
    
    Гарантирует, что пользователь ВСЕГДА получит информацию,
    даже если все возможности низкого качества
    """
    
    @staticmethod
    def select_top_3_with_warnings(
        opportunities: List[Dict[str, Any]],
        threshold: float,
        market_regime: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Select top 3 opportunities with appropriate warnings
        
        Args:
            opportunities: List of opportunities (sorted by score DESC)
            threshold: Adaptive threshold for this direction
            market_regime: Current market regime
            
        Returns:
            Top 3 opportunities with enhanced metadata
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
            # THRESHOLD-BASED WARNINGS
            # ═══════════════════════════════════════════════
            
            if score >= threshold and tier == "elite":
                # ✅ EXCELLENT - meets/exceeds threshold, elite tier
                enhanced_opp["warning"] = None
                enhanced_opp["display_recommendation"] = (
                    "✅ ОТЛИЧНЫЙ SETUP - рекомендуется к исполнению"
                )
                enhanced_opp["recommendation_level"] = "strong_buy"
                
            elif score >= threshold and tier == "professional":
                # ✅ GOOD - meets threshold, professional tier
                enhanced_opp["warning"] = "⚠️ Professional tier - уменьшите размер позиции"
                enhanced_opp["display_recommendation"] = (
                    "✅ ХОРОШИЙ SETUP - осторожно рекомендуется"
                )
                enhanced_opp["recommendation_level"] = "cautious_buy"
                
            elif score >= threshold - 0.5 and tier not in ["not_recommended", "high_risk"]:
                # ⚠️ CLOSE TO THRESHOLD - acceptable with extra caution
                enhanced_opp["warning"] = (
                    f"⚠️ Score {score:.1f} близок к порогу {threshold:.1f} - "
                    "повышенная осторожность"
                )
                enhanced_opp["display_recommendation"] = (
                    "⚠️ ПРИЕМЛЕМО - только для опытных, минимальный размер"
                )
                enhanced_opp["recommendation_level"] = "speculative"
                
            elif score >= 4.0:
                # 🔴 BELOW THRESHOLD - show but discourage
                enhanced_opp["warning"] = (
                    f"⚠️⚠️ Score {score:.1f} НИЖЕ порога {threshold:.1f} - "
                    "высокий риск"
                )
                enhanced_opp["display_recommendation"] = (
                    "🔴 ВЫСОКИЙ РИСК - не рекомендуется или paper trade"
                )
                enhanced_opp["recommendation_level"] = "avoid"
                
            else:
                # ⛔ VERY LOW SCORE - show for educational purposes only
                enhanced_opp["warning"] = (
                    f"⛔ Score {score:.1f} ОЧЕНЬ НИЗКИЙ - "
                    "показано только для полноты картины"
                )
                enhanced_opp["display_recommendation"] = (
                    "⛔ ПРОПУСТИТЬ - setup слишком слабый"
                )
                enhanced_opp["recommendation_level"] = "skip"
            
            # ═══════════════════════════════════════════════
            # REGIME-SPECIFIC WARNINGS
            # ═══════════════════════════════════════════════
            
            if regime_type == "strong_bull" and side == "short":
                enhanced_opp["regime_warning"] = (
                    "🔴 ПРОТИВ ТРЕНДА: BTC в сильном uptrend, SHORT крайне рискован"
                )
                # Increase warning level
                if enhanced_opp.get("recommendation_level") not in ["avoid", "skip"]:
                    enhanced_opp["recommendation_level"] = "speculative"
                    
            elif regime_type == "strong_bear" and side == "long":
                enhanced_opp["regime_warning"] = (
                    "🔴 ПРОТИВ ТРЕНДА: BTC в сильном downtrend, LONG крайне рискован"
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
        Format informative message when NO opportunities found
        
        Args:
            direction: "long" or "short"
            market_regime: Current market regime
            total_scanned: Number of assets scanned
            
        Returns:
            Informative message with context
        """
        regime_type = market_regime.get("type", "uncertain")
        
        # Explain WHY no opportunities
        explanation = SmartDisplay._explain_empty_direction(direction, regime_type)
        
        # What to wait for
        what_to_wait = SmartDisplay._what_to_wait_for(direction, regime_type)
        
        return {
            "direction": direction,
            "count": 0,
            "message": f"Не найдено {direction.upper()} возможностей при сканировании {total_scanned} активов",
            "explanation": explanation,
            "what_we_wait_for": what_to_wait,
            "is_normal": SmartDisplay._is_empty_normal(direction, regime_type)
        }
    
    @staticmethod
    def _explain_empty_direction(direction: str, regime_type: str) -> str:
        """Explain why direction is empty"""
        if direction == "long" and regime_type == "strong_bear":
            return (
                "В сильном медвежьем рынке LONG возможности крайне редки и опасны. "
                "Большинство активов следует за BTC вниз. Это НОРМАЛЬНАЯ ситуация."
            )
        elif direction == "short" and regime_type == "strong_bull":
            return (
                "В сильном бычьем рынке SHORT возможности крайне редки и рискованны. "
                "Попытка шортить в uptrend - стратегия с низкой вероятностью успеха. "
                "Это НОРМАЛЬНАЯ ситуация."
            )
        elif direction == "long":
            return (
                "Сейчас нет качественных LONG setup'ов, соответствующих нашим строгим критериям. "
                "Лучше подождать более ясных сигналов."
            )
        else:  # short
            return (
                "Сейчас нет качественных SHORT setup'ов, соответствующих нашим строгим критериям. "
                "Лучше подождать более ясных сигналов."
            )
    
    @staticmethod
    def _what_to_wait_for(direction: str, regime_type: str) -> str:
        """What conditions to wait for"""
        if direction == "long":
            return (
                "Ждём: \n"
                "• BTC стабилизация или разворот вверх\n"
                "• Oversold условия на нескольких таймфреймах\n"
                "• Volume spike с бычьими свечами\n"
                "• Reversal pattern формирование\n"
                "• Достижение сильной поддержки"
            )
        else:  # short
            return (
                "Ждём: \n"
                "• BTC слабость или разворот вниз\n"
                "• Overbought условия на нескольких таймфреймах\n"
                "• Distribution volume с медвежьими свечами\n"
                "• Topping pattern формирование\n"
                "• Достижение сильного сопротивления"
            )
    
    @staticmethod
    def _is_empty_normal(direction: str, regime_type: str) -> bool:
        """Is it normal to have empty direction in this regime?"""
        if direction == "long" and regime_type == "strong_bear":
            return True
        elif direction == "short" and regime_type == "strong_bull":
            return True
        return False