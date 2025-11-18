# ⚡ Быстрая настройка GitHub Secrets

## 🎯 За 5 минут

### Шаг 1: Перейдите в настройки репозитория

```
https://github.com/TheMacroeconomicDao/bybit-ai-trader/settings/secrets/actions
```

### Шаг 2: Добавьте секреты (копируйте и вставляйте)

Нажмите **"New repository secret"** для каждого:

#### 1. QWEN_API_KEY
```
Name: QWEN_API_KEY
Secret: sk-6f5319fb244f4f9faa1595825cf87a05
```

#### 2. BYBIT_API_KEY
```
Name: BYBIT_API_KEY
Secret: [ваш_bybit_api_key]
```

#### 3. BYBIT_API_SECRET
```
Name: BYBIT_API_SECRET
Secret: [ваш_bybit_api_secret]
```

#### 4. TELEGRAM_BOT_TOKEN
```
Name: TELEGRAM_BOT_TOKEN
Secret: 8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY
```

#### 5. TELEGRAM_CHAT_IDS
```
Name: TELEGRAM_CHAT_IDS
Secret: -1003382613825,-1003484839912
```

### Шаг 3: Проверка

```bash
# Через GitHub CLI
gh secret list

# Должны увидеть все 5 секретов
```

### Готово! ✅

Теперь при каждом push в `main` ветку:
1. GitHub Actions соберёт Docker образ
2. Запушит в GHCR
3. Обновит секреты в Kubernetes
4. Задеплоит CronJob

---

## 📋 Полная инструкция

См. `GITHUB_SECRETS_SETUP.md` для детальной информации.


