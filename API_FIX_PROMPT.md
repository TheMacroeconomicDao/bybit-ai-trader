# 🔧 ПРОМПТ: Исправление проблем с Bybit API и Account Balance

## 🎯 ЦЕЛЬ

Исправить критические проблемы с Bybit API, которые блокируют работу всех функций анализа рынка:
- `retCode 10003: API key is invalid`
- `Unable to get account balance`
- Функции падают полностью вместо graceful degradation

---

## 📋 КОНТЕКСТ ПРОБЛЕМЫ

### Текущие ошибки:

1. **API Key Invalid (retCode 10003)**
   ```
   bybit {"retCode":10003,"retMsg":"API key is invalid.","result":{},"retExtInfo":{},"time":1763656379796}
   ```

2. **Account Balance Errors**
   ```
   Market scan aborted: Unable to get account balance. Error: '"retCode"'
   ```

3. **Функции, которые падают:**
   - ❌ `find_oversold_assets` - требует account balance
   - ❌ `find_overbought_assets` - требует account balance
   - ❌ `find_breakout_opportunities` - требует account balance
   - ❌ `find_trend_reversals` - требует account balance
   - ❌ `scan_market` - требует account balance
   - ❌ `analyze_asset` - требует API для CVD analysis
   - ❌ `get_btc_correlation` - требует API

### Корневая причина:

1. **Невалидный API ключ** - основной API ключ не настроен или истек
2. **Нет graceful degradation** - функции полностью падают вместо работы в read-only режиме
3. **Жесткая зависимость от account balance** - даже для read-only анализа рынка

---

## 🔍 ЗАДАЧИ ДЛЯ ВЫПОЛНЕНИЯ

### 1. ПРОВЕРИТЬ И ИСПРАВИТЬ API КЛЮЧИ

**Файлы для проверки:**
- `mcp_server/bybit_client.py` - инициализация клиента
- `mcp_server/trading_operations.py` - использование API
- `.env` файл - переменные окружения
- `config/` - конфигурационные файлы

**Что проверить:**
- [ ] API ключ и секрет правильно загружаются из переменных окружения
- [ ] API ключ имеет правильные permissions (read для анализа, write для торговли)
- [ ] API ключ не истек
- [ ] Правильный accountType используется (SPOT/UNIFIED/CONTRACT)
- [ ] Testnet vs Mainnet настройки

**Действия:**
1. Найти где загружаются API ключи
2. Проверить формат и валидность
3. Добавить валидацию API ключей при инициализации
4. Добавить понятные ошибки если ключи невалидны

---

### 2. ДОБАВИТЬ GRACEFUL DEGRADATION

**Проблема:** Функции анализа рынка требуют account balance, но должны работать в read-only режиме даже без него.

**Файлы для изменения:**
- `mcp_server/market_scanner.py` - функции сканирования рынка
- `mcp_server/bybit_client.py` - клиент API
- `mcp_server/trading_operations.py` - торговые операции

**Что изменить:**

#### 2.1. Market Scanner (`market_scanner.py`)

**Текущий код (строки 51-64):**
```python
# 2. Get Account Balance for dynamic risk management
try:
    account_info = await self.client.get_account_info()
    account_balance = float(account_info.get("balance", {}).get("total", 0.0))
    
    if account_balance is None or account_balance <= 0:
        raise Exception(f"CRITICAL: Invalid account balance: {account_balance}. Cannot proceed with trading!")
    
    logger.info(f"✅ Account balance retrieved: ${account_balance:.2f}")
except Exception as e:
    logger.error(f"CRITICAL: Cannot get valid wallet balance: {e}")
    raise Exception(f"Market scan aborted: Unable to get account balance. Error: {e}")
```

**Исправленный код:**
```python
# 2. Get Account Balance for dynamic risk management
# ВАЖНО: Работаем в read-only режиме если баланс недоступен
account_balance = None
try:
    account_info = await self.client.get_account_info()
    account_balance = float(account_info.get("balance", {}).get("total", 0.0))
    
    if account_balance is None or account_balance <= 0:
        logger.warning(f"⚠️ Invalid account balance: {account_balance}. Continuing in read-only mode.")
        account_balance = None
    else:
        logger.info(f"✅ Account balance retrieved: ${account_balance:.2f}")
except Exception as e:
    logger.warning(f"⚠️ Cannot get wallet balance: {e}. Continuing in read-only mode (analysis only, no position sizing).")
    account_balance = None
    # НЕ ПРЕРЫВАЕМ выполнение - продолжаем анализ без расчета позиций
```

