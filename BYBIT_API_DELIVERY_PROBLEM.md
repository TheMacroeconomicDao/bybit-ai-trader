# 🔴 ПРОБЛЕМА: Доставка Bybit API ключей из GitHub Secrets в Kubernetes

## 📋 ТЕКУЩАЯ СИТУАЦИЯ

**Проблема:** API ключи есть в GitHub Secrets и системных переменных, но при вызове authenticated endpoints получаем ошибку:
```
retCode 10003: API key is invalid
```

**Что работает:**
- ✅ Public endpoints работают (`get_market_overview`, `get_ticker`)
- ✅ Ключи загружаются из ENV variables (логи показывают "Found credentials in ENVIRONMENT VARIABLES")
- ✅ Валидация формата ключей проходит (длина, не placeholder)
- ✅ `get_account_info` возвращает данные (хотя балансы 0)

**Что НЕ работает:**
- ❌ `analyze_asset` - ошибка `retCode 10003: API key is invalid`
- ❌ `find_oversold_assets` - ошибка при получении баланса
- ❌ `get_asset_price` - ошибка `"'\"retCode\"'"` (KeyError при парсинге)

---

## 🔍 ЧТО УЖЕ СДЕЛАНО

### 1. Исправлена загрузка credentials (`mcp_server/full_server.py:71-145`)
- ✅ Приоритет ENV variables над файлом
- ✅ Добавлен `.strip()` для удаления пробелов/переносов строк
- ✅ Детальное логирование длины ключей
- ✅ Проверка на пробелы внутри ключей

### 2. Добавлена валидация при старте (`mcp_server/full_server.py:1510-1541`)
- ✅ Вызов `bybit_client.validate_api_credentials()`
- ✅ Fail-fast если API невалиден
- ✅ Детальные сообщения об ошибках

### 3. Kubernetes конфигурация (`k8s/cronjob.yaml`)
- ✅ Secrets создаются из GitHub Secrets
- ✅ Environment variables передаются в pod
- ✅ Правильные имена переменных: `BYBIT_API_KEY`, `BYBIT_API_SECRET`

---

## 🎯 ВОЗМОЖНЫЕ ПРИЧИНЫ ПРОБЛЕМЫ

### 1. **Пробелы/переносы строк в GitHub Secrets**
**Симптомы:**
- Ключи загружаются, но содержат невидимые символы
- Логи показывают правильную длину, но API отклоняет

**Проверка:**
```bash
# В Kubernetes pod
kubectl exec -n trader-agent <pod-name> -- printenv | grep BYBIT
# Проверить есть ли пробелы/переносы

# В GitHub Secrets
# Убедиться что при копировании не добавились пробелы
```

**Решение:**
- ✅ Уже добавлен `.strip()` в `load_credentials()`
- ⚠️ НО: нужно проверить что ключи действительно чистые

### 2. **Разные ключи в разных местах**
**Симптомы:**
- Ключи в GitHub Secrets ≠ ключи в локальном `credentials.json`
- Ключи в Kubernetes Secrets ≠ ключи в ENV pod

**Проверка:**
```bash
# 1. Проверить GitHub Secrets
gh secret list

# 2. Проверить Kubernetes Secrets
kubectl get secret trader-agent-secrets -n trader-agent -o jsonpath='{.data.BYBIT_API_KEY}' | base64 -d
kubectl get secret trader-agent-secrets -n trader-agent -o jsonpath='{.data.BYBIT_API_SECRET}' | base64 -d

# 3. Проверить ENV в pod
kubectl exec -n trader-agent <pod-name> -- printenv | grep BYBIT

# 4. Сравнить все три источника
```

### 3. **Проблема с CCXT библиотекой**
**Симптомы:**
- Ключи правильные, но CCXT неправильно их передает
- Ошибка `retCode 10003` только для authenticated endpoints

**Проверка:**
- Посмотреть как CCXT формирует запросы
- Проверить что `apiKey` и `secret` правильно передаются в `ccxt.bybit()`

**Файлы для проверки:**
- `mcp_server/bybit_client.py:48-61` - инициализация CCXT
- `mcp_server/bybit_client.py:68-143` - валидация API

### 4. **Проблема с форматом ключей**
**Симптомы:**
- Ключи загружаются, но имеют неправильный формат
- Bybit API отклоняет даже валидные ключи

**Проверка:**
```python
# Добавить в load_credentials() после strip():
logger.info(f"API Key first 10 chars: {repr(bybit_api_key[:10])}")
logger.info(f"API Key last 10 chars: {repr(bybit_api_key[-10:])}")
logger.info(f"API Key contains whitespace: {bool(set(bybit_api_key) & set([' ', '\n', '\r', '\t']))}")
```

### 5. **Проблема с testnet/mainnet режимом**
**Симптомы:**
- Ключи для mainnet, но используется testnet (или наоборот)
- `BYBIT_TESTNET` переменная неправильно установлена

**Проверка:**
```bash
# В Kubernetes
kubectl exec -n trader-agent <pod-name> -- printenv | grep BYBIT_TESTNET

# В логах должно быть:
# Mode: 🚀 MAINNET  или  Mode: 🧪 TESTNET
```

---

## 🔧 ЧТО НУЖНО СДЕЛАТЬ

### Шаг 1: Проверить ключи в Kubernetes
```bash
# 1. Получить имя pod
kubectl get pods -n trader-agent

# 2. Проверить ENV variables
kubectl exec -n trader-agent <pod-name> -- printenv | grep BYBIT

# 3. Проверить Secrets
kubectl get secret trader-agent-secrets -n trader-agent -o yaml

# 4. Декодировать и проверить содержимое
kubectl get secret trader-agent-secrets -n trader-agent -o jsonpath='{.data.BYBIT_API_KEY}' | base64 -d | od -c
kubectl get secret trader-agent-secrets -n trader-agent -o jsonpath='{.data.BYBIT_API_SECRET}' | base64 -d | od -c
```

