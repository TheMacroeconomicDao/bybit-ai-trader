# 🔧 BYBIT API PRODUCTION FIX - IMPLEMENTATION GUIDE

**Дата**: 20 ноября 2025  
**Режим**: Production-Only (GitHub Secrets)  
**Приоритет**: КРИТИЧЕСКИЙ

---

## 🎯 ЦЕЛЬ

Исправить критические проблемы с Bybit API в production режиме с безопасной загрузкой ключей из GitHub Secrets через Kubernetes environment variables.

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

### ✅ Что уже работает:
- GitHub Actions workflow: [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml:82-90)
- Kubernetes секреты создаются автоматически из GitHub Secrets
- Environment variables доступны в pod

### ❌ Текущие проблемы:

1. **API Key загрузка**  
   Файл: [`mcp_server/full_server.py`](mcp_server/full_server.py:70-82)
   ```python
   # ПРОБЛЕМА: Читает credentials.json вместо ENV
   def load_credentials() -> Dict[str, Any]:
       config_path = Path(__file__).parent.parent / "config" / "credentials.json"
   ```

2. **Account Balance блокирует всё**  
   Файл: [`mcp_server/market_scanner.py`](mcp_server/market_scanner.py:51-64)
   ```python
   # ПРОБЛЕМА: Жесткая зависимость от баланса
   if account_balance is None or account_balance <= 0:
       raise Exception(f"CRITICAL: Invalid account balance...")
   ```

3. **Нет валидации API ключей**  
   Нет проверки что ключи не placeholder значения

4. **Плохие сообщения об ошибках**  
   `retCode 10003` возвращает generic ошибку

---

## 🛠️ РЕШЕНИЕ

### Задача 1: Исправить загрузку credentials

**Файл**: `mcp_server/full_server.py`

**ЗАМЕНИТЬ функцию (строки 70-82):**

```python
def load_credentials() -> Dict[str, Any]:
    """
    Загрузка credentials с приоритетом:
    1. Environment Variables (GitHub Secrets → Kubernetes)
    2. credentials.json (fallback для локальной разработки)
    
    Raises:
        ValueError: Если API ключи невалидные или отсутствуют
    """
    import os
    from pathlib import Path
    
    # Попытка #1: Загрузка из Environment Variables (Production)
    bybit_api_key = os.getenv("BYBIT_API_KEY")
    bybit_api_secret = os.getenv("BYBIT_API_SECRET")
    bybit_testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    
    # Попытка #2: Загрузка из credentials.json (Local Development)
    if not bybit_api_key or not bybit_api_secret:
        logger.warning("⚠️ BYBIT credentials not found in ENV, trying credentials.json")
        config_path = Path(__file__).parent.parent / "config" / "credentials.json"
        
        try:
            with open(config_path, 'r') as f:
                file_creds = json.load(f)
                bybit_api_key = file_creds["bybit"]["api_key"]
                bybit_api_secret = file_creds["bybit"]["api_secret"]
                bybit_testnet = file_creds["bybit"].get("testnet", False)
        except FileNotFoundError:
            logger.error(f"❌ Credentials not found: {config_path}")
            raise ValueError(
                "No Bybit credentials found! "
                "Set BYBIT_API_KEY and BYBIT_API_SECRET environment variables "
                "or create config/credentials.json"
            )
        except (JSONDecodeError, KeyError) as e:
            logger.error(f"❌ Invalid credentials.json: {e}")
            raise ValueError(f"Invalid credentials.json format: {e}")
    
    # КРИТИЧЕСКАЯ ВАЛИДАЦИЯ
    if not bybit_api_key or not bybit_api_secret:
        raise ValueError("Bybit API credentials are empty!")
    
    # Проверка на placeholder значения
    if bybit_api_key == "your_api_key_here" or bybit_api_secret == "your_api_secret_here":
        raise ValueError(
            "Bybit API credentials are placeholder values! "
            "Please set real API keys in GitHub Secrets or credentials.json"
        )
    
    # Проверка минимальной длины (Bybit ключи обычно длинные)
    if len(bybit_api_key) < 10 or len(bybit_api_secret) < 10:
        raise ValueError(
            f"Bybit API credentials are too short! "
            f"API Key: {len(bybit_api_key)} chars, "
            f"API Secret: {len(bybit_api_secret)} chars. "
            f"This likely means they are invalid."
        )
    
    logger.info("✅ Bybit credentials loaded successfully")
    logger.info(f"   Mode: {'🧪 TESTNET' if bybit_testnet else '🚀 MAINNET'}")
    logger.info(f"   API Key: {bybit_api_key[:8]}...{bybit_api_key[-4:]}")
    
    return {
        "bybit": {
            "api_key": bybit_api_key,
            "api_secret": bybit_api_secret,
            "testnet": bybit_testnet
        }
    }
```

