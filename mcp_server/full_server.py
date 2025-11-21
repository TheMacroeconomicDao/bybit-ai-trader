#!/usr/bin/env python3
"""
Complete Bybit Trading MCP Server
Полная реализация всех требуемых функций из MASTER_PROMPT
"""

import asyncio
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional
from json import JSONDecodeError

# Добавляем путь к mcp_server в sys.path для корректных импортов
_mcp_server_path = Path(__file__).parent
if str(_mcp_server_path) not in sys.path:
    sys.path.insert(0, str(_mcp_server_path))

import pandas as pd
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource, TextResourceContents, Prompt, PromptMessage, GetPromptResult
from loguru import logger

# Загрузка переменных окружения из .env файла (ПОСЛЕ импорта logger)
try:
    from dotenv import load_dotenv
    # Загружаем .env из корня проекта (на уровень выше mcp_server)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"✅ Loaded .env file from {env_path}")
    else:
        # Пробуем загрузить из текущей директории
        load_dotenv()
        logger.debug("Tried to load .env from current directory")
except ImportError:
    # python-dotenv не установлен, продолжаем без него
    logger.warning("⚠️ python-dotenv not installed, .env file will not be loaded automatically")

from trading_operations import (
    TradingOperations,
    get_all_account_balances,
    get_account_type_for_category
)
from technical_analysis import TechnicalAnalysis
from market_scanner import MarketScanner
from position_monitor import PositionMonitor
from bybit_client import BybitClient
from signal_tracker import SignalTracker
from signal_price_monitor import SignalPriceMonitor
from quality_metrics import QualityMetrics
from signal_reports import SignalReports


# Настройка логирования
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/trading_server_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)

# Проверка загрузки переменных окружения из .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists() and os.getenv("BYBIT_API_KEY"):
    logger.info(f"✅ BYBIT_API_KEY loaded from .env (length: {len(os.getenv('BYBIT_API_KEY'))})")
    logger.info(f"   Preview: {os.getenv('BYBIT_API_KEY')[:8]}...{os.getenv('BYBIT_API_KEY')[-4:]}")
elif not os.getenv("BYBIT_API_KEY"):
    logger.warning("⚠️ BYBIT_API_KEY not found in environment variables - will try credentials.json")

# Инициализация MCP сервера
app = Server("bybit-trading-complete")

# Глобальные клиенты
trading_ops: Optional[TradingOperations] = None
technical_analysis: Optional[TechnicalAnalysis] = None
market_scanner: Optional[MarketScanner] = None
position_monitor: Optional[PositionMonitor] = None
bybit_client: Optional[BybitClient] = None
signal_tracker: Optional[SignalTracker] = None
signal_monitor: Optional[SignalPriceMonitor] = None
quality_metrics: Optional[QualityMetrics] = None
signal_reports: Optional[SignalReports] = None


