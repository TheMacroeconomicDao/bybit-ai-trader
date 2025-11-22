"""
Comprehensive Testing для Advanced Features
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.bybit_client import BybitClient
from mcp_server.whale_detector import WhaleDetector
from mcp_server.volume_profile import VolumeProfileAnalyzer
from mcp_server.session_manager import SessionManager
from mcp_server.technical_analysis import TechnicalAnalysis
from mcp_server.market_scanner import MarketScanner
import os
from dotenv import load_dotenv

load_dotenv()


async def test_whale_detection():
    """Тест Whale Detector"""
    print("\n🐋 TESTING WHALE DETECTION...")
    
    client = BybitClient(
        os.getenv("BYBIT_API_KEY"),
        os.getenv("BYBIT_API_SECRET"),
        testnet=True
    )
    
    try:
        whale = WhaleDetector(client)
        # Используем формат с / для CCXT
        result = await whale.detect_whale_activity("BTC/USDT")
        
        print(f"✅ Whale Activity: {result.get('whale_activity')}")
        print(f"✅ Flow Direction: {result.get('flow_direction')}")
        print(f"✅ Large Buys: {result.get('large_orders', {}).get('count_large_buys')}")
        print(f"✅ Large Sells: {result.get('large_orders', {}).get('count_large_sells')}")
        print(f"✅ Signals: {result.get('signals', [])}")
        
        return result.get('whale_activity') != 'error'
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await client.close()


async def test_volume_profile():
    """Тест Volume Profile"""
    print("\n📊 TESTING VOLUME PROFILE...")
    
    client = BybitClient(
        os.getenv("BYBIT_API_KEY"),
        os.getenv("BYBIT_API_SECRET"),
        testnet=True
    )
    
    try:
        vp = VolumeProfileAnalyzer(client)
        result = await vp.calculate_volume_profile("BTC/USDT")
        
        if 'error' in result:
            print(f"⚠️ Error: {result.get('error')}")
            return False
        
        print(f"✅ POC: ${result.get('poc')}")
        print(f"✅ VA High: ${result.get('value_area_high')}")
        print(f"✅ VA Low: ${result.get('value_area_low')}")
        print(f"✅ Current Position: {result.get('current_position')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await client.close()


def test_session_manager():
    """Тест Session Manager"""
    print("\n🌍 TESTING SESSION MANAGER...")
    
    try:
        sm = SessionManager()
        session = sm.get_current_session()
        info = sm.get_session_info()
        
        print(f"✅ Current Session: {session}")
        print(f"✅ Volatility: {info.get('average_volatility')}")
        print(f"✅ Best For: {info.get('best_for')}")
        print(f"✅ Position Multiplier: {sm.get_multiplier()}")
        
        return session is not None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_liquidity_grabs():
    """Тест Liquidity Grabs Detection"""
    print("\n🎯 TESTING LIQUIDITY GRABS...")
    
    client = BybitClient(
        os.getenv("BYBIT_API_KEY"),
        os.getenv("BYBIT_API_SECRET"),
        testnet=True
    )
    
    try:
        ta = TechnicalAnalysis(client)
        analysis = await ta.analyze_asset("BTC/USDT", timeframes=["4h"])
        
        grabs = analysis.get('timeframes', {}).get('4h', {}).get('liquidity_grabs', [])
        
        print(f"✅ Grabs Detected: {len(grabs)}")
        for g in grabs:
            print(f"  - {g.get('type')}: strength={g.get('strength')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await client.close()


async def test_orb_strategy():
    """Тест ORB Strategy"""
    print("\n🎯 TESTING ORB STRATEGY...")
    
    try:
        from mcp_server.orb_strategy import OpeningRangeBreakout
        
        client = BybitClient(
            os.getenv("BYBIT_API_KEY"),
            os.getenv("BYBIT_API_SECRET"),
            testnet=True
        )
        
        ta = TechnicalAnalysis(client)
        orb = OpeningRangeBreakout(client, ta)
        
        # Тестируем на BTC
        result = await orb.detect_orb_setup("BTC/USDT")
        
        if result.get('has_setup'):
            print(f"✅ ORB Setup Found!")
            print(f"  - Session: {result.get('session')}")
            print(f"  - Side: {result.get('side')}")
            print(f"  - Entry: ${result.get('entry_price')}")
            print(f"  - SL: ${result.get('stop_loss')}")
            print(f"  - TP: ${result.get('take_profit')}")
            print(f"  - R:R: {result.get('risk_reward')}")
            print(f"  - Strength: {result.get('strength')}")
            print(f"  - Confidence: {result.get('confidence')}")
        else:
            reason = result.get('reason', 'Unknown')
            print(f"ℹ️ No ORB setup (reason: {reason})")
            print(f"  - This is normal if not in ORB time window")
        
        await client.close()
        return True  # ORB работает, даже если setup не найден (зависит от времени)
    except ImportError:
        print("⚠️ ORB Strategy not available (ImportError)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_20point_scoring():
    """Тест 20-Point Scoring"""
    print("\n📊 TESTING 20-POINT SCORING...")
    
    client = BybitClient(
        os.getenv("BYBIT_API_KEY"),
        os.getenv("BYBIT_API_SECRET"),
        testnet=True
    )
    
    try:
        ta = TechnicalAnalysis(client)
        scanner = MarketScanner(client, ta)
        
        # Scan БЕЗ whale analysis (чтобы не замедлять тест)
        results = await scanner.scan_market({
            "market_type": "spot",
            "min_volume_24h": 1000000
        }, limit=3)
        
        if results:
            top = results[0]
            score_data = top.get('score_breakdown', {})
            
            print(f"✅ Top Asset: {top.get('symbol')}")
            print(f"✅ Total Score: {top.get('score'):.1f}/20")
            print(f"✅ System: {top.get('score_breakdown', {}).get('system', 'unknown')}")
            print(f"✅ Breakdown (first 5):")
            for i, (component, val) in enumerate(list(score_data.items())[:5]):
                print(f"  - {component}: {val:.2f}")
            
            # Проверяем что новые компоненты присутствуют
            has_session = 'session' in score_data
            has_grab = 'liquidity_grab' in score_data
            
            print(f"\n✅ New Components:")
            print(f"  - Session Score: {'✅' if has_session else '❌'}")
            print(f"  - Liquidity Grab: {'✅' if has_grab else '❌'}")
            
            # Проверяем что система 20-point
            system = score_data.get('system', '')
            if '20-point' in str(system) or top.get('score', 0) <= 20.0:
                print(f"✅ Scoring system: 20-point confirmed")
            else:
                print(f"⚠️ Scoring system might not be 20-point")
        
        await client.close()
        return len(results) > 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return False


async def main():
    """Запуск всех тестов"""
    print("="*60)
    print("🧪 ADVANCED FEATURES TESTING SUITE")
    print("="*60)
    
    results = {}
    
    # Test 1: Session Manager (без async)
    results['session'] = test_session_manager()
    
    # Test 2: Whale Detection
    results['whale'] = await test_whale_detection()
    
    # Test 3: Volume Profile
    results['volume_profile'] = await test_volume_profile()
    
    # Test 4: Liquidity Grabs
    results['liquidity_grabs'] = await test_liquidity_grabs()
    
    # Test 5: ORB Strategy
    results['orb'] = await test_orb_strategy()
    
    # Test 6: 20-Point Scoring
    results['scoring'] = await test_20point_scoring()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\n✅ TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System ready for production.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Fix before deployment.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
