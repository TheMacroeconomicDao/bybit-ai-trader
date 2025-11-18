# Интеграция Telegram Bot для автоматической публикации торговых сигналов

## 📋 Обзор

Реализована система автоматической публикации торговых сигналов в Telegram каналы/группы через Telegram Bot API. Система поддерживает отправку сообщений на русском и английском языках с красивым HTML-форматированием.

---

## 🗂️ Структура файлов

### Основные модули:

1. **`mcp_server/telegram_bot.py`** - Основной модуль для работы с Telegram Bot API
   - Класс `TelegramBot` - основной класс для отправки сообщений
   - Функция `send_trading_signal()` - удобная функция для быстрой отправки

2. **`send_post.py`** - Скрипт для отправки русских сообщений
   - Поддерживает отправку в несколько каналов одновременно
   - Использует каналы по умолчанию из конфигурации

3. **`send_post_en.py`** - Скрипт для отправки английских сообщений
   - Аналогичен `send_post.py`, но с английским текстом

4. **`.telegram_chat_id`** - Файл с сохраненными chat_id каналов

---

## 🔑 Конфигурация

### Токен бота:
```
BOT_TOKEN = "8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY"
```

### Зарегистрированные каналы:
- **DIAMOND HEADZH**: `-1003382613825` (канал)
- **Hypov Hedge Fund (AI Signals)**: `-1003484839912` (канал)

---

## 📚 API и функции

### Класс `TelegramBot`

#### Инициализация:
```python
from mcp_server.telegram_bot import TelegramBot

bot = TelegramBot(token="YOUR_BOT_TOKEN")
```

#### Методы:

**1. `send_message(chat_id, text, parse_mode="HTML", disable_web_page_preview=True)`**
- Отправляет сообщение в указанный чат/канал
- **Параметры:**
  - `chat_id` (str): ID чата или канала
  - `text` (str): Текст сообщения
  - `parse_mode` (str, optional): "HTML" или "Markdown" (по умолчанию "HTML")
  - `disable_web_page_preview` (bool): Отключить превью ссылок
- **Возвращает:** dict с результатом от Telegram API
- **Пример:**
```python
result = await bot.send_message(
    chat_id="-1003382613825",
    text="<b>Текст сообщения</b>",
    parse_mode="HTML"
)
```

**2. `get_updates(offset=None, timeout=10)`**
- Получает обновления от бота (для поиска chat_id)
- **Параметры:**
  - `offset` (int, optional): ID первого обновления
  - `timeout` (int): Таймаут в секундах
- **Возвращает:** dict с обновлениями

**3. `get_chat_info(chat_id)`**
- Получает информацию о чате/канале
- **Параметры:**
  - `chat_id` (str): ID чата
- **Возвращает:** dict с информацией о чате

**4. `close()`**
- Закрывает HTTP сессию
- **Важно:** Вызывать после завершения работы

### Функция `send_trading_signal()`

Удобная функция для быстрой отправки торгового сигнала:

```python
from mcp_server.telegram_bot import send_trading_signal

success = await send_trading_signal(
    token="YOUR_BOT_TOKEN",
    chat_id="-1003382613825",
    message="Текст сообщения"
)
```

---

## 🔌 Интеграция с ботом автоматизации

### Вариант 1: Прямое использование класса TelegramBot

```python
import asyncio
from mcp_server.telegram_bot import TelegramBot

async def publish_signal(signal_data, channels=None):
    """
    Публикует торговый сигнал в указанные каналы
    
    Args:
        signal_data: dict с данными сигнала (entry, sl, tp, etc.)
        channels: list chat_id каналов (по умолчанию все зарегистрированные)
    """
    BOT_TOKEN = "8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY"
    
    DEFAULT_CHANNELS = [
        "-1003382613825",  # DIAMOND HEADZH
        "-1003484839912",  # Hypov Hedge Fund (AI Signals)
    ]
    
    if channels is None:
        channels = DEFAULT_CHANNELS
    
    bot = TelegramBot(BOT_TOKEN)
    
    try:
        # Формируем сообщение из данных сигнала
        message = format_trading_signal(signal_data)
        
        results = []
        for chat_id in channels:
            try:
                result = await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML"
                )
                results.append({"chat_id": chat_id, "success": True})
            except Exception as e:
                results.append({"chat_id": chat_id, "success": False, "error": str(e)})
        
        return results
    finally:
        await bot.close()

def format_trading_signal(data):
    """Форматирует данные сигнала в HTML сообщение"""
    return f"""<b>⚡ TRADING SIGNAL</b>

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 {data['symbol']}</b>

<b>Entry:</b> ${data['entry']}
<b>Stop-Loss:</b> ${data['stop_loss']}
<b>Take-Profit:</b> ${data['take_profit']}

<b>Risk/Reward:</b> {data['risk_reward']}

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"""
```