**Изменения в `_generate_entry_plan`:**
```python
def _generate_entry_plan(self, analysis: Dict, ticker: Dict, account_balance: Optional[float] = None, risk_percent: float = 0.02) -> Dict[str, Any]:
    """
    Генерирует план входа
    
    ВАЖНО: account_balance может быть None - в этом случае не рассчитываем position size
    """
    
    entry_plan = {
        "entry_price": ...,
        "stop_loss": ...,
        "take_profit": ...,
        "risk_reward": ...,
    }
    
    # Position size calculation - только если баланс доступен
    if account_balance is not None and account_balance > 0:
        risk_usd = account_balance * risk_percent
        # ... расчет позиции ...
        entry_plan["position_size"] = calculated_size
        entry_plan["risk_usd"] = risk_usd
    else:
        # Read-only режим - не рассчитываем позицию
        entry_plan["position_size"] = None
        entry_plan["risk_usd"] = None
        entry_plan["warning"] = "⚠️ Account balance unavailable. Analysis provided without position sizing. User must verify balance before trading."
    
    return entry_plan
```

---

#### 2.2. Bybit Client (`bybit_client.py`)

**Добавить метод для проверки API доступности:**
```python
async def check_api_health(self) -> Dict[str, Any]:
    """
    Проверяет доступность API и валидность ключей
    
    Returns:
        {
            "available": bool,
            "read_only": bool,  # True если только read доступен
            "error": Optional[str],
            "account_types": List[str]  # Доступные типы счетов
        }
    """
    try:
        # Пробуем простой read-only запрос (например, get_ticker)
        test_ticker = await self.exchange.fetch_ticker('BTC/USDT')
        
        # Пробуем получить баланс
        try:
            balance = await self.exchange.fetch_balance()
            return {
                "available": True,
                "read_only": False,
                "error": None,
                "account_types": list(balance.keys())
            }
        except Exception as e:
            # API доступен, но баланс недоступен (read-only режим)
            return {
                "available": True,
                "read_only": True,
                "error": str(e),
                "account_types": []
            }
    except Exception as e:
        # API полностью недоступен
        return {
            "available": False,
            "read_only": False,
            "error": str(e),
            "account_types": []
        }
```

---

#### 2.3. Trading Operations (`trading_operations.py`)

**Исправить `get_all_account_balances` для graceful degradation:**
```python
def get_all_account_balances(
    session: HTTP, 
    coin: Optional[str] = None,
    use_cache: bool = True,
    cache: Optional[BalanceCache] = None,
    allow_partial: bool = True  # НОВЫЙ ПАРАМЕТР
) -> Dict[str, Any]:
    """
    Получить балансы со всех счетов
    
    Args:
        allow_partial: Если True, возвращает частичные данные даже при ошибках
    
    Returns:
        {
            "success": bool,
            "balances": {...},
            "errors": {...},  # Ошибки по типам счетов
            "read_only": bool  # True если только read доступен
        }
    """
    balances = {}
    errors = {}
    read_only = False
    
    account_types = ["SPOT", "CONTRACT", "UNIFIED"]
    
    for account_type in account_types:
        try:
            # ... существующий код получения баланса ...
            balances[account_type] = balance_data
        except Exception as e:
            error_msg = str(e)
            errors[account_type] = error_msg
            
            # Проверяем если это проблема с API ключом
            if "10003" in error_msg or "invalid" in error_msg.lower():
                read_only = True
                logger.warning(f"⚠️ API key issue for {account_type}: {error_msg}")
            
            if not allow_partial:
                raise
    
    return {
        "success": len(balances) > 0,
        "balances": balances,
        "errors": errors,
        "read_only": read_only
    }
```

---

### 3. ИСПРАВИТЬ ОБРАБОТКУ ОШИБОК

**Проблема:** Ошибки API не обрабатываются правильно, функции падают с неясными сообщениями.

**Что исправить:**

#### 3.1. Улучшить обработку retCode ошибок

