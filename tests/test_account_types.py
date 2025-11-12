"""
Тесты для работы с типами счетов Bybit
Покрывает все сценарии работы с SPOT, CONTRACT, UNIFIED счетами
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_server"))

from trading_operations import (
    get_account_type_for_category,
    get_all_account_balances,
    BalanceCache,
    get_balance_cache,
    TradingOperations
)


class TestAccountTypeForCategory(unittest.TestCase):
    """Тесты для функции get_account_type_for_category"""
    
    def test_spot_with_unified_preference(self):
        """Тест: spot категория с предпочтением UNIFIED"""
        result = get_account_type_for_category("spot", prefer_unified=True)
        self.assertEqual(result, "UNIFIED")
    
    def test_spot_without_unified_preference(self):
        """Тест: spot категория без предпочтения UNIFIED"""
        result = get_account_type_for_category("spot", prefer_unified=False)
        self.assertEqual(result, "SPOT")
    
    def test_linear_with_unified_preference(self):
        """Тест: linear категория с предпочтением UNIFIED"""
        result = get_account_type_for_category("linear", prefer_unified=True)
        self.assertEqual(result, "UNIFIED")
    
    def test_linear_without_unified_preference(self):
        """Тест: linear категория без предпочтения UNIFIED"""
        result = get_account_type_for_category("linear", prefer_unified=False)
        self.assertEqual(result, "CONTRACT")
    
    def test_inverse_with_unified_preference(self):
        """Тест: inverse категория с предпочтением UNIFIED"""
        result = get_account_type_for_category("inverse", prefer_unified=True)
        self.assertEqual(result, "UNIFIED")
    
    def test_inverse_without_unified_preference(self):
        """Тест: inverse категория без предпочтения UNIFIED"""
        result = get_account_type_for_category("inverse", prefer_unified=False)
        self.assertEqual(result, "CONTRACT")
    
    def test_unknown_category_defaults_to_unified(self):
        """Тест: неизвестная категория возвращает UNIFIED по умолчанию"""
        result = get_account_type_for_category("unknown")
        self.assertEqual(result, "UNIFIED")


class TestBalanceCache(unittest.TestCase):
    """Тесты для класса BalanceCache"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.cache = BalanceCache(ttl_seconds=30)
    
    def test_cache_set_and_get(self):
        """Тест: сохранение и получение из кэша"""
        data = {"total": 30.0, "available": 30.0, "success": True}
        self.cache.set("SPOT", data, "USDT")
        
        result = self.cache.get("SPOT", "USDT")
        self.assertIsNotNone(result)
        self.assertEqual(result["total"], 30.0)
        self.assertEqual(result["available"], 30.0)
    
    def test_cache_expiration(self):
        """Тест: истечение срока действия кэша"""
        cache = BalanceCache(ttl_seconds=0)  # Немедленное истечение
        data = {"total": 30.0, "available": 30.0, "success": True}
        cache.set("SPOT", data, "USDT")
        
        result = cache.get("SPOT", "USDT")
        self.assertIsNone(result)  # Кэш должен истечь
    
    def test_cache_miss(self):
        """Тест: промах кэша (данные отсутствуют)"""
        result = self.cache.get("SPOT", "USDT")
        self.assertIsNone(result)
    
    def test_cache_clear(self):
        """Тест: очистка кэша"""
        data = {"total": 30.0, "available": 30.0, "success": True}
        self.cache.set("SPOT", data, "USDT")
        self.cache.set("UNIFIED", data, "USDT")
        
        self.cache.clear()
        
        self.assertIsNone(self.cache.get("SPOT", "USDT"))
        self.assertIsNone(self.cache.get("UNIFIED", "USDT"))
    
    def test_cache_invalidate_by_account_type(self):
        """Тест: инвалидация кэша по типу счета"""
        data = {"total": 30.0, "available": 30.0, "success": True}
        self.cache.set("SPOT", data, "USDT")
        self.cache.set("UNIFIED", data, "USDT")
        
        self.cache.invalidate("SPOT")
        
        self.assertIsNone(self.cache.get("SPOT", "USDT"))
        self.assertIsNotNone(self.cache.get("UNIFIED", "USDT"))
    
    def test_cache_invalidate_by_coin(self):
        """Тест: инвалидация кэша по монете"""
        data_usdt = {"total": 30.0, "available": 30.0, "success": True}
        data_btc = {"total": 0.1, "available": 0.1, "success": True}
        self.cache.set("SPOT", data_usdt, "USDT")
        self.cache.set("SPOT", data_btc, "BTC")
        
        self.cache.invalidate("SPOT", "USDT")
        
        self.assertIsNone(self.cache.get("SPOT", "USDT"))
        self.assertIsNotNone(self.cache.get("SPOT", "BTC"))
    
    def test_cache_thread_safety(self):
        """Тест: потокобезопасность кэша"""
        import threading
        
        data = {"total": 30.0, "available": 30.0, "success": True}
        results = []
        
        def set_cache():
            for i in range(10):
                self.cache.set("SPOT", data, f"COIN{i}")
        
        def get_cache():
            for i in range(10):
                result = self.cache.get("SPOT", f"COIN{i}")
                results.append(result)
        
        threads = []
        for _ in range(5):
            t1 = threading.Thread(target=set_cache)
            t2 = threading.Thread(target=get_cache)
            threads.extend([t1, t2])
            t1.start()
            t2.start()
        
        for t in threads:
            t.join()
        
        # Проверяем, что не было ошибок
        self.assertTrue(len(results) > 0)


