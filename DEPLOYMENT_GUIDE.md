# 🚀 Trader Agent - Полная инструкция по деплою

**Проект**: AI Trading Agent для Bybit  
**Репозиторий**: https://github.com/TheMacroeconomicDao/bybit-ai-trader  
**Последнее обновление**: 18 января 2025

---

## 📋 БЫСТРЫЙ СТАРТ (для AI ассистента в новом чате)

```bash
# 1. Переход в проект
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT

# 2. Проверка текущей ветки (работаем в MAIN)
git checkout main
git pull origin main

# 3. Сборка образа
docker build \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:main \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:latest \
  -f Dockerfile .

# 4. Push в registry (или используйте GitHub Actions для автоматического push)
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:main
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:latest

# 5. Deploy в Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml  # Секреты из GitHub Secrets
kubectl apply -f k8s/cronjob.yaml  # CronJob для автономного анализа

# 6. Проверка
kubectl get pods -n trader-agent -l app=trader-agent
kubectl get cronjob -n trader-agent
```

---

## 🏗️ АРХИТЕКТУРА ПРОЕКТА

### Основные компоненты:

- **Autonomous Agent**: Автономный анализатор рынка с Qwen AI
- **Telegram Bot Integration**: Публикация сигналов в Telegram каналы
- **Bybit API Integration**: Получение рыночных данных
- **Technical Analysis Engine**: Технический анализ активов
- **Market Scanner**: Сканирование рынка для поиска возможностей

### Окружения:

1. **Main** (production) - namespace: `trader-agent`
   - Автономный анализ каждые 30 минут
   - Публикация в Telegram каналы

---

## 🔐 НАСТРОЙКА GITHUB SECRETS

### Необходимые секреты в GitHub:

Перейдите в **Settings → Secrets and variables → Actions** и добавьте:

1. **QWEN_API_KEY**
   - Значение: `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`
   - Описание: OpenRouter API ключ для доступа к Qwen моделям
   - Формат: `sk-or-v1-...`

2. **BYBIT_API_KEY**
   - Значение: Ваш Bybit API ключ
   - Описание: Bybit API публичный ключ

3. **BYBIT_API_SECRET**
   - Значение: Ваш Bybit API секрет
   - Описание: Bybit API секретный ключ

4. **TELEGRAM_BOT_TOKEN**
   - Значение: `8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY`
   - Описание: Telegram Bot Token

5. **TELEGRAM_CHAT_IDS**
   - Значение: `-1003382613825,-1003484839912`
   - Описание: Chat ID каналов через запятую

6. **GITHUB_TOKEN**
   - Значение: Автоматически (для push в registry)
   - Описание: GitHub Personal Access Token с правами на packages

### Как добавить секреты:

```bash
# Через GitHub CLI (если установлен)
gh secret set QWEN_API_KEY --body "sk-6f5319fb244f4f9faa1595825cf87a05"
gh secret set BYBIT_API_KEY --body "your_bybit_api_key"
gh secret set BYBIT_API_SECRET --body "your_bybit_api_secret"
gh secret set TELEGRAM_BOT_TOKEN --body "8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY"
gh secret set TELEGRAM_CHAT_IDS --body "-1003382613825,-1003484839912"
```

Или через веб-интерфейс:
1. Перейдите в репозиторий → Settings → Secrets and variables → Actions
2. Нажмите "New repository secret"
3. Добавьте каждый секрет по отдельности

---

## 🔧 ПОДГОТОВКА К ДЕПЛОЮ

### 1. Проверка окружения

```bash
# Kubernetes доступен?
kubectl cluster-info

# Docker запущен?
docker info

# Правильная ветка?
git branch --show-current  # Должно быть: main

# Есть ли незакоммиченные изменения?
git status
```

### 2. Проверка GitHub Secrets

```bash
# Проверить что секреты настроены (через GitHub CLI)
gh secret list

# Или проверить через веб-интерфейс GitHub
```

---

## 📦 СБОРКА ОБРАЗА

### Стандартная сборка (с кешем):

```bash
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT

docker build \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:main \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:latest \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:$(git rev-parse --short HEAD) \
  -f Dockerfile .
```

**Время**: ~5-8 минут  
**Размер**: ~300-400 MB

### Проверка успешной сборки:

```bash
# Проверить что образ создался
docker images | grep trader-agent | head -3

# Должны увидеть:
# ghcr.io/themacroeconomicdao/bybit-ai-trader   main    XXXXX   N seconds/minutes ago   350MB
```

---

## 📤 PUSH В REGISTRY

