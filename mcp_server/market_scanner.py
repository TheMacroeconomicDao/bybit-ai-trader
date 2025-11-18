"""
Market Scanner
Сканирование рынка для поиска торговых возможностей
"""

import asyncio
from typing import Dict, List, Any, Optional
from loguru import logger


class MarketScanner:
    """Сканер рынка для поиска торговых возможностей"""
    
    def __init__(self, bybit_client, technical_analysis):
        self.client = bybit_client
        self.ta = technical_analysis
        logger.info("Market Scanner initialized")
    
    async def scan_market(
        self,
        criteria: Dict[str, Any],
        limit: int = 10,
        auto_track: bool = False,
        signal_tracker: Optional[Any] = None,
        track_limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Универсальное сканирование рынка по критериям
        
        Args:
            criteria: Критерии фильтрации
            limit: Максимальное количество результатов
            auto_track: Автоматически записывать топ-N сигналов в tracker
            signal_tracker: SignalTracker для записи сигналов (если auto_track=True)
            track_limit: Количество топ сигналов для записи (по умолчанию 3)
            
        Returns:
            Список активов, соответствующих критериям
        """
        logger.info(f"Scanning market with criteria: {criteria}")
        
        # Получаем все тикеры
        all_tickers = await self.client.get_all_tickers(
            market_type=criteria.get('market_type', 'spot')
        )
        
        # Проверяем, что получили данные
        if not all_tickers or len(all_tickers) == 0:
            logger.error("No tickers received from API - this indicates a critical error")
            raise Exception("API Error: No tickers received from Bybit API. Cannot perform market scan without market data.")
        
        # Фильтрация по базовым критериям
        filtered = []
        
        for ticker in all_tickers:
            # Минимальный объём
            min_volume = criteria.get('min_volume_24h', 100000)
            if ticker['volume_24h'] < min_volume:
                continue
            
            # Диапазон изменения цены
            price_range = criteria.get('price_change_range')
            if price_range:
                change = ticker['change_24h']
                if change < price_range[0] or change > price_range[1]:
                    continue
            
            filtered.append(ticker)
        
        # Детальный анализ для отфильтрованных с параллелизацией
        # Ограничиваем количество для анализа (топ по объёму)
        candidates = filtered[:min(limit * 5, 100)]  # Максимум 100 кандидатов (было 50)
        
        # Параллельный анализ с ограничением одновременных запросов
        semaphore = asyncio.Semaphore(10)  # Максимум 10 параллельно (было 5)
        
        async def analyze_ticker(ticker: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Анализ одного тикера с обработкой ошибок"""
            async with semaphore:
                try:
                    analysis = await self.ta.analyze_asset(
                        ticker['symbol'],
                        timeframes=["1h", "4h"],
                        include_patterns=True
                    )
                    
                    # Проверка индикаторных критериев
                    indicator_criteria = criteria.get('indicators', {})
                    if not self._check_indicator_criteria(analysis, indicator_criteria):
                        return None
                    
                    # Scoring
                    score = self._calculate_opportunity_score(analysis, ticker)
                    
                    # Entry plan
                    entry_plan = self._generate_entry_plan(analysis, ticker)
                    
                    return {
                        "symbol": ticker['symbol'],
                        "current_price": ticker['price'],
                        "change_24h": ticker['change_24h'],
                        "volume_24h": ticker['volume_24h'],
                        "score": score,
                        "probability": self._estimate_probability(score, analysis),
                        "entry_plan": entry_plan,
                        "analysis": analysis,
                        "why": self._generate_reasoning(analysis, score)
                    }
                except Exception as e:
                    logger.warning(f"Error analyzing {ticker['symbol']}: {e}")
                    return None
        
        # Параллельный анализ всех кандидатов
        tasks = [analyze_ticker(ticker) for ticker in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты и исключения
        opportunities = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Task failed with exception: {result}")
                continue
            if result is not None:
                opportunities.append(result)
        
        # Сортировка по score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # Ранний выход: если уже нашли достаточно качественных (score >= 7.0)
        high_quality = [opp for opp in opportunities if opp['score'] >= 7.0]
        if len(high_quality) >= limit:
            logger.info(f"Found {len(high_quality)} high-quality opportunities, returning top {limit}")
            final_opportunities = high_quality[:limit]
        else:
            final_opportunities = opportunities[:limit]
        
        # Автоматическая запись топ-N сигналов в tracker
        if auto_track and signal_tracker and final_opportunities:
            try:
                tracked_count = 0
                for opp in final_opportunities[:track_limit]:
                    # Проверяем что есть entry_plan с необходимыми данными
                    entry_plan = opp.get('entry_plan', {})
                    if not entry_plan:
                        continue
                    
                    entry_price = entry_plan.get('entry_price')
                    stop_loss = entry_plan.get('stop_loss')
                    take_profit = entry_plan.get('take_profit')
                    side = entry_plan.get('side', 'long')
                    
                    if not all([entry_price, stop_loss, take_profit]):
                        continue
                    
                    # Нормализуем symbol
                    symbol = opp.get('symbol', '').replace('/', '')
                    if not symbol:
                        continue
                    
                    # Извлекаем дополнительные данные
                    analysis = opp.get('analysis', {})
                    score = opp.get('score', 0)
                    probability = opp.get('probability', 0.5)
                    
                    # Извлекаем timeframe
                    timeframe = None
                    if 'timeframes' in analysis:
                        for tf in ["4h", "1h", "15m"]:
                            if tf in analysis['timeframes']:
                                timeframe = tf
                                break
                    
                    # Извлекаем паттерны
                    pattern_type = None
                    pattern_name = None
                    if 'patterns' in analysis:
                        patterns = analysis['patterns']
                        if patterns:
                            first_pattern = patterns[0] if isinstance(patterns, list) else list(patterns.values())[0]
                            if isinstance(first_pattern, dict):
                                pattern_type = first_pattern.get('type')
                                pattern_name = first_pattern.get('name')
                    
                    # Записываем сигнал
                    try:
                        signal_id = await signal_tracker.record_signal(
                            symbol=symbol,
                            side=side.lower(),
                            entry_price=float(entry_price),
                            stop_loss=float(stop_loss),
                            take_profit=float(take_profit),
                            confluence_score=float(score),
                            probability=float(probability),
                            analysis_data=analysis,
                            timeframe=timeframe,
                            pattern_type=pattern_type,
                            pattern_name=pattern_name
                        )
                        tracked_count += 1
                        logger.info(f"✅ Auto-tracked signal from scan_market: {signal_id} for {symbol} {side}")
                    except Exception as e:
                        logger.warning(f"Failed to track signal for {symbol}: {e}")
                        continue
                
                if tracked_count > 0:
                    logger.info(f"✅ Auto-tracked {tracked_count} signals from scan_market")
            except Exception as e:
                logger.warning(f"Failed to auto-track signals from scan_market: {e}")
                # Не прерываем выполнение
        
        return final_opportunities
    
    def _check_indicator_criteria(self, analysis: Dict, criteria: Dict) -> bool:
        """Проверка индикаторных критериев"""
        
        if not criteria:
            return True
        
        # Берём 4h данные для проверки
        h4_data = analysis['timeframes'].get('4h', {})
        indicators = h4_data.get('indicators', {})
        
        # RSI range
        rsi_range = criteria.get('rsi_range')
        if rsi_range:
            rsi = indicators.get('rsi', {}).get('rsi_14', 50)
            if rsi < rsi_range[0] or rsi > rsi_range[1]:
                return False
        
        # MACD crossover
        macd_cross = criteria.get('macd_crossover')
        if macd_cross:
            actual_cross = indicators.get('macd', {}).get('crossover')
            if actual_cross != macd_cross:
                return False
        
        # Price vs EMA50
        price_vs_ema = criteria.get('price_vs_ema50')
        if price_vs_ema:
            price = h4_data.get('current_price', 0)
            ema50 = indicators.get('ema', {}).get('ema_50', 0)
            
            if price_vs_ema == 'above' and price <= ema50:
                return False
            elif price_vs_ema == 'below' and price >= ema50:
                return False
        
        return True
    
    def _calculate_opportunity_score(self, analysis: Dict, ticker: Dict) -> float:
        """Расчёт scoring возможности (0-10) для ЛЮБОГО направления"""
        
        score = 5.0  # Базовый score
        
        composite = analysis.get('composite_signal', {})
        signal = composite.get('signal', 'HOLD')
        
        # Определяем направление по сигналу
        is_long_signal = signal in ['STRONG_BUY', 'BUY']
        is_short_signal = signal in ['STRONG_SELL', 'SELL']
        
        # Composite signal strength (для обоих направлений)
        if signal == 'STRONG_BUY':
            score += 2.5
        elif signal == 'BUY':
            score += 1.5
        elif signal == 'STRONG_SELL':
            score += 2.5  # Для шортов STRONG_SELL это хорошо!
        elif signal == 'SELL':
            score += 1.5  # Для шортов SELL это хорошо!
        
        # Confidence
        confidence = composite.get('confidence', 0.5)
        score += (confidence - 0.5) * 3  # -1.5 to +1.5
        
        # Alignment (для обоих направлений)
        alignment = composite.get('alignment', 0.5)
        if alignment > 0.75:
            score += 1.5
        elif alignment > 0.6:
            score += 0.5
        
        # Volume (относительно среднего)
        h4_data = analysis['timeframes'].get('4h', {})
        volume_ratio = h4_data.get('indicators', {}).get('volume', {}).get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            score += 1.0
        elif volume_ratio > 1.2:
            score += 0.5
        
        return max(0, min(10, score))
    
    def _estimate_probability(self, score: float, analysis: Dict) -> float:
        """Оценка вероятности успеха"""
        
        # Базовая вероятность от score
        base_prob = 0.5 + (score - 5) * 0.05  # 0.5 при score=5, 0.75 при score=10
        
        # Корректировка на confidence
        confidence = analysis.get('composite_signal', {}).get('confidence', 0.5)
        adjusted_prob = base_prob * (0.7 + confidence * 0.6)  # 0.7-1.3x multiplier
        
        return round(min(0.95, max(0.3, adjusted_prob)), 2)
    
    def _generate_entry_plan(self, analysis: Dict, ticker: Dict) -> Dict[str, Any]:
        """Генерация плана входа (для LONG или SHORT)"""
        
        current_price = ticker['price']
        h4_indicators = analysis['timeframes'].get('4h', {}).get('indicators', {})
        atr = h4_indicators.get('atr', {}).get('atr_14', current_price * 0.02)
        
        # Определяем направление по сигналу
        composite = analysis.get('composite_signal', {})
        signal = composite.get('signal', 'HOLD')
        
        is_long = signal in ['STRONG_BUY', 'BUY']
        is_short = signal in ['STRONG_SELL', 'SELL']
        
        # Если нет четкого сигнала, определяем по количеству buy/sell сигналов
        if not is_long and not is_short:
            buy_signals = composite.get('buy_signals', 0)
            sell_signals = composite.get('sell_signals', 0)
            is_long = buy_signals > sell_signals
            is_short = sell_signals > buy_signals
        
        # Расчёт SL и TP в зависимости от направления
        if is_short:
            # SHORT: SL выше цены, TP ниже цены
            stop_loss = current_price + (atr * 2)
            take_profit = current_price - (atr * 4)
            side = "short"
        else:
            # LONG: SL ниже цены, TP выше цены (по умолчанию)
            stop_loss = current_price - (atr * 2)
            take_profit = current_price + (atr * 4)
            side = "long"
        
        risk = abs(current_price - stop_loss)
        reward = abs(take_profit - current_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        return {
            "side": side,
            "entry_price": round(current_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "risk_reward": round(risk_reward, 2),
            "position_size_calc": "Use position sizing calculator with your risk %"
        }
    
    def _generate_reasoning(self, analysis: Dict, score: float) -> str:
        """Генерация объяснения почему это хорошая возможность"""
        
        composite = analysis.get('composite_signal', {})
        reasons = composite.get('reasons', [])
        
        if score >= 7.5:
            quality = "ОТЛИЧНАЯ"
        elif score >= 6.5:
            quality = "Хорошая"
        elif score >= 5.5:
            quality = "Средняя"
        else:
            quality = "Слабая"
        
        reasoning = f"{quality} возможность. "
        
        if reasons:
            reasoning += "Факторы: " + "; ".join(reasons[:3])
        
        return reasoning
    
    async def find_oversold_assets(
        self,
        market_type: str = "spot",
        min_volume_24h: float = 1000000
    ) -> List[Dict[str, Any]]:
        """
        Найти перепроданные активы (RSI < 30) с fallback на более мягкие критерии
        
        Args:
            market_type: "spot" или "futures"
            min_volume_24h: Минимальный объём за 24ч
            
        Returns:
            Список перепроданных активов
        """
        logger.info(f"Finding oversold assets on {market_type}")
        
        # Сначала строгие критерии (RSI < 30)
        strict_criteria = {
            "market_type": market_type,
            "min_volume_24h": min_volume_24h,
            "indicators": {
                "rsi_range": [0, 30]
            }
        }
        
        results = await self.scan_market(strict_criteria, limit=10)
        
        # Если мало результатов - смягчаем критерии (RSI < 35)
        if len(results) < 5:
            logger.info(f"Only {len(results)} results with RSI < 30, trying softer criteria (RSI < 35)")
            soft_criteria = {
                "market_type": market_type,
                "min_volume_24h": min_volume_24h,
                "indicators": {
                    "rsi_range": [0, 35]
                }
            }
            soft_results = await self.scan_market(soft_criteria, limit=10)
            
            # Объединяем результаты, убирая дубликаты
            seen_symbols = {r['symbol'] for r in results}
            for r in soft_results:
                if r['symbol'] not in seen_symbols:
                    results.append(r)
                    seen_symbols.add(r['symbol'])
            
            # Сортируем по score
            results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:10]
    
    async def find_overbought_assets(
        self,
        market_type: str = "spot",
        min_volume_24h: float = 1000000
    ) -> List[Dict[str, Any]]:
        """
        Найти перекупленные активы (RSI > 70) для SHORT позиций
        
        Args:
            market_type: "spot" или "futures"
            min_volume_24h: Минимальный объём за 24ч
            
        Returns:
            Список перекупленных активов (шорты)
        """
        logger.info(f"Finding overbought assets on {market_type}")
        
        # Сначала строгие критерии (RSI > 70)
        strict_criteria = {
            "market_type": market_type,
            "min_volume_24h": min_volume_24h,
            "indicators": {
                "rsi_range": [70, 100]
            }
        }
        
        results = await self.scan_market(strict_criteria, limit=10)
        
        # Если мало результатов - смягчаем критерии (RSI > 65)
        if len(results) < 5:
            logger.info(f"Only {len(results)} results with RSI > 70, trying softer criteria (RSI > 65)")
            soft_criteria = {
                "market_type": market_type,
                "min_volume_24h": min_volume_24h,
                "indicators": {
                    "rsi_range": [65, 100]
                }
            }
            soft_results = await self.scan_market(soft_criteria, limit=10)
            
            # Объединяем результаты, убирая дубликаты
            seen_symbols = {r['symbol'] for r in results}
            for r in soft_results:
                if r['symbol'] not in seen_symbols:
                    results.append(r)
                    seen_symbols.add(r['symbol'])
            
            # Сортируем по score
            results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:10]
    
    async def find_breakout_opportunities(
        self,
        market_type: str = "spot",
        min_volume_24h: float = 1000000
    ) -> List[Dict[str, Any]]:
        """
        Найти возможности пробоя (BB squeeze) с параллелизацией
        
        Args:
            market_type: "spot" или "futures"
            min_volume_24h: Минимальный объём
            
        Returns:
            Список активов готовых к пробою
        """
        logger.info(f"Finding breakout opportunities on {market_type}")
        
        # Получаем все тикеры
        all_tickers = await self.client.get_all_tickers(market_type)
        
        # Фильтруем по объёму и ограничиваем количество
        filtered = [
            t for t in all_tickers 
            if t['volume_24h'] >= min_volume_24h
        ][:100]  # Максимум 100 для анализа (было 50)
        
        # Параллельный анализ
        semaphore = asyncio.Semaphore(10)  # Увеличено с 5 до 10
        
        async def check_breakout(ticker: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Проверка одного тикера на BB squeeze"""
            async with semaphore:
                try:
                    analysis = await self.ta.analyze_asset(
                        ticker['symbol'],
                        timeframes=["4h"],
                        include_patterns=False
                    )
                    
                    h4_data = analysis['timeframes'].get('4h', {})
                    bb = h4_data.get('indicators', {}).get('bollinger_bands', {})
                    
                    # Проверка BB squeeze
                    if bb.get('squeeze', False):
                        score = self._calculate_opportunity_score(analysis, ticker)
                        
                        if score >= 6.0:
                            return {
                                "symbol": ticker['symbol'],
                                "current_price": ticker['price'],
                                "bb_width": bb.get('width', 0),
                                "score": score,
                                "type": "BB_SQUEEZE_BREAKOUT",
                                "why": f"BB Squeeze detected (width: {bb.get('width', 0):.2f}%). Готовится к сильному движению."
                            }
                except Exception as e:
                    logger.warning(f"Error analyzing {ticker['symbol']}: {e}")
                
                return None
        
        # Параллельный анализ
        tasks = [check_breakout(ticker) for ticker in filtered]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        opportunities = []
        for result in results:
            if isinstance(result, Exception):
                continue
            if result is not None:
                opportunities.append(result)
        
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities[:10]
    
    async def find_trend_reversals(
        self,
        market_type: str = "spot",
        min_volume_24h: float = 1000000
    ) -> List[Dict[str, Any]]:
        """
        Найти возможности разворота тренда (divergence)
        
        Args:
            market_type: "spot" или "futures"  
            min_volume_24h: Минимальный объём
            
        Returns:
            Список активов с сигналами разворота
        """
        logger.info(f"Finding trend reversals on {market_type}")
        
        # TODO: Реализовать детектор divergence
        # Требует сравнения price movement с RSI/MACD movement
        
        criteria = {
            "market_type": market_type,
            "min_volume_24h": min_volume_24h
        }
        
        return await self.scan_market(criteria, limit=10)
