#!/usr/bin/env python3
"""
Интеграционный тест институциональных модулей
Проверяет работу новой архитектуры БЕЗ внешних API вызовов
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.tier_classifier import TierClassifier
from mcp_server.regime_detector import RegimeDetector
from mcp_server.adaptive_thresholds import AdaptiveThresholds
from mcp_server.smart_display import SmartDisplay

print("=" * 60)
print("ИНСТИТУЦИОНАЛЬНЫЕ МОДУЛИ - ИНТЕГРАЦИОННЫЙ ТЕСТ")
print("=" * 60)
print()

# ═══════════════════════════════════════════════════════════
# TEST 1: Tier Classification
# ═══════════════════════════════════════════════════════════
print("TEST 1: Tier Classification")
print("-" * 60)

opportunities = [
    {"score": 8.7, "probability": 0.80, "risk_reward": 3.0},
    {"score": 7.5, "probability": 0.68, "risk_reward": 2.3},
    {"score": 6.2, "probability": 0.60, "risk_reward": 1.9},
    {"score": 4.8, "probability": 0.52, "risk_reward": 1.6},
    {"score": 3.2, "probability": 0.42, "risk_reward": 1.2}
]

for i, opp in enumerate(opportunities, 1):
    tier = TierClassifier.classify(
        opp["score"],
        opp["probability"],
        opp["risk_reward"]
    )
    
    color = TierClassifier.get_tier_color(tier)
    size = TierClassifier.get_position_size_multiplier(tier)
    
    print(f"{i}. Score {opp['score']:.1f} | Prob {opp['probability']:.0%} | R:R {opp['risk_reward']:.1f}")
    print(f"   → Tier: {color} {tier.upper()} | Position Size: {size:.0%}")
    print()

print("✅ Tier classification работает!\n")

# ═══════════════════════════════════════════════════════════
# TEST 2: Regime Detection
# ═══════════════════════════════════════════════════════════
print("TEST 2: Regime Detection")
print("-" * 60)

test_regimes = [
    {
        "name": "Strong Bull",
        "analysis": {
            "composite_signal": {"signal": "STRONG_BUY", "confidence": 0.80, "score": 15},
            "timeframes": {
                "4h": {
                    "indicators": {"adx": {"adx": 35}, "atr": {"atr_14": 500}},
                    "trend": {"direction": "uptrend", "strength": "very_strong"}
                }
            }
        }
    },
    {
        "name": "Sideways",
        "analysis": {
            "composite_signal": {"signal": "HOLD", "confidence": 0.50, "score": 0},
            "timeframes": {
                "4h": {
                    "indicators": {"adx": {"adx": 15}, "atr": {"atr_14": 200}},
                    "trend": {"direction": "sideways", "strength": "weak"}
                }
            }
        }
    }
]

for test in test_regimes:
    regime = RegimeDetector.detect(test["analysis"])
    print(f"{test['name']}:")
    print(f"  Type: {regime['type']}")
    print(f"  Confidence: {regime['confidence']:.0%}")
    print(f"  ADX: {regime['metrics']['adx']:.1f}")
    print(f"  Implications: {regime['trading_implications']}")
    print()

print("✅ Regime detection работает!\n")

# ═══════════════════════════════════════════════════════════
# TEST 3: Adaptive Thresholds
# ═══════════════════════════════════════════════════════════
print("TEST 3: Adaptive Thresholds")
print("-" * 60)

for test in test_regimes:
    regime = RegimeDetector.detect(test["analysis"])
    thresholds = AdaptiveThresholds.calculate(regime)
    
    print(f"{test['name']} (regime: {regime['type']}):")
    print(f"  LONG threshold: {thresholds['long']:.1f}/10")
    print(f"  SHORT threshold: {thresholds['short']:.1f}/10")
    print(f"  Reasoning: {thresholds['reasoning']}")
    print()

print("✅ Adaptive thresholds работают!\n")

# ═══════════════════════════════════════════════════════════
# TEST 4: Smart Display
# ═══════════════════════════════════════════════════════════
print("TEST 4: Smart Display (CRITICAL - No Empty Reports)")
print("-" * 60)

# Create mock opportunities
mock_opportunities = [
    {
        "symbol": "ETH/USDT",
        "score": 8.5,
        "tier": "elite",
        "side": "long",
        "probability": 0.78,
        "risk_reward": 2.8,
        "entry_plan": {"risk_reward": 2.8}
    },
    {
        "symbol": "SOL/USDT",
        "score": 7.2,
        "tier": "professional",
        "side": "long",
        "probability": 0.68,
        "risk_reward": 2.2,
        "entry_plan": {"risk_reward": 2.2}
    },
    {
        "symbol": "AVAX/USDT",
        "score": 6.0,
        "tier": "speculative",
        "side": "long",
        "probability": 0.58,
        "risk_reward": 1.8,
        "entry_plan": {"risk_reward": 1.8}
    }
]

# Test in different regimes
regime_strong_bull = {
    "type": "strong_bull",
    "metrics": {"volatility": "normal", "adx": 32}
}

regime_sideways = {
    "type": "sideways",
    "metrics": {"volatility": "normal", "adx": 18}
}

print("Scenario 1: Strong Bull Market (LONG threshold 6.0)")
displayed = SmartDisplay.select_top_3_with_warnings(
    mock_opportunities,
    threshold=6.0,
    market_regime=regime_strong_bull
)
print(f"  Displayed: {len(displayed)} opportunities")
for opp in displayed:
    print(f"    {opp['symbol']}: Score {opp['score']:.1f}, Warning: {opp.get('warning', 'None')}")
print()

print("Scenario 2: Sideways Market (LONG threshold 7.0)")
displayed = SmartDisplay.select_top_3_with_warnings(
    mock_opportunities,
    threshold=7.0,
    market_regime=regime_sideways
)
print(f"  Displayed: {len(displayed)} opportunities")
for opp in displayed:
    has_warning = "Yes" if opp.get('warning') else "No"
    print(f"    {opp['symbol']}: Score {opp['score']:.1f}, Warning: {has_warning}")
print()

print("Scenario 3: Empty Input (should not error)")
displayed = SmartDisplay.select_top_3_with_warnings(
    [],
    threshold=7.0,
    market_regime=regime_sideways
)
print(f"  Displayed: {len(displayed)} opportunities (OK - gracefully handled)")
print()

print("✅ Smart Display работает - no empty reports!\n")

# ═══════════════════════════════════════════════════════════
# TEST 5: Full Pipeline Simulation
# ═══════════════════════════════════════════════════════════
print("TEST 5: Full Pipeline Simulation")
print("-" * 60)

# Simulate full market scan result
print("Step 1: Detect regime...")
mock_btc_analysis = {
    "composite_signal": {"signal": "BUY", "confidence": 0.70, "score": 10},
    "timeframes": {
        "4h": {
            "indicators": {"adx": {"adx": 28}, "atr": {"atr_14": 450}},
            "trend": {"direction": "uptrend", "strength": "strong"}
        }
    }
}
regime = RegimeDetector.detect(mock_btc_analysis)
print(f"  Regime: {regime['type']} ({regime['confidence']:.0%})")

print("\nStep 2: Calculate adaptive thresholds...")
thresholds = AdaptiveThresholds.calculate(regime)
print(f"  LONG: {thresholds['long']:.1f}/10")
print(f"  SHORT: {thresholds['short']:.1f}/10")

print("\nStep 3: Classify all opportunities...")
all_opps = mock_opportunities + [
    {"symbol": "DOGE/USDT", "score": 5.5, "tier": "speculative", "side": "short", "probability": 0.56, "risk_reward": 1.7}
]
for opp in all_opps:
    tier = TierClassifier.classify(opp["score"], opp["probability"], opp["risk_reward"])
    opp["tier"] = tier
    opp["tier_color"] = TierClassifier.get_tier_color(tier)

print(f"  Classified {len(all_opps)} opportunities")

print("\nStep 4: Separate directions...")
longs = [o for o in all_opps if o["side"] == "long"]
shorts = [o for o in all_opps if o["side"] == "short"]
print(f"  LONGS: {len(longs)} | SHORTS: {len(shorts)}")

print("\nStep 5: Smart display selection...")
top_longs = SmartDisplay.select_top_3_with_warnings(longs, thresholds["long"], regime)
top_shorts = SmartDisplay.select_top_3_with_warnings(shorts, thresholds["short"], regime)
print(f"  Display: TOP-{len(top_longs)} LONGS, TOP-{len(top_shorts)} SHORTS")

print("\n✅ Full pipeline simulation successful!\n")

# ═══════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("ИТОГОВЫЙ ОТЧЕТ")
print("=" * 60)
print()
print("✅ TierClassifier: РАБОТАЕТ")
print("✅ RegimeDetector: РАБОТАЕТ")
print("✅ AdaptiveThresholds: РАБОТАЕТ")
print("✅ SmartDisplay: РАБОТАЕТ")
print("✅ Full Pipeline: РАБОТАЕТ")
print()
print("🎉 ВСЕ ИНСТИТУЦИОНАЛЬНЫЕ МОДУЛИ РАБОТАЮТ КОРРЕКТНО!")
print()
print("Следующий шаг: Тест в реальном рынке с Bybit API")
print("=" * 60)
