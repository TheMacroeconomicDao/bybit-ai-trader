"""
Autonomous Market Analyzer
Автономный агент для анализа рынка и поиска топовых точек входа
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

# Импорты из существующей системы
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.bybit_client import BybitClient
from mcp_server.technical_analysis import TechnicalAnalysis
from mcp_server.market_scanner import MarketScanner
from autonomous_agent.qwen_client import QwenClient
from mcp_server.score_normalizer import normalize_opportunity_score, validate_score_fields

# Advanced features imports
try:
    from mcp_server.whale_detector import WhaleDetector
    from mcp_server.volume_profile import VolumeProfileAnalyzer
    from mcp_server.session_manager import SessionManager
    from mcp_server.ml_predictor import MLPredictor
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    WhaleDetector = None
    VolumeProfileAnalyzer = None
    SessionManager = None
    MLPredictor = None

# ORB Strategy import
try:
    from mcp_server.orb_strategy import OpeningRangeBreakout
    ORB_AVAILABLE = True
except ImportError:
    ORB_AVAILABLE = False
    OpeningRangeBreakout = None

# Опциональный импорт для signal tracking
try:
    from mcp_server.signal_tracker import SignalTracker
    SIGNAL_TRACKING_AVAILABLE = True
except ImportError:
    SIGNAL_TRACKING_AVAILABLE = False
    SignalTracker = None

# Импорты для полной интеграции (Фаза 1)
try:
    from mcp_server.trading_operations import TradingOperations, get_all_account_balances
    TRADING_OPERATIONS_AVAILABLE = True
except ImportError:
    TRADING_OPERATIONS_AVAILABLE = False
    TradingOperations = None
    get_all_account_balances = None

try:
    from mcp_server.quality_metrics import QualityMetrics
    QUALITY_METRICS_AVAILABLE = True
except ImportError:
    QUALITY_METRICS_AVAILABLE = False
    QualityMetrics = None

try:
    from mcp_server.cache_manager import cached, get_cache_manager
    CACHE_MANAGER_AVAILABLE = True
except ImportError:
    CACHE_MANAGER_AVAILABLE = False
    cached = lambda ttl: lambda f: f  # No-op decorator
    get_cache_manager = None


class AutonomousAnalyzer:
    """Автономный анализатор рынка с Qwen AI"""
    
    def __init__(
        self,
        qwen_api_key: str,
        bybit_api_key: str,
        bybit_api_secret: str,
        qwen_model: str = "qwen/qwen-turbo",  # OpenRouter формат
        testnet: bool = False,
        signal_tracker: Optional[SignalTracker] = None,
        auto_trade: bool = False  # НОВЫЙ параметр для автоматической торговли
    ):
        """
        Инициализация автономного анализатора
        
        Args:
            qwen_api_key: API ключ Alibaba Cloud Qwen
            bybit_api_key: API ключ Bybit
            bybit_api_secret: API секрет Bybit
            qwen_model: Модель Qwen для использования
            testnet: Использовать testnet для Bybit
            signal_tracker: Опциональный SignalTracker для записи сигналов
            auto_trade: Включить автоматическое исполнение сделок
        """
        # Инициализация Qwen клиента
        self.qwen = QwenClient(qwen_api_key, qwen_model)
        
        # Инициализация Bybit клиента и компонентов анализа
        self.bybit_client = BybitClient(bybit_api_key, bybit_api_secret, testnet)
        self.technical_analysis = TechnicalAnalysis(self.bybit_client)
        self.market_scanner = MarketScanner(self.bybit_client, self.technical_analysis)
        
        # Advanced features (Whale, Volume Profile, Session, ML Predictor)
        self.whale_detector = None
        self.volume_profile = None
        self.session_manager = None
        self.ml_predictor = None
        if ADVANCED_FEATURES_AVAILABLE:
            self.whale_detector = WhaleDetector(self.bybit_client)
            self.volume_profile = VolumeProfileAnalyzer(self.bybit_client)
            self.session_manager = SessionManager()
            if MLPredictor:
                self.ml_predictor = MLPredictor()
            logger.info("Advanced features initialized (Whale, VP, Session, ML)")
        
        # ORB Strategy (если доступна)
        self.orb_strategy = None
        if ORB_AVAILABLE and OpeningRangeBreakout:
            self.orb_strategy = OpeningRangeBreakout(self.bybit_client, self.technical_analysis)
            logger.info("ORB Strategy initialized")
        
        # Signal tracker для контроля качества (создаём по умолчанию если доступен)
        if signal_tracker is None and SIGNAL_TRACKING_AVAILABLE:
            signal_tracker = SignalTracker("data/signals.db")
            logger.info("SignalTracker created automatically")
        
        self.signal_tracker = signal_tracker
        if self.signal_tracker:
            logger.info("Signal tracking enabled")
        
        # TradingOperations для автоматической торговли (Фаза 1)
        self.trading_ops = None
        self.auto_trade = auto_trade
        if TRADING_OPERATIONS_AVAILABLE:
            self.trading_ops = TradingOperations(
                bybit_api_key,
                bybit_api_secret,
                testnet
            )
            logger.info(f"Trading Operations initialized (auto_trade={auto_trade})")
        elif auto_trade:
            logger.warning("TradingOperations not available, auto_trade disabled")
            self.auto_trade = False
        
        # QualityMetrics для анализа эффективности (Фаза 2)
        self.quality_metrics = None
        if QUALITY_METRICS_AVAILABLE and self.signal_tracker:
            self.quality_metrics = QualityMetrics(self.signal_tracker)
            logger.info("Quality Metrics initialized")
        
        # CacheManager для оптимизации (Фаза 3)
        self.cache_manager = None
        if CACHE_MANAGER_AVAILABLE:
            self.cache_manager = get_cache_manager()
            logger.info("Cache Manager initialized")
        
        # Загружаем системные инструкции
        self.system_instructions = self._load_system_instructions()
        
        logger.info("Autonomous Analyzer initialized (full integration)")
    
    def _load_system_instructions(self) -> str:
        """Загрузка системных инструкций для Qwen"""
        base_path = Path(__file__).parent.parent
        
        # Читаем основные инструкции
        instructions_parts = []
        
        # Core instructions (ОБЯЗАТЕЛЬНО)
        core_file = base_path / "prompts" / "agent_core_instructions.md"
        if core_file.exists():
            instructions_parts.append(f"=== CORE INSTRUCTIONS ===\n{core_file.read_text(encoding='utf-8')}\n")
        
        # Market Analysis Protocol (КРИТИЧНО для анализа)
        protocol_file = base_path / "prompts" / "market_analysis_protocol_optimized.md"
        if protocol_file.exists():
            instructions_parts.append(f"=== MARKET ANALYSIS PROTOCOL ===\n{protocol_file.read_text(encoding='utf-8')}\n")
        else:
            # Fallback на обычный протокол
            protocol_file = base_path / "prompts" / "market_analysis_protocol.md"
            if protocol_file.exists():
                instructions_parts.append(f"=== MARKET ANALYSIS PROTOCOL ===\n{protocol_file.read_text(encoding='utf-8')}\n")
        
        # Entry Decision Framework (КРИТИЧНО для принятия решений)
        entry_framework_file = base_path / "prompts" / "entry_decision_framework.md"
        if entry_framework_file.exists():
            instructions_parts.append(f"=== ENTRY DECISION FRAMEWORK ===\n{entry_framework_file.read_text(encoding='utf-8')}\n")
        
        # Position Monitoring Protocol (для управления позициями)
        position_monitoring_file = base_path / "prompts" / "position_monitoring_protocol.md"
        if position_monitoring_file.exists():
            instructions_parts.append(f"=== POSITION MONITORING PROTOCOL ===\n{position_monitoring_file.read_text(encoding='utf-8')}\n")
        
        # Zero risk methodology (из knowledge_base)
        zero_risk_file = base_path / "knowledge_base" / "7_zero_risk_methodology.md"
        if zero_risk_file.exists():
            instructions_parts.append(f"=== ZERO RISK METHODOLOGY ===\n{zero_risk_file.read_text(encoding='utf-8')}\n")
        
        # Market analysis framework (из knowledge_base)
        analysis_file = base_path / "knowledge_base" / "6_market_analysis_framework.md"
        if analysis_file.exists():
            instructions_parts.append(f"=== MARKET ANALYSIS FRAMEWORK ===\n{analysis_file.read_text(encoding='utf-8')}\n")
        
        # Entry strategies (из knowledge_base)
        entry_file = base_path / "knowledge_base" / "4_entry_strategies.md"
        if entry_file.exists():
            instructions_parts.append(f"=== ENTRY STRATEGIES ===\n{entry_file.read_text(encoding='utf-8')}\n")
        
        full_instructions = "\n".join(instructions_parts)
        
        # Добавляем специфичные инструкции для автономного агента
        autonomous_instructions = """
