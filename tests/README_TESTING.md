# 🧪 Testing Guide

## Запуск тестов

### Базовые тесты Advanced Features
```bash
python tests/test_advanced_features.py
```

**Тесты включают:**
1. ✅ Session Manager
2. ✅ Whale Detection
3. ✅ Volume Profile
4. ✅ Liquidity Grabs
5. ✅ ORB Strategy
6. ✅ 20-Point Scoring

### Тест производительности ORB
```bash
python tests/test_orb_performance.py
```

**Проверяет:**
- ⚡ Время выполнения scan БЕЗ ORB
- ⚡ Время выполнения scan С ORB
- ⚡ Overhead от ORB scan
- ⏰ Правильность timing (ORB только в нужное время)

## Требования

Убедитесь что установлены зависимости:
```bash
pip install -r requirements.txt
```

И настроен `.env` файл:
```
BYBIT_API_KEY=your_key
BYBIT_API_SECRET=your_secret
```

## Ожидаемые результаты

### test_advanced_features.py
- Все 6 тестов должны пройти ✅
- ORB может не найти setup если не в нужное время (это нормально)

### test_orb_performance.py
- Overhead < 5s: ✅ EXCELLENT
- Overhead < 10s: ✅ GOOD
- Overhead < 20s: ⚠️ ACCEPTABLE
- Overhead > 20s: ❌ POOR

## Troubleshooting

### ModuleNotFoundError
Установите зависимости:
```bash
pip install ccxt loguru pandas numpy ta python-dotenv pytz
```

### API Errors
Проверьте `.env` файл и API ключи

### ORB не находит setups
Это нормально если:
- Не в European (08:00-10:00 UTC) или US (13:30-15:30 UTC) сессии
- Нет breakout в Opening Range
- Недостаточный volume









