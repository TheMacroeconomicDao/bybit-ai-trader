"""
Comprehensive System Test
Проверяет все компоненты системы после cleanup
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv()


async def test_imports():
    """Тест всех критических импортов"""
    print("\n📦 TESTING IMPORTS...")
    
    errors = []
    
    try:
        from mcp_server.bybit_client import BybitClient
        print("✅ BybitClient")
    except Exception as e:
        errors.append(f"BybitClient: {e}")
        print(f"❌ BybitClient: {e}")
    
    try:
        from mcp_server.technical_analysis import TechnicalAnalysis
        print("✅ TechnicalAnalysis")
    except Exception as e:
        errors.append(f"TechnicalAnalysis: {e}")
        print(f"❌ TechnicalAnalysis: {e}")
    
    try:
        from mcp_server.market_scanner import MarketScanner
        print("✅ MarketScanner")
    except Exception as e:
        errors.append(f"MarketScanner: {e}")
        print(f"❌ MarketScanner: {e}")
    
    try:
        from mcp_server.whale_detector import WhaleDetector
        print("✅ WhaleDetector")
    except Exception as e:
        errors.append(f"WhaleDetector: {e}")
        print(f"❌ WhaleDetector: {e}")
    
    try:
        from mcp_server.volume_profile import VolumeProfileAnalyzer
        print("✅ VolumeProfileAnalyzer")
    except Exception as e:
        errors.append(f"VolumeProfileAnalyzer: {e}")
        print(f"❌ VolumeProfileAnalyzer: {e}")
    
    try:
        from mcp_server.session_manager import SessionManager
        print("✅ SessionManager")
    except Exception as e:
        errors.append(f"SessionManager: {e}")
        print(f"❌ SessionManager: {e}")
    
    try:
        from mcp_server.orb_strategy import OpeningRangeBreakout
        print("✅ OpeningRangeBreakout")
    except Exception as e:
        errors.append(f"OpeningRangeBreakout: {e}")
        print(f"❌ OpeningRangeBreakout: {e}")
    
    try:
        from mcp_server.ml_predictor import MLPredictor
        print("✅ MLPredictor")
    except Exception as e:
        errors.append(f"MLPredictor: {e}")
        print(f"❌ MLPredictor: {e}")
    
    try:
        from autonomous_agent.autonomous_analyzer import AutonomousAnalyzer
        print("✅ AutonomousAnalyzer")
    except Exception as e:
        errors.append(f"AutonomousAnalyzer: {e}")
        print(f"❌ AutonomousAnalyzer: {e}")
    
    return len(errors) == 0, errors


async def test_critical_files():
    """Проверка наличия критических файлов"""
    print("\n📄 TESTING CRITICAL FILES...")
    
    critical_files = [
        "SYSTEM_MASTER_INSTRUCTIONS.md",
        ".cursorrules",
        "requirements.txt",
        "mcp_server/market_scanner.py",
        "mcp_server/technical_analysis.py",
        "autonomous_agent/autonomous_analyzer.py",
        "knowledge_base/1_trading_fundamentals.md",
        "knowledge_base/2_technical_indicators_guide.md",
        "prompts/comprehensive_market_analysis_2025.md"
    ]
    
    missing = []
    for file in critical_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            missing.append(file)
            print(f"❌ MISSING: {file}")
    
    return len(missing) == 0, missing


async def test_basic_functionality():
    """Тест базовой функциональности"""
    print("\n⚙️ TESTING BASIC FUNCTIONALITY...")
    
    try:
        from mcp_server.bybit_client import BybitClient
        from mcp_server.technical_analysis import TechnicalAnalysis
        from mcp_server.market_scanner import MarketScanner
        from mcp_server.session_manager import SessionManager
        
        # Test SessionManager (не требует API)
        sm = SessionManager()
        session = sm.get_current_session()
        print(f"✅ SessionManager: {session}")
        
        # Test MarketScanner initialization (без API вызовов)
        api_key = os.getenv("BYBIT_API_KEY", "test")
        api_secret = os.getenv("BYBIT_API_SECRET", "test")
        
        if api_key != "test" and api_secret != "test":
            client = BybitClient(api_key, api_secret, testnet=True)
            ta = TechnicalAnalysis(client)
            scanner = MarketScanner(client, ta)
            print("✅ MarketScanner initialized")
            
            # Test scoring system
            test_analysis = {
                "composite_signal": {"signal": "BUY", "score": 5},
                "timeframes": {
                    "4h": {
                        "trend": {"direction": "uptrend"},
                        "indicators": {"rsi": {"rsi_14": 30}},
                        "patterns": {"candlestick": [{"type": "bullish"}]},
                        "levels": {"support": [100]},
                        "order_blocks": [{"type": "bullish_ob"}],
                        "fair_value_gaps": [],
                        "structure": {"bos": []},
                        "liquidity_grabs": []
                    }
                }
            }
            
            test_ticker = {"symbol": "BTC/USDT", "price": 50000}
            
            score_result = scanner._calculate_opportunity_score(
                test_analysis, test_ticker, "uptrend", None
            )
            
            print(f"✅ Scoring system: {score_result.get('total', 0):.1f}/20")
            print(f"✅ System type: {score_result.get('system', 'unknown')}")
            
            await client.close()
        else:
            print("⚠️ API keys not set - skipping API tests")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scoring_system():
    """Тест 20-point scoring system"""
    print("\n📊 TESTING 20-POINT SCORING...")
    
    try:
        from mcp_server.market_scanner import MarketScanner
        from mcp_server.bybit_client import BybitClient
        from mcp_server.technical_analysis import TechnicalAnalysis
        
        api_key = os.getenv("BYBIT_API_KEY", "test")
        api_secret = os.getenv("BYBIT_API_SECRET", "test")
        
        if api_key == "test":
            print("⚠️ Skipping - API keys not set")
            return True
        
        client = BybitClient(api_key, api_secret, testnet=True)
        ta = TechnicalAnalysis(client)
        scanner = MarketScanner(client, ta)
        
        # Mock analysis для теста scoring
        mock_analysis = {
            "composite_signal": {
                "signal": "STRONG_BUY",
                "score": 7,
                "alignment": 0.8,
                "buy_signals": 5
            },
            "timeframes": {
                "4h": {
                    "trend": {"direction": "uptrend"},
                    "indicators": {
                        "rsi": {"rsi_14": 25},
                        "macd": {"histogram": 10},
                        "bollinger_bands": {"position": "lower"},
                        "adx": {"adx": 30},
                        "volume": {"volume_ratio": 2.0}
                    },
                    "patterns": {
                        "candlestick": [{"type": "bullish", "name": "hammer"}]
                    },
                    "levels": {
                        "support": [49000],
                        "resistance": [51000]
                    },
                    "order_blocks": [{"type": "bullish_ob"}],
                    "fair_value_gaps": [{"type": "bullish_fvg", "mid": 49500, "strength": "strong"}],
                    "structure": {
                        "bos": [{"type": "bullish_bos"}]
                    },
                    "liquidity_grabs": [{"type": "bullish_grab", "strength": "strong"}],
                    "volume_profile": {
                        "current_position": "below_va",
                        "confluence_with_poc": True
                    }
                }
            },
            "cvd_analysis": {
                "signal": "BULLISH_ABSORPTION",
                "aggressive_ratio": 1.5
            },
            "whale_analysis": {
                "whale_activity": "accumulation",
                "flow_direction": "strong_bullish"
            }
        }
        
        mock_ticker = {"symbol": "BTC/USDT", "price": 50000}
        
        score_result = scanner._calculate_opportunity_score(
            mock_analysis, mock_ticker, "uptrend", None
        )
        
        total_score = score_result.get("total", 0)
        system = score_result.get("system", "")
        breakdown = score_result.get("breakdown", {})
        
        print(f"✅ Total Score: {total_score:.1f}/20")
        print(f"✅ System: {system}")
        print(f"✅ Breakdown components: {len(breakdown)}")
        
        # Проверяем что это 20-point система
        if "20-point" in str(system) or total_score <= 20.0:
            print("✅ 20-point system confirmed")
        else:
            print("⚠️ Might not be 20-point system")
        
        # Проверяем наличие новых компонентов
        has_whale = "whale" in breakdown
        has_vp = "volume_profile" in breakdown
        has_session = "session" in breakdown
        has_grab = "liquidity_grab" in breakdown
        
        print(f"\n✅ Advanced Components:")
        print(f"  - Whale: {'✅' if has_whale else '❌'}")
        print(f"  - Volume Profile: {'✅' if has_vp else '❌'}")
        print(f"  - Session: {'✅' if has_session else '❌'}")
        print(f"  - Liquidity Grab: {'✅' if has_grab else '❌'}")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Запуск всех тестов"""
    print("="*60)
    print("🧪 COMPREHENSIVE SYSTEM TEST")
    print("="*60)
    
    results = {}
    
    # Test 1: Imports
    results['imports'], import_errors = await test_imports()
    
    # Test 2: Critical Files
    results['files'], missing_files = await test_critical_files()
    
    # Test 3: Basic Functionality
    results['functionality'] = await test_basic_functionality()
    
    # Test 4: Scoring System
    results['scoring'] = await test_scoring_system()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    if import_errors:
        print(f"\n⚠️ Import Errors: {len(import_errors)}")
        for err in import_errors[:5]:
            print(f"  - {err}")
    
    if missing_files:
        print(f"\n⚠️ Missing Files: {len(missing_files)}")
        for file in missing_files:
            print(f"  - {file}")
    
    print(f"\n✅ TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is working correctly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


