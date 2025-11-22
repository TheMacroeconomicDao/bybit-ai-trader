# 🔑 ПРОМПТ: Исправление загрузки Bybit API ключей для боевого режима

## 🎯 ПРОБЛЕМА

**Текущая ситуация:**
- GitHub Secrets правильно настроены и передаются в Kubernetes как environment variables
- НО код в `mcp_server/full_server.py` читает только из файла `credentials.json`
- Environment variables игнорируются!

**Результат:**
- ❌ API ключи не загружаются из GitHub Secrets
- ❌ `retCode 10003: API key is invalid`
- ❌ Все функции падают

---

## 🔍 КОРНЕВАЯ ПРИЧИНА

**Файл:** `mcp_server/full_server.py:70-82`

**Текущий код:**
```python
def load_credentials() -> Dict[str, Any]:
    """Загрузка credentials"""
    config_path = Path(__file__).parent.parent / "config" / "credentials.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Credentials not found: {config_path}")
        raise
```

**Проблема:** Читает ТОЛЬКО из файла, игнорирует ENV variables!

---

## ✅ РЕШЕНИЕ

### Шаг 1: Исправить `load_credentials()` в `full_server.py`

**ЗАМЕНИТЬ функцию (строки 70-82) на:**

```python
def load_credentials() -> Dict[str, Any]:
    """
    Загрузка credentials с приоритетом:
    1. Environment Variables (GitHub Secrets → Kubernetes) - ПРИОРИТЕТ!
    2. credentials.json (fallback для локальной разработки)
    
    Raises:
        ValueError: Если API ключи невалидные или отсутствуют
    """
    import os
    from pathlib import Path
    
    # ============================================
    # ПРИОРИТЕТ #1: Environment Variables (Production)
    # ============================================
    bybit_api_key = os.getenv("BYBIT_API_KEY")
    bybit_api_secret = os.getenv("BYBIT_API_SECRET")
    bybit_testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    
    logger.info("🔍 Loading Bybit credentials...")
    
    # Если нашли в ENV - используем их (Production режим)
    if bybit_api_key and bybit_api_secret:
        logger.info("✅ Found credentials in ENVIRONMENT VARIABLES (Production mode)")
        logger.info(f"   Mode: {'🧪 TESTNET' if bybit_testnet else '🚀 MAINNET'}")
        logger.info(f"   API Key: {bybit_api_key[:8]}...{bybit_api_key[-4:]}")
        
        # ВАЛИДАЦИЯ
        if len(bybit_api_key) < 10 or len(bybit_api_secret) < 10:
            raise ValueError(
                f"Bybit API credentials are too short! "
                f"This likely means they are invalid or placeholder values."
            )
        
        return {
            "bybit": {
                "api_key": bybit_api_key,
                "api_secret": bybit_api_secret,
                "testnet": bybit_testnet
            }
        }
    
    # ============================================
    # ПРИОРИТЕТ #2: credentials.json (Local Development)
    # ============================================
    logger.warning("⚠️ BYBIT credentials not found in ENV, trying credentials.json (Local mode)")
    config_path = Path(__file__).parent.parent / "config" / "credentials.json"
    
    try:
        with open(config_path, 'r') as f:
            file_creds = json.load(f)
            
            bybit_api_key = file_creds["bybit"]["api_key"]
            bybit_api_secret = file_creds["bybit"]["api_secret"]
            bybit_testnet = file_creds["bybit"].get("testnet", False)
            
            logger.info("✅ Found credentials in credentials.json (Local mode)")
            logger.info(f"   Mode: {'🧪 TESTNET' if bybit_testnet else '🚀 MAINNET'}")
            
            return {
                "bybit": {
                    "api_key": bybit_api_key,
                    "api_secret": bybit_api_secret,
                    "testnet": bybit_testnet
                }
            }
            
    except FileNotFoundError:
        logger.error(f"❌ Credentials not found: {config_path}")
        raise ValueError(
            "No Bybit credentials found!\n"
            "For PRODUCTION: Set BYBIT_API_KEY and BYBIT_API_SECRET environment variables\n"
            "For LOCAL: Create config/credentials.json"
        )
    except (JSONDecodeError, KeyError) as e:
        logger.error(f"❌ Invalid credentials.json: {e}")
        raise ValueError(f"Invalid credentials.json format: {e}")
```

---

### Шаг 2: Проверить что ENV variables доступны в Kubernetes

**Файл:** `.github/workflows/deploy.yml` (строки 82-90)

**Убедиться что секреты создаются правильно:**
```yaml
- name: Create or update Secrets from GitHub Secrets
  run: |
    kubectl create secret generic trader-agent-secrets \
      --from-literal=QWEN_API_KEY="${{ secrets.QWEN_API_KEY }}" \
      --from-literal=BYBIT_API_KEY="${{ secrets.BYBIT_API_KEY }}" \
      --from-literal=BYBIT_API_SECRET="${{ secrets.BYBIT_API_SECRET }}" \
      --from-literal=TELEGRAM_BOT_TOKEN="${{ secrets.TELEGRAM_BOT_TOKEN }}" \
      -n trader-agent \
      --dry-run=client -o yaml | kubectl apply -f -
```

**Проверить что в `k8s/cronjob.yaml` или `k8s/deployment.yaml` эти секреты используются:**