### Логин в GitHub Container Registry:

```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u TheMacroeconomicDao --password-stdin
```

### Push образа:

```bash
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:main
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:latest

# Опционально - версионный тег
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:$(git rev-parse --short HEAD)
```

**Время**: ~2-4 минуты

---

## 🚀 DEPLOYMENT В KUBERNETES

### 1. Создание namespace и базовых ресурсов:

```bash
# Namespace
kubectl apply -f k8s/namespace.yaml

# ConfigMap
kubectl apply -f k8s/configmap.yaml

# Secrets (из GitHub Secrets через workflow или вручную)
kubectl apply -f k8s/secrets.yaml
```

### 2. Deploy CronJob:

```bash
# CronJob для автономного анализа
kubectl apply -f k8s/cronjob.yaml
```

### 3. Проверка статуса:

```bash
# Проверить CronJob
kubectl get cronjob -n trader-agent

# Должно быть: trader-agent-analyzer   */30 * * * *   True    <none>

# Проверить последние Job
kubectl get jobs -n trader-agent --sort-by=.metadata.creationTimestamp | tail -5

# Проверить логи последнего Job
kubectl logs -n trader-agent -l job-name --tail=100
```

---

## 🧪 ТЕСТИРОВАНИЕ ПОСЛЕ ДЕПЛОЯ

### 1. Ручной запуск Job:

```bash
# Создать Job из CronJob вручную для тестирования
kubectl create job --from=cronjob/trader-agent-analyzer manual-test-$(date +%s) -n trader-agent

# Следить за выполнением
kubectl get jobs -n trader-agent -w

# Проверить логи
kubectl logs -n trader-agent -l job-name --tail=100 -f
```

### 2. Проверка результатов:

```bash
# Проверить что результаты сохранились (если используется PVC)
kubectl exec -n trader-agent deployment/trader-agent -- ls -la /app/data/

# Или проверить логи на наличие успешного завершения
kubectl logs -n trader-agent -l app=trader-agent --tail=50 | grep -i "success\|error"
```

### 3. Проверка Telegram публикации:

Проверьте Telegram каналы:
- **DIAMOND HEADZH**: `-1003382613825`
- **Hypov Hedge Fund (AI Signals)**: `-1003484839912`

Должны появиться сообщения с топовыми точками входа.

---

## 🔍 ДИАГНОСТИКА ПРОБЛЕМ

### Проверка логов:

```bash
# Последние 100 строк логов Job
kubectl logs -n trader-agent -l job-name --tail=100

# Следить за логами в реальном времени
kubectl logs -n trader-agent -l job-name -f

# Ошибки
kubectl logs -n trader-agent -l job-name --tail=200 | grep -i "error\|failed\|exception"
```

### Проверка статуса Job:

```bash
# Статус Job
kubectl get jobs -n trader-agent

# Детали Job
kubectl describe job -n trader-agent -l app=trader-agent

# События
kubectl get events -n trader-agent --sort-by='.lastTimestamp' | tail -20
```

### Если Job не запускается:

```bash
# Проверить причину
kubectl describe cronjob trader-agent-analyzer -n trader-agent

# Проверить Secrets
kubectl get secret trader-agent-secrets -n trader-agent -o jsonpath='{.data}' | jq .

# Проверить ConfigMap
kubectl get configmap trader-agent-config -n trader-agent -o yaml
```

---

## 🛠️ ЧАСТЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ

### Проблема 1: Build провалился

**Симптомы**: Python errors, module not found

**Решение**:

```bash
# Проверить что все зависимости установлены
pip install -r requirements.txt

# Пересобрать без кеша
docker build --no-cache -t ghcr.io/themacroeconomicdao/bybit-ai-trader:main -f Dockerfile .
```

### Проблема 2: "ImagePullBackOff" в Kubernetes

**Решение**:

```bash
# Проверить что образ существует в registry
docker manifest inspect ghcr.io/themacroeconomicdao/bybit-ai-trader:main

# Проверить imagePullSecrets
kubectl get secret -n trader-agent ghcr-secret

# Пересоздать если нужно
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=TheMacroeconomicDao \
  --docker-password=$GITHUB_TOKEN \
  -n trader-agent
```

### Проблема 3: Job завершается с ошибкой

**Решение**:

```bash
# Проверить логи
kubectl logs -n trader-agent -l job-name --tail=200

# Проверить что секреты правильно переданы
kubectl get secret trader-agent-secrets -n trader-agent -o jsonpath='{.data.QWEN_API_KEY}' | base64 -d

# Проверить переменные окружения в Pod
kubectl exec -n trader-agent -l job-name -- env | grep -E "QWEN|BYBIT|TELEGRAM"
```

