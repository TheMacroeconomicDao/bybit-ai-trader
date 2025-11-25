"""
Unit tests for TierClassifier
Tests 4-tier quality classification system
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.tier_classifier import TierClassifier


class TestTierClassifier:
    """Test suite for TierClassifier"""
    
    def test_elite_classification(self):
        """Test elite tier classification"""
        tier = TierClassifier.classify(
            score=8.5,
            probability=0.78,
            risk_reward=2.8
        )
        assert tier == "elite"
        assert TierClassifier.get_tier_color(tier) == "🟢"
        assert TierClassifier.get_tier_name(tier) == "Elite"
        assert TierClassifier.get_position_size_multiplier(tier) == 1.0
        assert TierClassifier.should_trade(tier) is True
        assert TierClassifier.get_expected_win_rate(tier) == 0.75
    
    def test_professional_classification(self):
        """Test professional tier"""
        tier = TierClassifier.classify(
            score=7.2,
            probability=0.68,
            risk_reward=2.2
        )
        assert tier == "professional"
        assert TierClassifier.get_tier_color(tier) == "🟡"
        assert TierClassifier.get_position_size_multiplier(tier) == 0.75
        assert TierClassifier.should_trade(tier) is True
        assert TierClassifier.get_expected_win_rate(tier) == 0.68
    
    def test_speculative_classification(self):
        """Test speculative tier"""
        tier = TierClassifier.classify(
            score=6.0,
            probability=0.58,
            risk_reward=1.8
        )
        assert tier == "speculative"
        assert TierClassifier.get_tier_color(tier) == "🟠"
        assert TierClassifier.get_position_size_multiplier(tier) == 0.5
        assert TierClassifier.should_trade(tier) is True
    
    def test_high_risk_classification(self):
        """Test high risk tier"""
        tier = TierClassifier.classify(
            score=4.5,
            probability=0.50,
            risk_reward=1.5
        )
        assert tier == "high_risk"
        assert TierClassifier.get_tier_color(tier) == "🔴"
        assert TierClassifier.get_position_size_multiplier(tier) == 0.25
        assert TierClassifier.should_trade(tier) is False
    
    def test_not_recommended_classification(self):
        """Test not recommended tier"""
        tier = TierClassifier.classify(
            score=3.0,
            probability=0.40,
            risk_reward=1.0
        )
        assert tier == "not_recommended"
        assert TierClassifier.get_tier_color(tier) == "⛔"
        assert TierClassifier.get_position_size_multiplier(tier) == 0.0
        assert TierClassifier.should_trade(tier) is False
    
    def test_tier_boundary_conditions(self):
        """Test edge cases at tier boundaries"""
        # Just below elite (should be professional)
        tier = TierClassifier.classify(7.9, 0.74, 2.4)
        assert tier == "professional"
        
        # Just at elite threshold (should be elite)
        tier = TierClassifier.classify(8.0, 0.75, 2.5)
        assert tier == "elite"
        
        # Just below professional (should be speculative)
        tier = TierClassifier.classify(6.4, 0.64, 1.9)
        assert tier == "speculative"
        
        # Just at professional threshold (should be professional)
        tier = TierClassifier.classify(6.5, 0.65, 2.0)
        assert tier == "professional"
    
    def test_missing_single_requirement(self):
        """Test when one requirement not met"""
        # High score but low probability
        tier = TierClassifier.classify(8.5, 0.60, 2.8)
        assert tier != "elite"  # Should fall to lower tier
        
        # High score but low R:R
        tier = TierClassifier.classify(8.5, 0.78, 1.5)
        assert tier != "elite"
        
        # High prob and R:R but low score
        tier = TierClassifier.classify(5.0, 0.78, 2.8)
        assert tier != "elite"
    
    def test_recommendation_messages(self):
        """Test recommendation messages are appropriate"""
        # Elite
        rec = TierClassifier.get_recommendation("elite")
        assert "ОТКРЫВАТЬ" in rec
        assert "75%" in rec
        
        # Professional
        rec = TierClassifier.get_recommendation("professional")
        assert "ОСТОРОЖНО" in rec
        assert "уменьшите" in rec
        
        # Not recommended
        rec = TierClassifier.get_recommendation("not_recommended")
        assert "ПРОПУСТИТЬ" in rec
    
    def test_position_sizing_logic(self):
        """Test position size multipliers are logical"""
        multipliers = {
            "elite": TierClassifier.get_position_size_multiplier("elite"),
            "professional": TierClassifier.get_position_size_multiplier("professional"),
            "speculative": TierClassifier.get_position_size_multiplier("speculative"),
            "high_risk": TierClassifier.get_position_size_multiplier("high_risk"),
            "not_recommended": TierClassifier.get_position_size_multiplier("not_recommended")
        }
        
        # Should be descending
        assert multipliers["elite"] > multipliers["professional"]
        assert multipliers["professional"] > multipliers["speculative"]
        assert multipliers["speculative"] > multipliers["high_risk"]
        assert multipliers["high_risk"] > multipliers["not_recommended"]
        
        # Elite should be full size
        assert multipliers["elite"] == 1.0
        
        # Not recommended should be zero
        assert multipliers["not_recommended"] == 0.0
    
    def test_expected_win_rates(self):
        """Test expected win rates are realistic"""
        # Elite should have highest
        assert TierClassifier.get_expected_win_rate("elite") >= 0.70
        
        # Should be descending
        assert (TierClassifier.get_expected_win_rate("elite") > 
                TierClassifier.get_expected_win_rate("professional"))
        assert (TierClassifier.get_expected_win_rate("professional") > 
                TierClassifier.get_expected_win_rate("speculative"))
        
        # Not recommended should be <50%
        assert TierClassifier.get_expected_win_rate("not_recommended") < 0.50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])