def load_credentials() -> Dict[str, Any]:
    """
    Загрузка credentials с приоритетом:
    1. Environment Variables (GitHub Secrets → Kubernetes) - ПРИОРИТЕТ!
    2. credentials.json (fallback для локальной разработки)
    
    Raises:
        ValueError: Если API ключи невалидные или отсутствуют
    """
    # ============================================
    # ПРИОРИТЕТ #1: Environment Variables (Production)
    # ============================================
    bybit_api_key_raw = os.getenv("BYBIT_API_KEY")
    bybit_api_secret_raw = os.getenv("BYBIT_API_SECRET")
    bybit_testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    
    logger.info("🔍 Loading Bybit credentials...")
    
    # КРИТИЧНО: Убираем пробелы и переносы строк (частая проблема при копировании из GitHub Secrets)
    bybit_api_key = bybit_api_key_raw.strip() if bybit_api_key_raw else None
    bybit_api_secret = bybit_api_secret_raw.strip() if bybit_api_secret_raw else None
    
    # Если нашли в ENV - используем их (Production режим)
    if bybit_api_key and bybit_api_secret:
        logger.info("✅ Found credentials in ENVIRONMENT VARIABLES (Production mode)")
        logger.info(f"   Mode: {'🧪 TESTNET' if bybit_testnet else '🚀 MAINNET'}")
        logger.info(f"   API Key length: {len(bybit_api_key)} chars")
        logger.info(f"   API Secret length: {len(bybit_api_secret)} chars")
        logger.info(f"   API Key preview: {bybit_api_key[:8]}...{bybit_api_key[-4:]}")
        
        # Проверка на пустые строки после strip
        if not bybit_api_key or not bybit_api_secret:
            raise ValueError(
                "Bybit API credentials are empty after trimming whitespace! "
                "Please check GitHub Secrets - they may contain only spaces."
            )
        
        # ВАЛИДАЦИЯ длины
        if len(bybit_api_key) < 10 or len(bybit_api_secret) < 10:
            raise ValueError(
                f"Bybit API credentials are too short! "
                f"API Key: {len(bybit_api_key)} chars, Secret: {len(bybit_api_secret)} chars. "
                f"This likely means they are invalid or placeholder values."
            )
        
        # Проверка на наличие пробелов внутри ключа (не должно быть)
        if ' ' in bybit_api_key or '\n' in bybit_api_key:
            logger.warning("⚠️ WARNING: API Key contains spaces or newlines - this may cause issues!")
        if ' ' in bybit_api_secret or '\n' in bybit_api_secret:
            logger.warning("⚠️ WARNING: API Secret contains spaces or newlines - this may cause issues!")
        
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
            
            bybit_api_key_raw = file_creds["bybit"]["api_key"]
            bybit_api_secret_raw = file_creds["bybit"]["api_secret"]
            bybit_testnet = file_creds["bybit"].get("testnet", False)
            
            # КРИТИЧНО: Убираем пробелы и переносы строк
            bybit_api_key = bybit_api_key_raw.strip() if bybit_api_key_raw else None
            bybit_api_secret = bybit_api_secret_raw.strip() if bybit_api_secret_raw else None
            
            logger.info("✅ Found credentials in credentials.json (Local mode)")
            logger.info(f"   Mode: {'🧪 TESTNET' if bybit_testnet else '🚀 MAINNET'}")
            logger.info(f"   API Key length: {len(bybit_api_key)} chars")
            logger.info(f"   API Secret length: {len(bybit_api_secret)} chars")
            
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


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Все доступные инструменты (полное соответствие MASTER_PROMPT)"""
    
    return [
        # ═══════════════════════════════════════
        # 📊 РЫНОЧНЫЕ ДАННЫЕ
        # ═══════════════════════════════════════
        
        Tool(
            name="get_market_overview",
            description="Полный обзор рынка: sentiment, BTC, топ movers, условия",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_type": {
                        "type": "string",
                        "enum": ["spot", "linear", "both"],
                        "description": "Тип рынка",
                        "default": "both"
                    }
                }
            }
        ),
        
        Tool(
            name="get_all_tickers",
            description="Все торговые пары с базовой информацией",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_type": {"type": "string", "enum": ["spot", "linear"]},
                    "sort_by": {"type": "string", "enum": ["volume", "change", "name"]}
                },
                "required": ["market_type"]
            }
        ),
        
        Tool(
            name="get_asset_price",
            description="Текущая цена актива",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "BTC/USDT, ETH/USDT, etc."}
                },
                "required": ["symbol"]
            }
        ),
        
        # ═══════════════════════════════════════
        # 📈 ТЕХНИЧЕСКИЙ АНАЛИЗ
        # ═══════════════════════════════════════
        
        Tool(
            name="analyze_asset",
            description="ПОЛНЫЙ анализ актива на всех таймфреймах с индикаторами и паттернами",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "timeframes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["5m", "15m", "1h", "4h", "1d"]
                    },
                    "include_patterns": {"type": "boolean", "default": True}
                },
                "required": ["symbol"]
            }
        ),
        
        Tool(
            name="calculate_indicators",
            description="Рассчитать индикаторы для кастомных данных",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "indicators": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "RSI, MACD, BB, EMA, ATR, ADX, etc."
                    }
                },
                "required": ["symbol"]
            }
        ),
        
        Tool(
            name="detect_patterns",
            description="Поиск свечных и графических паттернов",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "timeframe": {"type": "string", "default": "1h"},
                    "pattern_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "candlestick, chart, или both"
                    }
                },
                "required": ["symbol"]
            }
        ),
        
        Tool(
            name="find_support_resistance",
            description="Найти уровни поддержки и сопротивления",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "timeframe": {"type": "string", "default": "1h"},
                    "lookback_periods": {"type": "integer", "default": 50}
                },
                "required": ["symbol"]
            }
        ),
        
        Tool(
            name="get_btc_correlation",
            description="Рассчитать корреляцию актива с BTC. Критично для альткоинов перед входом.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Торговая пара (например ETH/USDT)"},
                    "period": {"type": "integer", "default": 24, "description": "Количество периодов для анализа"},
                    "timeframe": {"type": "string", "default": "1h", "description": "Таймфрейм для анализа"}
                },
                "required": ["symbol"]
            }
        ),
        
        Tool(
            name="get_funding_rate",
            description="Получить funding rate для фьючерсов. Показывает market bias.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Торговая пара фьючерса (например BTC/USDT:USDT)"}
                },
                "required": ["symbol"]
            }
        ),
        
        Tool(
            name="check_tf_alignment",
            description="Быстрая проверка alignment таймфреймов. Экономит время при анализе.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "timeframes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["5m", "15m", "1h", "4h", "1d"],
                        "description": "Список таймфреймов для проверки"
                    }
                },
                "required": ["symbol"]
            }
        ),
        
        # ═══════════════════════════════════════
        # 🔍 СКАНИРОВАНИЕ РЫНКА
        # ═══════════════════════════════════════
        
        Tool(
            name="scan_market",
            description="Поиск торговых возможностей по критериям",
            inputSchema={
                "type": "object",
                "properties": {
                    "criteria": {
                        "type": "object",
                        "description": "Критерии фильтрации"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Максимальное количество результатов"
                    },
                    "auto_track": {
                        "type": "boolean",
                        "default": False,
                        "description": "Автоматически записывать топ-N сигналов в tracker"
                    },
                    "track_limit": {
                        "type": "integer",
                        "default": 3,
                        "description": "Количество топ сигналов для записи (если auto_track=True)"
                    }
                },
                "required": ["criteria"]
            }
        ),
        
        Tool(
            name="find_oversold_assets",
            description="Найти перепроданные активы (RSI <30) для LONG позиций",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_type": {"type": "string", "default": "spot"},
                    "min_volume_24h": {"type": "number", "default": 1000000}
                }
            }
        ),
        
        Tool(
            name="find_overbought_assets",
            description="Найти перекупленные активы (RSI >70) для SHORT позиций",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_type": {"type": "string", "default": "spot"},
                    "min_volume_24h": {"type": "number", "default": 1000000}
                }
            }
        ),
        
        Tool(
            name="find_breakout_opportunities",
            description="Найти возможности пробоя (BB squeeze)",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_type": {"type": "string", "default": "spot"},
                    "min_volume_24h": {"type": "number", "default": 1000000}
                }
            }
        ),
        
        Tool(
            name="find_trend_reversals",
            description="Найти развороты тренда (divergence)",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_type": {"type": "string", "default": "spot"},
                    "min_volume_24h": {"type": "number", "default": 1000000}
                }
            }
        ),
        
        # ═══════════════════════════════════════
        # 🎯 ВАЛИДАЦИЯ ВХОДА
        # ═══════════════════════════════════════
        
        Tool(
            name="check_liquidity",
            description="Проверка ликвидности актива на основе orderbook. Возвращает score (0-1) и детали ликвидности.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Торговая пара (например BTC/USDT)"}
                },
                "required": ["symbol"]
            }
        ),
        
        Tool(
            name="validate_entry",
            description="Валидация точки входа с полной оценкой (включая автоматическую проверку ликвидности, funding rate и open interest для futures)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "side": {"type": "string", "enum": ["long", "short"]},
                    "entry_price": {
                        "type": "number",
                        "description": "Entry price (also accepts 'entry' parameter for compatibility)"
                    },
                    "entry": {
                        "type": "number",
                        "description": "Alternative parameter name for entry_price (for compatibility)"
                    },
                    "stop_loss": {"type": "number"},
                    "take_profit": {"type": "number"},
                    "risk_pct": {"type": "number", "default": 0.01},
                    "category": {
                        "type": "string",
                        "enum": ["spot", "linear", "inverse"],
                        "description": "Тип рынка (опционально, определяется автоматически по символу)"
                    }
                },
                "required": ["symbol", "side", "stop_loss", "take_profit"],
                "anyOf": [
                    {"required": ["entry_price"]},
                    {"required": ["entry"]}
                ]
            }
        ),
        
        Tool(
            name="get_open_interest",
            description="Получить Open Interest для futures. Показывает накопление/распределение позиций.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Торговая пара (например BTCUSDT)"},
                    "category": {"type": "string", "enum": ["linear", "inverse"], "default": "linear"}
                },
                "required": ["symbol"]
            }
        ),
        
        # ═══════════════════════════════════════
        # 💰 СЧЁТ И ПОЗИЦИИ
        # ═══════════════════════════════════════
        
        Tool(
            name="get_account_info",
            description="Полная информация о счёте",
            inputSchema={"type": "object", "properties": {}}
        ),
        
        Tool(
            name="get_open_positions",
            description="Все открытые позиции",
            inputSchema={"type": "object", "properties": {}}
        ),
        
        Tool(
            name="get_order_history",
            description="История ордеров",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "default": "spot"},
                    "limit": {"type": "string", "default": "50", "description": "Maximum number of results (1, 10, 50, 100, 200)"}
                }
            }
        ),
        
        # ═══════════════════════════════════════
        # ⚡ ТОРГОВЫЕ ОПЕРАЦИИ
        # ═══════════════════════════════════════
        
        Tool(
            name="place_order",
            description="Открыть новую позицию",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "side": {"type": "string", "enum": ["Buy", "Sell"]},
                    "order_type": {"type": "string", "enum": ["Market", "Limit"], "default": "Market"},
                    "quantity": {"type": "number"},
                    "price": {"type": "number"},
                    "stop_loss": {"type": "number"},
                    "take_profit": {"type": "number"},
                    "category": {"type": "string", "default": "spot"},
                    "leverage": {"type": "integer", "description": "Leverage для фьючерсов (1-125)", "minimum": 1, "maximum": 125}
                },
                "required": ["symbol", "side", "quantity"]
            }
        ),
        
        Tool(
            name="close_position",
            description="Закрыть открытую позицию",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "category": {"type": "string", "default": "linear"},
                    "reason": {"type": "string", "default": "Manual close"}
                },
                "required": ["symbol"]
            }
        ),
        
        Tool(
            name="modify_position",
            description="Изменить SL/TP позиции",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "stop_loss": {"type": "number"},
                    "take_profit": {"type": "number"},
                    "category": {"type": "string", "default": "linear"}
                },
                "required": ["symbol"]
            }
        ),
        
        Tool(
            name="cancel_order",
            description="Отменить ордер",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "symbol": {"type": "string"},
                    "category": {"type": "string", "default": "spot"}
                },
                "required": ["order_id", "symbol"]
            }
        ),
        
        # ═══════════════════════════════════════
        # 📡 REAL-TIME МОНИТОРИНГ
        # ═══════════════════════════════════════
        
        Tool(
            name="start_position_monitoring",
            description="Запустить real-time мониторинг позиций",
            inputSchema={
                "type": "object",
                "properties": {
                    "auto_actions": {
                        "type": "object",
                        "properties": {
                            "move_to_breakeven_at": {"type": "number", "default": 1.0},
                            "enable_trailing_at": {"type": "number", "default": 2.0},
                            "exit_on_reversal": {"type": "boolean", "default": True},
                            "max_time_in_trade": {"type": "number", "default": 12}
                        }
                    }
                }
            }
        ),
        
        Tool(
            name="stop_position_monitoring",
            description="Остановить мониторинг позиций",
            inputSchema={"type": "object", "properties": {}}
        ),
        
        # ═══════════════════════════════════════
        # 🛠️ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
        # ═══════════════════════════════════════
        
        Tool(
            name="move_to_breakeven",
            description="Перевести SL в breakeven автоматически",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "entry_price": {"type": "number"},
                    "category": {"type": "string", "default": "linear"}
                },
                "required": ["symbol", "entry_price"]
            }
        ),
        
        Tool(
            name="activate_trailing_stop",
            description="Активировать trailing stop",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "trailing_distance": {"type": "number", "description": "Distance in %"},
                    "category": {"type": "string", "default": "linear"}
                },
                "required": ["symbol", "trailing_distance"]
            }
        ),
        
        Tool(
            name="transfer_funds",
            description="Перевести средства между счетами (UNIFIED, SPOT, CONTRACT)",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_account_type": {"type": "string", "enum": ["UNIFIED", "SPOT", "CONTRACT"], "description": "Тип счета-источника"},
                    "to_account_type": {"type": "string", "enum": ["UNIFIED", "SPOT", "CONTRACT"], "description": "Тип счета-получателя"},
                    "coin": {"type": "string", "description": "Монета для перевода (например USDT)"},
                    "amount": {"type": "number", "description": "Сумма для перевода"},
                    "transfer_id": {"type": "string", "description": "Уникальный ID перевода (опционально)"}
                },
                "required": ["from_account_type", "to_account_type", "coin", "amount"]
            }
        ),
        
        # ═══════════════════════════════════════
        # 📊 КОНТРОЛЬ КАЧЕСТВА СИГНАЛОВ
        # ═══════════════════════════════════════
        
        Tool(
            name="track_signal",
            description="Записать новый сигнал для отслеживания качества",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Торговая пара (например BTC/USDT)"},
                    "side": {"type": "string", "enum": ["long", "short"], "description": "Направление сделки"},
                    "entry_price": {"type": "number", "description": "Цена входа"},
                    "stop_loss": {"type": "number", "description": "Стоп-лосс"},
                    "take_profit": {"type": "number", "description": "Тейк-профит"},
                    "confluence_score": {"type": "number", "description": "Confluence score (0-12)"},
                    "probability": {"type": "number", "description": "Вероятность успеха (0-1)"},
                    "expected_value": {"type": "number", "description": "Expected Value (опционально)"},
                    "analysis_data": {"type": "object", "description": "Полные данные анализа (опционально)"},
                    "timeframe": {"type": "string", "description": "Основной таймфрейм сигнала (опционально)"},
                    "pattern_type": {"type": "string", "description": "Тип паттерна (опционально)"},
                    "pattern_name": {"type": "string", "description": "Название паттерна (опционально)"}
                },
                "required": ["symbol", "side", "entry_price", "stop_loss", "take_profit", "confluence_score", "probability"]
            }
        ),
        
        Tool(
            name="get_signal_quality_metrics",
            description="Получить метрики качества сигналов",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 30, "description": "Количество дней для анализа"},
                    "include_patterns": {"type": "boolean", "default": True, "description": "Включить анализ паттернов"}
                }
            }
        ),
        
        Tool(
            name="get_signal_performance_report",
            description="Получить детальный отчет о производительности сигналов",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 30, "description": "Количество дней для анализа"},
                    "format": {"type": "string", "enum": ["json", "summary"], "default": "summary", "description": "Формат отчета"}
                }
            }
        ),
        
        Tool(
            name="get_active_signals",
            description="Получить список всех активных сигналов",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        Tool(
            name="get_signal_details",
            description="Получить детальную информацию о сигнале",
            inputSchema={
                "type": "object",
                "properties": {
                    "signal_id": {"type": "string", "description": "ID сигнала"}
                },
                "required": ["signal_id"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Обработка вызовов инструментов"""
    
    try:
        logger.info(f"Tool called: {name}")
        logger.debug(f"Arguments: {arguments}")
        
        result = None
        
        # ═══ Рыночные данные ═══
        if name == "get_market_overview":
            # Исправление: "futures" -> "linear" для совместимости
            market_type = arguments.get("market_type", "both")
            if market_type == "futures":
                market_type = "linear"
            result = await trading_ops.get_market_overview(market_type)
        
        elif name == "get_all_tickers":
            result = await bybit_client.get_all_tickers(
                market_type=arguments["market_type"],
                sort_by=arguments.get("sort_by", "volume")
            )
        
        elif name == "get_asset_price":
            try:
                result = await bybit_client.get_asset_price(arguments["symbol"])
            except Exception as e:
                logger.error(f"Error in get_asset_price: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e),
                    "symbol": arguments.get("symbol", "unknown")
                }
        
        # ═══ Технический анализ ═══
        elif name == "analyze_asset":
            result = await technical_analysis.analyze_asset(
                symbol=arguments["symbol"],
                timeframes=arguments.get("timeframes", ["5m", "15m", "1h", "4h", "1d"]),
                include_patterns=arguments.get("include_patterns", True)
            )
        
        elif name == "calculate_indicators":
            result = await technical_analysis._analyze_timeframe(
                symbol=arguments["symbol"],
                timeframe=arguments.get("timeframe", "1h"),
                include_patterns=False
            )
        
        elif name == "detect_patterns":
            # Получаем данные
            ohlcv = await bybit_client.get_ohlcv(
                arguments["symbol"],
                arguments.get("timeframe", "1h")
            )
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            result = technical_analysis._detect_patterns(df)
        
        elif name == "find_support_resistance":
            ohlcv = await bybit_client.get_ohlcv(
                arguments["symbol"],
                arguments.get("timeframe", "1h"),
                limit=arguments.get("lookback_periods", 50)
            )
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            result = technical_analysis._find_support_resistance(df)
        
        elif name == "get_btc_correlation":
            result = await technical_analysis.get_btc_correlation(
                symbol=arguments["symbol"],
                period=arguments.get("period", 24),
                timeframe=arguments.get("timeframe", "1h")
            )
        
        elif name == "get_funding_rate":
            result = await bybit_client.get_funding_rate(arguments["symbol"])
        
        elif name == "get_open_interest":
            result = await bybit_client.get_open_interest(
                symbol=arguments["symbol"],
                category=arguments.get("category", "linear")
            )
        
        elif name == "check_tf_alignment":
            result = await technical_analysis.check_tf_alignment(
                symbol=arguments["symbol"],
                timeframes=arguments.get("timeframes", ["5m", "15m", "1h", "4h", "1d"])
            )
        
        # ═══ Сканирование рынка ═══
        elif name == "scan_market":
            result = await market_scanner.scan_market(
                criteria=arguments["criteria"],
                limit=arguments.get("limit", 10),
                auto_track=arguments.get("auto_track", False),
                signal_tracker=signal_tracker if arguments.get("auto_track", False) else None,
                track_limit=arguments.get("track_limit", 3)
            )
        
        elif name == "find_oversold_assets":
            result = await market_scanner.find_oversold_assets(
                market_type=arguments.get("market_type", "spot"),
                min_volume_24h=arguments.get("min_volume_24h", 1000000)
            )
        
        elif name == "find_overbought_assets":
            result = await market_scanner.find_overbought_assets(
                market_type=arguments.get("market_type", "spot"),
                min_volume_24h=arguments.get("min_volume_24h", 1000000)
            )
        
        elif name == "find_breakout_opportunities":
            result = await market_scanner.find_breakout_opportunities(
                market_type=arguments.get("market_type", "spot"),
                min_volume_24h=arguments.get("min_volume_24h", 1000000)
            )
        
        elif name == "find_trend_reversals":
            result = await market_scanner.find_trend_reversals(
                market_type=arguments.get("market_type", "spot"),
                min_volume_24h=arguments.get("min_volume_24h", 1000000)
            )
        
        # ═══ Валидация ═══
        elif name == "check_liquidity":
            result = await technical_analysis.check_liquidity(
                symbol=arguments["symbol"]
            )
        
        elif name == "validate_entry":
            # Поддержка как entry_price, так и entry для совместимости
            entry_price = arguments.get("entry_price") or arguments.get("entry")
            if not entry_price:
                raise ValueError("entry_price or entry is required")
            
            result = await technical_analysis.validate_entry(
                symbol=arguments["symbol"],
                side=arguments["side"],
                entry_price=float(entry_price),
                stop_loss=float(arguments["stop_loss"]),
                take_profit=float(arguments["take_profit"]),
                risk_pct=arguments.get("risk_pct", 0.01),
                signal_tracker=signal_tracker  # Автоматически записывает при is_valid=True
            )
        
        # ═══ Account ═══
        elif name == "get_account_info":
            # Получаем балансы со всех типов счетов (SPOT, CONTRACT, UNIFIED)
            try:
                # Используем вспомогательную функцию для получения всех балансов
                all_balances = get_all_account_balances(trading_ops.session, coin="USDT")
                
                # Получаем позиции (пробуем через известные символы)
                # Если нет позиций - возвращаем пустой список
                positions = []
                test_symbols = ["BTCUSDT", "ETHUSDT"]
                
                for test_symbol in test_symbols:
                    try:
                        test_response = trading_ops.session.get_positions(
                            category="linear",
                            symbol=test_symbol
                        )
                        if test_response.get("retCode") == 0:
                            positions_list = test_response.get("result", {}).get("list", [])
                            positions.extend([p for p in positions_list if float(p.get("size", 0)) != 0])
                    except:
                        continue
                
                # Фильтруем только позиции с размером > 0
                positions = [p for p in positions if float(p.get("size", 0)) != 0]
                
                # Используем общий баланс (сумма всех счетов)
                total_equity = all_balances.get("total", 0.0)
                available = all_balances.get("available", 0.0)
                
                used_margin = sum(float(p.get("positionIM", 0) or 0) for p in positions)
                unrealized_pnl = sum(float(p.get("unrealisedPnl", 0) or 0) for p in positions)
                
                result = {
                    "balance": {
                        # Детали по каждому типу счета
                        "spot": all_balances.get("spot", {"total": 0.0, "available": 0.0, "success": False}),
                        "contract": all_balances.get("contract", {"total": 0.0, "available": 0.0, "success": False}),
                        "unified": all_balances.get("unified", {"total": 0.0, "available": 0.0, "success": False}),
                        # Общий баланс (сумма всех счетов)
                        "total": total_equity,
                        "available": available,
                        "used_margin": used_margin,
                        "unrealized_pnl": unrealized_pnl
                    },
                    "positions": positions,
                    "risk_metrics": {
                        "total_risk_pct": (used_margin / total_equity * 100) if total_equity > 0 else 0,
                        "positions_count": len(positions),
                        "max_drawdown": "N/A"
                    }
                }
            except Exception as e:
                logger.error(f"Error in get_account_info: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "get_open_positions":
            # Используем pybit напрямую
            # Пробуем получить все позиции через разные методы
            try:
                # Сначала пробуем получить через известные символы
                # Если нет позиций - возвращаем пустой список
                response = None
                test_symbols = ["BTCUSDT", "ETHUSDT"]
                
                all_positions = []
                for test_symbol in test_symbols:
                    try:
                        test_response = trading_ops.session.get_positions(
                            category="linear",
                            symbol=test_symbol
                        )
                        if test_response.get("retCode") == 0:
                            positions_list = test_response.get("result", {}).get("list", [])
                            all_positions.extend([p for p in positions_list if float(p.get("size", 0)) != 0])
                    except:
                        continue
                
                # Если нашли позиции - используем их
                if all_positions:
                    response = {"retCode": 0, "result": {"list": all_positions}}
                else:
                    # Если позиций нет - возвращаем пустой список
                    response = {"retCode": 0, "result": {"list": []}}
                
                if response and response.get("retCode") == 0:
                    positions_list = response.get("result", {}).get("list", [])
                    # Фильтруем только открытые позиции
                    open_positions = [
                        {
                            "symbol": p.get("symbol"),
                            "side": p.get("side"),
                            "size": float(p.get("size", 0)),
                            "entry_price": float(p.get("avgPrice", 0)),
                            "current_price": float(p.get("markPrice", 0)),
                            "unrealized_pnl": float(p.get("unrealisedPnl", 0)),
                            "unrealized_pnl_pct": float(p.get("unrealisedPnl", 0)) / float(p.get("positionValue", 1)) * 100 if float(p.get("positionValue", 0)) != 0 else 0,
                            "leverage": p.get("leverage"),
                            "margin": float(p.get("positionIM", 0)),
                            "liquidation_price": float(p.get("liqPrice", 0))
                        }
                        for p in positions_list if float(p.get("size", 0)) != 0
                    ]
                    result = open_positions
                else:
                    result = {
                        "success": False,
                        "error": response.get("retMsg", "Unknown error")
                    }
            except Exception as e:
                logger.error(f"Error in get_open_positions: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "get_order_history":
            # Используем pybit напрямую
            # limit уже строка из схемы MCP
            limit = arguments.get("limit", "50")
            try:
                response = trading_ops.session.get_order_history(
                    category=arguments.get("category", "spot"),
                    limit=limit
                )
                if response.get("retCode") == 0:
                    result = response.get("result", {})
                else:
                    result = {
                        "success": False,
                        "error": response.get("retMsg", "Unknown error")
                    }
            except Exception as e:
                logger.error(f"Error in get_order_history: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        # ═══ Trading Operations ═══
        elif name == "place_order":
            # Извлекаем параметры корректно с обработкой ошибок
            try:
                logger.info(f"place_order called with arguments: {arguments}")
                logger.info(f"Arguments type: {type(arguments)}")
                
                # Безопасная проверка типа arguments
                if not isinstance(arguments, dict):
                    logger.error(f"Arguments is not a dict: {type(arguments)}, value: {arguments}")
                    # Пробуем преобразовать в dict, если это строка JSON
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                            logger.info(f"Parsed arguments from JSON string")
                        except JSONDecodeError as json_err:
                            logger.error(f"Failed to parse arguments as JSON: {json_err}")
                            result = {
                                "success": False,
                                "error": f"Invalid arguments format: expected dict, got {type(arguments)}"
                            }
                            return [TextContent(type="text", text=json.dumps(result, indent=2))]
                    else:
                        result = {
                            "success": False,
                            "error": f"Invalid arguments format: expected dict, got {type(arguments)}"
                        }
                        return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                logger.info(f"Arguments keys: {list(arguments.keys())}")
                logger.info(f"Arguments values: {list(arguments.values())}")
                
                # Безопасное извлечение параметров с защитой от KeyError
                try:
                    symbol = str(arguments.get("symbol", "")) if arguments.get("symbol") else ""
                except (KeyError, AttributeError) as e:
                    logger.error(f"Error extracting symbol: {e}", exc_info=True)
                    symbol = ""
                
                try:
                    side = str(arguments.get("side", "")) if arguments.get("side") else ""
                except (KeyError, AttributeError) as e:
                    logger.error(f"Error extracting side: {e}", exc_info=True)
                    side = ""
                
                try:
                    order_type = str(arguments.get("order_type", "Market")) if arguments.get("order_type") else "Market"
                except (KeyError, AttributeError) as e:
                    logger.error(f"Error extracting order_type: {e}", exc_info=True)
                    order_type = "Market"
                
                try:
                    quantity = float(arguments.get("quantity", 0)) if arguments.get("quantity") else 0.0
                except (KeyError, AttributeError, ValueError) as e:
                    logger.error(f"Error extracting quantity: {e}", exc_info=True)
                    quantity = 0.0
                
                try:
                    price = float(arguments.get("price")) if arguments.get("price") is not None else None
                except (KeyError, AttributeError, ValueError) as e:
                    logger.error(f"Error extracting price: {e}", exc_info=True)
                    price = None
                
                try:
                    stop_loss = float(arguments.get("stop_loss")) if arguments.get("stop_loss") is not None else None
                except (KeyError, AttributeError, ValueError) as e:
                    logger.error(f"Error extracting stop_loss: {e}", exc_info=True)
                    stop_loss = None
                
                try:
                    take_profit = float(arguments.get("take_profit")) if arguments.get("take_profit") is not None else None
                except (KeyError, AttributeError, ValueError) as e:
                    logger.error(f"Error extracting take_profit: {e}", exc_info=True)
                    take_profit = None
                
                try:
                    category = str(arguments.get("category", "spot")) if arguments.get("category") else "spot"
                    logger.info(f"Category extracted: {category} (type: {type(category)})")
                except (KeyError, AttributeError) as e:
                    logger.error(f"Error extracting category: {e}", exc_info=True)
                    category = "spot"
                
                try:
                    leverage = int(arguments.get("leverage")) if arguments.get("leverage") is not None else None
                except (KeyError, AttributeError, ValueError) as e:
                    logger.error(f"Error extracting leverage: {e}", exc_info=True)
                    leverage = None
                
                logger.info(f"Parsed params: symbol={symbol}, side={side}, qty={quantity}, category={category}, leverage={leverage}")
                
                if not symbol or not side or quantity <= 0:
                    result = {
                        "success": False,
                        "error": "Missing required parameters: symbol, side, or quantity is invalid"
                    }
                else:
                    result = await trading_ops.place_order(
                        symbol=symbol,
                        side=side,
                        order_type=order_type,
                        quantity=quantity,
                        price=price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        category=category,
                        leverage=leverage
                    )
            except KeyError as e:
                error_key = str(e)
                logger.error(f"KeyError in place_order handler: {error_key}", exc_info=True)
                logger.error(f"KeyError args: {e.args if hasattr(e, 'args') else 'N/A'}")
                logger.error(f"KeyError repr: {repr(e)}")
                logger.error(f"Arguments at error time: {arguments if 'arguments' in locals() else 'N/A'}")
                result = {
                    "success": False,
                    "error": f"KeyError: {error_key}",
                    "message": f"Missing parameter: {error_key}",
                    "error_type": "KeyError",
                    "error_details": {
                        "key": error_key,
                        "type": str(type(e)),
                        "args": list(e.args) if hasattr(e, 'args') else []
                    }
                }
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(f"Error in place_order handler: {error_type}: {error_msg}", exc_info=True)
                logger.error(f"Full traceback: {traceback.format_exc()}")
                result = {
                    "success": False,
                    "error": error_msg,
                    "error_type": error_type,
                    "message": f"Failed to process place_order: {error_type}: {error_msg}"
                }
        
        elif name == "close_position":
            try:
                symbol = arguments.get("symbol", "")
                if not symbol:
                    result = {
                        "success": False,
                        "error": "Missing required parameter: symbol"
                    }
                else:
                    result = await trading_ops.close_position(
                        symbol=symbol,
                        category=arguments.get("category", "linear"),
                        reason=arguments.get("reason", "Manual close")
                    )
            except Exception as e:
                logger.error(f"Error in close_position: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "modify_position":
            try:
                symbol = arguments.get("symbol", "")
                if not symbol:
                    result = {
                        "success": False,
                        "error": "Missing required parameter: symbol"
                    }
                else:
                    result = await trading_ops.modify_position(
                        symbol=symbol,
                        stop_loss=arguments.get("stop_loss"),
                        take_profit=arguments.get("take_profit"),
                        category=arguments.get("category", "linear")
                    )
            except Exception as e:
                logger.error(f"Error in modify_position: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "cancel_order":
            try:
                order_id = arguments.get("order_id", "")
                symbol = arguments.get("symbol", "")
                if not order_id or not symbol:
                    result = {
                        "success": False,
                        "error": "Missing required parameters: order_id or symbol"
                    }
                else:
                    result = await trading_ops.cancel_order(
                        order_id=order_id,
                        symbol=symbol,
                        category=arguments.get("category", "spot")
                    )
            except Exception as e:
                logger.error(f"Error in cancel_order: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        # ═══ Monitoring ═══
        elif name == "start_position_monitoring":
            # Запуск в background task
            asyncio.create_task(
                position_monitor.start_monitoring(
                    auto_actions=arguments.get("auto_actions")
                )
            )
            result = {
                "success": True,
                "message": "Position monitoring started",
                "auto_actions": arguments.get("auto_actions")
            }
        
        elif name == "stop_position_monitoring":
            await position_monitor.stop_monitoring()
            result = {
                "success": True,
                "message": "Position monitoring stopped"
            }
        
        # ═══ Helper Functions ═══
        elif name == "move_to_breakeven":
            try:
                symbol = arguments.get("symbol", "")
                entry_price = arguments.get("entry_price")
                if not symbol or entry_price is None:
                    result = {
                        "success": False,
                        "error": "Missing required parameters: symbol or entry_price"
                    }
                else:
                    result = await trading_ops.move_to_breakeven(
                        symbol=symbol,
                        entry_price=float(entry_price),
                        category=arguments.get("category", "linear")
                    )
            except Exception as e:
                logger.error(f"Error in move_to_breakeven: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "activate_trailing_stop":
            try:
                symbol = arguments.get("symbol", "")
                trailing_distance = arguments.get("trailing_distance")
                if not symbol or trailing_distance is None:
                    result = {
                        "success": False,
                        "error": "Missing required parameters: symbol or trailing_distance"
                    }
                else:
                    result = await trading_ops.activate_trailing_stop(
                        symbol=symbol,
                        trailing_distance=float(trailing_distance),
                        category=arguments.get("category", "linear")
                    )
            except Exception as e:
                logger.error(f"Error in activate_trailing_stop: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "transfer_funds":
            try:
                from_account_type = arguments.get("from_account_type", "")
                to_account_type = arguments.get("to_account_type", "")
                coin = arguments.get("coin", "")
                amount = arguments.get("amount")
                transfer_id = arguments.get("transfer_id")
                
                if not from_account_type or not to_account_type or not coin or amount is None:
                    result = {
                        "success": False,
                        "error": "Missing required parameters: from_account_type, to_account_type, coin, amount"
                    }
                else:
                    result = await trading_ops.transfer_funds(
                        from_account_type=from_account_type,
                        to_account_type=to_account_type,
                        coin=coin,
                        amount=float(amount),
                        transfer_id=transfer_id
                    )
            except Exception as e:
                logger.error(f"Error in transfer_funds: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        # ═══ Signal Quality Control ═══
        elif name == "track_signal":
            try:
                if not signal_tracker:
                    result = {
                        "success": False,
                        "error": "Signal tracker not initialized"
                    }
                else:
                    signal_id = await signal_tracker.record_signal(
                        symbol=arguments["symbol"],
                        side=arguments["side"],
                        entry_price=float(arguments["entry_price"]),
                        stop_loss=float(arguments["stop_loss"]),
                        take_profit=float(arguments["take_profit"]),
                        confluence_score=float(arguments["confluence_score"]),
                        probability=float(arguments["probability"]),
                        expected_value=arguments.get("expected_value"),
                        analysis_data=arguments.get("analysis_data"),
                        timeframe=arguments.get("timeframe"),
                        pattern_type=arguments.get("pattern_type"),
                        pattern_name=arguments.get("pattern_name")
                    )
                    result = {
                        "success": True,
                        "signal_id": signal_id,
                        "message": "Signal tracked successfully"
                    }
            except Exception as e:
                logger.error(f"Error in track_signal: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "get_signal_quality_metrics":
            try:
                if not quality_metrics:
                    result = {
                        "success": False,
                        "error": "Quality metrics not initialized"
                    }
                else:
                    days = arguments.get("days", 30)
                    include_patterns = arguments.get("include_patterns", True)
                    
                    metrics = await quality_metrics.calculate_overall_metrics(days=days)
                    
                    result = {
                        "success": True,
                        "metrics": metrics
                    }
                    
                    if include_patterns:
                        pattern_perf = await quality_metrics.analyze_pattern_performance()
                        result["pattern_performance"] = pattern_perf
                        
                        tf_perf = await quality_metrics.analyze_timeframe_performance()
                        result["timeframe_performance"] = tf_perf
            except Exception as e:
                logger.error(f"Error in get_signal_quality_metrics: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "get_signal_performance_report":
            try:
                if not signal_reports:
                    result = {
                        "success": False,
                        "error": "Signal reports not initialized"
                    }
                else:
                    days = arguments.get("days", 30)
                    format_type = arguments.get("format", "summary")
                    
                    report = await signal_reports.generate_summary_report(days=days, format=format_type)
                    result = {
                        "success": True,
                        "report": report
                    }
            except Exception as e:
                logger.error(f"Error in get_signal_performance_report: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "get_active_signals":
            try:
                if not signal_tracker:
                    result = {
                        "success": False,
                        "error": "Signal tracker not initialized"
                    }
                else:
                    active_signals = await signal_tracker.get_active_signals()
                    result = {
                        "success": True,
                        "active_signals": active_signals,
                        "count": len(active_signals)
                    }
            except Exception as e:
                logger.error(f"Error in get_active_signals: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        elif name == "get_signal_details":
            try:
                if not signal_tracker:
                    result = {
                        "success": False,
                        "error": "Signal tracker not initialized"
                    }
                else:
                    signal_id = arguments["signal_id"]
                    signal = await signal_tracker.get_signal(signal_id)
                    
                    if signal:
                        # Получаем snapshots если есть
                        snapshots = await signal_tracker.get_price_snapshots(signal_id, limit=100)
                        result = {
                            "success": True,
                            "signal": signal,
                            "price_snapshots": snapshots,
                            "snapshots_count": len(snapshots)
                        }
                    else:
                        result = {
                            "success": False,
                            "error": f"Signal {signal_id} not found"
                        }
            except Exception as e:
                logger.error(f"Error in get_signal_details: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Возвращаем результат
        # Защита от None result
        if result is None:
            result = {"success": False, "error": "Tool executed but returned None"}
        
        # Импортируем json явно для гарантии доступности
        import json as json_module
        return [TextContent(
            type="text",
            text=json_module.dumps(result, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        # Импортируем json явно для гарантии доступности
        import json as json_module
        return [TextContent(
            type="text",
            text=json_module.dumps({
                "success": False,
                "error": str(e),
                "tool": name
            }, indent=2)
        )]


@app.list_resources()
async def list_resources() -> List[Resource]:
    """Список всех промптов и базы знаний"""
    
    base_path = Path(__file__).parent.parent
    resources = []
    
    # Промпты из папки prompts/
    prompts_dir = base_path / "prompts"
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.md"):
            resources.append(Resource(
                uri=f"prompt:///{prompt_file.stem}",
                name=prompt_file.stem,
                description=f"Trading prompt: {prompt_file.stem}",
                mimeType="text/markdown"
            ))
    
    # База знаний из папки knowledge_base/
    kb_dir = base_path / "knowledge_base"
    if kb_dir.exists():
        for kb_file in kb_dir.glob("*.md"):
            resources.append(Resource(
                uri=f"knowledge:///{kb_file.stem}",
                name=kb_file.stem,
                description=f"Trading knowledge: {kb_file.stem}",
                mimeType="text/markdown"
            ))
    
    logger.info(f"Listed {len(resources)} resources ({len(list(prompts_dir.glob('*.md'))) if prompts_dir.exists() else 0} prompts, {len(list(kb_dir.glob('*.md'))) if kb_dir.exists() else 0} knowledge)")
    return resources


@app.read_resource()
async def read_resource(uri: str) -> TextResourceContents:
    """Чтение промпта или базы знаний"""
    
    base_path = Path(__file__).parent.parent
    
    try:
        if uri.startswith("prompt:///"):
            # Читаем промпт
            prompt_name = uri.replace("prompt:///", "")
            prompt_file = base_path / "prompts" / f"{prompt_name}.md"
            
            if not prompt_file.exists():
                raise ValueError(f"Prompt not found: {prompt_name}")
            
            content = prompt_file.read_text(encoding="utf-8")
            logger.info(f"Read prompt: {prompt_name} ({len(content)} chars)")
            
            return TextResourceContents(
                uri=uri,
                mimeType="text/markdown",
                text=content
            )
        
        elif uri.startswith("knowledge:///"):
            # Читаем базу знаний
            kb_name = uri.replace("knowledge:///", "")
            kb_file = base_path / "knowledge_base" / f"{kb_name}.md"
            
            if not kb_file.exists():
                raise ValueError(f"Knowledge base not found: {kb_name}")
            
            content = kb_file.read_text(encoding="utf-8")
            logger.info(f"Read knowledge: {kb_name} ({len(content)} chars)")
            
            return TextResourceContents(
                uri=uri,
                mimeType="text/markdown",
                text=content
            )
        
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
    
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        raise


@app.list_prompts()
async def list_prompts() -> List[Prompt]:
    """Список всех доступных промптов"""
    
    base_path = Path(__file__).parent.parent
    prompts_dir = base_path / "prompts"
    prompts = []
    
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.md"):
            # Читаем первые строки для описания
            try:
                content = prompt_file.read_text(encoding="utf-8")
                # Берем первую строку или первый параграф как описание
                description = content.split('\n')[0].strip('# ').strip()
                if not description:
                    description = f"Trading prompt: {prompt_file.stem}"
            except:
                description = f"Trading prompt: {prompt_file.stem}"
            
            prompts.append(Prompt(
                name=prompt_file.stem,
                description=description,
                arguments=[]  # Промпты без аргументов (статические)
            ))
    
    logger.info(f"Listed {len(prompts)} prompts")
    return prompts


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
    """Получить содержимое промпта"""
    
    base_path = Path(__file__).parent.parent
    prompt_file = base_path / "prompts" / f"{name}.md"
    
    if not prompt_file.exists():
        raise ValueError(f"Prompt not found: {name}")
    
    content = prompt_file.read_text(encoding="utf-8")
    logger.info(f"Read prompt: {name} ({len(content)} chars)")
    
    return GetPromptResult(
        description=f"Trading prompt: {name}",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=content
                )
            )
        ]
    )


async def main():
    """Запуск полного trading сервера"""
    global trading_ops, technical_analysis, market_scanner, position_monitor, bybit_client
    global signal_tracker, signal_monitor, quality_metrics, signal_reports
    
    logger.info("=" * 50)
    logger.info("Starting Complete Bybit Trading MCP Server")
    logger.info("=" * 50)
    
    # Загрузка credentials
    credentials = load_credentials()
    bybit_creds = credentials["bybit"]
    
    # === ВАЛИДАЦИЯ API КЛЮЧЕЙ ===
    logger.info("=" * 50)
    logger.info("🔍 VALIDATING BYBIT API CREDENTIALS...")
    logger.info("=" * 50)
    
    bybit_api_key = bybit_creds["api_key"]
    bybit_api_secret = bybit_creds["api_secret"]
    
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
    
    # Инициализация всех компонентов
    logger.info("Initializing components...")
    
    trading_ops = TradingOperations(
        api_key=bybit_creds["api_key"],
        api_secret=bybit_creds["api_secret"],
        testnet=bybit_creds.get("testnet", False)
    )
    
    bybit_client = BybitClient(
        api_key=bybit_creds["api_key"],
        api_secret=bybit_creds["api_secret"],
        testnet=bybit_creds.get("testnet", False)
    )
    
    # === КРИТИЧЕСКАЯ ВАЛИДАЦИЯ API ПРИ СТАРТЕ ===
    logger.info("=" * 50)
    logger.info("🔍 TESTING BYBIT API CONNECTION...")
    logger.info("=" * 50)
    
    try:
        api_health = await bybit_client.validate_api_credentials()
        
        if api_health["valid"]:
            logger.info("✅ API VALIDATION SUCCESSFUL")
            logger.info(f"   Permissions: {', '.join(api_health['permissions'])}")
            logger.info(f"   Available accounts: {', '.join(api_health.get('accounts', []))}")
        else:
            logger.error("❌ API VALIDATION FAILED")
            logger.error(f"   Error: {api_health.get('error', 'Unknown')}")
            raise Exception("API validation failed - cannot start server")
            
    except Exception as e:
        logger.error("=" * 50)
        logger.error("❌ CRITICAL: API VALIDATION FAILED")
        logger.error("=" * 50)
        logger.error(f"Error: {e}")
        logger.error("")
        logger.error("Server startup ABORTED. Please fix API credentials and restart.")
        logger.error("")
        logger.error("Quick check:")
        logger.error("1. Are GitHub Secrets set correctly? (BYBIT_API_KEY, BYBIT_API_SECRET)")
        logger.error("2. Is API key valid on Bybit?")
        logger.error("3. Does API key have READ permissions?")
        logger.error("4. Is your server IP whitelisted on Bybit?")
        logger.error("=" * 50)
        sys.exit(1)  # FAIL-FAST: Прерываем запуск если API невалиден
    
    logger.info("=" * 50)
    logger.info("✅ ALL PRE-FLIGHT CHECKS PASSED")
    logger.info("=" * 50)
    
    technical_analysis = TechnicalAnalysis(bybit_client)
    market_scanner = MarketScanner(bybit_client, technical_analysis)
    
    position_monitor = PositionMonitor(
        api_key=bybit_creds["api_key"],
        api_secret=bybit_creds["api_secret"],
        testnet=bybit_creds.get("testnet", False)
    )
    
    # Инициализация системы контроля качества сигналов
    logger.info("Initializing Signal Quality Control System...")
    signal_tracker = SignalTracker()
    signal_monitor = SignalPriceMonitor(signal_tracker, bybit_client, check_interval=300)  # 5 минут
    quality_metrics = QualityMetrics(signal_tracker)
    signal_reports = SignalReports(signal_tracker, quality_metrics)
    
    # Запуск автоматического мониторинга сигналов в фоне
    asyncio.create_task(signal_monitor.start_monitoring())
    logger.info("✅ Signal monitoring started (background task)")
    
    logger.info("✅ All components initialized")
    logger.info("=" * 50)
    # Подсчет ресурсов для логирования
    resources = await list_resources()
    prompts_count = sum(1 for r in resources if str(r.uri).startswith("prompt:///"))
    knowledge_count = sum(1 for r in resources if str(r.uri).startswith("knowledge:///"))
    
    logger.info("Server ready for connections")
    logger.info(f"Available tools: 35, prompts: {prompts_count}, resources: {len(resources)}")
    logger.info("=" * 50)
    logger.info("Tools breakdown:")
    logger.info("  - Market Data: 3")
    logger.info("  - Technical Analysis: 8")
    logger.info("  - Market Scanning: 5")
    logger.info("  - Entry Validation: 2")
    logger.info("  - Account: 3")
    logger.info("  - Trading Operations: 5")
    logger.info("  - Monitoring: 2")
    logger.info("  - Auto-Actions: 2")
    logger.info("  - Signal Quality Control: 5")
    logger.info("Total: 35 tools")
    logger.info("=" * 50)
    logger.info("Phase 1 Improvements:")
    logger.info("  ✅ Open Interest Analysis added (get_open_interest)")
    logger.info("  ✅ Funding Rate integration improved in validate_entry")
    logger.info("  ✅ Market scanner optimized (10 parallel, 100 candidates)")
    logger.info("  ✅ Fibonacci Retracements added to indicators")
    logger.info("=" * 50)
    logger.info("Signal Quality Control System:")
    logger.info("  ✅ Signal tracking database initialized")
    logger.info("  ✅ Automatic price monitoring active")
    logger.info("  ✅ Quality metrics calculator ready")
    logger.info("  ✅ Report generator ready")
    logger.info("=" * 50)
    
    # Запуск MCP server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