### Вариант 2: Использование готовых шаблонов сообщений

```python
from mcp_server.telegram_bot import TelegramBot

# Шаблоны сообщений уже определены в send_post.py и send_post_en.py
# Можно импортировать их или создать свои

RUSSIAN_TEMPLATE = """<b>⚡ ДЕТАЛЬНЫЙ ПЛАН СДЕЛОК</b>
..."""

ENGLISH_TEMPLATE = """<b>⚡ DETAILED TRADING PLAN</b>
..."""

async def publish_multiple_signals(signals, language="en"):
    """Публикует несколько сигналов"""
    bot = TelegramBot(BOT_TOKEN)
    
    template = ENGLISH_TEMPLATE if language == "en" else RUSSIAN_TEMPLATE
    
    for signal in signals:
        message = format_signal_from_template(template, signal)
        for chat_id in DEFAULT_CHANNELS:
            await bot.send_message(chat_id, message, parse_mode="HTML")
    
    await bot.close()
```

### Вариант 3: Интеграция через MCP инструменты

Если бот автоматизации использует MCP протокол, можно добавить инструменты в `mcp_server/full_server.py`:

```python
@tool()
async def publish_trading_signal_to_telegram(
    symbol: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    risk_reward: str,
    channels: List[str] = None,
    language: str = "en"
) -> dict:
    """
    Публикует торговый сигнал в Telegram каналы
    
    Args:
        symbol: Торговая пара (например, "ZEN/USDT")
        entry: Цена входа
        stop_loss: Стоп-лосс
        take_profit: Тейк-профит
        risk_reward: Соотношение риск/награда
        channels: Список chat_id каналов (опционально)
        language: Язык сообщения ("en" или "ru")
    
    Returns:
        dict: Результаты отправки
    """
    from mcp_server.telegram_bot import TelegramBot
    
    BOT_TOKEN = "8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY"
    DEFAULT_CHANNELS = ["-1003382613825", "-1003484839912"]
    
    if channels is None:
        channels = DEFAULT_CHANNELS
    
    bot = TelegramBot(BOT_TOKEN)
    
    try:
        # Формируем сообщение
        message = create_signal_message(
            symbol, entry, stop_loss, take_profit, risk_reward, language
        )
        
        results = []
        for chat_id in channels:
            try:
                await bot.send_message(chat_id, message, parse_mode="HTML")
                results.append({"chat_id": chat_id, "status": "success"})
            except Exception as e:
                results.append({"chat_id": chat_id, "status": "error", "error": str(e)})
        
        return {"results": results, "total": len(channels), "success": len([r for r in results if r["status"] == "success"])}
    finally:
        await bot.close()
```

---

## 📝 Формат сообщений

### HTML форматирование

Система использует HTML форматирование для красивого отображения:

- `<b>текст</b>` - жирный текст
- `<code>код</code>` - моноширинный текст
- `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━` - разделители
- Эмодзи для визуального разделения

### Структура сообщения:

1. **Заголовок** - название сигнала
2. **Разделитель**
3. **Детали сделки** - Entry, SL, TP, R:R
4. **Расчет размера позиции**
5. **Временные окна**
6. **Разделитель**
7. **Риск портфеля** (если несколько сделок)
8. **Confidence анализ**
9. **Рекомендации**

---

## 🔧 Примеры использования

### Пример 1: Отправка одного сигнала

```python
import asyncio
from mcp_server.telegram_bot import TelegramBot

async def send_single_signal():
    bot = TelegramBot("8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY")
    
    message = """<b>⚡ TRADING SIGNAL</b>
    
<b>📊 ZEN/USDT</b>
<b>Entry:</b> $15.89
<b>Stop-Loss:</b> $13.58
<b>Take-Profit:</b> $20.52"""
    
    await bot.send_message("-1003382613825", message, parse_mode="HTML")
    await bot.close()

asyncio.run(send_single_signal())
```

### Пример 2: Отправка в несколько каналов

```python
async def send_to_multiple_channels():
    bot = TelegramBot("8003689195:AAGxQsopKvlLS34H2TZ0S1a0K7s4yV4iOBY")
    
    channels = ["-1003382613825", "-1003484839912"]
    message = "Ваше сообщение"
    
    for chat_id in channels:
        await bot.send_message(chat_id, message, parse_mode="HTML")
    
    await bot.close()
```

### Пример 3: Динамическое формирование сообщения

```python
def create_signal_message(symbol, entry, sl, tp, rr, language="en"):
    """Создает сообщение из данных сигнала"""
    
    if language == "en":
        return f"""<b>⚡ TRADING SIGNAL</b>

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 {symbol}</b>

<b>Entry:</b> ${entry}
<b>Stop-Loss:</b> ${sl}
<b>Take-Profit:</b> ${tp}

<b>Risk/Reward:</b> {rr}

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"""
    else:
        return f"""<b>⚡ ТОРГОВЫЙ СИГНАЛ</b>

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>

<b>📊 {symbol}</b>

<b>Entry:</b> ${entry}
<b>Stop-Loss:</b> ${sl}
<b>Take-Profit:</b> ${tp}

<b>Risk/Reward:</b> {rr}

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"""
```