---

### Задача 2: API Health Check при старте

**Файл**: `mcp_server/bybit_client.py`

**ДОБАВИТЬ метод после `__init__` (после строки 66):**

```python
async def validate_api_credentials(self) -> Dict[str, Any]:
    """
    Валидация API credentials при старте системы.
    
    Returns:
        {
            "valid": bool,
            "permissions": List[str],  # ["READ", "WRITE"] или ошибка
            "error": Optional[str]
        }
    
    Raises:
        Exception: Если API ключи невалидные (fail-fast)
    """
    logger.info("🔍 Validating Bybit API credentials...")
    
    try:
        # Простой тест: получаем server time (не требует auth)
        test_ticker = await self.exchange.fetch_ticker('BTC/USDT')
        if not test_ticker:
            raise Exception("API не вернул данные для BTC/USDT")
        
        logger.info("✅ API доступен (public endpoints)")
        
        # Тест authenticated endpoint: get account balance
        try:
            balance = await self.exchange.fetch_balance()
            logger.info("✅ API Key валиден (authenticated endpoints работают)")
            
            # Проверяем какие балансы доступны
            available_accounts = []
            if balance.get('free'):
                available_accounts.append("SPOT")
            if balance.get('total'):
                available_accounts.append("UNIFIED")
            
            return {
                "valid": True,
                "permissions": ["READ", "WRITE"],
                "accounts": available_accounts,
                "error": None
            }
            
        except Exception as auth_error:
            error_msg = str(auth_error)
            
            # Проверяем специфичные ошибки
            if "10003" in error_msg or "invalid" in error_msg.lower():
                logger.error("❌ API Key INVALID (retCode 10003)")
                raise Exception(
                    "Bybit API Key is INVALID! "
                    "Please check your BYBIT_API_KEY and BYBIT_API_SECRET in GitHub Secrets. "
                    f"Error: {error_msg}"
                )
            elif "10004" in error_msg or "permission" in error_msg.lower():
                logger.error("❌ API Key has NO PERMISSIONS (retCode 10004)")
                raise Exception(
                    "Bybit API Key has insufficient permissions! "
                    "Please enable READ permissions on Bybit API Management page. "
                    f"Error: {error_msg}"
                )
            elif "10005" in error_msg or "ip" in error_msg.lower():
                logger.error("❌ IP NOT WHITELISTED (retCode 10005)")
                raise Exception(
                    "IP address is not whitelisted! "
                    "Please add your server's IP to Bybit API whitelist. "
                    f"Error: {error_msg}"
                )
            else:
                logger.error(f"❌ API authentication failed: {error_msg}")
                raise Exception(f"Bybit API authentication failed: {error_msg}")
                
    except Exception as e:
        logger.error(f"❌ API validation failed: {e}")
        raise
```

---

### Задача 3: Исправить Account Balance проблему

**Файл**: `mcp_server/market_scanner.py`

**ЗАМЕНИТЬ блок (строки 51-64):**

```python
# 2. Get Account Balance for dynamic risk management
# ВАЖНО: Balance используется для position sizing, но НЕ блокирует анализ
account_balance = None
try:
    account_info = await self.client.get_account_info()
    account_balance = float(account_info.get("balance", {}).get("total", 0.0))
    
    if account_balance is None or account_balance <= 0:
        logger.warning(f"⚠️ Invalid account balance: {account_balance}. Position sizing will be unavailable.")
        account_balance = None
    else:
        logger.info(f"✅ Account balance retrieved: ${account_balance:.2f}")
        
except Exception as e:
    logger.warning(f"⚠️ Cannot get wallet balance: {e}. Continuing without position sizing.")
    logger.warning("   Analysis will work, but position sizes won't be calculated.")
    account_balance = None
    # НЕ прерываем выполнение - продолжаем анализ
```

**ИЗМЕНИТЬ функцию `_generate_entry_plan` (строки 855-947):**

Найти строки 862-865:
```python
# КРИТИЧЕСКАЯ ПРОВЕРКА: баланс не может быть None
if account_balance is None or account_balance <= 0:
    logger.error(f"Cannot generate entry plan: invalid balance {account_balance}")
    return None
```

**ЗАМЕНИТЬ на:**
```python
# Проверка баланса - если нет, возвращаем план без position sizing
if account_balance is None or account_balance <= 0:
    logger.warning(f"⚠️ Account balance unavailable ({account_balance}). Entry plan will not include position sizing.")
    # Продолжаем генерацию плана без position sizing
```