=== AUTONOMOUS AGENT MODE ===

Ты - автономный торговый агент, который анализирует криптовалютный рынок и находит ТОП 3 лучших ЛОНГА и ТОП 3 лучших ШОРТА.

ТВОЯ ЗАДАЧА:
1. Проанализировать предоставленные рыночные данные
2. Найти ТОП 3 ЛОНГА с confluence ≥ 8.0/10
3. Найти ТОП 3 ШОРТА с confluence ≥ 8.0/10
4. Вероятность успеха ≥ 70% для каждой возможности
5. R:R минимум 1:2 для каждой возможности
6. Детально объяснить каждую возможность

КРИТИЧЕСКИ ВАЖНО:
- НЕ предлагай возможности с confluence < 8.0
- Разделяй ЛОНГИ и ШОРТЫ отдельно
- Для ЛОНГОВ ищи oversold условия, поддержки, bullish паттерны
- Для ШОРТОВ ищи overbought условия, сопротивления, bearish паттерны
- НЕ предлагай возможности с вероятностью < 70%
- НЕ предлагай возможности с R:R < 1:2
- Всегда проверяй BTC статус перед рекомендацией altcoins
- Используй multi-timeframe анализ
- Объясняй ДЕТАЛЬНО почему именно эта возможность

ФОРМАТ ОТВЕТА:
Всегда возвращай валидный JSON с полями:
- top_longs: массив из 3 лучших ЛОНГОВ
- top_shorts: массив из 3 лучших ШОРТОВ
- market_summary: краткое резюме рынка
- btc_status: статус BTC
- recommendations: общие рекомендации

