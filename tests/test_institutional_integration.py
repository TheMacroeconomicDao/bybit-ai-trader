"""
Integration test for Institutional modules
Tests the complete pipeline without real API calls
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.tier_classifier import TierClassifier
from mcp_server.regime_detector import RegimeDetector
from mcp_server.adaptive_thresholds import AdaptiveThresholds
from mcp_server.smart_display import SmartDisplay


def test_institutional_pipeline():
    """
    Test complete institutional pipeline
    
    VERIFIES:
    1. Regime detection works
    2. Adaptive thresholds calculated
    3. Tier classification works
    4. Smart display shows both directions
    5. Warnings added appropriately
    """
    
    print("\n" + "="*60)
    print("INSTITUTIONAL PIPELINE INTEGRATION TEST")
    print("="*60 + "\n")
    
    # ═══════════════════════════════════════════════════════
    # STAGE 1: REGIME DETECTION
    # ═══════════════════════════════════════════════════════
    
    print("Stage 1: Regime Detection...")
    
    # Mock BTC analysis (strong bull scenario)
    mock_btc_analysis = {
        "composite_signal": {
            "signal": "STRONG_BUY",
            "confidence": 0.78,
            "score": 15
        },
        "timeframes": {
            "4h": {
                "indicators": {
                    "adx": {"adx": 32},
                    "atr": {"atr_14": 500}
                },
                "trend": {
                    "direction": "uptrend",
                    "strength": "very_strong"
                }
            },
            "1d": {
                "current_price": 50000,
                "trend": {
                    "direction": "uptrend",
                    "strength": "strong"
                }
            }
        }
    }
    
    market_regime = RegimeDetector.detect(mock_btc_analysis)
    