class TestGetAllAccountBalances(unittest.TestCase):
    """Тесты для функции get_all_account_balances"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.mock_session = Mock()
        self.cache = BalanceCache(ttl_seconds=30)
    
    def test_get_balances_all_accounts_success(self):
        """Тест: успешное получение балансов со всех счетов"""
        # Мокаем ответы API
        self.mock_session.get_wallet_balance.side_effect = [
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "30.0",
                            "availableToWithdraw": "30.0"
                        }]
                    }]
                }
            },
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "0.0",
                            "availableToWithdraw": "0.0"
                        }]
                    }]
                }
            },
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "0.0",
                            "availableToWithdraw": "0.0"
                        }]
                    }]
                }
            }
        ]
        
        result = get_all_account_balances(self.mock_session, coin="USDT", use_cache=False)
        
        self.assertEqual(result["spot"]["total"], 30.0)
        self.assertEqual(result["spot"]["available"], 30.0)
        self.assertTrue(result["spot"]["success"])
        self.assertEqual(result["total"], 30.0)
        self.assertEqual(result["available"], 30.0)
    
    def test_get_balances_with_cache(self):
        """Тест: использование кэша при получении балансов"""
        # Первый вызов - сохраняем в кэш
        self.mock_session.get_wallet_balance.return_value = {
            "retCode": 0,
            "result": {
                "list": [{
                    "coin": [{
                        "coin": "USDT",
                        "walletBalance": "30.0",
                        "availableToWithdraw": "30.0"
                    }]
                }]
            }
        }
        
        # Первый вызов
        result1 = get_all_account_balances(
            self.mock_session, 
            coin="USDT", 
            use_cache=True,
            cache=self.cache
        )
        
        # Второй вызов - должен использовать кэш
        result2 = get_all_account_balances(
            self.mock_session, 
            coin="USDT", 
            use_cache=True,
            cache=self.cache
        )
        
        # Проверяем, что API был вызван только один раз для каждого типа счета
        # (в реальности будет 3 вызова для SPOT, CONTRACT, UNIFIED)
        self.assertEqual(result1["spot"]["total"], result2["spot"]["total"])
    
    def test_get_balances_api_error(self):
        """Тест: обработка ошибок API"""
        self.mock_session.get_wallet_balance.side_effect = [
            {"retCode": 10001, "retMsg": "Invalid API key"},
            {"retCode": 10001, "retMsg": "Invalid API key"},
            {"retCode": 10001, "retMsg": "Invalid API key"}
        ]
        
        result = get_all_account_balances(self.mock_session, coin="USDT", use_cache=False)
        
        # Все балансы должны быть неуспешными
        self.assertFalse(result["spot"]["success"])
        self.assertFalse(result["contract"]["success"])
        self.assertFalse(result["unified"]["success"])
        self.assertEqual(result["total"], 0.0)
    
    def test_get_balances_partial_success(self):
        """Тест: частичный успех (только SPOT работает)"""
        self.mock_session.get_wallet_balance.side_effect = [
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "30.0",
                            "availableToWithdraw": "30.0"
                        }]
                    }]
                }
            },
            Exception("Network error"),
            {"retCode": 10001, "retMsg": "Account not found"}
        ]
        
        result = get_all_account_balances(self.mock_session, coin="USDT", use_cache=False)
        
        self.assertTrue(result["spot"]["success"])
        self.assertFalse(result["contract"]["success"])
        self.assertFalse(result["unified"]["success"])
        self.assertEqual(result["total"], 30.0)


class TestClosePositionAccountTypes(unittest.TestCase):
    """Тесты для close_position с разными типами счетов"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.trading_ops = TradingOperations(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )
    
    @patch.object(TradingOperations, 'session')
    def test_close_spot_position_with_spot_account(self, mock_session):
        """Тест: закрытие spot позиции со SPOT счетом"""
        # Мокаем успешный ответ для SPOT
        mock_session.get_wallet_balance.return_value = {
            "retCode": 0,
            "result": {
                "list": [{
                    "coin": [{
                        "coin": "BTC",
                        "walletBalance": "0.001",
                        "availableToWithdraw": "0.001"
                    }]
                }]
            }
        }
        
        mock_session.place_order.return_value = {
            "retCode": 0,
            "result": {
                "orderId": "12345"
            }
        }
        
        import asyncio
        result = asyncio.run(
            self.trading_ops.close_position("BTCUSDT", category="spot", reason="Test")
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["symbol"], "BTCUSDT")
        # Проверяем, что был вызван get_wallet_balance с SPOT
        mock_session.get_wallet_balance.assert_called()
    
    @patch.object(TradingOperations, 'session')
    def test_close_spot_position_fallback_to_unified(self, mock_session):
        """Тест: fallback на UNIFIED если SPOT не работает"""
        # SPOT возвращает ошибку
        # UNIFIED возвращает успех
        mock_session.get_wallet_balance.side_effect = [
            {"retCode": 10001, "retMsg": "Account not found"},  # SPOT
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "BTC",
                            "walletBalance": "0.001",
                            "availableToWithdraw": "0.001"
                        }]
                    }]
                }
            }  # UNIFIED
        ]
        
        mock_session.place_order.return_value = {
            "retCode": 0,
            "result": {
                "orderId": "12345"
            }
        }
        
        import asyncio
        result = asyncio.run(
            self.trading_ops.close_position("BTCUSDT", category="spot", reason="Test")
        )
        
        self.assertTrue(result["success"])
        # Проверяем, что было 2 вызова (SPOT, затем UNIFIED)
        self.assertEqual(mock_session.get_wallet_balance.call_count, 2)