```yaml
env:
  - name: BYBIT_API_KEY
    valueFrom:
      secretKeyRef:
        name: trader-agent-secrets
        key: BYBIT_API_KEY
  - name: BYBIT_API_SECRET
    valueFrom:
      secretKeyRef:
        name: trader-agent-secrets
        key: BYBIT_API_SECRET
  - name: BYBIT_TESTNET
    value: "false"  # или из ConfigMap
```

---

### Шаг 3: Добавить валидацию API ключей при старте

**Файл:** `mcp_server/full_server.py` в функции `main()` после строки 1397

**ДОБАВИТЬ после `credentials = load_credentials()`:**

```python
# === ВАЛИДАЦИЯ API КЛЮЧЕЙ ===
logger.info("=" * 50)
logger.info("🔍 VALIDATING BYBIT API CREDENTIALS...")
logger.info("=" * 50)

bybit_api_key = credentials["bybit"]["api_key"]
bybit_api_secret = credentials["bybit"]["api_secret"]

# Проверка на placeholder значения
if bybit_api_key == "your_api_key_here" or bybit_api_secret == "your_api_secret_here":
    logger.error("❌ CRITICAL: API credentials are placeholder values!")
    logger.error("   Please set real API keys in GitHub Secrets or credentials.json")
    raise ValueError("Invalid API credentials: placeholder values detected")

# Проверка минимальной длины
if len(bybit_api_key) < 10 or len(bybit_api_secret) < 10:
    logger.error("❌ CRITICAL: API credentials are too short!")
    logger.error(f"   API Key length: {len(bybit_api_key)}")
    logger.error(f"   API Secret length: {len(bybit_api_secret)}")
    raise ValueError("Invalid API credentials: too short")

logger.info("✅ API credentials format validation passed")
logger.info(f"   Source: {'ENVIRONMENT VARIABLES' if os.getenv('BYBIT_API_KEY') else 'credentials.json'}")
logger.info("=" * 50)
```

---

## 📋 ЧЕКЛИСТ ПРОВЕРКИ

### 1. GitHub Secrets настроены:
```bash
gh secret list
```

**Должны быть:**
- ✅ `BYBIT_API_KEY`
- ✅ `BYBIT_API_SECRET`
- ✅ `QWEN_API_KEY`
- ✅ `TELEGRAM_BOT_TOKEN`

### 2. Kubernetes Secrets созданы:
```bash
kubectl get secrets -n trader-agent
kubectl describe secret trader-agent-secrets -n trader-agent
```

### 3. Environment variables в pod:
```bash
kubectl exec -n trader-agent <pod-name> -- env | grep BYBIT
```

**Должно показать:**
```
BYBIT_API_KEY=xxxxx
BYBIT_API_SECRET=xxxxx
```

### 4. Логи при старте:
```bash
kubectl logs -n trader-agent <pod-name> | grep "Loading Bybit credentials"
```

**Должно показать:**
```
✅ Found credentials in ENVIRONMENT VARIABLES (Production mode)
   Mode: 🚀 MAINNET
   API Key: xxxxxxxx...xxxx
```

---

## 🚨 ЧАСТЫЕ ПРОБЛЕМЫ

### Проблема 1: "Credentials not found in ENV"

**Причина:** Environment variables не передаются в pod

**Решение:**
1. Проверить что секреты созданы: `kubectl get secrets -n trader-agent`
2. Проверить что в deployment/cronjob есть `envFrom` или `env` секция
3. Проверить что secret name правильный: `trader-agent-secrets`

### Проблема 2: "API key is invalid (retCode 10003)"

**Причина:** API ключ невалидный или истек

**Решение:**
1. Проверить ключ на Bybit → API Management
2. Убедиться что ключ активен
3. Обновить в GitHub Secrets если истек

### Проблема 3: "API key has no permissions (retCode 10004)"

**Причина:** У ключа нет прав для чтения баланса

**Решение:**
1. На Bybit → API Management
2. Включить "Read" permissions
3. Если нужна торговля - включить "Trade" permissions

---

## ✅ РЕЗУЛЬТАТ

После исправления:

1. ✅ **Код читает ENV variables ПЕРВЫМ** (Production режим)
2. ✅ **Fallback на credentials.json** (Local режим)
3. ✅ **Валидация при старте** - fail-fast если ключи невалидные
4. ✅ **Понятные логи** - видно откуда загружены ключи
5. ✅ **Полная работа в боевом режиме** - все функции доступны

---

## 🚀 БЫСТРАЯ ПРОВЕРКА

После деплоя проверить:

```bash
# 1. Проверить что секреты в Kubernetes
kubectl get secrets -n trader-agent trader-agent-secrets

# 2. Проверить что ENV variables в pod
kubectl exec -n trader-agent <pod-name> -- printenv | grep BYBIT

# 3. Проверить логи старта
kubectl logs -n trader-agent <pod-name> --tail=50 | grep -A 5 "Loading Bybit"

# 4. Проверить что API работает
kubectl logs -n trader-agent <pod-name> | grep "API VALIDATION"
```

**Ожидаемый результат:**
```
✅ Found credentials in ENVIRONMENT VARIABLES (Production mode)
   Mode: 🚀 MAINNET
   API Key: xxxxxxxx...xxxx
✅ API credentials format validation passed
   Source: ENVIRONMENT VARIABLES
```

---

**Версия:** 1.0  
**Приоритет:** КРИТИЧЕСКИЙ  
**Время на исправление:** 5-10 минут

