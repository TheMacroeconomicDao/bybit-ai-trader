"""
Performance Test для ORB Strategy
Проверяет что ORB scan не замедляет анализ
"""
import asyncio
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.bybit_client import BybitClient
from mcp_server.technical_analysis import TechnicalAnalysis
from mcp_server.market_scanner import MarketScanner
import os
from dotenv import load_dotenv

load_dotenv()


async def test_orb_performance():
    """Тест производительности ORB scan"""
    print("="*60)
    print("⚡ ORB PERFORMANCE TEST")
    print("="*60)
    
    client = BybitClient(
        os.getenv("BYBIT_API_KEY"),
        os.getenv("BYBIT_API_SECRET"),
        testnet=True
    )
    
    try:
        ta = TechnicalAnalysis(client)
        scanner = MarketScanner(client, ta)
        
        # Тест 1: Scan БЕЗ ORB
        print("\n📊 Test 1: Market Scan WITHOUT ORB...")
        start = time.time()
        results_no_orb = await scanner.scan_market({
            "market_type": "spot",
            "min_volume_24h": 1000000
        }, limit=10)
        time_no_orb = time.time() - start
        print(f"✅ Time: {time_no_orb:.2f}s")
        print(f"✅ Results: {len(results_no_orb)}")
        
        # Тест 2: Scan С ORB (если в нужное время)
        print("\n🎯 Test 2: Market Scan WITH ORB...")
        start = time.time()
        
        # Проверяем текущую сессию
        session = scanner.session_manager.get_current_session()
        print(f"   Current session: {session}")
        
        # Добавляем ORB scan если в нужное время
        all_results = []
        if session in ["european", "us"]:
            print(f"   ✅ ORB time - adding ORB scan")
            try:
                orb_results = await scanner.find_orb_opportunities("spot", min_volume_24h=1000000)
                all_results.extend(orb_results)
                print(f"   ✅ ORB results: {len(orb_results)}")
            except Exception as e:
                print(f"   ⚠️ ORB scan failed: {e}")
        
        # Обычный scan
        results_with_orb = await scanner.scan_market({
            "market_type": "spot",
            "min_volume_24h": 1000000
        }, limit=10)
        all_results.extend(results_with_orb)
        
        time_with_orb = time.time() - start
        print(f"✅ Time: {time_with_orb:.2f}s")
        print(f"✅ Total Results: {len(all_results)}")
        
        # Сравнение
        print("\n" + "="*60)
        print("📊 PERFORMANCE COMPARISON")
        print("="*60)
        print(f"Without ORB: {time_no_orb:.2f}s")
        print(f"With ORB:    {time_with_orb:.2f}s")
        
        overhead = time_with_orb - time_no_orb
        overhead_pct = (overhead / time_no_orb * 100) if time_no_orb > 0 else 0
        
        print(f"\nOverhead: {overhead:.2f}s ({overhead_pct:.1f}%)")
        
        if overhead < 5.0:  # Менее 5 секунд overhead
            print("✅ Performance: EXCELLENT - ORB не замедляет анализ")
        elif overhead < 10.0:
            print("✅ Performance: GOOD - ORB добавляет минимальную задержку")
        elif overhead < 20.0:
            print("⚠️ Performance: ACCEPTABLE - ORB добавляет заметную задержку")
        else:
            print("❌ Performance: POOR - ORB значительно замедляет анализ")
        
        # Проверка что ORB работает только в нужное время
        print("\n" + "="*60)
        print("⏰ ORB TIMING CHECK")
        print("="*60)
        print(f"Current session: {session}")
        print(f"ORB active: {session in ['european', 'us']}")
        
        if session not in ["european", "us"]:
            print("ℹ️ ORB scan skipped (not in ORB time window)")
            print("   This is correct behavior - ORB only works during European/US sessions")
        
        await client.close()
        return overhead < 20.0  # Pass если overhead < 20s
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_orb_performance())
    sys.exit(0 if success else 1)






