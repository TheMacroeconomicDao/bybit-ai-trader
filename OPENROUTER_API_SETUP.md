# OpenRouter API Setup Guide

## 1. Получение API ключа

1. Перейти на https://openrouter.ai/keys
2. Войти или зарегистрироваться
3. Создать новый API ключ
4. Скопировать ключ (начинается с `sk-or-v1-`)

## 2. Настройка .env

```bash
# OpenRouter API для Qwen
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
QWEN_MODEL=qwen/qwen-turbo
```

## 3. Проверка баланса

- Перейти на https://openrouter.ai/credits
- Убедиться что есть credits
- Минимум рекомендуется $5

## 4. Доступные модели

- `qwen/qwen-turbo` - быстрая, дешевая (рекомендуется)
- `qwen/qwen-plus` - сбалансированная
- `qwen/qwen-max` - самая мощная

## 5. Troubleshooting

### 401 Error
- Проверить формат ключа (должен начинаться с `sk-or-v1-`)
- Проверить баланс credits
- Попробовать создать новый ключ

### Rate Limits
- OpenRouter: 200 requests/minute
- Если превышен - подождать 1 минуту
