#!/usr/bin/env python3
"""
Complete Bybit Trading MCP Server
Полная реализация всех требуемых функций из MASTER_PROMPT
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from loguru import logger

from trading_operations import TradingOperations
from technical_analysis import TechnicalAnalysis
from market_scanner import MarketScanner
from position_monitor import PositionMonitor
from bybit_client import BybitClient


def json_serialize(obj: Any) -> Any:
    """Конвертировать объект в JSON-совместимый формат"""
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [json_serialize(item) for item in obj]
    else:
        return obj


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

# Инициализация MCP сервера
app = Server("bybit-trading-complete")

# Глобальные клиенты
trading_ops: Optional[TradingOperations] = None
technical_analysis: Optional[TechnicalAnalysis] = None
market_scanner: Optional[MarketScanner] = None
position_monitor: Optional[PositionMonitor] = None
bybit_client: Optional[BybitClient] = None


def load_credentials() -> Dict[str, Any]:
    """Загрузка credentials"""
    config_path = Path(__file__).parent.parent / "config" / "credentials.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Credentials not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        raise


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
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["criteria"]
            }
        ),
        
        Tool(
            name="find_oversold_assets",
            description="Найти перепроданные активы (RSI <30)",
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
            name="validate_entry",
            description="Валидация точки входа с полной оценкой",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "side": {"type": "string", "enum": ["long", "short"]},
                    "entry_price": {"type": "number"},
                    "stop_loss": {"type": "number"},
                    "take_profit": {"type": "number"},
                    "risk_pct": {"type": "number", "default": 0.01}
                },
                "required": ["symbol", "side", "entry_price", "stop_loss", "take_profit"]
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
                    "limit": {"type": "integer", "default": 50}
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
                    "category": {"type": "string", "default": "spot"}
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
            result = await trading_ops.get_market_overview(
                arguments.get("market_type", "both")
            )
        
        elif name == "get_all_tickers":
            result = await bybit_client.get_all_tickers(
                market_type=arguments["market_type"],
                sort_by=arguments.get("sort_by", "volume")
            )
        
        elif name == "get_asset_price":
            result = await bybit_client.get_asset_price(arguments["symbol"])
        
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
            import pandas as pd
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            result = technical_analysis._detect_patterns(df)
        
        elif name == "find_support_resistance":
            ohlcv = await bybit_client.get_ohlcv(
                arguments["symbol"],
                arguments.get("timeframe", "1h"),
                limit=arguments.get("lookback_periods", 50)
            )
            import pandas as pd
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            result = technical_analysis._find_support_resistance(df)
        
        # ═══ Сканирование рынка ═══
        elif name == "scan_market":
            result = await market_scanner.scan_market(
                criteria=arguments["criteria"],
                limit=arguments.get("limit", 10)
            )
        
        elif name == "find_oversold_assets":
            result = await market_scanner.find_oversold_assets(
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
        elif name == "validate_entry":
            result = await technical_analysis.validate_entry(
                symbol=arguments["symbol"],
                side=arguments["side"],
                entry_price=arguments["entry_price"],
                stop_loss=arguments["stop_loss"],
                take_profit=arguments["take_profit"],
                risk_pct=arguments.get("risk_pct", 0.01)
            )
        
        # ═══ Account ═══
        elif name == "get_account_info":
            result = await bybit_client.get_account_info()
        
        elif name == "get_open_positions":
            result = await bybit_client.get_open_positions()
        
        elif name == "get_order_history":
            # Используем pybit напрямую
            limit = arguments.get("limit", 50)
            # Конвертируем в строку если нужно
            limit_str = str(limit) if isinstance(limit, (int, float)) else limit
            response = trading_ops.session.get_order_history(
                category=arguments.get("category", "spot"),
                limit=limit_str
            )
            result = response.get("result", {})
        
        # ═══ Trading Operations ═══
        elif name == "place_order":
            # Извлекаем параметры корректно
            logger.info(f"place_order called with arguments: {arguments}")
            result = await trading_ops.place_order(
                symbol=str(arguments.get("symbol", "")),
                side=str(arguments.get("side", "")),
                order_type=str(arguments.get("order_type", "Market")),
                quantity=float(arguments.get("quantity", 0)),
                price=float(arguments["price"]) if arguments.get("price") else None,
                stop_loss=float(arguments["stop_loss"]) if arguments.get("stop_loss") else None,
                take_profit=float(arguments["take_profit"]) if arguments.get("take_profit") else None,
                category=str(arguments.get("category", "spot"))
            )
        
        elif name == "close_position":
            result = await trading_ops.close_position(
                symbol=arguments["symbol"],
                category=arguments.get("category", "linear"),
                reason=arguments.get("reason", "Manual close")
            )
        
        elif name == "modify_position":
            result = await trading_ops.modify_position(
                symbol=arguments["symbol"],
                stop_loss=arguments.get("stop_loss"),
                take_profit=arguments.get("take_profit"),
                category=arguments.get("category", "linear")
            )
        
        elif name == "cancel_order":
            result = await trading_ops.cancel_order(
                order_id=arguments["order_id"],
                symbol=arguments["symbol"],
                category=arguments.get("category", "spot")
            )
        
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
            result = await trading_ops.move_to_breakeven(
                symbol=arguments["symbol"],
                entry_price=arguments["entry_price"],
                category=arguments.get("category", "linear")
            )
        
        elif name == "activate_trailing_stop":
            result = await trading_ops.activate_trailing_stop(
                symbol=arguments["symbol"],
                trailing_distance=arguments["trailing_distance"],
                category=arguments.get("category", "linear")
            )
        
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Возвращаем результат (конвертируем все типы в JSON-совместимые)
        serialized_result = json_serialize(result)
        return [TextContent(
            type="text",
            text=json.dumps(serialized_result, indent=2, ensure_ascii=False)
        )]
        
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "tool": name
            }, indent=2)
        )]


async def main():
    """Запуск полного trading сервера"""
    global trading_ops, technical_analysis, market_scanner, position_monitor, bybit_client
    
    logger.info("=" * 50)
    logger.info("Starting Complete Bybit Trading MCP Server")
    logger.info("=" * 50)
    
    # Загрузка credentials
    credentials = load_credentials()
    bybit_creds = credentials["bybit"]
    
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
    
    technical_analysis = TechnicalAnalysis(bybit_client)
    market_scanner = MarketScanner(bybit_client, technical_analysis)
    
    position_monitor = PositionMonitor(
        api_key=bybit_creds["api_key"],
        api_secret=bybit_creds["api_secret"],
        testnet=bybit_creds.get("testnet", False)
    )
    
    logger.info("✅ All components initialized")
    logger.info("=" * 50)
    logger.info("Server ready for connections")
    logger.info("Available tools: 23")
    logger.info("=" * 50)
    logger.info("Tools breakdown:")
    logger.info("  - Market Data: 3")
    logger.info("  - Technical Analysis: 5")
    logger.info("  - Market Scanning: 4")
    logger.info("  - Account: 3")
    logger.info("  - Trading Operations: 4")
    logger.info("  - Monitoring: 2")
    logger.info("  - Auto-Actions: 2")
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