### Проблема 4: Telegram сообщения не отправляются

**Решение**:

```bash
# Проверить токен бота
kubectl get secret trader-agent-secrets -n trader-agent -o jsonpath='{.data.TELEGRAM_BOT_TOKEN}' | base64 -d

# Проверить chat IDs
kubectl get configmap trader-agent-config -n trader-agent -o jsonpath='{.data.TELEGRAM_CHAT_IDS}'

# Проверить логи на ошибки Telegram API
kubectl logs -n trader-agent -l job-name | grep -i "telegram\|bot"
```

---

## 📊 ПРОВЕРКА КОНФИГУРАЦИИ

### Критичные env переменные:

```bash
kubectl get cronjob trader-agent-analyzer -n trader-agent -o yaml | grep -A 10 "env:"
```

Должны быть:
- `QWEN_API_KEY` (из Secret)
- `BYBIT_API_KEY` (из Secret)
- `BYBIT_API_SECRET` (из Secret)
- `TELEGRAM_BOT_TOKEN` (из Secret)
- `QWEN_MODEL=qwen-max` (из ConfigMap)
- `BYBIT_TESTNET=false` (из ConfigMap)

### ConfigMap значения:

```bash
kubectl get configmap -n trader-agent trader-agent-config -o jsonpath='{.data}' | jq .
```

---

## 🔄 ПОЛНЫЙ ЦИКЛ ДЕПЛОЯ (copy-paste ready)

```bash
#!/bin/bash
set -e

echo "🚀 Trader Agent - Полный деплой в production (main)"
echo ""

# 1. Переход в проект
cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT
echo "✅ В директории проекта"

# 2. Переключение на main и pull
git checkout main
git pull origin main
echo "✅ Main ветка обновлена"

# 3. Проверка Docker
docker info >/dev/null 2>&1 || { echo "❌ Docker не запущен!"; exit 1; }
echo "✅ Docker работает"

# 4. Сборка образа
echo "🔨 Собираю образ (5-8 минут)..."
COMMIT_HASH=$(git rev-parse --short HEAD)
docker build \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:main \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:latest \
  -t ghcr.io/themacroeconomicdao/bybit-ai-trader:$COMMIT_HASH \
  -f Dockerfile .
echo "✅ Образ собран"

# 5. Push в registry
echo "📤 Пушу в registry..."
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:main
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:latest
echo "✅ Образ запушен"

# 6. Deploy в Kubernetes
echo "🚀 Деплою в Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml  # Убедитесь что секреты настроены!
kubectl apply -f k8s/cronjob.yaml

echo "✅ Deployment завершен"

# 7. Проверка статуса
echo ""
echo "📊 Статус CronJob:"
kubectl get cronjob -n trader-agent
echo ""
echo "📦 Последние Job:"
kubectl get jobs -n trader-agent --sort-by=.metadata.creationTimestamp | tail -3
echo ""
echo "🧪 Тест - запуск Job вручную:"
kubectl create job --from=cronjob/trader-agent-analyzer manual-test-$(date +%s) -n trader-agent
echo ""
echo "📋 Логи (последние 50 строк):"
sleep 5
kubectl logs -n trader-agent -l job-name --tail=50
echo ""
echo "🎉 Деплой завершен успешно!"
```

---

## 📝 ЧТО НУЖНО ЗНАТЬ О ПРОЕКТЕ

### Критичные файлы:

1. **`autonomous_agent/main.py`** - точка входа автономного агента
   - Запускает анализ рынка
   - Сохраняет результаты в `data/`
   - Готовит сообщения для Telegram

2. **`autonomous_agent/autonomous_analyzer.py`** - основной анализатор
   - Интеграция с Bybit API
   - Использование Qwen AI для анализа
   - Поиск топ 3 точек входа

3. **`autonomous_agent/telegram_formatter.py`** - форматирование для Telegram
   - Создание красивых сообщений
   - HTML форматирование

4. **`mcp_server/telegram_bot.py`** - Telegram Bot интеграция
   - Отправка сообщений в каналы
   - Обработка ошибок

### Компоненты системы:

- ✅ **BybitClient** - получение рыночных данных
- ✅ **TechnicalAnalysis** - технический анализ
- ✅ **MarketScanner** - сканирование рынка
- ✅ **QwenClient** - AI анализ через Qwen
- ✅ **TelegramBot** - публикация в Telegram

