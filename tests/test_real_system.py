"""
Real System Testing
Проверяет реальную работу всех компонентов с API
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv()

from mcp_server.bybit_client import BybitClient
from mcp_server.technical_analysis import TechnicalAnalysis
from mcp_server.market_scanner import MarketScanner
from mcp_server.whale_detector import WhaleDetector
from mcp_server.volume_profile import VolumeProfileAnalyzer
from mcp_server.session_manager import SessionManager
from mcp_server.orb_strategy import OpeningRangeBreakout
from mcp_server.ml_predictor import MLPredictor


async def test_session_manager():
    """Тест Session Manager (не требует API)"""
    print("\n🌍 TESTING SESSION MANAGER...")
    
    try:
        sm = SessionManager()
        session = sm.get_current_session()
        info = sm.get_session_info()
        multiplier = sm.get_multiplier()
        
        print(f"✅ Current Session: {session}")
        print(f"✅ Session Info: {info.get('name')}")
        print(f"✅ Volatility: {info.get('volatility')}")
        print(f"✅ Position Multiplier: {multiplier}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ml_predictor():
    """Тест ML Predictor (не требует API)"""
    print("\n🤖 TESTING ML PREDICTOR...")
    
    try:
        ml = MLPredictor()
        
        # Test prediction
        result = ml.predict_success_probability(
            confluence_score=15.0,
            pattern_type="bull_flag",
            volume_ratio=1.5,
            btc_aligned=True,
            session="overlap",
            rsi=30.0,
            risk_reward=2.5
        )
        
        print(f"✅ Predicted Probability: {result.get('predicted_probability'):.3f}")
        print(f"✅ Confidence: {result.get('confidence'):.3f}")
        print(f"✅ Method: {result.get('method')}")
        print(f"✅ Base Probability: {result.get('base_probability'):.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bybit_connection():
    """Тест подключения к Bybit"""
    print("\n🔌 TESTING BYBIT CONNECTION...")
    
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("⚠️ API keys not set - skipping API tests")
        return None
    
    try:
        client = BybitClient(api_key, api_secret, testnet=True)
        
        # Test connection
        price_data = await client.get_asset_price("BTC/USDT")
        print(f"✅ Connection OK")
        print(f"✅ BTC Price: ${price_data.get('price', 'N/A')}")
        
        await client.close()
        return True
    except Exception as e:
        error_msg = str(e)
        # Если это ошибка аутентификации - это нормально для теста
        if "API key is invalid" in error_msg or "AuthenticationError" in error_msg or "retCode\":10003" in error_msg:
            print(f"⚠️ API keys invalid or not set - skipping API tests")
            print("   Set BYBIT_API_KEY and BYBIT_API_SECRET in .env for full testing")
            try:
                await client.close()
            except:
                pass
            return None  # Skip, not fail
        print(f"❌ Error: {error_msg}")
        import traceback
        traceback.print_exc()
        try:
            await client.close()
        except:
            pass
        return False


async def test_scoring_system_real():
    """Тест scoring системы на реальных данных"""
    print("\n📊 TESTING SCORING SYSTEM (REAL DATA)...")
    
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("⚠️ API keys not set - skipping")
        return None
    
    try:
        client = BybitClient(api_key, api_secret, testnet=True)
        ta = TechnicalAnalysis(client)
        scanner = MarketScanner(client, ta)
        
        # Real market scan
        print("   Scanning market...")
        results = await scanner.scan_market({
            "market_type": "spot",
            "min_volume_24h": 1000000
        }, limit=3)
        
        if results:
            top = results[0]
            score_data = top.get('score_breakdown', {})
            
            print(f"✅ Top Asset: {top.get('symbol')}")
            print(f"✅ Total Score: {top.get('score', 0):.1f}/20")
            print(f"✅ System: {score_data.get('system', 'unknown')}")
            
            # Проверяем компоненты
            components = ['trend', 'indicators', 'cvd', 'volume', 'order_blocks', 
                        'fvg', 'structure', 'liquidity_grab', 'session', 'whale', 
                        'volume_profile']
            
            found = [c for c in components if c in score_data]
            print(f"✅ Components found: {len(found)}/{len(components)}")
            
            # Проверяем что это 20-point система
            total = top.get('score', 0)
            if total <= 20.0 and '20-point' in str(score_data.get('system', '')):
                print("✅ 20-point system confirmed")
            else:
                print(f"⚠️ Might not be 20-point (score={total})")
        else:
            print("⚠️ No results from scan")
        
        await client.close()
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orb_strategy_real():
    """Тест ORB Strategy на реальных данных"""
    print("\n🎯 TESTING ORB STRATEGY (REAL DATA)...")
    
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("⚠️ API keys not set - skipping")
        return None
    
    try:
        client = BybitClient(api_key, api_secret, testnet=True)
        ta = TechnicalAnalysis(client)
        orb = OpeningRangeBreakout(client, ta)
        
        # Test ORB detection
        result = await orb.detect_orb_setup("BTC/USDT")
        
        if result.get('has_setup'):
            print(f"✅ ORB Setup Found!")
            print(f"   Session: {result.get('session')}")
            print(f"   Side: {result.get('side')}")
            print(f"   Entry: ${result.get('entry_price')}")
            print(f"   R:R: {result.get('risk_reward')}")
            print(f"   Strength: {result.get('strength')}")
        else:
            reason = result.get('reason', 'Unknown')
            print(f"ℹ️ No ORB setup (reason: {reason})")
            print("   This is normal if not in ORB time window")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_advanced_features_real():
    """Тест Advanced Features на реальных данных"""
    print("\n🐋 TESTING ADVANCED FEATURES (REAL DATA)...")
    
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("⚠️ API keys not set - skipping")
        return None
    
    try:
        client = BybitClient(api_key, api_secret, testnet=True)
        
        # Test Whale Detector
        print("   Testing Whale Detector...")
        whale = WhaleDetector(client)
        whale_result = await whale.detect_whale_activity("BTC/USDT", lookback_trades=500)
        print(f"✅ Whale Activity: {whale_result.get('whale_activity')}")
        print(f"✅ Flow: {whale_result.get('flow_direction')}")
        
        # Test Volume Profile
        print("   Testing Volume Profile...")
        vp = VolumeProfileAnalyzer(client)
        vp_result = await vp.calculate_volume_profile("BTC/USDT", timeframe="4h", lookback=50)
        if 'error' not in vp_result:
            print(f"✅ POC: ${vp_result.get('poc')}")
            print(f"✅ Position: {vp_result.get('current_position')}")
        else:
            print(f"⚠️ VP Error: {vp_result.get('error')}")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Запуск всех реальных тестов"""
    print("="*60)
    print("🧪 REAL SYSTEM TESTING")
    print("="*60)
    
    results = {}
    
    # Test 1: Session Manager (не требует API)
    results['session'] = await test_session_manager()
    
    # Test 2: ML Predictor (не требует API)
    results['ml_predictor'] = await test_ml_predictor()
    
    # Test 3: Bybit Connection
    results['connection'] = await test_bybit_connection()
    
    # Test 4: Scoring System (требует API)
    if results.get('connection'):
        results['scoring'] = await test_scoring_system_real()
        results['orb'] = await test_orb_strategy_real()
        results['advanced'] = await test_advanced_features_real()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    skipped = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)
    total = len(results)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is None:
            status = "⚠️ SKIPPED (no API keys)"
        else:
            status = "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\n✅ PASSED: {passed}")
    print(f"⚠️ SKIPPED: {skipped}")
    print(f"❌ FAILED: {failed}")
    print(f"📊 TOTAL: {total}")
    
    if passed == total - skipped:
        print("\n🎉 ALL AVAILABLE TESTS PASSED!")
    elif failed > 0:
        print(f"\n⚠️ {failed} test(s) failed. Review errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)






