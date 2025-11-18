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

# Опциональный импорт для signal tracking
try:
    from mcp_server.signal_tracker import SignalTracker
    SIGNAL_TRACKING_AVAILABLE = True
except ImportError:
    SIGNAL_TRACKING_AVAILABLE = False
    SignalTracker = None


class AutonomousAnalyzer:
    """Автономный анализатор рынка с Qwen AI"""
    
    def __init__(
        self,
        qwen_api_key: str,
        bybit_api_key: str,
        bybit_api_secret: str,
        qwen_model: str = "qwen/qwen-turbo",  # OpenRouter формат
        testnet: bool = False,
        signal_tracker: Optional[SignalTracker] = None
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
        """
        # Инициализация Qwen клиента
        self.qwen = QwenClient(qwen_api_key, qwen_model)
        
        # Инициализация Bybit клиента и компонентов анализа
        self.bybit_client = BybitClient(bybit_api_key, bybit_api_secret, testnet)
        self.technical_analysis = TechnicalAnalysis(self.bybit_client)
        self.market_scanner = MarketScanner(self.bybit_client, self.technical_analysis)
        
        # Signal tracker для контроля качества
        self.signal_tracker = signal_tracker
        if self.signal_tracker:
            logger.info("Signal tracking enabled")
        
        # Загружаем системные инструкции
        self.system_instructions = self._load_system_instructions()
        
        logger.info("Autonomous Analyzer initialized")
    
    def _load_system_instructions(self) -> str:
        """Загрузка системных инструкций для Qwen"""
        base_path = Path(__file__).parent.parent
        
        # Читаем основные инструкции
        instructions_parts = []
        
        # Core instructions
        core_file = base_path / "prompts" / "agent_core_instructions.md"
        if core_file.exists():
            instructions_parts.append(f"=== CORE INSTRUCTIONS ===\n{core_file.read_text(encoding='utf-8')}\n")
        
        # Zero risk methodology
        zero_risk_file = base_path / "knowledge_base" / "7_zero_risk_methodology.md"
        if zero_risk_file.exists():
            instructions_parts.append(f"=== ZERO RISK METHODOLOGY ===\n{zero_risk_file.read_text(encoding='utf-8')}\n")
        
        # Market analysis framework
        analysis_file = base_path / "knowledge_base" / "6_market_analysis_framework.md"
        if analysis_file.exists():
            instructions_parts.append(f"=== MARKET ANALYSIS FRAMEWORK ===\n{analysis_file.read_text(encoding='utf-8')}\n")
        
        # Entry strategies
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
            
            # ШАГ 5: Анализ через Qwen
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
    
    async def _analyze_btc(self) -> Dict[str, Any]:
        """Детальный анализ BTC"""
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
            
            return {
                "price": btc_price,
                "technical_analysis": btc_analysis,
                "funding_rate": funding_rate,
                "status": self._determine_btc_status(btc_analysis)
            }
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
        """Параллельное сканирование всех возможностей"""
        all_opportunities = []
        
        # Параллельный запуск всех типов сканирования с увеличенными лимитами
        tasks = [
            # Разные критерии для scan_market - увеличенные лимиты для полного охвата
            self.market_scanner.scan_market({
                "market_type": "spot",
                "min_volume_24h": 1000000,
                "indicators": {"rsi_range": [0, 35]}  # Oversold
            }, limit=100),  # Увеличено с 20 до 100
            
            self.market_scanner.scan_market({
                "market_type": "spot",
                "min_volume_24h": 1000000,
                "indicators": {"rsi_range": [65, 100]}  # Overbought для шортов
            }, limit=100),
            
            self.market_scanner.scan_market({
                "market_type": "spot",
                "min_volume_24h": 1000000,
                "indicators": {"macd_crossover": "bullish"}
            }, limit=100),
            
            self.market_scanner.scan_market({
                "market_type": "spot",
                "min_volume_24h": 1000000,
                "indicators": {"macd_crossover": "bearish"}
            }, limit=100),
            
            # Специализированные поиски
            self.market_scanner.find_oversold_assets("spot", min_volume_24h=1000000),
            self.market_scanner.find_overbought_assets("spot", min_volume_24h=1000000),
            self.market_scanner.find_breakout_opportunities("spot", min_volume_24h=1000000),
            self.market_scanner.find_trend_reversals("spot", min_volume_24h=1000000)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Объединяем результаты
        seen_symbols = set()
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Scan task failed: {result}")
                continue
            
            for opp in result:
                symbol = opp.get("symbol", "")
                if symbol and symbol not in seen_symbols:
                    all_opportunities.append(opp)
                    seen_symbols.add(symbol)
        
        # Сортируем по score
        all_opportunities.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        logger.info(f"Found {len(all_opportunities)} total opportunities")
        return all_opportunities
    
    async def _deep_analyze_top_candidates(
        self,
        opportunities: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Детальный анализ топ кандидатов"""
        # Берем топ N по score
        top_candidates = opportunities[:top_n]
        
        # Фильтруем по минимальному score
        filtered = [opp for opp in top_candidates if opp.get("score", 0) >= 7.0]
        
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
                
                detailed_analysis.append(detailed_opp)
            
            except Exception as e:
                logger.warning(f"Error in deep analysis for {opp.get('symbol', 'unknown')}: {e}")
                continue
        
        # Сортируем по final_score
        detailed_analysis.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return detailed_analysis
    
    def _calculate_final_score(
        self,
        opp: Dict,
        analysis: Dict,
        validation: Optional[Dict]
    ) -> float:
        """Расчёт финального score"""
        base_score = opp.get("score", 5.0)
        
        # Бонус за composite signal
        composite = analysis.get("composite_signal", {})
        signal = composite.get("signal", "HOLD")
        if signal == "STRONG_BUY":
            base_score += 1.0
        elif signal == "BUY":
            base_score += 0.5
        
        # Бонус за confidence
        confidence = composite.get("confidence", 0.5)
        base_score += (confidence - 0.5) * 2
        
        # Бонус за validation
        if validation and validation.get("is_valid", False):
            base_score += 1.0
        
        return min(10.0, max(0.0, base_score))
    
    async def _finalize_top_3_longs_and_shorts(
        self,
        candidates: List[Dict[str, Any]],
        qwen_analysis: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Финализация топ 3 лонгов и топ 3 шортов"""
        # Фильтруем по минимальным требованиям
        filtered = [
            opp for opp in candidates
            if opp.get("final_score", 0) >= 8.0
            and opp.get("probability", 0) >= 0.70
        ]
        
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
                return formatted_longs, formatted_shorts
        
        # Если Qwen не дал рекомендаций, используем наши кандидаты
        # Разделяем на лонги и шорты
        longs = [opp for opp in filtered if opp.get("side", "long").lower() == "long"]
        shorts = [opp for opp in filtered if opp.get("side", "long").lower() == "short"]
        
        # Сортируем по final_score
        longs.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        shorts.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        # Берем топ 3 каждого
        top_longs = longs[:3]
        top_shorts = shorts[:3]
        
        # Форматируем для публикации
        formatted_longs = [self._format_opportunity(opp) for opp in top_longs]
        formatted_shorts = [self._format_opportunity(opp) for opp in top_shorts]
        
        return formatted_longs, formatted_shorts
    
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
        
        return {
            "symbol": opp.get("symbol", ""),
            "current_price": opp.get("current_price", 0),
            "side": "long",  # Можно улучшить определение
            "entry_price": entry_plan.get("entry_price", opp.get("current_price", 0)),
            "stop_loss": entry_plan.get("stop_loss", 0),
            "take_profit": entry_plan.get("take_profit", 0),
            "risk_reward": entry_plan.get("risk_reward", 0),
            "confluence_score": round(opp.get("final_score", 0), 1),
            "probability": opp.get("probability", 0),
            "reasoning": opp.get("why", ""),
            "timeframes_alignment": list(analysis.get("timeframes", {}).keys()) if analysis else [],
            "key_factors": self._extract_key_factors(opp, analysis),
            "validation": opp.get("validation", {})
        }
    
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
    
    async def close(self):
        """Закрытие соединений"""
        await self.bybit_client.close()
        logger.info("Autonomous Analyzer closed")