---

## 🔐 СЕКРЕТЫ И ПЕРЕМЕННЫЕ

### GitHub Secrets (обязательные):

```bash
# В GitHub Secrets (настроены через веб-интерфейс):
- QWEN_API_KEY (sk-6f5319fb244f4f9faa1595825cf87a05)
- BYBIT_API_KEY (ваш Bybit API ключ)
- BYBIT_API_SECRET (ваш Bybit API секрет)
- TELEGRAM_BOT_TOKEN (8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY)
- TELEGRAM_CHAT_IDS (-1003382613825,-1003484839912)
- GITHUB_TOKEN (для push в registry)
```

### ConfigMap значения:

```bash
# В ConfigMap (k8s/configmap.yaml):
- QWEN_MODEL=qwen-max
- BYBIT_TESTNET=false
- ANALYSIS_SCHEDULE=*/30 * * * *  # Каждые 30 минут
```

---

## 📋 CHECKLIST ПЕРЕД ДЕПЛОЕМ

- [ ] Git: main ветка, pull завершен
- [ ] Docker: запущен и отвечает
- [ ] GitHub Secrets: все секреты добавлены
- [ ] Build: образ собрался успешно
- [ ] Push: образ в registry
- [ ] ConfigMap: правильные значения
- [ ] Secrets: созданы из GitHub Secrets
- [ ] CronJob: создан и активен
- [ ] Test Job: ручной запуск успешен
- [ ] Telegram: сообщения публикуются

---

## 🆘 ROLLBACK (если что-то пошло не так)

### Откат к предыдущей версии:

```bash
# 1. Найти предыдущий рабочий коммит
git log --oneline -10

# 2. Откатить main
git reset --hard <PREVIOUS_COMMIT_HASH>
git push origin main --force

# 3. Пересобрать и задеплоить
docker build -t ghcr.io/themacroeconomicdao/bybit-ai-trader:main -f Dockerfile .
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:main
kubectl rollout restart cronjob/trader-agent-analyzer -n trader-agent
```

### Откат CronJob без изменения кода:

```bash
# Использовать старый образ
kubectl set image cronjob/trader-agent-analyzer \
  trader-agent=ghcr.io/themacroeconomicdao/bybit-ai-trader:<OLD_TAG> \
  -n trader-agent
```

---

## 💡 ВАЖНЫЕ КОМАНДЫ

```bash
# Быстрая пересборка и деплой
docker build -t ghcr.io/themacroeconomicdao/bybit-ai-trader:main -f Dockerfile . && \
docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:main && \
kubectl rollout restart cronjob/trader-agent-analyzer -n trader-agent

# Посмотреть логи ошибок
kubectl logs -n trader-agent -l job-name --tail=100 | grep -i error

# Проверить env в работающем Pod
kubectl exec -n trader-agent -l job-name -- env | grep -E "QWEN|BYBIT|TELEGRAM"

# Ручной запуск анализа
kubectl create job --from=cronjob/trader-agent-analyzer manual-$(date +%s) -n trader-agent

# Проверить статус CronJob
kubectl get cronjob -n trader-agent
```

---

## 🎯 ДЛЯ AI АССИСТЕНТА

**Когда пользователь просит "собери и задеплой":**

1. `cd /Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT`
2. `git checkout main && git pull origin main`
3. `docker build -t ghcr.io/themacroeconomicdao/bybit-ai-trader:main -f Dockerfile .`
4. `docker push ghcr.io/themacroeconomicdao/bybit-ai-trader:main`
5. `kubectl apply -f k8s/secrets.yaml` (если секреты обновлялись)
6. `kubectl rollout restart cronjob/trader-agent-analyzer -n trader-agent`
7. `kubectl create job --from=cronjob/trader-agent-analyzer manual-test-$(date +%s) -n trader-agent`
8. Проверить логи и Telegram каналы

**Помнить**:
- Работаем в **main** ветке
- Namespace: **trader-agent**
- CronJob: **trader-agent-analyzer**
- Расписание: **каждые 30 минут**
- Telegram каналы: **-1003382613825, -1003484839912**

---

## 🔄 GITHUB ACTIONS WORKFLOW

Автоматический деплой через GitHub Actions настроен в `.github/workflows/deploy.yml`:

- Автоматическая сборка при push в main
- Push образа в GHCR
- Обновление секретов в Kubernetes из GitHub Secrets
- Деплой CronJob

---

**Автор**: AI Assistant  
**Дата**: 18 января 2025  
**Версия**: 1.0