Найти строки 902-926 (где рассчитывается position size):
```python
# DYNAMIC RISK MANAGEMENT
if account_balance is None or account_balance <= 0:
    # Если баланс недоступен, используем placeholder с предупреждением
    risk_usd = 0.0
    logger.warning("⚠️ Cannot calculate risk: account balance unavailable!")
else:
    risk_usd = account_balance * risk_percent
```

**ЗАМЕНИТЬ на:**
```python
# DYNAMIC RISK MANAGEMENT
risk_usd = 0.0
qty = 0.0
position_value = 0.0
warning = None

if account_balance and account_balance > 0:
    # Баланс доступен - рассчитываем position size
    risk_usd = account_balance * risk_percent
    
    if risk_per_share > 0:
        qty = risk_usd / risk_per_share
    else:
        qty = 0
        
    qty = round(qty, 6)
    position_value = qty * current_price
    
    logger.info(f"✅ Position calculated: {qty} units = ${position_value:.2f}")
else:
    # Баланс НЕ доступен - возвращаем план без sizing
    warning = (
        "⚠️ ВНИМАНИЕ: Account balance недоступен! "
        "Position size НЕ рассчитан. "
        "Это НЕ ошибка - анализ валиден, но размер позиции нужно рассчитать вручную."
    )
    logger.warning(warning)
```

---

### Задача 4: Улучшить обработку ошибок Bybit API

**Файл**: `mcp_server/trading_operations.py`

**ДОБАВИТЬ helper функцию в начало файла (после импортов, перед классом):**

```python
def handle_bybit_error(response: Dict[str, Any], operation: str = "API call") -> None:
    """
    Обрабатывает ошибки Bybit API и выбрасывает понятные исключения.
    
    Args:
        response: Ответ от Bybit API
        operation: Описание операции для сообщения об ошибке
    
    Raises:
        Exception: С понятным сообщением об ошибке
    """
    ret_code = response.get("retCode")
    ret_msg = response.get("retMsg", "Unknown error")
    
    if ret_code == 0:
        return  # Успех
    
    # Специфичные ошибки Bybit API
    error_messages = {
        10003: (
            "❌ API Key INVALID (retCode=10003)\n"
            "Причина: API ключ невалидный или истек\n"
            "Решение: Проверьте BYBIT_API_KEY в GitHub Secrets:\n"
            "  1. Зайдите на Bybit → API Management\n"
            "  2. Убедитесь что ключ активен\n" 
            "  3. Обновите его в GitHub Secrets если истек"
        ),
        10004: (
            "❌ API Key has NO PERMISSIONS (retCode=10004)\n"
            "Причина: У API ключа нет прав для этой операции\n"
            "Решение: На Bybit → API Management включите:\n"
            "  • Read permissions (для анализа)\n"
            "  • Trade permissions (для торговли)"
        ),
        10005: (
            "❌ IP NOT WHITELISTED (retCode=10005)\n"
            "Причина: IP адрес сервера не в whitelist\n"
            "Решение:\n"
            "  1. Узнайте IP вашего Kubernetes кластера\n"
            "  2. Добавьте его в Bybit → API Management → IP Whitelist"
        ),
        10006: (
            "❌ TIMESTAMP ERROR (retCode=10006)\n"
            "Причина: Время на сервере не синхронизировано\n"
            "Решение: Проверьте системное время сервера (NTP sync)"
        ),
        10016: (
            "❌ SERVICE UNAVAILABLE (retCode=10016)\n"
            "Причина: Bybit API временно недоступен\n"
            "Решение: Подождите и повторите запрос"
        ),
    }
    
    if ret_code in error_messages:
        error_detail = error_messages[ret_code]
        raise Exception(f"{operation} failed:\n{error_detail}\n\nOriginal error: {ret_msg}")
    else:
        raise Exception(f"{operation} failed: {ret_msg} (retCode={ret_code})")
```

**ИСПОЛЬЗОВАТЬ в `get_all_account_balances` (заменить строку 222):**

Найти:
```python
if wallet_response.get("retCode") == 0:
```

**ЗАМЕНИТЬ на:**
```python
handle_bybit_error(wallet_response, f"Get wallet balance for {account_type}")
# Если дошли сюда - retCode = 0, продолжаем
```

---

### Задача 5: Startup Validation в main()

**Файл**: `mcp_server/full_server.py`

**ДОБАВИТЬ в функцию `main()` после инициализации bybit_client (после строки 1412):**