### Шаг 2: Добавить детальное логирование
В `mcp_server/full_server.py` в функции `load_credentials()` после `.strip()`:

```python
# После strip(), перед return
logger.info(f"🔍 DEBUG: API Key details:")
logger.info(f"   Raw length: {len(bybit_api_key_raw) if bybit_api_key_raw else 0}")
logger.info(f"   Stripped length: {len(bybit_api_key)}")
logger.info(f"   First 15 chars: {repr(bybit_api_key[:15])}")
logger.info(f"   Last 15 chars: {repr(bybit_api_key[-15:])}")
logger.info(f"   Contains whitespace: {' ' in bybit_api_key or '\n' in bybit_api_key}")
logger.info(f"   Is ASCII: {bybit_api_key.isascii()}")
```

### Шаг 3: Проверить передачу в CCXT
В `mcp_server/bybit_client.py:48-61` добавить логирование:

```python
# После создания exchange
logger.info(f"🔍 DEBUG: CCXT initialization:")
logger.info(f"   apiKey length: {len(api_key)}")
logger.info(f"   secret length: {len(api_secret)}")
logger.info(f"   apiKey first 8: {api_key[:8]}...")
logger.info(f"   testnet: {testnet}")
```

### Шаг 4: Проверить валидацию API
В `mcp_server/bybit_client.py:68-143` метод `validate_api_credentials()` должен:
1. ✅ Тестировать public endpoint (работает)
2. ❌ Тестировать authenticated endpoint (падает с 10003)

**Добавить логирование:**
```python
# В validate_api_credentials() перед fetch_balance()
logger.info(f"🔍 DEBUG: Testing authenticated endpoint with:")
logger.info(f"   API Key: {self.api_key[:8]}...{self.api_key[-4:]}")
logger.info(f"   API Key length: {len(self.api_key)}")
logger.info(f"   Secret length: {len(self.api_secret)}")
logger.info(f"   Testnet: {self.testnet}")
```

### Шаг 5: Сравнить с рабочим ключом
Если есть рабочий ключ в `credentials.json`:
1. Сравнить формат с ключом из ENV
2. Проверить что оба ключа одинаковой длины
3. Убедиться что оба без пробелов

---

## 🚨 КРИТИЧЕСКИЕ ВОПРОСЫ ДЛЯ ПРОВЕРКИ

1. **Ключи в GitHub Secrets правильные?**
   - Проверить на Bybit → API Management
   - Убедиться что ключ активен и не истек
   - Проверить что есть READ permissions

2. **Ключи правильно передаются в Kubernetes?**
   - GitHub Secrets → Kubernetes Secrets → Pod ENV
   - Нет ли потери данных при передаче?

3. **Ключи правильно передаются в CCXT?**
   - Проверить что `apiKey` и `secret` в CCXT совпадают с ENV
   - Нет ли преобразований/кодировок?

4. **Правильный режим (testnet/mainnet)?**
   - Ключи для mainnet, но используется testnet?
   - `BYBIT_TESTNET` правильно установлен?

5. **IP whitelist настроен?**
   - Если требуется IP whitelist на Bybit
   - IP сервера добавлен в whitelist?

---

## 📝 ФАЙЛЫ ДЛЯ ПРОВЕРКИ

1. **`mcp_server/full_server.py`**
   - Строки 71-145: `load_credentials()` - загрузка ключей
   - Строки 1498-1508: Инициализация клиентов
   - Строки 1510-1541: Валидация API

2. **`mcp_server/bybit_client.py`**
   - Строки 34-66: `__init__()` - инициализация CCXT
   - Строки 68-143: `validate_api_credentials()` - валидация

3. **`k8s/cronjob.yaml`**
   - Строки 23-44: Environment variables из Secrets

4. **`.github/workflows/deploy.yml`**
   - Создание Kubernetes Secrets из GitHub Secrets

---

## ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

После исправления:
1. ✅ Логи показывают: `✅ API VALIDATION SUCCESSFUL`
2. ✅ `analyze_asset` работает без ошибок
3. ✅ `find_oversold_assets` работает без ошибок
4. ✅ Все authenticated endpoints работают

---

## 🔍 ДИАГНОСТИЧЕСКИЕ КОМАНДЫ

```bash
# 1. Проверить что сервер запустился с правильными ключами
kubectl logs -n trader-agent <pod-name> | grep "Loading Bybit credentials"

# 2. Проверить валидацию API
kubectl logs -n trader-agent <pod-name> | grep "API VALIDATION"

# 3. Проверить ошибки
kubectl logs -n trader-agent <pod-name> | grep "retCode 10003"

# 4. Проверить ENV в запущенном pod
kubectl exec -n trader-agent <pod-name> -- env | grep BYBIT

# 5. Тест API ключа вручную (если есть доступ к Python в pod)
kubectl exec -n trader-agent <pod-name> -- python3 -c "
import os
key = os.getenv('BYBIT_API_KEY', '')
secret = os.getenv('BYBIT_API_SECRET', '')
print(f'Key length: {len(key)}')
print(f'Secret length: {len(secret)}')
print(f'Key first 10: {repr(key[:10])}')
print(f'Key last 10: {repr(key[-10:])}')
"
```

---

**Версия:** 1.0  
**Приоритет:** КРИТИЧЕСКИЙ  
**Статус:** В РАБОТЕ  
**Последнее обновление:** 2025-11-20