"""
        
        return full_instructions + "\n" + autonomous_instructions
    
    async def analyze_market(self) -> Dict[str, Any]:
        """
        Полный анализ рынка с поиском топовых точек входа
        
        Returns:
            Результаты анализа с топовыми возможностями
        """
        logger.info("Starting comprehensive market analysis...")
        
        try:
            # ШАГ 1: Получение market overview
            logger.info("Step 1: Getting market overview...")
            market_overview = await self.bybit_client.get_market_overview("both")
            
            # ШАГ 2: Анализ BTC
            logger.info("Step 2: Analyzing BTC...")
            btc_analysis = await self._analyze_btc()
            
            # ШАГ 3: Параллельное сканирование рынка
            logger.info("Step 3: Scanning market for opportunities...")
            opportunities = await self._scan_all_opportunities()
            
            # Получаем общее количество активов для статистики
            all_tickers = await self.bybit_client.get_all_tickers("spot")
            total_assets_scanned = len(all_tickers) if all_tickers else 0
            
            # ШАГ 4: Детальный анализ топ кандидатов
            logger.info("Step 4: Deep analysis of top candidates...")
            top_candidates = await self._deep_analyze_top_candidates(opportunities)
            
            # ШАГ 5: Анализ через Qwen (с graceful fallback)
            logger.info("Step 5: Qwen AI analysis...")
            market_data = {
                "market_overview": market_overview,
                "btc_analysis": btc_analysis,
                "scanned_opportunities": top_candidates,
                "timestamp": datetime.now().isoformat()
            }
            
            qwen_analysis = await self.qwen.analyze_market_opportunities(
                market_data=market_data,
                system_instructions=self.system_instructions
            )
            
            # НОВЫЙ GRACEFUL FALLBACK
            if not qwen_analysis.get("success"):
                if qwen_analysis.get("graceful_fallback"):
                    logger.warning(
                        f"Qwen AI analysis skipped: {qwen_analysis.get('message', 'Unknown reason')}. "
                        "Continuing with technical analysis only."
                    )
                    # Продолжаем без Qwen анализа
                    qwen_analysis = {
                        "success": False,
                        "graceful_fallback": True,
                        "message": qwen_analysis.get("message", "AI analysis unavailable")
                    }
                else:
                    logger.error(f"Qwen analysis failed: {qwen_analysis.get('error', 'Unknown error')}")
            
            # ШАГ 6: Фильтрация и ранжирование финальных возможностей
            logger.info("Step 6: Finalizing top 3 longs and top 3 shorts...")
            top_longs, top_shorts = await self._finalize_top_3_longs_and_shorts(
                top_candidates,
                qwen_analysis
            )
            
            # ШАГ 7: Запись сигналов для отслеживания качества (если tracker доступен)
            if self.signal_tracker:
                logger.info("Step 7: Recording signals for quality tracking...")
                tracked_signals = []
                
                # Записываем топ-3 лонги
                for long_signal in top_longs:
                    try:
                        signal_id = await self._record_signal_to_tracker(long_signal, "long")
                        if signal_id:
                            tracked_signals.append(signal_id)
                    except Exception as e:
                        logger.warning(f"Failed to track long signal {long_signal.get('symbol', 'unknown')}: {e}")
                
                # Записываем топ-3 шорты
                for short_signal in top_shorts:
                    try:
                        signal_id = await self._record_signal_to_tracker(short_signal, "short")
                        if signal_id:
                            tracked_signals.append(signal_id)
                    except Exception as e:
                        logger.warning(f"Failed to track short signal {short_signal.get('symbol', 'unknown')}: {e}")
                
                logger.info(f"Recorded {len(tracked_signals)} signals for quality tracking")
            
            # Разделяем все возможности на лонги и шорты для статистики
            all_longs = [opp for opp in top_candidates if opp.get("entry_plan", {}).get("side", "long") == "long"]
            all_shorts = [opp for opp in top_candidates if opp.get("entry_plan", {}).get("side", "long") == "short"]
            
            # ШАГ 7: Сохранить результаты для publish_market_analysis
            logger.info("Step 7: Saving scan results...")
            await self._save_scan_results(
                opportunities=top_candidates,
                longs=top_longs,
                shorts=top_shorts
            )
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "market_overview": market_overview,
                "btc_analysis": btc_analysis,
                "top_3_longs": top_longs,
                "top_3_shorts": top_shorts,
                "all_longs": all_longs[:10],  # Топ 10 для статистики
                "all_shorts": all_shorts[:10],  # Топ 10 для статистики
                "qwen_analysis": qwen_analysis,
                "total_scanned": total_assets_scanned,
                "total_analyzed": len(top_candidates),
                "potential_candidates": len(opportunities),
                "longs_found": len(all_longs),
                "shorts_found": len(all_shorts)
            }
        
        except Exception as e:
            logger.error(f"Error during market analysis: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _save_scan_results(
        self,
        opportunities: List[Dict[str, Any]],
        longs: List[Dict[str, Any]],
        shorts: List[Dict[str, Any]]
    ) -> None:
        """
        Сохранить результаты сканирования в JSON файлы для publish_market_analysis
        
        Args:
            opportunities: Все найденные возможности
            longs: Топ 3 лонга
            shorts: Топ 3 шорта
        """
        try:
            from pathlib import Path
            import json
            from datetime import datetime
            
            # Создаём директорию data если не существует
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            
            # Генерируем имя файла с timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = data_dir / f"scan_results_{timestamp}.json"
            
            # Подготавливаем данные для сохранения
            # Нормализуем все opportunities перед сохранением
            normalized_opportunities = [
                normalize_opportunity_score(opp.copy())
                for opp in opportunities
            ]
            
            normalized_longs = [
                normalize_opportunity_score(opp.copy())
                for opp in longs
            ]
            
            normalized_shorts = [
                normalize_opportunity_score(opp.copy())
                for opp in shorts
            ]
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "total_opportunities": len(normalized_opportunities),
                "longs_count": len(normalized_longs),
                "shorts_count": len(normalized_shorts),
                "opportunities": normalized_opportunities[:50],  # Топ 50
                "top_longs": normalized_longs,
                "top_shorts": normalized_shorts
            }
            
            # Сохраняем в файл
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Scan results saved to {filename}")
            
            # Удаляем старые файлы (оставляем последние 10)
            scan_files = sorted(
                data_dir.glob("scan_results_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            for old_file in scan_files[10:]:
                old_file.unlink()
                logger.debug(f"Deleted old scan file: {old_file.name}")
                
        except Exception as e:
            logger.error(f"Failed to save scan results: {e}", exc_info=True)
    
    async def _analyze_btc(self) -> Dict[str, Any]:
        """Детальный анализ BTC (с кэшированием 5 минут если доступно)"""
        # Используем кэш если доступен
        if self.cache_manager:
            cache_key = f"_analyze_btc"
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for BTC analysis")
                return cached_result
        
        try:
            # Получаем цену BTC
            btc_price = await self.bybit_client.get_asset_price("BTC/USDT")
            
            # Полный технический анализ BTC
            btc_analysis = await self.technical_analysis.analyze_asset(
                "BTC/USDT",
                timeframes=["1h", "4h", "1d"],
                include_patterns=True
            )
            
            # Получаем funding rate (для фьючерсов)
            try:
                funding_rate = await self.bybit_client.get_funding_rate("BTC/USDT:USDT")
            except:
                funding_rate = None
            
            result = {
                "price": btc_price,
                "technical_analysis": btc_analysis,
                "funding_rate": funding_rate,
                "status": self._determine_btc_status(btc_analysis)
            }
            
            # Сохраняем в кэш если доступен
            if self.cache_manager:
                self.cache_manager.set("_analyze_btc", result, ttl=300)
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing BTC: {e}")
            return {"error": str(e)}
    
    def _determine_btc_status(self, analysis: Dict) -> str:
        """Определение статуса BTC"""
        composite = analysis.get("composite_signal", {})
        signal = composite.get("signal", "HOLD")
        confidence = composite.get("confidence", 0.5)
        
        if signal in ["STRONG_BUY", "BUY"] and confidence > 0.6:
            return "bullish"
        elif signal in ["STRONG_SELL", "SELL"] and confidence > 0.6:
            return "bearish"
        else:
            return "neutral"
    
    async def _scan_all_opportunities(self) -> List[Dict[str, Any]]:
        """Параллельное сканирование всех возможностей (с кэшированием 3 минуты если доступно)"""
        # Используем кэш если доступен
        if self.cache_manager:
            cache_key = f"_scan_all_opportunities"
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for market scan")
                return cached_result
        
        all_opportunities = []
        
        # Параллельный запуск всех типов сканирования с увеличенными лимитами
        # Включаем advanced features если доступны (для топ активов с большим объемом)
        enable_advanced = ADVANCED_FEATURES_AVAILABLE
        
        tasks = [
            # Разные критерии для scan_market - увеличенные лимиты для полного охвата
            self.market_scanner.scan_market({
                "market_type": "spot",
                "min_volume_24h": 1000000,
                "indicators": {"rsi_range": [0, 35]},  # Oversold
                "include_whale_analysis": enable_advanced,  # Для активов с volume > 5M
                "include_volume_profile": enable_advanced
            }, limit=100),  # Увеличено с 20 до 100
            
            self.market_scanner.scan_market({
                "market_type": "spot",
                "min_volume_24h": 1000000,
                "indicators": {"rsi_range": [65, 100]},  # Overbought для шортов
                "include_whale_analysis": enable_advanced,
                "include_volume_profile": enable_advanced
            }, limit=100),
            
            self.market_scanner.scan_market({
                "market_type": "spot",
                "min_volume_24h": 1000000,
                "indicators": {"macd_crossover": "bullish"},
                "include_whale_analysis": enable_advanced,
                "include_volume_profile": enable_advanced
            }, limit=100),
            
            self.market_scanner.scan_market({
                "market_type": "spot",
                "min_volume_24h": 1000000,
                "indicators": {"macd_crossover": "bearish"},
                "include_whale_analysis": enable_advanced,
                "include_volume_profile": enable_advanced
            }, limit=100),
            
            # Специализированные поиски
            self.market_scanner.find_oversold_assets("spot", min_volume_24h=1000000),
            self.market_scanner.find_overbought_assets("spot", min_volume_24h=1000000),
            self.market_scanner.find_breakout_opportunities("spot", min_volume_24h=1000000),
            self.market_scanner.find_trend_reversals("spot", min_volume_24h=1000000)
        ]
        
        # Add ORB scan если в нужное время (European или US session)
        if ORB_AVAILABLE and hasattr(self, 'orb_strategy') and self.orb_strategy and self.session_manager:
            current_session = self.session_manager.get_current_session()
            if current_session in ["european", "us"]:
                tasks.append(
                    self.market_scanner.find_orb_opportunities("spot", min_volume_24h=1000000)
                )
                logger.info(f"ORB scan added for {current_session} session")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Объединяем результаты
        seen_symbols = set()
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Scan task failed: {result}")
                continue
            
            # ✅ FIX: Обрабатываем Dict ответы от market_scanner функций
            if isinstance(result, dict):
                # Проверяем success
                if not result.get("success", False):
                    logger.warning(f"Scan task returned error: {result.get('error', 'Unknown error')}")
                    continue
                # Извлекаем opportunities из Dict
                opportunities_list = result.get("opportunities", [])
            elif isinstance(result, list):
                # Старый формат (если где-то еще используется)
                opportunities_list = result
            else:
                logger.warning(f"Unexpected result type: {type(result)}")
                continue
            
            for opp in opportunities_list:
                symbol = opp.get("symbol", "")
                if symbol and symbol not in seen_symbols:
                    all_opportunities.append(opp)
                    seen_symbols.add(symbol)
        
        # Сортируем по score
        all_opportunities.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        logger.info(f"Found {len(all_opportunities)} total opportunities")
        
        # Сохраняем в кэш если доступен
        if self.cache_manager:
            self.cache_manager.set("_scan_all_opportunities", all_opportunities, ttl=180)
        
        return all_opportunities
    
    async def _deep_analyze_top_candidates(
        self,
        opportunities: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Детальный анализ топ кандидатов (с кэшированием 2 минуты если доступно)"""
        # Используем кэш если доступен (но только для одинаковых входных данных)
        if self.cache_manager and len(opportunities) > 0:
            # Создаём ключ на основе первых N символов символов
            symbols_key = "_".join([opp.get("symbol", "") for opp in opportunities[:top_n]])
            cache_key = f"_deep_analyze_top_candidates_{symbols_key}_{top_n}"
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for deep analysis")
                return cached_result
        
        # Берем топ N по score
        top_candidates = opportunities[:top_n]
        
        # ═══════════════════════════════════════════════════════
        # REMOVED HARD FILTER! Process ALL candidates
        # ═══════════════════════════════════════════════════════
        # NO FILTERING by score - tier classification handles quality
        # Process all candidates (already sorted by score)
        filtered = top_candidates  # Keep ALL
        logger.info(f"Processing {len(filtered)} candidates (no hard score filter)")
        
        # Детальный анализ каждого кандидата
        detailed_analysis = []
        
        for opp in filtered[:10]:  # Максимум 10 для детального анализа
            try:
                symbol = opp.get("symbol", "")
                if not symbol:
                    continue
                
                # Полный анализ на всех таймфреймах
                full_analysis = await self.technical_analysis.analyze_asset(
                    symbol,
                    timeframes=["15m", "1h", "4h", "1d"],
                    include_patterns=True
                )
                
                # Валидация входа
                entry_plan = opp.get("entry_plan", {})
                if entry_plan:
                    validation = await self.technical_analysis.validate_entry(
                        symbol=symbol,
                        side="long",  # Предполагаем long, можно улучшить
                        entry_price=entry_plan.get("entry_price", 0),
                        stop_loss=entry_plan.get("stop_loss", 0),
                        take_profit=entry_plan.get("take_profit", 0)
                    )
                else:
                    validation = None
                
                detailed_opp = {
                    **opp,
                    "full_analysis": full_analysis,
                    "validation": validation,
                    "final_score": self._calculate_final_score(opp, full_analysis, validation)
                }
                
                # ✅ НОРМАЛИЗАЦИЯ score полей
                detailed_opp = normalize_opportunity_score(detailed_opp)
                
                detailed_analysis.append(detailed_opp)
            
            except Exception as e:
                logger.warning(f"Error in deep analysis for {opp.get('symbol', 'unknown')}: {e}")
                continue
        
        # Сортируем по final_score
        detailed_analysis.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        # Сохраняем в кэш если доступен
        if self.cache_manager and len(opportunities) > 0:
            symbols_key = "_".join([opp.get("symbol", "") for opp in opportunities[:top_n]])
            cache_key = f"_deep_analyze_top_candidates_{symbols_key}_{top_n}"
            self.cache_manager.set(cache_key, detailed_analysis, ttl=120)
        
        return detailed_analysis
    
    def _calculate_final_score(
        self,
        opp: Dict,
        analysis: Dict,
        validation: Optional[Dict]
    ) -> float:
        """
        Расчёт финального score на основе Entry Decision Framework
        
        CONFLUENCE SCORING MATRIX (из entry_decision_framework.md):
        1. Trend Alignment (3-4 TF): 0-2 points
        2. Multiple Indicators (5+): 0-2 points
        3. Strong S/R Level: 0-1 point
        4. Volume Confirmation: 0-1 point
        5. Pattern >70% Reliability: 0-1 point
        6. R:R ≥ 1:2: 0-1 point
        7. Favorable Market Conditions: 0-1 point
        8. BTC Supports Direction: 0-1 point
        9. Positive Sentiment: 0-1 point
        10. On-Chain Supports: 0-1 point (BONUS)
        
        МИНИМУМ ДЛЯ ВХОДА: 8.0 points
        """
        
        score = 0.0
        side = opp.get("side", "long").lower()
        
        # 1. Trend Alignment (0-2 points)
        if analysis:
            timeframes = analysis.get("timeframes", {})
            aligned_tfs = 0
            
            for tf_data in timeframes.values():
                trend = tf_data.get("trend", {})
                direction = trend.get("direction", "").lower()
                
                if side == "long":
                    if direction in ["uptrend", "bullish", "rising"]:
                        aligned_tfs += 1
                else:  # short
                    if direction in ["downtrend", "bearish", "falling"]:
                        aligned_tfs += 1
            
            if aligned_tfs >= 4:
                score += 2.0  # Все 4 TF aligned
            elif aligned_tfs == 3:
                score += 1.5
            elif aligned_tfs == 2:
                score += 1.0
        
        # 2. Multiple Indicators (0-2 points)
        confirmed_indicators = 0
        if analysis:
            for tf_data in timeframes.values():
                indicators = tf_data.get("indicators", {})
                
                # RSI
                rsi = indicators.get("rsi", {})
                rsi_value = rsi.get("rsi_14", 50)
                if side == "long" and rsi_value < 35:
                    confirmed_indicators += 1
                elif side == "short" and rsi_value > 65:
                    confirmed_indicators += 1
                
                # MACD
                macd = indicators.get("macd", {})
                histogram = macd.get("histogram", 0)
                if side == "long" and histogram > 0:
                    confirmed_indicators += 1
                elif side == "short" and histogram < 0:
                    confirmed_indicators += 1
                
                # Bollinger Bands
                bb = indicators.get("bollinger_bands", {})
                bb_position = bb.get("position", "middle")
                if side == "long" and bb_position == "lower":
                    confirmed_indicators += 1
                elif side == "short" and bb_position == "upper":
                    confirmed_indicators += 1
        
        # Также проверяем общий счетчик если есть
        confirmed_indicators = max(
            confirmed_indicators,
            opp.get("confirmed_indicators_count", 0)
        )
        
        if confirmed_indicators >= 7:
            score += 2.0
        elif confirmed_indicators >= 6:
            score += 1.5
        elif confirmed_indicators >= 5:
            score += 1.0
        elif confirmed_indicators >= 4:
            score += 0.5
        
        # 3. Strong S/R Level (0-1 point)
        sr_levels = opp.get("support_resistance", {})
        has_strong_level = False
        
        if side == "long":
            support = sr_levels.get("support", [])
            entry_price = opp.get("entry_price", 0)
            for level in support:
                if entry_price > 0 and abs(entry_price - level) / entry_price < 0.02:
                    has_strong_level = True
                    break
        else:  # short
            resistance = sr_levels.get("resistance", [])
            entry_price = opp.get("entry_price", 0)
            for level in resistance:
                if entry_price > 0 and abs(entry_price - level) / entry_price < 0.02:
                    has_strong_level = True
                    break
        
        if has_strong_level or opp.get("near_support", False) or opp.get("near_resistance", False):
            score += 1.0
        
        # 4. Volume Confirmation (0-1 point)
        volume_ratio = opp.get("volume_ratio", 1.0)
        if volume_ratio >= 2.0:
            score += 1.0
        elif volume_ratio >= 1.5:
            score += 0.75
        elif volume_ratio >= 1.3:
            score += 0.5
        
        # 5. Pattern Reliability (0-1 point)
        pattern_success = opp.get("pattern_success_rate", 0)
        if pattern_success == 0:
            patterns = analysis.get("patterns", [])
            if patterns:
                pattern_success = max(
                    p.get("reliability", 0) / 100.0 if isinstance(p.get("reliability"), (int, float)) else 0
                    for p in patterns
                    if isinstance(p, dict)
                )
        
        if pattern_success > 0.75:
            score += 1.0
        elif pattern_success > 0.70:
            score += 0.75
        elif pattern_success > 0.65:
            score += 0.5
        elif pattern_success > 0.60:
            score += 0.25
        
        # 6. R:R Ratio (0-1 point)
        rr_ratio = opp.get("risk_reward", 0)
        if rr_ratio == 0:
            # Рассчитываем из entry, stop_loss, take_profit
            entry = opp.get("entry_price", 0)
            stop_loss = opp.get("stop_loss", 0)
            take_profit = opp.get("take_profit", 0)
            
            if entry > 0 and stop_loss > 0 and take_profit > 0:
                if side == "long":
                    risk = abs(entry - stop_loss)
                    reward = abs(take_profit - entry)
                else:  # short
                    risk = abs(stop_loss - entry)
                    reward = abs(entry - take_profit)
                
                if risk > 0:
                    rr_ratio = reward / risk
        
        if rr_ratio >= 3.0:
            score += 1.0
        elif rr_ratio >= 2.5:
            score += 0.75
        elif rr_ratio >= 2.0:
            score += 0.5
        
        # 7. Market Conditions (0-1 point)
        market_conditions = opp.get("market_conditions", {})
        volatility = market_conditions.get("volatility", "normal")
        trend_strength = market_conditions.get("trend_strength", "medium")
        
        if volatility in ["normal", "low"] and trend_strength in ["strong", "medium"]:
            score += 1.0
        elif volatility in ["normal"] and trend_strength in ["medium"]:
            score += 0.75
        elif volatility in ["normal", "low"]:
            score += 0.5
        
        # 8. BTC Support (0-1 point)
        btc_status = opp.get("btc_status", "neutral").lower()
        btc_trend = opp.get("btc_trend", "neutral").lower()
        
        if side == "long":
            if btc_status in ["bullish"] or btc_trend in ["bullish"]:
                score += 1.0
            elif btc_status in ["neutral"] or btc_trend in ["neutral"]:
                score += 0.75
        else:  # short
            if btc_status in ["bearish"] or btc_trend in ["bearish"]:
                score += 1.0
            elif btc_status in ["neutral"] or btc_trend in ["neutral"]:
                score += 0.75
        
        # 9. Sentiment (0-1 point)
        sentiment = opp.get("sentiment", "neutral").lower()
        if sentiment == "positive":
            score += 1.0
        elif sentiment == "neutral":
            score += 0.5
        
        # 10. On-Chain Support (0-1 point BONUS)
        onchain = opp.get("onchain_support", False)
        if onchain:
            score += 1.0
        
        # Бонус за validation
        if validation and validation.get("is_valid", False):
            validation_score = validation.get("score", 0)
            # Небольшой бонус (максимум +0.5)
            score += min(0.5, validation_score / 20.0)
        
        # Experience Logging (только логирование, без влияния на score)
        if self.ml_predictor:
            try:
                # Собираем данные для логирования опыта
                pattern_type = opp.get("pattern_type", "unknown")
                volume_ratio = opp.get("volume_ratio", 1.0)
                btc_aligned = (
                    (side == "long" and btc_trend in ["bullish", "uptrend"]) or
                    (side == "short" and btc_trend in ["bearish", "downtrend"])
                )
                session = self.session_manager.get_current_session() if self.session_manager else "neutral"
                
                # Получаем RSI из analysis
                rsi = 50.0
                if analysis:
                    timeframes = analysis.get("timeframes", {})
                    for tf_data in timeframes.values():
                        indicators = tf_data.get("indicators", {})
                        rsi_data = indicators.get("rsi", {})
                        if rsi_data:
                            rsi = rsi_data.get("rsi_14", 50.0)
                            break
                
                risk_reward = opp.get("risk_reward", 2.0)
                
                # Логируем опыт для будущего обучения (без влияния на score)
                experience_data = {
                    "confluence_score": score,
                    "pattern_type": pattern_type,
                    "volume_ratio": volume_ratio,
                    "btc_aligned": btc_aligned,
                    "session": session,
                    "rsi": rsi,
                    "risk_reward": risk_reward,
                    "side": side,
                    "symbol": opp.get("symbol", "unknown")
                }
                
                # Сохраняем для логирования (опыт будет записан в SignalTracker при закрытии позиции)
                opp["experience_data"] = experience_data
                logger.info(  # ИЗМЕНЕНО: info вместо debug
                    f"Experience logged for {opp.get('symbol')}: "
                    f"pattern={pattern_type}, score={score:.1f}, "
                    f"rsi={rsi:.1f}, volume_ratio={volume_ratio:.2f}"
                )
                
            except Exception as e:
                logger.warning(f"Experience logging failed: {e}")
        
        # Округляем до 0.5
        score = round(score * 2) / 2
        
        return min(12.0, max(0.0, score))
    
    async def _finalize_top_3_longs_and_shorts(
        self,
        candidates: List[Dict[str, Any]],
        qwen_analysis: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Финализация ТОП 3 лонгов и ТОП 3 шортов
        
        КРИТИЧЕСКИ ВАЖНО (из CRITICAL_REQUIREMENTS.md):
        - ВСЕГДА возвращать ОБА направления
        - Даже если score низкий - показывать с предупреждением
        - НЕ фильтровать по направлению до финального отчета
        """
        
        # Используем рекомендации Qwen если есть
        qwen_longs = []
        qwen_shorts = []
        
        if qwen_analysis.get("success") and "analysis" in qwen_analysis:
            analysis = qwen_analysis["analysis"]
            qwen_longs = analysis.get("top_longs", [])
            qwen_shorts = analysis.get("top_shorts", [])
            
            # Если Qwen дал рекомендации, используем их как приоритет
            if qwen_longs or qwen_shorts:
                logger.info(f"Using Qwen recommendations: {len(qwen_longs)} longs, {len(qwen_shorts)} shorts")
                # Форматируем Qwen рекомендации
                formatted_longs = [self._format_qwen_opportunity(opp) for opp in qwen_longs[:3]]
                formatted_shorts = [self._format_qwen_opportunity(opp) for opp in qwen_shorts[:3]]
                
                # Валидация через MCP validate_entry
                validated_longs = await self._validate_opportunities(formatted_longs, "long")
                validated_shorts = await self._validate_opportunities(formatted_shorts, "short")
                
                # КРИТИЧЕСКИ ВАЖНО: Если недостаточно - добавляем из candidates
                if len(validated_longs) < 3:
                    logger.warning(f"Only {len(validated_longs)} longs from Qwen, adding from candidates")
                    validated_longs = await self._ensure_top_3(validated_longs, candidates, "long")
                
                if len(validated_shorts) < 3:
                    logger.warning(f"Only {len(validated_shorts)} shorts from Qwen, adding from candidates")
                    validated_shorts = await self._ensure_top_3(validated_shorts, candidates, "short")
                
                return validated_longs[:3], validated_shorts[:3]
        
        # Если Qwen не дал рекомендаций, используем наши кандидаты
        # КРИТИЧЕСКИ ВАЖНО: НЕ фильтруем по score - показываем ВСЕ с предупреждениями
        
        # ═══════════════════════════════════════════════════════
        # Используем side из entry_plan для более точного определения
        # ═══════════════════════════════════════════════════════
        all_longs = []
        all_shorts = []
        
        for opp in candidates:
            # Определяем side из entry_plan (более надежно)
            entry_plan = opp.get("entry_plan", {})
            side = entry_plan.get("side", "long").lower()
            
            # Также проверяем альтернативные поля
            if side not in ["long", "short"]:
                side = opp.get("side", "long").lower()
            
            if side == "long":
                all_longs.append(opp)
            else:
                all_shorts.append(opp)
        
        logger.info(f"Direction split: {len(all_longs)} LONGS, {len(all_shorts)} SHORTS")
        
        # Сортируем по final_score
        all_longs.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        all_shorts.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        # КРИТИЧЕСКИ ВАЖНО: Берем ТОП 3 каждого направления
        # ДАЖЕ ЕСЛИ score < 8.0 - показываем с предупреждением
        top_longs = []
        top_shorts = []
        
        # Топ 3 ЛОНГА
        for i, opp in enumerate(all_longs[:3]):
            formatted = self._format_opportunity(opp)
            
            # Добавляем предупреждение если score < 8.0
            final_score = opp.get("final_score", 0)
            if final_score < 8.0:
                formatted["warning"] = (
                    f"⚠️ ВНИМАНИЕ: Score {final_score:.1f}/12 "
                    f"ниже минимума (8.0). Рекомендуется ОСТОРОЖНОСТЬ или ПОДОЖДАТЬ."
                )
                formatted["recommendation"] = "ОСТОРОЖНО - только для опытных"
            else:
                formatted["recommendation"] = "ОТКРЫВАТЬ"
            
            top_longs.append(formatted)
        
        # Топ 3 ШОРТА  
        for i, opp in enumerate(all_shorts[:3]):
            formatted = self._format_opportunity(opp)
            
            # Добавляем предупреждение если score < 8.0
            final_score = opp.get("final_score", 0)
            if final_score < 8.0:
                formatted["warning"] = (
                    f"⚠️ ВНИМАНИЕ: Score {final_score:.1f}/12 "
                    f"ниже минимума (8.0). Рекомендуется ОСТОРОЖНОСТЬ или ПОДОЖДАТЬ."
                )
                formatted["recommendation"] = "ОСТОРОЖНО - только для опытных"
            else:
                formatted["recommendation"] = "ОТКРЫВАТЬ"
            
            top_shorts.append(formatted)
        
        # Валидация через MCP validate_entry
        validated_longs = await self._validate_opportunities(top_longs, "long")
        validated_shorts = await self._validate_opportunities(top_shorts, "short")
        
        logger.info(
            f"Finalized: {len(validated_longs)} longs, {len(validated_shorts)} shorts"
        )
        
        return validated_longs, validated_shorts
    
    async def _ensure_top_3(
        self,
        existing: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        side: str
    ) -> List[Dict[str, Any]]:
        """Обеспечивает минимум 3 возможности для направления"""
        
        existing_symbols = {opp.get("symbol") for opp in existing}
        
        # Берем из candidates те, которых еще нет
        additional = [
            opp for opp in candidates
            if opp.get("side", "long").lower() == side
            and opp.get("symbol") not in existing_symbols
        ]
        
        # Сортируем и берем недостающие
        additional.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        needed = 3 - len(existing)
        
        for opp in additional[:needed]:
            formatted = self._format_opportunity(opp)
            final_score = opp.get("final_score", 0)
            if final_score < 8.0:
                formatted["warning"] = (
                    f"⚠️ ВНИМАНИЕ: Score {final_score:.1f}/12 "
                    f"ниже минимума (8.0). Рекомендуется ОСТОРОЖНОСТЬ."
                )
                formatted["recommendation"] = "ОСТОРОЖНО - только для опытных"
            else:
                formatted["recommendation"] = "ОТКРЫВАТЬ"
            
            existing.append(formatted)
        
        return existing
    
    async def _validate_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        side: str
    ) -> List[Dict[str, Any]]:
        """
        Валидация возможностей через MCP validate_entry
        
        Args:
            opportunities: Список возможностей для валидации
            side: Направление ('long' или 'short')
            
        Returns:
            Список валидированных возможностей
        """
        validated = []
        
        for opp in opportunities:
            try:
                symbol = opp.get("symbol", "")
                entry_price = opp.get("entry_price", 0)
                stop_loss = opp.get("stop_loss", 0)
                take_profit = opp.get("take_profit", 0)
                
                # Проверяем что все необходимые данные есть
                if not all([symbol, entry_price, stop_loss, take_profit]):
                    logger.warning(f"Incomplete data for {symbol}, skipping validation")
                    continue
                
                # Валидация через MCP validate_entry
                validation = await self.technical_analysis.validate_entry(
                    symbol=symbol,
                    side=side,
                    entry_price=float(entry_price),
                    stop_loss=float(stop_loss),
                    take_profit=float(take_profit),
                    risk_pct=0.02  # 2% риск по умолчанию
                )
                
                # Добавляем валидацию к возможности
                opp["validation"] = validation
                
                # Обновляем final_score на основе валидации
                if validation.get("is_valid", False):
                    validation_score = validation.get("score", 0)
                    # Комбинируем существующий score с validation score
                    base_score = opp.get("confluence_score", 0)
                    opp["final_score"] = min(10.0, (base_score + validation_score) / 2)
                    opp["validation_passed"] = True
                    validated.append(opp)
                    logger.info(f"Validation passed for {symbol} {side}: score={validation_score}")
                else:
                    logger.warning(
                        f"Validation failed for {symbol} {side}: "
                        f"{validation.get('message', 'Unknown reason')}"
                    )
                    # Не добавляем в validated, но сохраняем информацию о валидации
                    opp["validation_passed"] = False
                    
            except Exception as e:
                logger.error(f"Error validating {opp.get('symbol', 'unknown')}: {e}", exc_info=True)
                # В случае ошибки валидации, всё равно добавляем возможность
                # но помечаем что валидация не прошла
                opp["validation"] = {"error": str(e), "is_valid": False}
                opp["validation_passed"] = False
                validated.append(opp)
        
        # Сортируем по final_score после валидации
        validated.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        # Возвращаем топ-3
        return validated[:3]
    
    def _format_qwen_opportunity(self, qwen_opp: Dict[str, Any]) -> Dict[str, Any]:
        """Форматирование возможности от Qwen"""
        return {
            "symbol": qwen_opp.get("symbol", ""),
            "side": qwen_opp.get("side", "long"),
            "entry_price": qwen_opp.get("entry_price", 0),
            "stop_loss": qwen_opp.get("stop_loss", 0),
            "take_profit": qwen_opp.get("take_profit", 0),
            "confluence_score": qwen_opp.get("confluence_score", 0),
            "probability": qwen_opp.get("probability", 0),
            "risk_reward": qwen_opp.get("risk_reward", 0),
            "reasoning": qwen_opp.get("reasoning", ""),
            "key_factors": qwen_opp.get("key_factors", []),
            "timeframes_alignment": qwen_opp.get("timeframes_alignment", [])
        }
    
    def _format_opportunity(self, opp: Dict[str, Any]) -> Dict[str, Any]:
        """Форматирование возможности для публикации"""
        entry_plan = opp.get("entry_plan", {})
        analysis = opp.get("full_analysis", {})
        composite = analysis.get("composite_signal", {}) if analysis else {}
        
        # ✅ Используем нормализованное значение
        final_score = opp.get("final_score", 0.0)
        
        formatted = {
            "symbol": opp.get("symbol", ""),
            "current_price": opp.get("current_price", 0),
            "side": opp.get("side", "long"),
            "entry_price": entry_plan.get("entry_price", opp.get("current_price", 0)),
            "stop_loss": entry_plan.get("stop_loss", 0),
            "take_profit": entry_plan.get("take_profit", 0),
            "risk_reward": entry_plan.get("risk_reward", 0),
            # ✅ Все три варианта с одним значением
            "final_score": round(final_score, 2),
            "confluence_score": round(final_score, 2),
            "score": round(final_score, 2),
            "probability": opp.get("probability", 0),
            "reasoning": opp.get("why", ""),
            "timeframes_alignment": list(analysis.get("timeframes", {}).keys()) if analysis else [],
            "key_factors": self._extract_key_factors(opp, analysis),
            "validation": opp.get("validation", {})
        }
        
        return formatted
    
    def _extract_key_factors(self, opp: Dict, analysis: Dict) -> List[str]:
        """Извлечение ключевых факторов"""
        factors = []
        
        if analysis:
            composite = analysis.get("composite_signal", {})
            signal = composite.get("signal", "")
            if signal:
                factors.append(f"Signal: {signal}")
            
            # Проверяем индикаторы на разных таймфреймах
            for tf, tf_data in analysis.get("timeframes", {}).items():
                indicators = tf_data.get("indicators", {})
                rsi = indicators.get("rsi", {}).get("rsi_14", 50)
                if rsi < 30:
                    factors.append(f"{tf} RSI oversold ({rsi:.1f})")
                elif rsi > 70:
                    factors.append(f"{tf} RSI overbought ({rsi:.1f})")
        
        return factors[:5]  # Максимум 5 факторов
    
    async def _record_signal_to_tracker(self, signal: Dict[str, Any], side: str) -> Optional[str]:
        """
        Записать сигнал в tracker для отслеживания качества
        
        Args:
            signal: Данные сигнала
            side: Направление ('long' или 'short')
            
        Returns:
            signal_id или None если запись не удалась
        """
        if not self.signal_tracker:
            return None
        
        try:
            # Извлекаем необходимые данные
            symbol = signal.get("symbol", "")
            entry_price = signal.get("entry_price", 0)
            stop_loss = signal.get("stop_loss", 0)
            take_profit = signal.get("take_profit", 0)
            confluence_score = signal.get("confluence_score", 0)
            probability = signal.get("probability", 0)
            
            # Проверяем что все необходимые данные есть
            if not all([symbol, entry_price, stop_loss, take_profit, confluence_score, probability]):
                logger.warning(f"Incomplete signal data for {symbol}, skipping tracking")
                return None
            
            # Извлекаем дополнительные данные
            analysis_data = signal.get("full_analysis") or signal.get("analysis") or signal
            timeframe = None
            pattern_type = None
            pattern_name = None
            
            # Пытаемся извлечь timeframe и pattern из analysis_data
            if isinstance(analysis_data, dict):
                # Ищем timeframe в timeframes
                timeframes = analysis_data.get("timeframes", {})
                if timeframes:
                    # Берем первый доступный timeframe
                    timeframe = list(timeframes.keys())[0] if timeframes else None
                
                # Ищем паттерны
                for tf_data in timeframes.values():
                    patterns = tf_data.get("patterns", {})
                    if patterns:
                        # Берем первый найденный паттерн
                        for ptype, pdata in patterns.items():
                            if isinstance(pdata, dict) and pdata.get("detected"):
                                pattern_type = ptype
                                pattern_name = pdata.get("name") or ptype
                                break
                        if pattern_type:
                            break
            
            # Записываем сигнал
            signal_id = await self.signal_tracker.record_signal(
                symbol=symbol,
                side=side,
                entry_price=float(entry_price),
                stop_loss=float(stop_loss),
                take_profit=float(take_profit),
                confluence_score=float(confluence_score),
                probability=float(probability),
                analysis_data=analysis_data,
                timeframe=timeframe,
                pattern_type=pattern_type,
                pattern_name=pattern_name
            )
            
            return signal_id
            
        except Exception as e:
            logger.error(f"Error recording signal to tracker: {e}", exc_info=True)
            return None
    
    async def execute_top_signals(
        self,
        longs: List[Dict[str, Any]],
        shorts: List[Dict[str, Any]],
        max_positions: int = 1,
        risk_per_trade: float = 0.02
    ) -> Dict[str, Any]:
        """
        Автоматическое исполнение топ сигналов
        
        Args:
            longs: Топ long сигналы
            shorts: Топ short сигналы
            max_positions: Максимум одновременных позиций
            risk_per_trade: Риск на сделку (2% по умолчанию)
            
        Returns:
            Результаты исполнения
        """
        if not self.auto_trade:
            logger.warning("Auto-trade disabled, skipping execution")
            return {"success": False, "message": "Auto-trade disabled"}
        
        if not self.trading_ops:
            logger.error("TradingOperations not available")
            return {"success": False, "error": "TradingOperations not available"}
        
        executed_trades = []
        
        try:
            # Получаем баланс используя функцию напрямую
            if get_all_account_balances:
                balances = get_all_account_balances(
                    self.trading_ops.session,
                    coin="USDT"
                )
                available_balance = balances.get("available", 0)
            else:
                logger.error("get_all_account_balances function not available")
                return {"success": False, "error": "get_all_account_balances not available"}
            
            if available_balance < 100:  # Минимум $100
                return {
                    "success": False,
                    "error": "Insufficient balance",
                    "message": f"Available: ${available_balance:.2f}, need at least $100"
                }
            
            # Выбираем лучший сигнал (highest confluence)
            all_signals = longs + shorts
            all_signals.sort(key=lambda x: x.get('confluence_score', 0), reverse=True)
            
            for signal in all_signals[:max_positions]:
                try:
                    # Расчет размера позиции на основе риска
                    risk_amount = available_balance * risk_per_trade
                    entry_price = float(signal.get('entry_price', 0))
                    stop_loss = float(signal.get('stop_loss', 0))
                    
                    if entry_price <= 0 or stop_loss <= 0:
                        logger.warning(f"Invalid prices for {signal.get('symbol')}: entry={entry_price}, sl={stop_loss}")
                        continue
                    
                    # Расчет количества
                    risk_per_unit = abs(entry_price - stop_loss)
                    if risk_per_unit <= 0:
                        logger.warning(f"Invalid risk per unit for {signal.get('symbol')}")
                        continue
                    
                    quantity = risk_amount / risk_per_unit
                    
                    if quantity <= 0:
                        logger.warning(f"Invalid quantity calculated for {signal.get('symbol')}: {quantity}")
                        continue
                    
                    # Определяем category (по умолчанию linear для фьючерсов)
                    category = signal.get('category', 'linear')
                    side_str = "Buy" if signal.get('side', 'long').lower() == 'long' else "Sell"
                    
                    # Исполнение ордера
                    result = await self.trading_ops.place_order(
                        symbol=signal.get('symbol', '').replace('/', '').replace(':', ''),
                        side=side_str,
                        order_type="Market",
                        quantity=quantity,
                        stop_loss=stop_loss,
                        take_profit=float(signal.get('take_profit', 0)),
                        category=category,
                        leverage=2 if category != 'spot' else None
                    )
                    
                    executed_trades.append({
                        "signal": signal,
                        "order_result": result,
                        "quantity": quantity,
                        "risk_amount": risk_amount
                    })
                    
                    logger.info(
                        f"Executed: {signal.get('symbol')} {signal.get('side')} "
                        f"@ {entry_price} qty={quantity:.6f}"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to execute {signal.get('symbol', 'unknown')}: {e}", exc_info=True)
                    continue
            
            total_invested = sum(
                float(t['signal'].get('entry_price', 0)) * t.get('quantity', 0)
                for t in executed_trades
            )
            
            return {
                "success": True,
                "executed_trades": len(executed_trades),
                "trades": executed_trades,
                "remaining_balance": available_balance - total_invested,
                "total_invested": total_invested
            }
        
        except Exception as e:
            logger.error(f"Error in execute_top_signals: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "executed_trades": len(executed_trades)
            }
    
    async def close(self):
        """Закрытие соединений"""
        await self.bybit_client.close()
        logger.info("Autonomous Analyzer closed")

