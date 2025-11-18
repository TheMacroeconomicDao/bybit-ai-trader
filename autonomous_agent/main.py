"""
Main Entry Point для Autonomous Trading Agent
Точка входа для запуска автономного анализатора
"""

import asyncio
import os
import json
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

from autonomous_agent.autonomous_analyzer import AutonomousAnalyzer
from autonomous_agent.telegram_formatter import TelegramFormatter

# Добавляем путь к mcp_server для импорта TelegramBot
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_server.telegram_bot import TelegramBot


def load_config() -> dict:
    """Загрузка конфигурации"""
    config = {}
    
    # Из переменных окружения
    config["qwen_api_key"] = os.getenv("QWEN_API_KEY", "")
    config["bybit_api_key"] = os.getenv("BYBIT_API_KEY", "")
    config["bybit_api_secret"] = os.getenv("BYBIT_API_SECRET", "")
    config["qwen_model"] = os.getenv("QWEN_MODEL", "qwen/qwen-turbo")  # OpenRouter формат модели
    config["testnet"] = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    
    # Из файла конфигурации (если есть)
    config_file = Path(__file__).parent.parent / "config" / "autonomous_agent.json"
    if config_file.exists():
        try:
            file_config = json.loads(config_file.read_text(encoding="utf-8"))
            config.update(file_config)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
    
    # Проверка обязательных параметров
    if not config["qwen_api_key"]:
        raise ValueError("QWEN_API_KEY environment variable is required")
    if not config["bybit_api_key"]:
        raise ValueError("BYBIT_API_KEY environment variable is required")
    if not config["bybit_api_secret"]:
        raise ValueError("BYBIT_API_SECRET environment variable is required")
    
    return config


async def publish_to_telegram(bot_token: str, chat_ids_str: str, message: str, parse_mode: str = None):
    """Публикует сообщение в Telegram каналы"""
    chat_ids = [cid.strip() for cid in chat_ids_str.split(",") if cid.strip()]
    
    if not chat_ids:
        logger.warning("No Telegram chat IDs provided")
        return
    
    bot = TelegramBot(bot_token)
    
    try:
        results = []
        for chat_id in chat_ids:
            try:
                send_params = {
                    "chat_id": chat_id,
                    "text": message
                }
                if parse_mode:
                    send_params["parse_mode"] = parse_mode
                await bot.send_message(**send_params)
                logger.info(f"Message sent to Telegram channel {chat_id}")
                results.append({"chat_id": chat_id, "success": True})
            except Exception as e:
                logger.error(f"Failed to send to {chat_id}: {e}")
                results.append({"chat_id": chat_id, "success": False, "error": str(e)})
        
        return results
    finally:
        await bot.close()


async def main():
    """Основная функция"""
    try:
        # Настройка логирования
        logger.add(
            "logs/autonomous_agent_{time}.log",
            rotation="1 day",
            retention="7 days",
            level="INFO"
        )
        
        logger.info("=" * 60)
        logger.info("Starting Autonomous Trading Agent")
        logger.info("=" * 60)
        
        # Загрузка конфигурации
        config = load_config()
        logger.info(f"Configuration loaded: Qwen model={config['qwen_model']}, Testnet={config['testnet']}")
        
        # Инициализация анализатора
        analyzer = AutonomousAnalyzer(
            qwen_api_key=config["qwen_api_key"],
            bybit_api_key=config["bybit_api_key"],
            bybit_api_secret=config["bybit_api_secret"],
            qwen_model=config["qwen_model"],
            testnet=config["testnet"]
        )
        
        # Запуск анализа
        logger.info("Starting market analysis...")
        result = await analyzer.analyze_market()
        
        if result.get("success"):
            logger.info("Analysis completed successfully")
            
            # Форматирование для Telegram
            formatter = TelegramFormatter()
            telegram_message = formatter.format_top_opportunities(result)
            
            # Вывод результата
            print("\n" + "=" * 60)
            print("ANALYSIS RESULT")
            print("=" * 60)
            print(telegram_message)
            print("=" * 60)
            
            # Сохранение результата в файл (для дальнейшей обработки ботом)
            output_file = Path(__file__).parent.parent / "data" / "latest_analysis.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            logger.info(f"Result saved to {output_file}")
            
            # Сохранение Telegram сообщения
            telegram_file = Path(__file__).parent.parent / "data" / "latest_telegram_message.txt"
            telegram_file.write_text(telegram_message, encoding="utf-8")
            logger.info(f"Telegram message saved to {telegram_file}")
            
            # Публикация в Telegram каналы
            telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            telegram_chat_ids = os.getenv("TELEGRAM_CHAT_IDS", "")
            
            if telegram_token and telegram_chat_ids:
                try:
                    # Отправляем без HTML режима, так как используем специальные символы
                await publish_to_telegram(telegram_token, telegram_chat_ids, telegram_message, parse_mode=None)
                except Exception as e:
                    logger.error(f"Failed to publish to Telegram: {e}")
            else:
                logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_IDS not set, skipping Telegram publication")
            
            # Возвращаем результат для использования в боте
            return {
                "success": True,
                "telegram_message": telegram_message,
                "analysis": result
            }
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Analysis failed: {error}")
            
            formatter = TelegramFormatter()
            error_message = formatter.format_error(error)
            print(error_message)
            
            return {
                "success": False,
                "error": error,
                "telegram_message": error_message
            }
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return {"success": False, "error": "Interrupted"}
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    finally:
        # Закрытие соединений
        try:
            if 'analyzer' in locals():
                await analyzer.close()
        except:
            pass


if __name__ == "__main__":
    # Запуск асинхронной функции
    result = asyncio.run(main())
    
    # Код выхода
    sys.exit(0 if result.get("success") else 1)