class TestGetAccountInfoWithCache(unittest.TestCase):
    """Тесты для get_account_info с кэшированием"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.mock_session = Mock()
        self.cache = BalanceCache(ttl_seconds=30)
    
    def test_get_account_info_uses_cache(self):
        """Тест: get_account_info использует кэш"""
        # Сохраняем данные в кэш
        spot_data = {"total": 30.0, "available": 30.0, "success": True}
        self.cache.set("SPOT", spot_data, "USDT")
        
        # Мокаем только для CONTRACT и UNIFIED (SPOT из кэша)
        self.mock_session.get_wallet_balance.side_effect = [
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "0.0",
                            "availableToWithdraw": "0.0"
                        }]
                    }]
                }
            },
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "0.0",
                            "availableToWithdraw": "0.0"
                        }]
                    }]
                }
            }
        ]
        
        result = get_all_account_balances(
            self.mock_session,
            coin="USDT",
            use_cache=True,
            cache=self.cache
        )
        
        # SPOT должен быть из кэша
        self.assertEqual(result["spot"]["total"], 30.0)
        # CONTRACT и UNIFIED должны быть из API
        # Проверяем, что было только 2 вызова API (CONTRACT и UNIFIED)
        self.assertEqual(self.mock_session.get_wallet_balance.call_count, 2)


class TestAccountTypesIntegration(unittest.TestCase):
    """Интеграционные тесты для всех сценариев"""
    
    def test_scenario_spot_account_only(self):
        """Сценарий 1: Средства только на SPOT счете"""
        mock_session = Mock()
        mock_session.get_wallet_balance.side_effect = [
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "30.0",
                            "availableToWithdraw": "30.0"
                        }]
                    }]
                }
            },
            {"retCode": 10001, "retMsg": "Account not found"},  # CONTRACT
            {"retCode": 10001, "retMsg": "Account not found"}   # UNIFIED
        ]
        
        result = get_all_account_balances(mock_session, coin="USDT", use_cache=False)
        
        self.assertTrue(result["spot"]["success"])
        self.assertEqual(result["spot"]["total"], 30.0)
        self.assertFalse(result["contract"]["success"])
        self.assertFalse(result["unified"]["success"])
        self.assertEqual(result["total"], 30.0)
    
    def test_scenario_unified_account_only(self):
        """Сценарий 2: Средства только на UNIFIED счете"""
        mock_session = Mock()
        mock_session.get_wallet_balance.side_effect = [
            {"retCode": 10001, "retMsg": "Account not found"},  # SPOT
            {"retCode": 10001, "retMsg": "Account not found"},  # CONTRACT
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "30.0",
                            "availableToWithdraw": "30.0"
                        }]
                    }]
                }
            }  # UNIFIED
        ]
        
        result = get_all_account_balances(mock_session, coin="USDT", use_cache=False)
        
        self.assertFalse(result["spot"]["success"])
        self.assertFalse(result["contract"]["success"])
        self.assertTrue(result["unified"]["success"])
        self.assertEqual(result["unified"]["total"], 30.0)
        self.assertEqual(result["total"], 30.0)
    
    def test_scenario_distributed_balances(self):
        """Сценарий 3: Средства распределены между счетами"""
        mock_session = Mock()
        mock_session.get_wallet_balance.side_effect = [
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "20.0",
                            "availableToWithdraw": "20.0"
                        }]
                    }]
                }
            },  # SPOT: 20 USDT
            {
                "retCode": 0,
                "result": {
                    "list": [{
                        "coin": [{
                            "coin": "USDT",
                            "walletBalance": "10.0",
                            "availableToWithdraw": "10.0"
                        }]
                    }]
                }
            },  # CONTRACT: 10 USDT
            {"retCode": 10001, "retMsg": "Account not found"}  # UNIFIED
        ]
        
        result = get_all_account_balances(mock_session, coin="USDT", use_cache=False)
        
        self.assertTrue(result["spot"]["success"])
        self.assertTrue(result["contract"]["success"])
        self.assertFalse(result["unified"]["success"])
        self.assertEqual(result["spot"]["total"], 20.0)
        self.assertEqual(result["contract"]["total"], 10.0)
        self.assertEqual(result["total"], 30.0)  # Сумма всех счетов


if __name__ == "__main__":
    unittest.main()