---

## ⚙️ Настройка для автоматизации

### 1. Добавление новых каналов

Чтобы добавить новый канал:

1. Добавьте бота в канал как администратора
2. Отправьте любое сообщение в канал
3. Получите chat_id через `get_updates()`:
```python
bot = TelegramBot(BOT_TOKEN)
updates = await bot.get_updates()
# Найдите chat_id в updates
```
4. Добавьте chat_id в `DEFAULT_CHANNELS` в скриптах

### 2. Обработка ошибок

Система автоматически пробует отправить без форматирования при ошибке HTML:

```python
try:
    await bot.send_message(chat_id, message, parse_mode="HTML")
except Exception as e:
    # Автоматический fallback на обычный текст
    await bot.send_message(chat_id, message, parse_mode=None)
```

### 3. Логирование

Используется `loguru` для логирования:
```python
from loguru import logger

logger.info("Сообщение отправлено")
logger.error("Ошибка отправки")
```

---

## 🚀 Рекомендации для интеграции

1. **Используйте async/await** - все функции асинхронные
2. **Всегда закрывайте сессию** - вызывайте `await bot.close()` после использования
3. **Обрабатывайте ошибки** - Telegram API может вернуть ошибку
4. **Кэшируйте chat_id** - не запрашивайте их каждый раз
5. **Используйте HTML форматирование** - оно дает лучший результат
6. **Проверяйте лимиты API** - Telegram имеет лимиты на отправку сообщений

---

## 📦 Зависимости

Все необходимые зависимости уже есть в `requirements.txt`:
- `aiohttp>=3.9.0` - для HTTP запросов
- `loguru>=0.7.0` - для логирования

---

## 🔐 Безопасность

⚠️ **Важно:**
- Токен бота хранится в коде (для продакшена лучше использовать переменные окружения)
- Chat_id каналов можно хранить в конфигурационном файле
- Рекомендуется использовать `.env` файл для секретов

---

## 📞 Контакты и поддержка

Если нужна помощь с интеграцией:
1. Проверьте логи через `loguru`
2. Убедитесь что бот имеет права администратора в каналах
3. Проверьте что chat_id корректны (отрицательные числа для каналов)

---

## 📄 Пример полной интеграции

```python
"""
Пример интеграции с ботом автоматизации анализа
"""
import asyncio
from typing import List, Dict, Optional
from mcp_server.telegram_bot import TelegramBot

class TelegramPublisher:
    """Класс для публикации торговых сигналов в Telegram"""
    
    def __init__(self, bot_token: str, default_channels: List[str] = None):
        self.bot_token = bot_token
        self.default_channels = default_channels or [
            "-1003382613825",
            "-1003484839912"
        ]
        self.bot = None
    
    async def __aenter__(self):
        self.bot = TelegramBot(self.bot_token)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.bot:
            await self.bot.close()
    
    async def publish_signal(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        risk_reward: str,
        additional_info: Optional[Dict] = None,
        channels: Optional[List[str]] = None,
        language: str = "en"
    ) -> Dict:
        """
        Публикует торговый сигнал
        
        Returns:
            dict: {"success": bool, "sent_to": List[str], "errors": List[str]}
        """
        if channels is None:
            channels = self.default_channels
        
        message = self._format_message(
            symbol, entry, stop_loss, take_profit, risk_reward,
            additional_info, language
        )
        
        results = {
            "success": True,
            "sent_to": [],
            "errors": []
        }
        
        for chat_id in channels:
            try:
                await self.bot.send_message(chat_id, message, parse_mode="HTML")
                results["sent_to"].append(chat_id)
            except Exception as e:
                results["success"] = False
                results["errors"].append(f"{chat_id}: {str(e)}")
        
        return results
    
    def _format_message(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        risk_reward: str,
        additional_info: Optional[Dict],
        language: str
    ) -> str:
        """Форматирует сообщение"""
        # Реализация форматирования
        # Можно использовать шаблоны из send_post.py или send_post_en.py
        pass

# Использование:
async def main():
    async with TelegramPublisher("YOUR_BOT_TOKEN") as publisher:
        result = await publisher.publish_signal(
            symbol="ZEN/USDT",
            entry=15.89,
            stop_loss=13.58,
            take_profit=20.52,
            risk_reward="1:2.0",
            language="en"
        )
        print(result)

asyncio.run(main())
```

---

**Версия:** 1.0  
**Дата создания:** 2025-01-13  
**Автор:** AI Trading Assistant


