# 📚 Руководство по типам счетов Bybit

## 🎯 Обзор

Bybit поддерживает несколько типов счетов для разных видов торговли. Понимание различий между ними критично для правильной работы с API.

---

## 📋 Типы счетов

### 1. **SPOT** (Спот-счет)
- **Назначение:** Торговля спот-активами (покупка/продажа криптовалют)
- **Использование:** `category="spot"` в торговых операциях
- **accountType:** `"SPOT"` при запросе баланса
- **Особенности:**
  - Средства доступны сразу после покупки
  - Нет маржинальной торговли
  - Нет ливереджа

### 2. **CONTRACT** (Деривативный счет)
- **Назначение:** Торговля фьючерсами и перпетуалами
- **Использование:** `category="linear"` или `category="inverse"` в торговых операциях
- **accountType:** `"CONTRACT"` при запросе баланса
- **Особенности:**
  - Маржинальная торговля
  - Поддержка ливереджа
  - Отдельный баланс от спот-счета

### 3. **UNIFIED** (Объединенный счет / UTA)
- **Назначение:** Unified Trading Account - объединяет все типы торговли
- **Использование:** Может использоваться для всех категорий
- **accountType:** `"UNIFIED"` при запросе баланса
- **Особенности:**
  - Единый баланс для всех типов торговли
  - Более эффективное использование капитала
  - Поддержка Portfolio Margin Mode
  - Упрощенное управление средствами

---

## 🔗 Связь между category и accountType

### Правила соответствия:

| category | Рекомендуемый accountType | Альтернативный accountType |
|----------|---------------------------|----------------------------|
| `spot` | `SPOT` | `UNIFIED` (если включен UTA) |
| `linear` | `UNIFIED` (предпочтительно) или `CONTRACT` | `CONTRACT` (Classic Account) |
| `inverse` | `UNIFIED` (предпочтительно) или `CONTRACT` | `CONTRACT` (Classic Account) |

### Логика выбора:

1. **Для spot торговли:**
   - Сначала пробуем `SPOT` (Classic Account)
   - Если не найдено, пробуем `UNIFIED` (UTA режим)

2. **Для futures торговли (linear/inverse):**
   - Сначала пробуем `UNIFIED` (UTA режим - предпочтительно)
   - Если не найдено, пробуем `CONTRACT` (Classic Account)

3. **Универсальный подход:**
   - Проверяем все типы счетов последовательно
   - Используем первый успешный ответ

---

## 💾 Кэширование балансов

Для уменьшения количества API запросов реализовано кэширование балансов с TTL (Time To Live).

### BalanceCache

Класс для кэширования балансов с автоматическим истечением:

```python
from trading_operations import BalanceCache, get_balance_cache

# Получить глобальный экземпляр кэша
cache = get_balance_cache()

# Или создать свой экземпляр с кастомным TTL
cache = BalanceCache(ttl_seconds=60)  # 60 секунд

# Сохранить в кэш
cache.set("SPOT", {"total": 30.0, "available": 30.0, "success": True}, "USDT")

# Получить из кэша
data = cache.get("SPOT", "USDT")

# Инвалидировать кэш
cache.invalidate("SPOT", "USDT")  # Конкретная монета
cache.invalidate("SPOT")  # Все монеты для SPOT
cache.clear()  # Весь кэш
```

### Автоматическая инвалидация

Кэш автоматически инвалидируется после торговых операций:

- После `place_order()` - инвалидируется соответствующий accountType
- После `close_position()` - инвалидируется баланс закрытой монеты

### Ручная инвалидация

```python
from trading_operations import TradingOperations

trading_ops = TradingOperations(api_key="...", api_secret="...")

# Инвалидировать кэш после торговой операции
trading_ops.invalidate_balance_cache(account_type="SPOT", coin="USDT")
trading_ops.invalidate_balance_cache(account_type="SPOT")  # Все монеты
trading_ops.invalidate_balance_cache()  # Весь кэш
```

### Настройка TTL

По умолчанию TTL = 30 секунд. Это оптимально для:
- ✅ Уменьшения количества API запросов
- ✅ Актуальности данных баланса
- ✅ Производительности системы

Для изменения TTL создайте свой экземпляр кэша:

```python
from trading_operations import BalanceCache

# Кэш с TTL 60 секунд
cache = BalanceCache(ttl_seconds=60)
```

---

## 🛠️ Использование в коде

### Вспомогательные функции

#### `get_account_type_for_category(category, prefer_unified=True)`

Определяет правильный accountType для category.

```python
from trading_operations import get_account_type_for_category

# Для spot
account_type = get_account_type_for_category("spot", prefer_unified=False)
# Вернет: "SPOT"

account_type = get_account_type_for_category("spot", prefer_unified=True)
# Вернет: "UNIFIED"

# Для futures
account_type = get_account_type_for_category("linear", prefer_unified=True)
# Вернет: "UNIFIED"

account_type = get_account_type_for_category("linear", prefer_unified=False)
# Вернет: "CONTRACT"
```

#### `get_all_account_balances(session, coin=None, use_cache=True, cache=None)`

Получает балансы со всех типов счетов с поддержкой кэширования.

