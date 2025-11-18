#!/usr/bin/env python3
"""
Тестирование новой логики сканера и скоринга (после исправлений)
Проверяет:
1. Матрицу скоринга (10 факторов)
2. Корреляцию с BTC
3. Hard-coded риск-менеджмент ($30 депозит)
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Добавляем путь к mcp_server
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

# from loguru import logger
class Logger:
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARN] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def remove(self): pass
    def add(self, *args, **kwargs): pass

logger = Logger()

from technical_analysis import TechnicalAnalysis
from market_scanner import MarketScanner
from bybit_client import BybitClient

# Настройка логирования
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)

def load_credentials() -> Dict[str, Any]:
    """Загрузка credentials"""
    config_path = Path(__file__).parent / "config" / "credentials.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Credentials not found: {config_path}")
        sys.exit(1)

async def main():
    logger.info("🚀 ЗАПУСК ТЕСТА СИСТЕМНЫХ ИСПРАВЛЕНИЙ")
    
    # Инициализация
    creds = load_credentials()["bybit"]
    client = BybitClient(creds["api_key"], creds["api_secret"], testnet=creds.get("testnet", False))
    ta = TechnicalAnalysis(client)
    scanner = MarketScanner(client, ta)
    
    try:
        # 1. Тест BTC Correlation
        logger.info("\n🧪 ТЕСТ 1: BTC Correlation")
        eth_corr = await ta.get_btc_correlation("ETH/USDT")
        
        if "correlation" in eth_corr:
            logger.info(f"✅ BTC Correlation calculated: {eth_corr['correlation']} ({eth_corr['interpretation']})")
            print(json.dumps(eth_corr, indent=2, ensure_ascii=False)[:500] + "...")
        else:
            logger.error(f"❌ BTC Correlation failed: {eth_corr}")

        # 2. Тест Scan Market & Scoring Matrix
        logger.info("\n🧪 ТЕСТ 2: Scan Market & Scoring Matrix")
        
        # Сканируем топ 5 по объему
        criteria = {
            "market_type": "spot",
            "min_volume_24h": 5000000, # $5M volume
        }
        
        results = await scanner.scan_market(criteria, limit=3)
        
        if results:
            logger.info(f"✅ Found {len(results)} candidates")
            
            for item in results:
                symbol = item['symbol']
                score = item['score']
                breakdown = item.get('score_breakdown', {})
                plan = item.get('entry_plan', {})
                
                logger.info(f"\n📌 {symbol} | Score: {score}/10")
                
                # Проверка breakdown
                required_keys = ['trend', 'indicators', 'volume', 'pattern', 'risk_reward', 'btc_support', 'sr_level']
                missing_keys = [k for k in required_keys if k not in breakdown]
                
                if not missing_keys:
                    logger.info("✅ Score Breakdown structure correct")
                    print("   Breakdown:", json.dumps(breakdown, indent=2))
                else:
                    logger.error(f"❌ Missing breakdown keys: {missing_keys}")
                
                # 3. Тест Risk Management
                logger.info("🧪 ТЕСТ 3: Risk Management Check")
                
                risk_usd = plan.get('risk_usd')
                rec_size = plan.get('recommended_size')
                
                if risk_usd is not None and rec_size is not None:
                    # Проверяем что риск около $0.60 (0.02 * 30)
                    if 0.58 <= risk_usd <= 0.62:
                        logger.info(f"✅ Risk USD correct: ${risk_usd} (Target: $0.60)")
                    else:
                        logger.warning(f"⚠️ Risk USD deviates: ${risk_usd} (Target: $0.60)")
                        
                    logger.info(f"   Position Size: {rec_size}")
                    logger.info(f"   Entry: {plan.get('entry_price')} | SL: {plan.get('stop_loss')}")
                else:
                    logger.error("❌ Missing risk management fields in entry plan")
                    
        else:
            logger.warning("⚠️ No results found (market might be quiet or filters too strict)")

    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())