**В `trading_operations.py` добавить helper функцию:**
```python
def handle_bybit_error(response: Dict[str, Any], operation: str = "API call") -> None:
    """
    Обрабатывает ошибки Bybit API и выбрасывает понятные исключения
    
    Args:
        response: Ответ от Bybit API
        operation: Описание операции для сообщения об ошибке
    """
    ret_code = response.get("retCode")
    ret_msg = response.get("retMsg", "Unknown error")
    
    if ret_code == 0:
        return  # Успех
    
    # Специфичные ошибки
    error_messages = {
        10003: "API key is invalid. Please check your API credentials in .env file.",
        10004: "API key has no permission. Please check API key permissions on Bybit.",
        10005: "IP address is not whitelisted. Please add your IP to Bybit API whitelist.",
        10006: "Timestamp error. Please check system time synchronization.",
        10016: "Service unavailable. Please try again later.",
    }
    
    if ret_code in error_messages:
        raise Exception(f"{operation} failed: {error_messages[ret_code]} (retCode={ret_code})")
    else:
        raise Exception(f"{operation} failed: {ret_msg} (retCode={ret_code})")
```

#### 3.2. Использовать helper во всех местах

**Найти все места где проверяется `retCode` и заменить на:**
```python
# БЫЛО:
if response.get("retCode") != 0:
    raise Exception(f"Error: {response.get('retMsg')}")

# СТАЛО:
handle_bybit_error(response, operation="Get wallet balance")
```

---

### 4. ДОБАВИТЬ FALLBACK ДЛЯ АНАЛИЗА РЫНКА

**Проблема:** Функции анализа требуют account balance даже для read-only анализа.

**Решение:** Разделить анализ на два режима:

1. **Full Mode** (с account balance) - полный анализ с расчетом позиций
2. **Read-Only Mode** (без account balance) - анализ рынка без расчета позиций

**Изменить функции:**

#### 4.1. `find_oversold_assets`
```python
async def find_oversold_assets(
    self,
    market_type: str = "spot",
    min_volume_24h: float = 1000000
) -> Dict[str, Any]:
    """
    Найти перепроданные активы
    
    ВАЖНО: Работает в read-only режиме если account balance недоступен
    """
    try:
        # Пробуем получить баланс (не обязательно)
        account_balance = None
        try:
            account_info = await self.client.get_account_info()
            account_balance = float(account_info.get("balance", {}).get("total", 0.0))
        except:
            logger.warning("⚠️ Account balance unavailable. Continuing in read-only mode.")
        
        # Получаем тикеры (read-only операция)
        all_tickers = await self.client.get_all_tickers(market_type=market_type)
        
        # Фильтруем по RSI < 30
        oversold = []
        for ticker in all_tickers:
            # ... анализ RSI ...
            if rsi < 30 and volume_24h >= min_volume_24h:
                asset_data = {
                    "symbol": symbol,
                    "price": price,
                    "rsi": rsi,
                    "change_24h": change_24h,
                    "volume_24h": volume_24h,
                }
                
                # Добавляем entry plan только если баланс доступен
                if account_balance:
                    asset_data["entry_plan"] = self._generate_entry_plan(...)
                else:
                    asset_data["entry_plan"] = None
                    asset_data["warning"] = "Account balance unavailable. Entry plan not calculated."
                
                oversold.append(asset_data)
        
        return {
            "success": True,
            "assets": oversold,
            "read_only": account_balance is None,
            "count": len(oversold)
        }
    except Exception as e:
        logger.error(f"Error finding oversold assets: {e}")
        return {
            "success": False,
            "error": str(e),
            "assets": [],
            "read_only": True
        }
```

#### 4.2. Применить то же самое для:
- `find_overbought_assets`
- `find_breakout_opportunities`
- `find_trend_reversals`
- `scan_market`

---

### 5. ИСПРАВИТЬ CVD ANALYSIS

**Проблема:** `analyze_asset` падает из-за ошибки CVD analysis.

**Файл:** `mcp_server/market_scanner.py` или где реализован CVD

