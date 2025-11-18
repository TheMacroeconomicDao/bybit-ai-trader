# ✅ Чеклист готовности к развёртыванию

## 🎯 Перед деплоем

### ✅ 1. API ключи готовы

- [x] **QWEN_API_KEY** - OpenRouter ключ
  - Значение: `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`
  - Статус: ✅ Протестирован и работает
  - Баланс: ✅ Есть кредиты

- [ ] **BYBIT_API_KEY** - Bybit публичный ключ
  - Статус: ⚠️ Нужно добавить в GitHub Secrets

- [ ] **BYBIT_API_SECRET** - Bybit секретный ключ
  - Статус: ⚠️ Нужно добавить в GitHub Secrets

- [x] **TELEGRAM_BOT_TOKEN** - Telegram бот токен
  - Значение: `8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY`
  - Статус: ✅ Уже настроен

- [x] **TELEGRAM_CHAT_IDS** - ID каналов
  - Значение: `-1003382613825,-1003484839912`
  - Статус: ✅ Уже настроен

---

## 🔐 ШАГ 1: Обновить GitHub Secrets

### Перейдите в GitHub репозиторий:
👉 **Settings → Secrets and variables → Actions**

### Обновите/Добавьте секреты:

1. **QWEN_API_KEY** (ОБНОВИТЬ)
   ```
   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
   ```

2. **BYBIT_API_KEY** (ДОБАВИТЬ если нет)
   ```
   ваш_bybit_api_key
   ```

3. **BYBIT_API_SECRET** (ДОБАВИТЬ если нет)
   ```
   ваш_bybit_api_secret
   ```

4. **TELEGRAM_BOT_TOKEN** (проверить что есть)
   ```
   8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY
   ```

5. **TELEGRAM_CHAT_IDS** (проверить что есть)
   ```
   -1003382613825,-1003484839912
   ```

---

## 🐳 ШАГ 2: Проверка Docker образа

### Локальная проверка:

```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT

# Сборка образа
docker build -t trader-agent:test -f Dockerfile .

# Тест запуска (требует переменные окружения)
docker run --rm \
  -e QWEN_API_KEY="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" \
  -e BYBIT_API_KEY="test" \
  -e BYBIT_API_SECRET="test" \
  trader-agent:test
```

---

## ☸️ ШАГ 3: Развёртывание в Kubernetes

### Вариант А: Через GitHub Actions (автоматически)

1. **Закоммитьте изменения:**
   ```bash
   git add .
   git commit -m "Migrate to OpenRouter, update deployment configs"
   git push origin main
   ```

2. **GitHub Actions автоматически:**
   - Соберёт Docker образ
   - Запушит в GitHub Container Registry
   - Развернёт в Kubernetes

### Вариант Б: Вручную

```bash
# 1. Сборка и push образа
docker build \
  -t ghcr.io/themacroeconomicdao/trader-agent:main \
  -t ghcr.io/themacroeconomicdao/trader-agent:latest \
  -f Dockerfile .

docker push ghcr.io/themacroeconomicdao/trader-agent:main
docker push ghcr.io/themacroeconomicdao/trader-agent:latest

# 2. Создание namespace
kubectl apply -f k8s/namespace.yaml

# 3. Создание ConfigMap
kubectl apply -f k8s/configmap.yaml

# 4. Создание Secrets
kubectl create secret generic trader-agent-secrets \
  --from-literal=QWEN_API_KEY="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" \
  --from-literal=BYBIT_API_KEY="ваш_bybit_api_key" \
  --from-literal=BYBIT_API_SECRET="ваш_bybit_api_secret" \
  --from-literal=TELEGRAM_BOT_TOKEN="8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY" \
  -n trader-agent \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. Развёртывание CronJob
kubectl apply -f k8s/cronjob.yaml
```

---

## ✅ ШАГ 4: Проверка развёртывания

### Проверка CronJob:

```bash
# Статус CronJob
kubectl get cronjob -n trader-agent

# Последние Jobs
kubectl get jobs -n trader-agent --sort-by=.metadata.creationTimestamp

# Логи последнего Job
kubectl logs -n trader-agent -l app=trader-agent --tail=100
```

### Ручной запуск для теста:

```bash
# Создать Job из CronJob для немедленного запуска
kubectl create job --from=cronjob/trader-agent-analysis trader-agent-test-$(date +%s) -n trader-agent

# Проверить логи
kubectl logs -n trader-agent -l job-name=trader-agent-test-* --tail=100 -f
```

---

## 📊 ШАГ 5: Мониторинг

### Проверка работы:

1. **Логи CronJob:**
   ```bash
   kubectl logs -n trader-agent -l app=trader-agent -f
   ```

2. **Telegram канал:**
   - Проверьте что сообщения приходят каждые 30 минут
   - Формат сообщений правильный

3. **Результаты анализа:**
   - Проверьте что `data/latest_analysis.json` обновляется
   - Проверьте что найдены топ 3 возможности

---

## 🔧 Конфигурация CronJob

Текущая конфигурация (`k8s/cronjob.yaml`):
- **Расписание:** Каждые 30 минут (`*/30 * * * *`)
- **Timeout:** 10 минут
- **Restart policy:** Never

### Изменить расписание:

Отредактируйте `k8s/cronjob.yaml`:
```yaml
spec:
  schedule: "*/30 * * * *"  # Каждые 30 минут
  # Или:
  # schedule: "0 * * * *"   # Каждый час
  # schedule: "0 */2 * * *"  # Каждые 2 часа
```

---

## 🆘 Решение проблем

### Проблема: Pod не запускается

```bash
# Проверка событий
kubectl describe pod -n trader-agent -l app=trader-agent

# Проверка логов
kubectl logs -n trader-agent -l app=trader-agent
```

### Проблема: Ошибка "QWEN_API_KEY not found"

```bash
# Проверка секретов
kubectl get secret trader-agent-secrets -n trader-agent -o yaml

# Обновление секрета
kubectl create secret generic trader-agent-secrets \
  --from-literal=QWEN_API_KEY="sk-or-v1-..." \
  -n trader-agent \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Проблема: Job завершается с ошибкой

```bash
# Проверка логов
kubectl logs -n trader-agent -l app=trader-agent --tail=200

# Проверка статуса
kubectl get jobs -n trader-agent
```

---

## ✅ Финальный чеклист

- [ ] GitHub Secrets обновлены (QWEN_API_KEY, BYBIT_API_KEY, BYBIT_API_SECRET)
- [ ] Docker образ собран и запушен
- [ ] Kubernetes namespace создан
- [ ] ConfigMap применён
- [ ] Secrets созданы
- [ ] CronJob развёрнут
- [ ] Первый Job выполнен успешно
- [ ] Telegram сообщения приходят
- [ ] Логи проверены

---

## 🚀 Готово к развёртыванию!

После выполнения всех шагов система будет:
- ✅ Автоматически анализировать рынок каждые 30 минут
- ✅ Находить топ 3 точки входа
- ✅ Публиковать результаты в Telegram каналы
- ✅ Сохранять результаты в `data/latest_analysis.json`

---

**Дата:** 2025-11-18  
**Версия:** OpenRouter Integration  
**Статус:** ✅ ГОТОВО К ДЕПЛОЮ