```python
from trading_operations import get_all_account_balances

# С кэшированием (по умолчанию)
balances = get_all_account_balances(trading_ops.session, coin="USDT")

# Без кэширования
balances = get_all_account_balances(trading_ops.session, coin="USDT", use_cache=False)

# С кастомным кэшем
from trading_operations import BalanceCache
custom_cache = BalanceCache(ttl_seconds=60)
balances = get_all_account_balances(
    trading_ops.session, 
    coin="USDT", 
    use_cache=True,
    cache=custom_cache
)

# Результат:
{
    "spot": {
        "total": 30.0,
        "available": 30.0,
        "success": True
    },
    "contract": {
        "total": 0.0,
        "available": 0.0,
        "success": False
    },
    "unified": {
        "total": 0.0,
        "available": 0.0,
        "success": False
    },
    "total": 30.0,      # Сумма всех счетов
    "available": 30.0   # Сумма доступных средств
}
```

---

## 📊 Примеры использования

### Пример 1: Получение баланса для spot торговли

```python
# Старый подход (только UNIFIED)
wallet_response = session.get_wallet_balance(accountType="UNIFIED")

# Новый подход (проверка всех типов)
from trading_operations import get_all_account_balances
all_balances = get_all_account_balances(session, coin="USDT")

# Используем баланс со SPOT счета
spot_balance = all_balances["spot"]["available"]
```

### Пример 2: Закрытие spot позиции

```python
# Код автоматически пробует SPOT, затем UNIFIED, затем CONTRACT
result = await trading_ops.close_position(
    symbol="BTCUSDT",
    category="spot",
    reason="Take profit"
)
```

### Пример 3: Получение информации об аккаунте

```python
# get_account_info теперь возвращает балансы всех типов счетов
account_info = await call_tool("get_account_info", {})

# Структура ответа:
{
    "balance": {
        "spot": {"total": 30.0, "available": 30.0, "success": True},
        "contract": {"total": 0.0, "available": 0.0, "success": False},
        "unified": {"total": 0.0, "available": 0.0, "success": False},
        "total": 30.0,
        "available": 30.0,
        "used_margin": 0.0,
        "unrealized_pnl": 0.0
    },
    "positions": [],
    "risk_metrics": {...}
}
```

---

## ⚠️ Важные замечания

### 1. Classic Account vs Unified Trading Account (UTA)

- **Classic Account:** Раздельные счета (SPOT и CONTRACT)
- **UTA:** Объединенный счет (UNIFIED для всех категорий)

### 2. Проверка баланса

**Всегда проверяйте все типы счетов**, если не уверены в типе аккаунта пользователя:

```python
# ❌ Плохо - только UNIFIED
wallet_response = session.get_wallet_balance(accountType="UNIFIED")

# ✅ Хорошо - проверка всех типов
all_balances = get_all_account_balances(session, coin="USDT")
```

### 3. Обработка ошибок

Если запрос к одному типу счета не удался, это не означает, что средства отсутствуют. Продолжайте проверку других типов:

```python
account_types = ["SPOT", "UNIFIED", "CONTRACT"]
for account_type in account_types:
    try:
        response = session.get_wallet_balance(accountType=account_type, coin="USDT")
        if response.get("retCode") == 0:
            # Нашли баланс!
            break
    except Exception as e:
        # Продолжаем проверку
        continue
```

### 4. Суммирование балансов

Если средства распределены между несколькими счетами, суммируйте их для получения общего баланса:

```python
total_balance = (
    balances["spot"]["total"] +
    balances["contract"]["total"] +
    balances["unified"]["total"]
)
```

---

## 🔍 Отладка

### Логирование

Все функции логируют попытки получения баланса:

```python
logger.info(f"Successfully retrieved balance from {account_type} account")
logger.debug(f"Failed to get balance from {account_type}: {e}")
```

### Проверка успешности

Используйте поле `success` в результатах:

```python
if balances["spot"]["success"]:
    print(f"SPOT balance: {balances['spot']['available']}")
else:
    print("SPOT account not available or empty")
```

---

## 📝 Чеклист для разработчиков

При работе с балансами Bybit:

- [ ] Используйте `get_all_account_balances()` для получения полной информации
- [ ] Проверяйте все типы счетов (SPOT, CONTRACT, UNIFIED)
- [ ] Используйте `get_account_type_for_category()` для определения правильного типа
- [ ] Обрабатывайте случаи, когда счет не существует или пуст
- [ ] Логируйте все попытки получения баланса
- [ ] Суммируйте балансы, если средства распределены между счетами
- [ ] Предоставляйте детальную информацию пользователю о балансах по типам счетов
- [ ] Используйте кэширование для уменьшения количества API запросов
- [ ] Инвалидируйте кэш после торговых операций
- [ ] Настраивайте TTL кэша в зависимости от требований к актуальности данных

---

## 🚀 Миграция с старого кода

### Было:
```python
# Только UNIFIED
wallet_response = session.get_wallet_balance(accountType="UNIFIED")
```

### Стало:
```python
# Проверка всех типов счетов
from trading_operations import get_all_account_balances
all_balances = get_all_account_balances(session, coin="USDT")
```

---

## 📚 Дополнительные ресурсы

- [Bybit API v5 Documentation](https://bybit-exchange.github.io/docs/v5/)
- [Unified Trading Account Guide](https://www.bybit.com/en/help-center/article/Introduction-to-Bybit-Unified-Trading-Account/)
- [Account Types Comparison](https://bybit-exchange.github.io/docs/v5/acct-mode)

---

**Версия:** 1.0  
**Последнее обновление:** 2024  
**Автор:** AI Trading Agent Team