**Исправление:**
```python
async def _get_cvd_analysis(self, symbol: str) -> Dict[str, Any]:
    """
    Получить CVD (Cumulative Volume Delta) анализ
    
    ВАЖНО: Graceful degradation если API недоступен
    """
    try:
        # ... существующий код CVD ...
        return cvd_data
    except Exception as e:
        error_msg = str(e)
        
        # Проверяем если это проблема с API
        if "10003" in error_msg or "invalid" in error_msg.lower():
            logger.warning(f"⚠️ CVD analysis unavailable (API issue): {error_msg}")
            return {
                "signal": "UNAVAILABLE",
                "error": "API key issue - CVD analysis requires valid API credentials",
                "read_only": True
            }
        else:
            logger.warning(f"⚠️ CVD analysis failed: {error_msg}")
            return {
                "signal": "ERROR",
                "error": error_msg,
                "read_only": False
            }
```

---

### 6. ДОБАВИТЬ ВАЛИДАЦИЮ ПРИ СТАРТЕ

**Создать функцию проверки системы:**
```python
async def validate_system_health(client: BybitClient) -> Dict[str, Any]:
    """
    Проверяет здоровье системы и доступность API
    
    Returns:
        {
            "api_available": bool,
            "read_only": bool,
            "account_balance_available": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    health = {
        "api_available": False,
        "read_only": False,
        "account_balance_available": False,
        "errors": [],
        "warnings": []
    }
    
    # 1. Проверка API доступности
    try:
        api_health = await client.check_api_health()
        health["api_available"] = api_health["available"]
        health["read_only"] = api_health["read_only"]
        
        if not api_health["available"]:
            health["errors"].append(f"API unavailable: {api_health['error']}")
        elif api_health["read_only"]:
            health["warnings"].append("API available in read-only mode. Trading functions will be limited.")
    except Exception as e:
        health["errors"].append(f"API health check failed: {e}")
    
    # 2. Проверка account balance
    try:
        account_info = await client.get_account_info()
        balance = float(account_info.get("balance", {}).get("total", 0.0))
        if balance > 0:
            health["account_balance_available"] = True
        else:
            health["warnings"].append("Account balance is 0 or unavailable")
    except Exception as e:
        health["warnings"].append(f"Account balance check failed: {e}")
    
    return health
```

---

## 📝 ПЛАН ВЫПОЛНЕНИЯ

### Шаг 1: Диагностика
1. Проверить где загружаются API ключи
2. Проверить валидность API ключей
3. Проверить permissions API ключей на Bybit
4. Проверить логи ошибок

### Шаг 2: Исправление API ключей
1. Найти проблему с загрузкой/валидацией ключей
2. Исправить инициализацию клиента
3. Добавить валидацию при старте

### Шаг 3: Добавление Graceful Degradation
1. Изменить `market_scanner.py` - убрать жесткую зависимость от баланса
2. Изменить `bybit_client.py` - добавить read-only режим
3. Изменить `trading_operations.py` - улучшить обработку ошибок
4. Изменить все функции поиска - добавить fallback

### Шаг 4: Тестирование
1. Протестировать с валидным API ключом
2. Протестировать с невалидным API ключом (read-only режим)
3. Протестировать без API ключа (только публичные данные)
4. Проверить что анализ рынка работает во всех режимах

---

## ✅ КРИТЕРИИ УСПЕХА

После исправления:

1. ✅ **Анализ рынка работает** даже без валидного API ключа (read-only режим)
2. ✅ **Понятные ошибки** если API ключ невалидный
3. ✅ **Graceful degradation** - функции не падают, а работают в ограниченном режиме
4. ✅ **Position sizing** рассчитывается только если баланс доступен
5. ✅ **Логи показывают** режим работы (full/read-only)

---

## 🚨 ВАЖНЫЕ ЗАМЕЧАНИЯ

1. **Не удалять существующий функционал** - только добавлять fallback
2. **Сохранить обратную совместимость** - если баланс доступен, работает как раньше
3. **Понятные сообщения** - пользователь должен понимать в каком режиме работает система
4. **Логирование** - все режимы работы должны логироваться

---

## 📚 ФАЙЛЫ ДЛЯ ИЗМЕНЕНИЯ

1. `mcp_server/market_scanner.py` - убрать жесткую зависимость от баланса
2. `mcp_server/bybit_client.py` - добавить health check и read-only режим
3. `mcp_server/trading_operations.py` - улучшить обработку ошибок
4. `mcp_server/full_server.py` - добавить валидацию при старте

---

**Версия:** 1.0  
**Дата:** 2025-11-20  
**Приоритет:** КРИТИЧЕСКИЙ

