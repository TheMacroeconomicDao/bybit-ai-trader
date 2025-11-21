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
        
        # 1. Get BTC Analysis first
        try:
            btc_analysis = await self.ta.analyze_asset("BTC/USDT", timeframes=["1h", "4h"])
            btc_trend = btc_analysis.get('timeframes', {}).get('4h', {}).get('trend', {}).get('direction', 'neutral')
        except Exception as e:
            logger.warning(f"Failed to analyze BTC: {e}")
            btc_trend = "neutral"
            btc_analysis = {}

        # 2. Get Account Balance for dynamic risk management
        # ВАЖНО: Balance используется для position sizing, но НЕ блокирует анализ
        account_balance = None
        try:
            account_info = await self.client.get_account_info()
            account_balance = float(account_info.get("balance", {}).get("total", 0.0))
            
            if account_balance is None or account_balance <= 0:
                logger.warning(f"⚠️ Invalid account balance: {account_balance}. Position sizing will be unavailable.")
                account_balance = None
            else:
                logger.info(f"✅ Account balance retrieved: ${account_balance:.2f}")
                
        except Exception as e:
            logger.warning(f"⚠️ Cannot get wallet balance: {e}. Continuing without position sizing.")
            logger.warning("   Analysis will work, but position sizes won't be calculated.")
            account_balance = None
            # НЕ прерываем выполнение - продолжаем анализ
            
        # 3. Get Open Positions for correlation check
        open_positions_symbols = []
        try:
            open_positions_data = await self.client.get_open_positions()
            open_positions_symbols = [p['symbol'] for p in open_positions_data]
            if open_positions_symbols:
                logger.info(f"Found open positions: {open_positions_symbols}. Will check correlation.")
        except Exception as e:
            logger.warning(f"Failed to get open positions: {e}")
        
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
            
            # Skip if already in open positions
            if ticker['symbol'] in open_positions_symbols:
                return None
                
            async with semaphore:
                try:
                    # Correlation Check
                    if open_positions_symbols:
                        is_correlated = False
                        for pos_symbol in open_positions_symbols:
                            corr = await self.ta.get_correlation(ticker['symbol'], pos_symbol)
                            if corr > 0.7:
                                # logger.debug(f"Skipping {ticker['symbol']} - high correlation ({corr:.2f}) with {pos_symbol}")
                                is_correlated = True
                                break
                        if is_correlated:
                            return None

                    analysis = await self.ta.analyze_asset(
                        ticker['symbol'],
                        timeframes=["1h", "4h"],
                        include_patterns=True
                    )
                    
                    # Проверка индикаторных критериев
                    indicator_criteria = criteria.get('indicators', {})
                    if not self._check_indicator_criteria(analysis, indicator_criteria):
                        return None
                    
                    # Entry plan (FIRST) - Pass account_balance
                    # ВАЖНО: Если баланс недоступен, entry_plan будет с предупреждением
                    entry_plan = self._generate_entry_plan(analysis, ticker, account_balance)
                    
                    # Scoring (SECOND) - Pass risk_reward from plan
                    score_data = self._calculate_opportunity_score(analysis, ticker, btc_trend, entry_plan)
                    score = score_data["total"]
                    
                    return {
                        "symbol": ticker['symbol'],
                        "current_price": ticker['price'],
                        "change_24h": ticker['change_24h'],
                        "volume_24h": ticker['volume_24h'],
                        "score": score,
                        "score_breakdown": score_data["breakdown"],
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
    
    
    def _calculate_opportunity_score(self, analysis: Dict, ticker: Dict, btc_trend: str = "neutral", entry_plan: Dict = None) -> Dict[str, Any]:
        """
        15-POINT CONFLUENCE MATRIX (SIMPLIFIED - NO PARANOID STOPS)
        
        CLASSIC TA (6 points):
        1. Trend Alignment: 0-2
        2. Indicators: 0-2
        3. Pattern: 0-1
        4. S/R Level: 0-1
        
        ORDER FLOW (4 points):
        5. CVD + Aggressive: 0-2
        6. Volume: 0-1
        7. BTC Support: 0-1
        
        SMART MONEY (3 points):
        8. Order Blocks: 0-1
        9. FVG: 0-1
        10. BOS/ChoCh: 0-1
        
        BONUSES (2 points):
        11. R:R ≥ 2.5: 0-1
        12. ADX > 25: 0-1
        
        РЕКОМЕНДАЦИИ:
        7.0+/15 = Можно рассмотреть (с warning)
        10.0+/15 = Recommended
        12.0+/15 = Strong
        13.5+/15 = Excellent
        """
        
        score = 0.0
        breakdown = {}
        
        composite = analysis.get('composite_signal', {})
        signal = composite.get('signal', 'HOLD')
        is_long = signal in ['STRONG_BUY', 'BUY']
        is_short = signal in ['STRONG_SELL', 'SELL']
        
        if not is_long and not is_short:
            buy_signals = composite.get('buy_signals', 0)
            sell_signals = composite.get('sell_signals', 0)
            is_long = buy_signals > sell_signals
            is_short = sell_signals > buy_signals
        
        h4_data = analysis.get('timeframes', {}).get('4h', {})
        current_price = ticker['price']
        
        # === CLASSIC TA (6 points) ===
        
        # 1. Trend Alignment (0-2)
        alignment = composite.get('alignment', 0.5)
        h4_trend = h4_data.get('trend', {}).get('direction', 'neutral')
        
        trend_score = 0.0
        if alignment >= 0.8: trend_score = 2.0
        elif alignment >= 0.6: trend_score = 1.5
        elif alignment >= 0.5: trend_score = 1.0
        
        if is_long and h4_trend == 'uptrend': trend_score = min(2.0, trend_score + 0.5)
        if is_short and h4_trend == 'downtrend': trend_score = min(2.0, trend_score + 0.5)
        
        breakdown['trend'] = min(2.0, trend_score)
        score += breakdown['trend']
        
        # 2. Indicators (0-2)
        comp_score = abs(composite.get('score', 0))
        if comp_score >= 7: indicator_score = 2.0
        elif comp_score >= 5: indicator_score = 1.5
        elif comp_score >= 3: indicator_score = 1.0
        else: indicator_score = 0.5
        
        breakdown['indicators'] = indicator_score
        score += indicator_score
        
        # 3. Pattern (0-1)
        patterns = h4_data.get('patterns', {}).get('candlestick', [])
        pattern_score = 0.0
        for p in patterns:
            if (is_long and p['type'] == 'bullish') or (is_short and p['type'] == 'bearish'):
                pattern_score = 1.0
                break
        breakdown['pattern'] = pattern_score
        score += pattern_score
        
        # 4. S/R Level (0-1)
        levels = h4_data.get('levels', {})
        sr_score = 0.5
        
        if is_long:
            supports = levels.get('support', [])
            if supports:
                closest = max([s for s in supports if s < current_price], default=0)
                if closest > 0:
                    dist_pct = (current_price - closest) / current_price
                    if dist_pct < 0.02: sr_score = 1.0
                    elif dist_pct < 0.05: sr_score = 0.8
        elif is_short:
            resistances = levels.get('resistance', [])
            if resistances:
                closest = min([r for r in resistances if r > current_price], default=float('inf'))
                if closest != float('inf'):
                    dist_pct = (closest - current_price) / current_price
                    if dist_pct < 0.02: sr_score = 1.0
                    elif dist_pct < 0.05: sr_score = 0.8
        
        breakdown['sr_level'] = sr_score
        score += sr_score
        
        # === ORDER FLOW (4 points) ===
        
        # 5. CVD + Aggressive (0-2)
        cvd_score = 0.0
        cvd_data = analysis.get('cvd_analysis', {})
        signal_type = cvd_data.get('signal', 'NONE')
        aggressive_ratio = cvd_data.get('aggressive_ratio', 1.0)
        
        if signal_type == 'BULLISH_ABSORPTION' and is_long:
            cvd_score = 2.0
        elif signal_type == 'BEARISH_ABSORPTION' and is_short:
            cvd_score = 2.0
        elif signal_type == 'AGGRESSIVE_BUYING' and is_long:
            cvd_score = 1.5
        elif signal_type == 'AGGRESSIVE_SELLING' and is_short:
            cvd_score = 1.5
        elif signal_type == 'BEARISH_ABSORPTION' and is_long:
            cvd_score = -1.0
        elif signal_type == 'BULLISH_ABSORPTION' and is_short:
            cvd_score = -1.0
        
        breakdown['cvd'] = cvd_score
        score += cvd_score
        
        # 6. Volume (0-1)
        vol_ratio = h4_data.get('indicators', {}).get('volume', {}).get('volume_ratio', 1.0)
        vol_score = 0.0
        if vol_ratio >= 2.0: vol_score = 1.0
        elif vol_ratio >= 1.5: vol_score = 0.8
        elif vol_ratio >= 1.2: vol_score = 0.5
        
        breakdown['volume'] = vol_score
        score += vol_score
        
        # 7. BTC Support (0-1)
        btc_score = 0.0
        if is_long:
            if btc_trend == 'uptrend': btc_score = 1.0
            elif btc_trend == 'sideways': btc_score = 0.5
        elif is_short:
            if btc_trend == 'downtrend': btc_score = 1.0
            elif btc_trend == 'sideways': btc_score = 0.5
        
        breakdown['btc_support'] = btc_score
        score += btc_score
        
        # === SMART MONEY (3 points) ===
        
        # 8. Order Blocks (0-1)
        ob_score = 0.0
        order_blocks = h4_data.get('order_blocks', [])
        
        if is_long:
            has_bullish_ob = any(ob['type'] == 'bullish_ob' for ob in order_blocks)
            if has_bullish_ob: ob_score = 1.0
        elif is_short:
            has_bearish_ob = any(ob['type'] == 'bearish_ob' for ob in order_blocks)
            if has_bearish_ob: ob_score = 1.0
        
        breakdown['order_blocks'] = ob_score
        score += ob_score
        
        # 9. FVG (0-1)
        fvg_score = 0.0
        fvgs = h4_data.get('fair_value_gaps', [])
        
        if is_long:
            bullish_fvgs = [fvg for fvg in fvgs if fvg['type'] == 'bullish_fvg']
            if bullish_fvgs:
                closest = bullish_fvgs[0]
                dist_pct = abs(current_price - closest['mid']) / current_price * 100
                if dist_pct < 2.0:
                    fvg_score = 1.0 if closest['strength'] == 'strong' else 0.75
        elif is_short:
            bearish_fvgs = [fvg for fvg in fvgs if fvg['type'] == 'bearish_fvg']
            if bearish_fvgs:
                closest = bearish_fvgs[0]
                dist_pct = abs(current_price - closest['mid']) / current_price * 100
                if dist_pct < 2.0:
                    fvg_score = 1.0 if closest['strength'] == 'strong' else 0.75
        
        breakdown['fvg'] = fvg_score
        score += fvg_score
        
        # 10. BOS/ChoCh (0-1)
        structure_score = 0.0
        structure = h4_data.get('structure', {})
        
        if is_long:
            bos_events = structure.get('bos', [])
            bullish_bos = [e for e in bos_events if e['type'] == 'bullish_bos']
            if bullish_bos: structure_score = 1.0
        elif is_short:
            bos_events = structure.get('bos', [])
            bearish_bos = [e for e in bos_events if e['type'] == 'bearish_bos']
            if bearish_bos: structure_score = 1.0
        
        breakdown['structure'] = structure_score
        score += structure_score
        
        # === BONUSES (2 points) ===
        
        # 11. R:R ≥ 2.5 (0-1)
        rr_score = 0.0
        if entry_plan:
            risk_reward = entry_plan.get('risk_reward', 0)
            if risk_reward >= 3.0: rr_score = 1.0
            elif risk_reward >= 2.5: rr_score = 0.75
            elif risk_reward >= 2.0: rr_score = 0.5
        
        breakdown['risk_reward'] = rr_score
        score += rr_score
        
        # 12. ADX > 25 (0-1)
        adx = h4_data.get('indicators', {}).get('adx', {}).get('adx', 0)
        adx_score = 0.0
        if adx > 30: adx_score = 1.0
        elif adx > 25: adx_score = 0.75
        elif adx > 20: adx_score = 0.5
        
        breakdown['trend_strength'] = adx_score
        score += adx_score
        
        # Ограничиваем score в диапазоне 0-15
        final_score = min(15.0, max(0.0, score))
        
        # Логируем финальный score
        symbol = ticker.get('symbol', 'UNKNOWN')
        logger.info(f"{symbol}: 15-point score = {final_score:.2f}/15")
        
        # Добавляем warning если score низкий
        warning = None
        if final_score < 7.0:
            warning = f"⚠️ Score {final_score:.1f}/15 too low - not recommended"
        elif final_score < 10.0:
            warning = f"⚠️ Score {final_score:.1f}/15 below recommended minimum (need 10.0+)"
        
        return {
            "total": final_score,
            "breakdown": breakdown,
            "blocked": False,
            "reason": None,
            "warning": warning
        }
    
    def _estimate_probability(self, score: float, analysis: Dict) -> float:
        """
        Оценка вероятности для 15-point системы (SIMPLIFIED)
        
        Score 7.0/15 = 50% probability (can consider)
        Score 10.0/15 = 70% probability (recommended)
        Score 12.0/15 = 80% probability (strong)
        Score 13.5/15 = 90% probability (excellent)
        
        Args:
            score: Confluence score (0-15)
            analysis: Полный анализ актива
        
        Returns:
            Вероятность успеха (0.30-0.95)
        """
        composite = analysis.get('composite_signal', {})
        confidence = composite.get('confidence', 0.7)
        
        # Базовая вероятность от 15-point score
        # Простая линейная формула: score/15 * 1.35
        # 7/15 = 0.46 * 1.35 = 0.62 → ~0.50 после adjustment
        # 10/15 = 0.67 * 1.35 = 0.90 → ~0.70 после adjustment
        # 12/15 = 0.80 * 1.35 = 1.08 → ~0.80 после adjustment
        base_prob = min(0.95, max(0.30, (score / 15.0) * 1.35))
        
        # Умножаем на confidence (but keep reasonable)
        adjusted_prob = base_prob * max(0.7, confidence)
        
        return round(min(0.95, max(0.30, adjusted_prob)), 2)
    
    def _generate_entry_plan(self, analysis: Dict, ticker: Dict, account_balance: Optional[float] = None, risk_percent: float = 0.02) -> Dict[str, Any]:
        """Генерация плана входа (для LONG или SHORT) с Динамическим риск-менеджментом
        
        ВАЖНО: account_balance должен быть передан из get_account_info()!
        Если None - вернёт план с предупреждением о недоступности баланса.
        """
        
        # Проверка баланса - если нет, возвращаем план без position sizing
        if account_balance is None or account_balance <= 0:
            logger.warning(f"⚠️ Account balance unavailable ({account_balance}). Entry plan will not include position sizing.")
            # Продолжаем генерацию плана без position sizing
        
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
        
        risk_per_share = abs(current_price - stop_loss)
        reward_per_share = abs(take_profit - current_price)
        risk_reward = reward_per_share / risk_per_share if risk_per_share > 0 else 0
        
        # DYNAMIC RISK MANAGEMENT
        risk_usd = 0.0
        qty = 0.0
        position_value = 0.0
        warning = None

        if account_balance and account_balance > 0:
            # Баланс доступен - рассчитываем position size
            risk_usd = account_balance * risk_percent
            
            if risk_per_share > 0:
                qty = risk_usd / risk_per_share
            else:
                qty = 0
                
            qty = round(qty, 6)
            position_value = qty * current_price
            
            logger.info(f"✅ Position calculated: {qty} units = ${position_value:.2f}")
        else:
            # Баланс НЕ доступен - возвращаем план без sizing
            warning = (
                "⚠️ ВНИМАНИЕ: Account balance недоступен! "
                "Position size НЕ рассчитан. "
                "Это НЕ ошибка - анализ валиден, но размер позиции нужно рассчитать вручную."
            )
            logger.warning(warning)
        
        result = {
            "side": side,
            "entry_price": round(current_price, 4),
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4),
            "risk_reward": round(risk_reward, 2),
            "recommended_size": qty,
            "recommended_value_usd": round(position_value, 2),
            "risk_usd": round(risk_usd, 2),
            "max_risk_allowed": round(risk_usd, 2),
            "leverage_hint": "Use 1x-3x max",
            "position_size_calc": f"Risk ${risk_usd:.2f} / Stop Dist {risk_per_share:.4f} = {qty} units" if account_balance else "BALANCE UNAVAILABLE - CANNOT CALCULATE"
        }
        
        if warning:
            result["warning"] = warning
            result["balance_available"] = False
        else:
            result["balance_available"] = True
        
        return result
    
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