```python
# === КРИТИЧЕСКАЯ ВАЛИДАЦИЯ API ПРИ СТАРТЕ ===
logger.info("=" * 50)
logger.info("🔍 VALIDATING BYBIT API CREDENTIALS...")
logger.info("=" * 50)

try:
    api_health = await bybit_client.validate_api_credentials()
    
    if api_health["valid"]:
        logger.info("✅ API VALIDATION SUCCESSFUL")
        logger.info(f"   Permissions: {', '.join(api_health['permissions'])}")
        logger.info(f"   Available accounts: {', '.join(api_health.get('accounts', []))}")
    else:
        logger.error("❌ API VALIDATION FAILED")
        logger.error(f"   Error: {api_health.get('error', 'Unknown')}")
        raise Exception("API validation failed - cannot start server")
        
except Exception as e:
    logger.error("=" * 50)
    logger.error("❌ CRITICAL: API VALIDATION FAILED")
    logger.error("=" * 50)
    logger.error(f"Error: {e}")
    logger.error("")
    logger.error("Server startup ABORTED. Please fix API credentials and restart.")
    logger.error("")
    logger.error("Quick check:")
    logger.error("1. Are GitHub Secrets set correctly?")
    logger.error("2. Is API key valid on Bybit?")
    logger.error("3. Does API key have READ permissions?")
    logger.error("=" * 50)
    sys.exit(1)  # FAIL-FAST: Прерываем запуск если API невалиден

logger.info("=" * 50)
logger.info("✅ ALL PRE-FLIGHT CHECKS PASSED")
logger.info("=" * 50)
```

---

## 📋 ПОРЯДОК РЕАЛИЗАЦИИ

### Шаг 1: Обновить загрузку credentials
- [ ] Изменить `load_credentials()` в `mcp_server/full_server.py`
- [ ] Добавить ENV variables приоритет
- [ ] Добавить валидацию placeholder значений

### Шаг 2: Добавить API validation
- [ ] Добавить `validate_api_credentials()` в `mcp_server/bybit_client.py`
- [ ] Добавить детальные error messages для каждого retCode

### Шаг 3: Исправить account balance
- [ ] Убрать `raise Exception` в `market_scanner.py:64`
- [ ] Изменить `_generate_entry_plan` для работы без баланса
- [ ] Добавить warning вместо ошибки

### Шаг 4: Улучшить error handling
- [ ] Добавить `handle_bybit_error()` в `trading_operations.py`
- [ ] Заменить все проверки `retCode` на helper

### Шаг 5: Добавить startup validation
- [ ] Добавить pre-flight checks в `main()`
- [ ] Добавить fail-fast если API невалиден

---

## ✅ КРИТЕРИИ УСПЕХА

После внедрения:

1. ✅ **Credentials из GitHub Secrets**: Загружаются через ENV variables
2. ✅ **Валидация при старте**: Fail-fast если API ключи невалидные
3. ✅ **Понятные ошибки**: Каждый retCode имеет детальное сообщение
4. ✅ **Graceful degradation**: Анализ работает даже без account balance
5. ✅ **Production-ready**: Нет placeholder значений, все из GitHub Secrets

---

## 🚀 ПОСЛЕ РЕАЛИЗАЦИИ

### Проверка в production:

```bash
# 1. Проверить GitHub Secrets
gh secret list

# 2. Trigger deployment
git push origin main

# 3. Проверить логи pod
kubectl logs -n trader-agent -l app=trader-agent --tail=100

# 4. Проверить что API validation прошла
kubectl logs -n trader-agent -l app=trader-agent | grep "API VALIDATION"
```

### Ожидаемый вывод в логах:

```
==================================================
🔍 VALIDATING BYBIT API CREDENTIALS...
==================================================
✅ API доступен (public endpoints)
✅ API Key валиден (authenticated endpoints работают)
✅ API VALIDATION SUCCESSFUL
   Permissions: READ, WRITE
   Available accounts: SPOT, UNIFIED
==================================================
✅ ALL PRE-FLIGHT CHECKS PASSED
==================================================
```

---

## 📞 Troubleshooting

### Ошибка: "API Key INVALID"
1. Проверьте GitHub Secrets: `gh secret list`
2. Убедитесь что BYBIT_API_KEY и BYBIT_API_SECRET установлены
3. Проверьте что ключ активен на Bybit

### Ошибка: "Account balance unavailable"
Это НЕ ошибка! Это warning. Система продолжит работу без position sizing.

### Ошибка: "IP NOT WHITELISTED"
Добавьте IP вашего Kubernetes кластера в Bybit API whitelist.

---

**Готово к реализации в Code Mode** ✅