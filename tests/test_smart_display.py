"""
Unit tests for SmartDisplay
Tests intelligent opportunity presentation with warnings
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.smart_display import SmartDisplay


class TestSmartDisplay:
    """Test suite for SmartDisplay"""
    
    def test_select_top_3_always_returns_list(self):
        """Test that we always get a list (even if empty input)"""
        result = SmartDisplay.select_top_3_with_warnings(
            opportunities=[],
            threshold=7.0,
            market_regime={"type": "sideways"}
        )
        
        assert isinstance(result, list)
        assert len(result) == 0  # Empty input = empty output, but NO ERROR
    
    def test_warnings_added_below_threshold(self):
        """Test that warnings are added for scores below threshold"""
        opps = [
            {
                "symbol": "ETH/USDT",
                "score": 5.5,
                "tier": "speculative",
                "side": "long",
                "probability": 0.58,
                "risk_reward": 2.0,
                "entry_plan": {"risk_reward": 2.0}
            }
        ]
        
        result = SmartDisplay.select_top_3_with_warnings(
            opportunities=opps,
            threshold=7.0,
            market_regime={"type": "sideways", "metrics": {}}
        )
        
        assert len(result) == 1
        assert result[0]["warning"] is not None
        assert "ниже порога" in result[0]["warning"].lower()
    
    def test_no_warning_for_elite_above_threshold(self):
        """Test elite tier above threshold gets no warning"""
        opps = [
            {
                "symbol": "BTC/USDT",
                "score": 8.5,
                "tier": "elite",
                "side": "long",
                "probability": 0.78,
                "risk_reward": 2.8,
                "entry_plan": {"risk_reward": 2.8}
            }
        ]
        
        result = SmartDisplay.select_top_3_with_warnings(
            opportunities=opps,
            threshold=7.0,
            market_regime={"type": "sideways", "metrics": {}}
        )
        
        assert len(result) == 1
        assert result[0]["warning"] is None
        assert result[0]["display_recommendation"] == "✅ ОТЛИЧНЫЙ SETUP - рекомендуется к исполнению"
        assert result[0]["recommendation_level"] == "strong_buy"
    
    def test_regime_warnings_against_trend(self):
        """Test regime warnings for counter-trend trades"""
        opps = [
            {
                "symbol": "BTC/USDT",
                "score": 6.0,
                "tier": "professional",
                "side": "short",
                "probability": 0.65,
                "risk_reward": 2.2,
                "entry_plan": {"risk_reward": 2.2}
            }
        ]
        
        result = SmartDisplay.select_top_3_with_warnings(
            opportunities=opps,
            threshold=8.5,  # High threshold for SHORT in bull
            market_regime={"type": "strong_bull", "metrics": {}}
        )
        
        assert len(result) == 1
        assert result[0]["regime_warning"] is not None
        assert "ПРОТИВ ТРЕНДА" in result[0]["regime_warning"]
        assert "uptrend" in result[0]["regime_warning"] or "Bull" in result[0]["regime_warning"]
    
    def test_regime_warning_short_in_bull(self):
        """SHORT in strong bull gets regime warning"""
        opps = [{
            "symbol": "ETH/USDT",
            "score": 7.0,
            "tier": "professional",
            "side": "short",
            "probability": 0.65,
            "risk_reward": 2.0
        }]
        
        result = SmartDisplay.select_top_3_with_warnings(
            opps,
            8.5,
            {"type": "strong_bull", "metrics": {}}
        )
        
        assert result[0]["regime_warning"] is not None
        assert result[0]["recommendation_level"] in ["speculative", "avoid"]
    
    def test_regime_warning_long_in_bear(self):
        """LONG in strong bear gets regime warning"""
        opps = [{
            "symbol": "ETH/USDT",
            "score": 7.0,
            "tier": "professional",
            "side": "long",
            "probability": 0.65,
            "risk_reward": 2.0
        }]
        
        result = SmartDisplay.select_top_3_with_warnings(
            opps,
            8.5,
            {"type": "strong_bear", "metrics": {}}
        )
        
        assert result[0]["regime_warning"] is not None
        assert result[0]["recommendation_level"] in ["speculative", "avoid"]
    
    def test_multiple_opportunities_ranking(self):
        """Test that opportunities are ranked and enhanced properly"""
        opps = [
            {"symbol": "A", "score": 8.5, "tier": "elite", "side": "long", "probability": 0.78, "risk_reward": 2.8},
            {"symbol": "B", "score": 7.0, "tier": "professional", "side": "long", "probability": 0.68, "risk_reward": 2.2},
            {"symbol": "C", "score": 5.5, "tier": "speculative", "side": "long", "probability": 0.58, "risk_reward": 1.8}
        ]
        
        result = SmartDisplay.select_top_3_with_warnings(
            opps,
            7.0,
            {"type": "sideways", "metrics": {}}
        )
        
        assert len(result) == 3
        assert result[0]["rank"] == 1
        assert result[1]["rank"] == 2
        assert result[2]["rank"] == 3
        
        # First should have no warning (elite, above threshold)
        assert result[0]["warning"] is None
        
        # Third should have warning (below threshold)
        assert result[2]["warning"] is not None
    
    def test_threshold_metadata_added(self):
        """Test that threshold comparison metadata is added"""
        opps = [{
            "symbol": "BTC/USDT",
            "score": 7.5,
            "tier": "professional",
            "side": "long",
            "probability": 0.70,
            "risk_reward": 2.3
        }]
        
        result = SmartDisplay.select_top_3_with_warnings(
            opps,
            7.0,
            {"type": "sideways", "metrics": {}}
        )
        
        assert result[0]["threshold_used"] == 7.0
        assert result[0]["meets_threshold"] is True
        assert result[0]["score_vs_threshold"] == 0.5
    
    def test_no_opportunities_message_formatting(self):
        """Test formatting when no opportunities found"""
        msg = SmartDisplay.format_no_opportunities_message(
            direction="long",
            market_regime={"type": "strong_bear", "metrics": {}},
            total_scanned=100
        )
        
        assert msg["direction"] == "long"
        assert msg["count"] == 0
        assert "message" in msg
        assert "explanation" in msg
        assert "what_we_wait_for" in msg
        assert msg["is_normal"] is True  # LONG empty in bear is normal
    
    def test_is_empty_normal_logic(self):
        """Test _is_empty_normal logic"""
        # LONG empty in bear = normal
        assert SmartDisplay._is_empty_normal("long", "strong_bear") is True
        
        # SHORT empty in bull = normal
        assert SmartDisplay._is_empty_normal("short", "strong_bull") is True
        
        # LONG empty in bull = NOT normal
        assert SmartDisplay._is_empty_normal("long", "strong_bull") is False
        
        # SHORT empty in bear = NOT normal
        assert SmartDisplay._is_empty_normal("short", "strong_bear") is False
    
    def test_handles_less_than_3_opportunities(self):
        """Test handling when fewer than 3 opportunities available"""
        opps = [
            {"symbol": "A", "score": 8.0, "tier": "elite", "side": "long", "probability": 0.75, "risk_reward": 2.5}
        ]
        
        result = SmartDisplay.select_top_3_with_warnings(
            opps,
            7.0,
            {"type": "sideways", "metrics": {}}
        )
        
        # Should return 1, not error or pad to 3
        assert len(result) == 1
        assert result[0]["rank"] == 1


class TestAdaptiveThresholdsIntegration:
    """Test SmartDisplay with AdaptiveThresholds"""
    
    def test_bull_market_thresholds(self):
        """Test display in bull market with adapted thresholds"""
        from mcp_server.adaptive_thresholds import AdaptiveThresholds
        
        regime = {
            "type": "strong_bull",
            "metrics": {
                "volatility": "normal",
                "adx": 30
            }
        }
        
        thresholds = AdaptiveThresholds.calculate(regime)
        
        # LONG threshold should be lowered
        assert thresholds["long"] < 7.0
        # SHORT threshold should be raised
        assert thresholds["short"] > 7.0
        
        # Test with SmartDisplay
        long_opps = [{"symbol": "ETH/USDT", "score": 6.2, "tier": "professional", "side": "long", "probability": 0.67, "risk_reward": 2.1}]
        short_opps = [{"symbol": "DOGE/USDT", "score": 6.2, "tier": "speculative", "side": "short", "probability": 0.58, "risk_reward": 1.8}]
        
        longs = SmartDisplay.select_top_3_with_warnings(long_opps, thresholds["long"], regime)
        shorts = SmartDisplay.select_top_3_with_warnings(short_opps, thresholds["short"], regime)
        
        # LONG should meet lowered threshold
        assert longs[0]["meets_threshold"] is True
        
        # SHORT should NOT meet raised threshold
        assert shorts[0]["meets_threshold"] is False
        assert shorts[0]["regime_warning"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])