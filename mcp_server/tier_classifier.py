# ═══════════════════════════════════════════════════════════
# FILE: mcp_server/tier_classifier.py
# PURPOSE: Tier Classifier - Opportunity Quality Classification
# VERSION: 3.0 INSTITUTIONAL
# ═══════════════════════════════════════════════════════════

"""
Tier Classifier - Opportunity Quality Classification
Implements 4-tier quality system instead of binary approve/reject

TIERS:

🟢 Elite (8.0-10.0 score, 75%+ prob, 2.5+ R:R)
   • Win rate target: 75%+
   • Position size: 100% (2% risk)
   • Recommendation: TRADE IMMEDIATELY
   
🟡 Professional (6.5-7.9 score, 65%+ prob, 2.0+ R:R)
   • Win rate target: 65-74%
   • Position size: 75% (1.5% risk)
   • Recommendation: TRADE WITH CAUTION
   
🟠 Speculative (5.0-6.4 score, 55%+ prob, 1.5+ R:R)  
   • Win rate target: 55-64%
   • Position size: 50% (1% risk)
   • Recommendation: EXPERIENCED TRADERS ONLY
   
🔴 High Risk (4.0-4.9 score)
   • Win rate target: <55%
   • Position size: 25% (0.5% risk)
   • Recommendation: NOT RECOMMENDED, paper trade only
   
⛔ Not Recommended (<4.0 score)
   • Win rate target: <50%
   • Position size: 0%
   • Recommendation: SKIP
"""

from typing import Literal
from loguru import logger

TierType = Literal["elite", "professional", "speculative", "high_risk", "not_recommended"]


class TierClassifier:
    """
    Классификация торговых возможностей по уровням качества
    
    Заменяет бинарный approve/reject на 5-уровневую систему
    для более гранулярного управления риском
    """
    
    @staticmethod
    def classify(
        score: float,
        probability: float,
        risk_reward: float
    ) -> TierType:
        """
        Classify opportunity into quality tier
        
        Args:
            score: Confluence score (0-10, normalized)
            probability: Win probability (0-1)
            risk_reward: Risk/reward ratio
            
        Returns:
            Tier classification
        """
        # 🟢 Elite Tier
        if score >= 8.0 and probability >= 0.75 and risk_reward >= 2.5:
            logger.debug(f"Classified as ELITE: score={score:.1f}, prob={probability:.2f}, rr={risk_reward:.1f}")
            return "elite"
        
        # 🟡 Professional Tier  
        elif score >= 6.5 and probability >= 0.65 and risk_reward >= 2.0:
            logger.debug(f"Classified as PROFESSIONAL: score={score:.1f}, prob={probability:.2f}, rr={risk_reward:.1f}")
            return "professional"
        
        # 🟠 Speculative Tier
        elif score >= 5.0 and probability >= 0.55 and risk_reward >= 1.5:
            logger.debug(f"Classified as SPECULATIVE: score={score:.1f}, prob={probability:.2f}, rr={risk_reward:.1f}")
            return "speculative"
        
        # 🔴 High Risk
        elif score >= 4.0:
            logger.debug(f"Classified as HIGH_RISK: score={score:.1f}")
            return "high_risk"
        
        # ⛔ Not Recommended
        else:
            logger.debug(f"Classified as NOT_RECOMMENDED: score={score:.1f}")
            return "not_recommended"
    
    @staticmethod
    def get_recommendation(tier: TierType) -> str:
        """Get recommendation text for tier"""
        recommendations = {
            "elite": "✅ ОТКРЫВАТЬ - Отличный setup с высокой вероятностью успеха (75%+)",
            "professional": "⚠️ ОСТОРОЖНО - Хороший setup, уменьшите размер позиции (65-74% вероятность)",
            "speculative": "⚠️⚠️ ВЫСОКИЙ РИСК - Только для опытных, минимальный размер (55-64% вероятность)",
            "high_risk": "🔴 НЕ РЕКОМЕНДУЕТСЯ - Низкая confluence (<55%), paper trade only",
            "not_recommended": "⛔ ПРОПУСТИТЬ - Setup слишком слабый (<50% вероятность)"
        }
        return recommendations.get(tier, "Unknown tier")
    
    @staticmethod
    def get_position_size_multiplier(tier: TierType) -> float:
        """
        Get position size multiplier based on tier
        
        Returns:
            Multiplier for base position size
            Base = 2% risk, multiplier scales it down for lower tiers
        """
        multipliers = {
            "elite": 1.0,          # 100% = 2% risk
            "professional": 0.75,  # 75% = 1.5% risk  
            "speculative": 0.5,    # 50% = 1% risk
            "high_risk": 0.25,     # 25% = 0.5% risk
            "not_recommended": 0.0  # 0% = don't trade
        }
        return multipliers.get(tier, 0.0)
    
    @staticmethod
    def get_tier_color(tier: TierType) -> str:
        """Get color emoji for tier"""
        colors = {
            "elite": "🟢",
            "professional": "🟡",
            "speculative": "🟠",
            "high_risk": "🔴",
            "not_recommended": "⛔"
        }
        return colors.get(tier, "⚪")
    
    @staticmethod
    def get_tier_name(tier: TierType) -> str:
        """Get display name for tier"""
        names = {
            "elite": "Elite",
            "professional": "Professional",
            "speculative": "Speculative",
            "high_risk": "High Risk",
            "not_recommended": "Not Recommended"
        }
        return names.get(tier, "Unknown")
    
    @staticmethod
    def get_expected_win_rate(tier: TierType) -> float:
        """
        Get expected win rate for tier
        
        Returns:
            Expected win rate (0-1)
        """
        win_rates = {
            "elite": 0.75,
            "professional": 0.68,
            "speculative": 0.58,
            "high_risk": 0.48,
            "not_recommended": 0.35
        }
        return win_rates.get(tier, 0.50)
    
    @staticmethod
    def should_trade(tier: TierType) -> bool:
        """
        Should this tier be traded?
        
        Returns:
            True if tier is tradeable (elite/professional/speculative)
        """
        return tier in ["elite", "professional", "speculative"]