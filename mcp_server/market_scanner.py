"""
Market Scanner
Сканирование рынка для поиска торговых возможностей
"""

import asyncio
from typing import Dict, List, Any, Optional
from loguru import logger

# Импорты для advanced features
try:
    from .whale_detector import WhaleDetector
    from .volume_profile import VolumeProfileAnalyzer
    from .session_manager import SessionManager
except ImportError:
    from whale_detector import WhaleDetector
    from volume_profile import VolumeProfileAnalyzer
    from session_manager import SessionManager

# NEW: Institutional modules imports
try:
    from .tier_classifier import TierClassifier
    from .regime_detector import RegimeDetector
    from .adaptive_thresholds import AdaptiveThresholds
    from .smart_display import SmartDisplay
except ImportError:
    from tier_classifier import TierClassifier
    from regime_detector import RegimeDetector
    from adaptive_thresholds import AdaptiveThresholds
    from smart_display import SmartDisplay

# OPTIONAL: ML predictor
try:
    from .ml_probability_predictor import MLProbabilityPredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    MLProbabilityPredictor = None


class MarketScanner:
    """Сканер рынка для поиска торговых возможностей"""
    
    def __init__(self, bybit_client, technical_analysis):
        self.client = bybit_client
        self.ta = technical_analysis
        
        # Advanced modules
        self.whale_detector = WhaleDetector(bybit_client)
        self.volume_profile = VolumeProfileAnalyzer(bybit_client)
        self.session_manager = SessionManager()
        
        # NEW: Institutional modules
        self.tier_classifier = TierClassifier()
        self.regime_detector = RegimeDetector()
        
        # NEW: ML predictor (optional)
        self.ml_predictor = None
        if ML_AVAILABLE:
            self.ml_predictor = MLProbabilityPredictor()
            if self.ml_predictor.model_available():
                logger.info("✅ ML probability predictor enabled")
        
        logger.info("Market Scanner initialized (institutional mode)")
    
    async def scan_market(
        self,
        criteria: Dict[str, Any],
        limit: int = 10,
        auto_track: bool = False,
        signal_tracker: Optional[Any] = None,
        track_limit: int = 3
    ) -> Dict[str, Any]:
        """
        Универсальное сканирование рынка по критериям
        
        Args:
            criteria: Критерии фильтрации
            limit: Максимальное количество результатов
            auto_track: Автоматически записывать топ-N сигналов в tracker
            signal_tracker: SignalTracker для записи сигналов (если auto_track=True)
            track_limit: Количество топ сигналов для записи (по умолчанию 3)
            
        Returns:
            Dict с ключами:
            - success: bool
            - opportunities: List[Dict] или []
            - error: Optional[str]
            - scanned_count: int
            - found_count: int
        """
        try:
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
            
            # Сохраняем BTC анализ для publish_market_analysis
            try:
                from pathlib import Path
                from datetime import datetime
                import json
                
                btc_file = Path(__file__).parent.parent / "data" / "btc_analysis.json"
                btc_file.parent.mkdir(exist_ok=True)
                
                # Извлекаем необходимые данные из btc_analysis
                h4_indicators = btc_analysis.get('timeframes', {}).get('4h', {}).get('indicators', {})
                
                btc_data = {
                    "timestamp": datetime.now().isoformat(),
                    "status": "bearish" if btc_trend == "downtrend" else "bullish" if btc_trend == "uptrend" else "neutral",
                    "trend": btc_analysis.get('composite_signal', {}).get('signal', 'HOLD'),
                    "rsi_values": [
                        btc_analysis.get('timeframes', {}).get('1h', {}).get('indicators', {}).get('rsi', {}).get('rsi_14', 50),
                        h4_indicators.get('rsi', {}).get('rsi_14', 50),
                        btc_analysis.get('timeframes', {}).get('1d', {}).get('indicators', {}).get('rsi', {}).get('rsi_14', 50)
                    ],
                    "adx": h4_indicators.get('adx', {}).get('adx', 20),
                    "price": btc_analysis.get('timeframes', {}).get('4h', {}).get('current_price', 0),
                    "change_24h": 0  # TODO: добавить если доступно
                }
                
                with open(btc_file, 'w', encoding='utf-8') as f:
                    json.dump(btc_data, f, indent=2)
                
                logger.debug("BTC analysis saved")
            except Exception as e:
                logger.warning(f"Failed to save BTC analysis: {e}")
                
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
            try:
                all_tickers = await self.client.get_all_tickers(
                    market_type=criteria.get('market_type', 'spot')
                )
            except Exception as e:
                logger.error(f"Failed to get tickers: {e}")
                return {
                    "success": False,
                    "opportunities": [],
                    "error": f"Failed to fetch market tickers: {str(e)}",
                    "scanned_count": 0,
                    "found_count": 0
                }
            
            # Проверяем, что получили данные
            if not all_tickers or len(all_tickers) == 0:
                logger.error("No tickers received from API")
                return {
                    "success": False,
                    "opportunities": [],
                    "error": "API Error: No tickers received from Bybit API",
                    "scanned_count": 0,
                    "found_count": 0
                }
            
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
                
                # ═══════════════════════════════════════════════════════
                # НОВОЕ: Фильтрация стейбл/стейбл пар
                # ═══════════════════════════════════════════════════════
                if self._is_stable_stable_pair(ticker['symbol']):
                    logger.debug(f"Skipping stable/stable pair: {ticker['symbol']}")
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
                        
                        # Whale Analysis (опционально, если enabled и volume достаточен)
                        enable_whale_analysis = criteria.get('include_whale_analysis', False)
                        if enable_whale_analysis and ticker.get('volume_24h', 0) > 5000000:
                            try:
                                whale_data = await self.whale_detector.detect_whale_activity(ticker['symbol'])
                                analysis['whale_analysis'] = whale_data
                                logger.debug(f"Whale analysis added for {ticker['symbol']}")
                            except Exception as e:
                                logger.warning(f"Failed whale analysis for {ticker['symbol']}: {e}")
                        
                        # Volume Profile (для топ по volume или если enabled)
                        enable_volume_profile = criteria.get('include_volume_profile', False)
                        if enable_volume_profile or (enable_whale_analysis and ticker.get('volume_24h', 0) > 5000000):
                            try:
                                vp_data = await self.volume_profile.calculate_volume_profile(
                                    ticker['symbol'],
                                    timeframe="4h"
                                )
                                # Добавляем VP в h4 data для использования в scoring
                                if '4h' in analysis.get('timeframes', {}):
                                    analysis['timeframes']['4h']['volume_profile'] = vp_data
                                logger.debug(f"Volume profile added for {ticker['symbol']}")
                            except Exception as e:
                                logger.warning(f"Failed volume profile for {ticker['symbol']}: {e}")
                        
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
            
            # ═══════════════════════════════════════════════════════
            # NEW: Institutional pipeline - NO HARD FILTERING!
            # ═══════════════════════════════════════════════════════
            
            # Get regime and adaptive thresholds
            btc_full = await self.ta.analyze_asset("BTC/USDT", timeframes=["1h", "4h", "1d"])
            market_regime = self.regime_detector.detect(btc_full)
            adaptive_thresholds = AdaptiveThresholds.calculate(market_regime)
            
            logger.info(
                f"Regime: {market_regime['type']}, "
                f"Thresholds: LONG={adaptive_thresholds['long']:.1f}, SHORT={adaptive_thresholds['short']:.1f}"
            )
            
            # Normalize ALL scores immediately (20-point → 10-point)
            for opp in opportunities:
                raw_score = opp.get("score", 0)
                normalized = (raw_score / 20.0) * 10.0
                opp["score"] = round(normalized, 2)
                opp["confluence_score"] = round(normalized, 2)
                opp["final_score"] = round(normalized, 2)
                opp["raw_score_20"] = raw_score
            
            # Classify tiers for ALL opportunities
            for opp in opportunities:
                entry_plan = opp.get("entry_plan", {})
                tier = self.tier_classifier.classify(
                    score=opp["score"],
                    probability=opp.get("probability", 0.5),
                    risk_reward=entry_plan.get("risk_reward", 2.0)
                )
                opp["tier"] = tier
                opp["tier_color"] = self.tier_classifier.get_tier_color(tier)
                opp["tier_name"] = self.tier_classifier.get_tier_name(tier)
                opp["tier_recommendation"] = self.tier_classifier.get_recommendation(tier)
                opp["position_size_multiplier"] = self.tier_classifier.get_position_size_multiplier(tier)
            
            # Separate LONG and SHORT directions
            all_longs = [o for o in opportunities if o.get("entry_plan", {}).get("side") == "long"]
            all_shorts = [o for o in opportunities if o.get("entry_plan", {}).get("side") == "short"]
            
            all_longs.sort(key=lambda x: x["score"], reverse=True)
            all_shorts.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"Direction split: {len(all_longs)} LONGS, {len(all_shorts)} SHORTS")
            
            # Smart display selection (TOP-3 each direction with warnings)
            top_longs = SmartDisplay.select_top_3_with_warnings(
                all_longs[:limit],
                adaptive_thresholds["long"],
                market_regime
            )
            
            top_shorts = SmartDisplay.select_top_3_with_warnings(
                all_shorts[:limit],
                adaptive_thresholds["short"],
                market_regime
            )
            
            # ✅ УБЕДИТЬСЯ что даже если сигналов мало, показываем лучшие:
            if len(top_longs) < 3 and len(all_longs) > 0:
                # Добавляем недостающие из all_longs (даже если score низкий)
                for opp in all_longs[len(top_longs):3]:
                    if opp.get("score", 0) >= 3.0:  # Минимум 3.0/20
                        top_longs.append(opp)
            
            if len(top_shorts) < 3 and len(all_shorts) > 0:
                # Добавляем недостающие из all_shorts
                for opp in all_shorts[len(top_shorts):3]:
                    if opp.get("score", 0) >= 3.0:  # Минимум 3.0/20
                        top_shorts.append(opp)
            
            logger.info(f"Display: TOP-{len(top_longs)} LONGS, TOP-{len(top_shorts)} SHORTS")
            
            # ML enhancement if available
            if self.ml_predictor and self.ml_predictor.model_available():
                for opp in top_longs + top_shorts:
                    ml_prob = self.ml_predictor.predict_probability(
                        confluence_score=opp["score"],
                        volume_ratio=opp.get("volume_ratio", 1.0),
                        btc_aligned=opp.get("btc_aligned", False),
                        rsi_14=opp.get("rsi_14", 50),
                        risk_reward=opp.get("risk_reward", 2.0),
                        pattern_type=opp.get("pattern_type", "unknown"),
                        session=self.session_manager.get_current_session() if self.session_manager else "neutral"
                    )
                    opp["ml_probability"] = ml_prob
                    opp["static_probability"] = opp["probability"]
                    opp["probability"] = round((opp["probability"] + ml_prob) / 2, 2)
            
            # Combine for backward compatibility (but split is primary)
            final_opportunities = top_longs + top_shorts
            
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
            
            # ✅ INSTITUTIONAL SUCCESS RESPONSE
            tier_distribution = {
                "elite": sum(1 for o in opportunities if o.get("tier") == "elite"),
                "professional": sum(1 for o in opportunities if o.get("tier") == "professional"),
                "speculative": sum(1 for o in opportunities if o.get("tier") == "speculative"),
                "high_risk": sum(1 for o in opportunities if o.get("tier") == "high_risk")
            }
            
            return {
                "success": True,
                "opportunities": final_opportunities,  # Backward compatibility
                "market_regime": market_regime,
                "adaptive_thresholds": adaptive_thresholds,
                "top_3_longs": top_longs,
                "top_3_shorts": top_shorts,
                "all_longs_count": len(all_longs),
                "all_shorts_count": len(all_shorts),
                "tier_distribution": tier_distribution,
                "total_scanned": len(candidates),
                "total_analyzed": len(opportunities),
                "error": None,
                "scanned_count": len(candidates),  # Backward compatibility
                "found_count": len(final_opportunities)  # Backward compatibility
            }
            
        except Exception as e:
            # ✅ ERROR RESPONSE (не бросаем исключение!)
            logger.error(f"Error in scan_market: {e}", exc_info=True)
            return {
                "success": False,
                "opportunities": [],
                "error": str(e),
                "scanned_count": 0,
                "found_count": 0
            }
    
    @staticmethod
    def _is_stable_stable_pair(symbol: str) -> bool:
        """
        Проверка, является ли пара СТЕЙБЛ/СТЕЙБЛ
        
        Исключаем:
        - USDC/USDT, BUSD/USDT (стейбл/стейбл)
        - USDT/TRY, USDT/BRL (стейбл/фиат)
        - RLUSD/USDT и подобные
        
        НЕ исключаем:
        - BTC/USDT, ETH/USDT (крипта/стейбл)
        """
        if not symbol:
            return False
        
        # Список стабильных монет и фиатов
        stablecoins = {
            'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 
            'USDP', 'USDD', 'FRAX', 'LUSD', 'MIM', 'RLUSD'
        }
        fiats = {'TRY', 'BRL', 'EUR', 'GBP', 'AUD', 'RUB'}
        stable_and_fiat = stablecoins | fiats
        
        # Нормализуем символ
        symbol_upper = symbol.upper().replace('/', '').replace('-', '').replace(':', '')
        
        # Проверяем все комбинации
        for stable1 in stable_and_fiat:
            if symbol_upper.endswith(stable1):
                base = symbol_upper[:-len(stable1)]
                if base in stable_and_fiat:
                    return True
            if symbol_upper.startswith(stable1):
                quote = symbol_upper[len(stable1):]
                if quote in stable_and_fiat:
                    return True
        
        return False
    
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
        20-POINT CONFLUENCE MATRIX с PENALTIES для слабых сигналов
        
        ВАЖНО: Penalties применяются ПЕРЕД основным scoring!
        """
        score = 0.0
        breakdown = {}
        penalties = []  # НОВОЕ: список примененных penalties
        warnings = []   # НОВОЕ: список warnings
        
        composite = analysis.get('composite_signal', {})
        signal = composite.get('signal', 'HOLD')
        confidence = composite.get('confidence', 0.5)
        
        # ═══════════════════════════════════════════════════════
        # PENALTY PHASE: Применяем penalties ПЕРЕД scoring
        # ═══════════════════════════════════════════════════════
        
        # PENALTY #1: Composite Signal HOLD
        if signal == 'HOLD':
            penalty = -2.0
            score += penalty
            penalties.append(f"HOLD signal: {penalty:.1f}")
            breakdown['hold_penalty'] = penalty
            warnings.append("⚠️ Composite signal is HOLD (uncertainty)")
            
            # Дополнительный penalty если confidence низкая
            if confidence < 0.5:
                additional_penalty = -1.0
                score += additional_penalty
                penalties.append(f"HOLD + low confidence ({confidence:.2f}): {additional_penalty:.1f}")
                breakdown['hold_low_conf_penalty'] = additional_penalty
                warnings.append(f"⚠️ Very low confidence ({confidence:.2f})")
        
        # PENALTY #2: Low Confidence (независимо от signal)
        if confidence < 0.4:
            penalty = -1.5
            score += penalty
            penalties.append(f"Very low confidence ({confidence:.2f}): {penalty:.1f}")
            breakdown['low_confidence_penalty'] = penalty
            warnings.append(f"🔴 Critical: Confidence too low ({confidence:.2f} < 0.4)")
        
        # Определяем направление (после penalties, но до основного scoring)
        is_long = signal in ['STRONG_BUY', 'BUY']
        is_short = signal in ['STRONG_SELL', 'SELL']
        
        if not is_long and not is_short:
            buy_signals = composite.get('buy_signals', 0)
            sell_signals = composite.get('sell_signals', 0)
            is_long = buy_signals > sell_signals
            is_short = sell_signals > buy_signals
        
        # PENALTY #3: Volume на коротких TF (для скальпинга)
        entry_timeframe = entry_plan.get('entry_timeframe', '5m') if entry_plan else '5m'
        
        if entry_timeframe in ['1m', '5m', '15m']:
            volume_penalties = self._check_scalping_volume_penalties(analysis, entry_timeframe, is_long)
            if volume_penalties:
                total_vol_penalty = sum(volume_penalties.values())
                score += total_vol_penalty
                penalties.append(f"Low volume on short TF: {total_vol_penalty:.1f}")
                breakdown['volume_penalties'] = volume_penalties
                warnings.append(f"⚠️ Low volume detected on {entry_timeframe}")
        
        # PENALTY #4: MACD Alignment на коротких TF
        if entry_timeframe in ['1m', '5m', '15m']:
            macd_penalty = self._check_macd_alignment_penalty(analysis, is_long, entry_timeframe)
            if macd_penalty < 0:
                score += macd_penalty
                penalties.append(f"MACD contradiction: {macd_penalty:.1f}")
                breakdown['macd_penalty'] = macd_penalty
                warnings.append("⚠️ MACD contradicts direction on short timeframes")
        
        # ═══════════════════════════════════════════════════════
        # SCORING PHASE: Продолжаем обычный scoring
        # ═══════════════════════════════════════════════════════
        
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
        
        # === BONUSES & ADVANCED (6 points) ===
        
        # 11. Liquidity Grab (0-1)
        grab_score = 0.0
        grabs = h4_data.get('liquidity_grabs', [])
        if is_long and any(g['type'] == 'bullish_grab' for g in grabs):
            grab_score = 1.0 if grabs[0].get('strength') == 'strong' else 0.5
        elif is_short and any(g['type'] == 'bearish_grab' for g in grabs):
            grab_score = 1.0 if grabs[0].get('strength') == 'strong' else 0.5
        breakdown['liquidity_grab'] = grab_score
        score += grab_score
        
        # 12. Session Timing (0-1)
        session_score = 0.0
        session = self.session_manager.get_current_session()
        if session == "overlap": session_score = 1.0
        elif session in ["european", "us"]: session_score = 0.75
        elif session == "asian": session_score = 0.25
        breakdown['session'] = session_score
        score += session_score
        
        # 13. R:R ≥2.5 (0-1)
        rr_score = 0.0
        if entry_plan:
            rr = entry_plan.get('risk_reward', 0)
            if rr >= 3.0: rr_score = 1.0
            elif rr >= 2.5: rr_score = 0.75
            elif rr >= 2.0: rr_score = 0.5
        breakdown['risk_reward'] = rr_score
        score += rr_score
        
        # 14. ADX >25 (0-1)
        adx = h4_data.get('indicators', {}).get('adx', {}).get('adx', 0)
        adx_score = 1.0 if adx > 30 else 0.75 if adx > 25 else 0.5 if adx > 20 else 0.0
        breakdown['trend_strength'] = adx_score
        score += adx_score
        
        # 15. Whale Activity (0-1) - НОВЫЙ!
        whale_score = 0.0
        whale_data = analysis.get('whale_analysis', {})
        if whale_data:
            activity = whale_data.get('whale_activity', 'neutral')
            flow = whale_data.get('flow_direction', 'neutral')
            
            if is_long and activity == "accumulation" and flow in ["bullish", "strong_bullish"]:
                whale_score = 1.0
            elif is_short and activity == "distribution" and flow in ["bearish", "strong_bearish"]:
                whale_score = 1.0
            elif (is_long and flow == "bullish") or (is_short and flow == "bearish"):
                whale_score = 0.5
        breakdown['whale'] = whale_score
        score += whale_score
        
        # 16. Volume Profile (0-1) - НОВЫЙ!
        vp_score = 0.0
        vp_data = h4_data.get('volume_profile', {})
        if vp_data:
            position = vp_data.get('current_position', 'unknown')
            near_poc = vp_data.get('confluence_with_poc', False)
            
            if is_long and (position == "below_va" or near_poc):
                vp_score = 1.0
            elif is_short and (position == "above_va" or near_poc):
                vp_score = 1.0
            elif position == "in_va":
                vp_score = 0.5
        breakdown['volume_profile'] = vp_score
        score += vp_score
        
        # НОВЫЙ MAXIMUM: 20 points (но может быть отрицательным после penalties!)
        final_score = min(20.0, max(-5.0, score))  # Разрешаем до -5.0 для очень плохих
        
        # Добавляем penalties и warnings в breakdown
        breakdown['penalties_applied'] = penalties
        breakdown['warnings'] = warnings
        breakdown['penalties_total'] = sum([
            p for p in breakdown.values() 
            if isinstance(p, (int, float)) and p < 0
        ])
        
        # Генерируем warning сообщение
        warning = self._generate_warning_from_penalties(penalties, warnings) if penalties else None
        
        # Логируем финальный score с penalties
        symbol = ticker.get('symbol', 'UNKNOWN')
        if penalties:
            logger.info(
                f"{symbol}: Applied {len(penalties)} penalties, "
                f"total: {breakdown.get('penalties_total', 0):.1f}, "
                f"final score: {final_score:.2f}/20"
            )
        else:
            logger.info(f"{symbol}: 20-point score = {final_score:.2f}/20")
        
        return {
            "total": final_score,
            "breakdown": breakdown,
            "system": "20-point-advanced-with-penalties",
            "blocked": False,  # НЕ блокируем, только снижаем score
            "reason": None,
            "warning": warning
        }
    
    def _check_scalping_volume_penalties(
        self,
        analysis: Dict,
        entry_timeframe: str,
        is_long: bool
    ) -> Dict[str, float]:
        """
        Проверка volume на коротких TF и применение penalties
        
        Args:
            analysis: Полный анализ актива
            entry_timeframe: Таймфрейм входа ('1m', '5m', '15m')
            is_long: True для LONG, False для SHORT
        
        Returns:
            Dict с penalties по каждому TF: {"1m": -1.5, "5m": -1.0, ...}
        """
        penalties = {}
        short_tfs = ['1m', '5m', '15m']
        
        for tf in short_tfs:
            tf_data = analysis.get('timeframes', {}).get(tf, {})
            if 'error' in tf_data:
                continue
            
            vol_data = tf_data.get('indicators', {}).get('volume', {})
            vol_ratio = vol_data.get('volume_ratio', 1.0)
            
            # Критически низкий volume (<0.3)
            if vol_ratio < 0.3:
                if tf == entry_timeframe:
                    penalties[tf] = -2.0  # Критический penalty на entry TF
                else:
                    penalties[tf] = -1.5  # Большой penalty на других TF
            
            # Низкий volume для скальпинга (<0.5)
            elif vol_ratio < 0.5:
                if tf == '1m':
                    penalties[tf] = -1.5
                elif tf == '5m':
                    penalties[tf] = -1.0
                elif tf == '15m':
                    penalties[tf] = -0.5
            
            # Умеренно низкий volume (<0.7) - только на entry TF
            elif vol_ratio < 0.7 and tf == entry_timeframe:
                penalties[tf] = -0.5
        
        return penalties
    
    def _check_macd_alignment_penalty(
        self,
        analysis: Dict,
        is_long: bool,
        entry_timeframe: str
    ) -> float:
        """
        Проверка MACD alignment на коротких TF
        
        Args:
            analysis: Полный анализ актива
            is_long: True для LONG, False для SHORT
            entry_timeframe: Таймфрейм входа
        
        Returns:
            Penalty (отрицательное число) если есть противоречия, 0.0 если OK
        """
        short_tfs = ['1m', '5m', '15m']
        bearish_count = 0
        bullish_count = 0
        macd_details = {}
        
        for tf in short_tfs:
            tf_data = analysis.get('timeframes', {}).get(tf, {})
            if 'error' in tf_data:
                continue
            
            macd = tf_data.get('indicators', {}).get('macd', {})
            crossover = macd.get('crossover', 'neutral')
            macd_details[tf] = crossover
            
            if crossover == 'bearish':
                bearish_count += 1
            elif crossover == 'bullish':
                bullish_count += 1
        
        # Penalty для LONG если MACD bearish
        if is_long:
            if bearish_count >= 2:
                return -1.5  # 2+ TF показывают bearish → большой penalty
            elif bearish_count >= 1:
                return -0.5  # 1 TF bearish → небольшой penalty
        
        # Penalty для SHORT если MACD bullish
        else:  # is_short
            if bullish_count >= 2:
                return -1.5  # 2+ TF показывают bullish → большой penalty
            elif bullish_count >= 1:
                return -0.5  # 1 TF bullish → небольшой penalty
        
        return 0.0  # Нет противоречий
    
    def _generate_warning_from_penalties(
        self, 
        penalties: List[str], 
        warnings: List[str] = None
    ) -> Optional[str]:
        """
        Генерация warning сообщения из списка penalties
        
        Args:
            penalties: Список строк с описанием penalties
            warnings: Список дополнительных warnings
        
        Returns:
            Warning сообщение или None
        """
        if not penalties:
            return None
        
        # Вычисляем общий penalty
        total_penalty = 0.0
        for p in penalties:
            if ':' in p:
                try:
                    penalty_value = float(p.split(':')[-1].strip())
                    total_penalty += penalty_value
                except ValueError:
                    continue
        
        # Генерируем warning в зависимости от severity
        if total_penalty <= -6.0:
            severity = "🔴 CRITICAL"
            message = f"Multiple critical issues detected ({len(penalties)} penalties, total: {total_penalty:.1f})"
        elif total_penalty <= -4.0:
            severity = "🔴 HIGH RISK"
            message = f"Several serious issues detected ({len(penalties)} penalties, total: {total_penalty:.1f})"
        elif total_penalty <= -2.0:
            severity = "⚠️ WARNING"
            message = f"Some issues detected ({len(penalties)} penalties, total: {total_penalty:.1f})"
        else:
            severity = "⚠️"
            message = f"Minor issues: {', '.join(penalties[:2])}"
        
        # Добавляем детали если есть warnings
        if warnings:
            message += f" | {', '.join(warnings[:2])}"
        
        return f"{severity} {message}"
    
    def _estimate_probability(self, score: float, analysis: Dict) -> float:
        """
        Оценка вероятности успеха - ИСПРАВЛЕННАЯ ВЕРСИЯ
        
        Args:
            score: Confluence score (0-20, raw, МОЖЕТ БЫТЬ ОТРИЦАТЕЛЬНЫМ после penalties!)
            analysis: Полный анализ актива
        
        Returns:
            Вероятность успеха (0.25-0.75) - РЕАЛИСТИЧНАЯ!
        """
        composite = analysis.get('composite_signal', {})
        signal = composite.get('signal', 'HOLD')
        confidence = composite.get('confidence', 0.5)
        comp_score = abs(composite.get('score', 0))
        
        # ═══════════════════════════════════════════════════════
        # HARD STOP: HOLD с низкой confidence → очень низкая probability
        # ═══════════════════════════════════════════════════════
        if signal == 'HOLD' and confidence < 0.5:
            return 0.30  # Минимум 30% для HOLD с низкой confidence
        
        # ═══════════════════════════════════════════════════════
        # Базовая вероятность от score (20-point → 25-75%)
        # ═══════════════════════════════════════════════════════
        # Score может быть отрицательным после penalties!
        # Score 0.0 = 25%, Score 5.0 = 30%, Score 10.0 = 45%, Score 15.0 = 60%, Score 20.0 = 75%
        base_score = max(0.0, score)  # Не позволяем отрицательному score снижать ниже 25%
        base_prob = 0.25 + (base_score - 0.0) * 0.025  # 0.0=25%, 20.0=75%
        base_prob = max(0.25, min(0.75, base_prob))  # Ограничиваем 25-75%
        
        # ═══════════════════════════════════════════════════════
        # КРИТИЧНО: Confidence как MULTIPLIER (не минимум!)
        # ═══════════════════════════════════════════════════════
        # Если confidence = 0.5, то probability = 50% от base
        # Если confidence = 0.8, то probability = 80% от base
        # Если confidence = 0.3, то probability = 30% от base (но минимум 25%)
        confidence_multiplier = max(0.3, confidence)  # Минимум 30% от confidence
        adjusted_prob = base_prob * confidence_multiplier
        
        # ═══════════════════════════════════════════════════════
        # Корректировка на signal type
        # ═══════════════════════════════════════════════════════
        if signal == 'STRONG_BUY' or signal == 'STRONG_SELL':
            adjusted_prob *= 1.1  # +10% за strong signal
        elif signal == 'BUY' or signal == 'SELL':
            adjusted_prob *= 1.0  # Без изменений
        elif signal == 'HOLD':
            adjusted_prob *= 0.5  # -50% за HOLD (даже если confidence OK)
        
        # ═══════════════════════════════════════════════════════
        # Корректировка на composite score
        # ═══════════════════════════════════════════════════════
        if comp_score < 3:
            adjusted_prob *= 0.7  # Ещё больше снижаем при слабом composite score
        elif comp_score > 7:
            adjusted_prob *= 1.05  # Небольшой бонус за сильный composite score
        
        # ═══════════════════════════════════════════════════════
        # Финальные ограничения
        # ═══════════════════════════════════════════════════════
        final_prob = min(0.75, max(0.25, adjusted_prob))  # 25-75% максимум!
        
        return round(final_prob, 2)
    
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
            "position_size_calc": f"Risk ${risk_usd:.2f} / Stop Dist {risk_per_share:.4f} = {qty} units" if account_balance else "BALANCE UNAVAILABLE - CANNOT CALCULATE",
            "entry_timeframe": "5m"  # По умолчанию для скальпинга (может быть переопределен)
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
    ) -> Dict[str, Any]:
        """
        Найти перепроданные активы (RSI < 30)
        
        Returns:
            Dict с ключами:
            - success: bool
            - opportunities: List[Dict] или []
            - error: Optional[str]
        """
        try:
            logger.info(f"Finding oversold assets on {market_type}")
            
            # Strict criteria (RSI < 30)
            strict_criteria = {
                "market_type": market_type,
                "min_volume_24h": min_volume_24h,
                "indicators": {
                    "rsi_range": [0, 30]
                }
            }
            
            results = await self.scan_market(strict_criteria, limit=10)
            
            # ✅ Проверяем, что scan_market вернул Dict
            if not isinstance(results, dict):
                logger.error(f"scan_market returned invalid type: {type(results)}")
                return {
                    "success": False,
                    "opportunities": [],
                    "error": "Internal error: scan_market returned invalid response"
                }
            
            # ✅ Если scan_market не succeeded, возвращаем его ошибку
            if not results.get("success"):
                return results
            
            opportunities = results.get("opportunities", [])
            
            # If few results - soften criteria (RSI < 35)
            if len(opportunities) < 5:
                logger.info(f"Only {len(opportunities)} results with RSI < 30, trying softer criteria (RSI < 35)")
                soft_criteria = {
                    "market_type": market_type,
                    "min_volume_24h": min_volume_24h,
                    "indicators": {
                        "rsi_range": [0, 35]
                    }
                }
                soft_results = await self.scan_market(soft_criteria, limit=10)
                
                if soft_results.get("success"):
                    soft_opportunities = soft_results.get("opportunities", [])
                    
                    # Merge results, remove duplicates
                    seen_symbols = {opp['symbol'] for opp in opportunities}
                    for opp in soft_opportunities:
                        if opp['symbol'] not in seen_symbols:
                            opportunities.append(opp)
                            seen_symbols.add(opp['symbol'])
                    
                    # Sort by score
                    opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            # ✅ SUCCESS RESPONSE
            return {
                "success": True,
                "opportunities": opportunities[:10],
                "error": None
            }
            
        except Exception as e:
            # ✅ ERROR RESPONSE
            logger.error(f"Error in find_oversold_assets: {e}", exc_info=True)
            return {
                "success": False,
                "opportunities": [],
                "error": str(e)
            }
    
    async def find_overbought_assets(
        self,
        market_type: str = "spot",
        min_volume_24h: float = 1000000
    ) -> Dict[str, Any]:
        """
        Найти перекупленные активы (RSI > 70) для SHORT позиций
        
        Returns:
            Dict с ключами:
            - success: bool
            - opportunities: List[Dict] или []
            - error: Optional[str]
        """
        try:
            logger.info(f"Finding overbought assets on {market_type}")
            
            # Strict criteria (RSI > 70)
            strict_criteria = {
                "market_type": market_type,
                "min_volume_24h": min_volume_24h,
                "indicators": {
                    "rsi_range": [70, 100]
                }
            }
            
            results = await self.scan_market(strict_criteria, limit=10)
            
            if not isinstance(results, dict):
                return {
                    "success": False,
                    "opportunities": [],
                    "error": "Internal error: scan_market returned invalid response"
                }
            
            if not results.get("success"):
                return results
            
            opportunities = results.get("opportunities", [])
            
            # If few results - soften criteria (RSI > 65)
            if len(opportunities) < 5:
                logger.info(f"Only {len(opportunities)} results with RSI > 70, trying softer criteria (RSI > 65)")
                soft_criteria = {
                    "market_type": market_type,
                    "min_volume_24h": min_volume_24h,
                    "indicators": {
                        "rsi_range": [65, 100]
                    }
                }
                soft_results = await self.scan_market(soft_criteria, limit=10)
                
                if soft_results.get("success"):
                    soft_opportunities = soft_results.get("opportunities", [])
                    
                    seen_symbols = {opp['symbol'] for opp in opportunities}
                    for opp in soft_opportunities:
                        if opp['symbol'] not in seen_symbols:
                            opportunities.append(opp)
                            seen_symbols.add(opp['symbol'])
                    
                    opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                "success": True,
                "opportunities": opportunities[:10],
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error in find_overbought_assets: {e}", exc_info=True)
            return {
                "success": False,
                "opportunities": [],
                "error": str(e)
            }
    
    async def find_breakout_opportunities(
        self,
        market_type: str = "spot",
        min_volume_24h: float = 1000000
    ) -> Dict[str, Any]:
        """
        Найти возможности пробоя (BB squeeze)
        
        Returns:
            Dict с ключами:
            - success: bool
            - opportunities: List[Dict] или []
            - error: Optional[str]
        """
        try:
            logger.info(f"Finding breakout opportunities on {market_type}")
            
            # Get BTC trend for scoring
            try:
                btc_analysis = await self.ta.analyze_asset("BTC/USDT", timeframes=["4h"])
                btc_trend = btc_analysis.get('timeframes', {}).get('4h', {}).get('trend', {}).get('direction', 'neutral')
            except Exception as e:
                logger.warning(f"Failed to analyze BTC: {e}")
                btc_trend = "neutral"
            
            # Get account balance for entry plan
            account_balance = None
            try:
                account_info = await self.client.get_account_info()
                account_balance = float(account_info.get("balance", {}).get("total", 0.0))
                if account_balance is None or account_balance <= 0:
                    account_balance = None
            except Exception as e:
                logger.warning(f"Cannot get wallet balance: {e}")
                account_balance = None
            
            # Get all tickers
            try:
                all_tickers = await self.client.get_all_tickers(market_type)
            except Exception as e:
                logger.error(f"Failed to get tickers: {e}")
                return {
                    "success": False,
                    "opportunities": [],
                    "error": f"Failed to fetch tickers: {str(e)}"
                }
            
            # Filter by volume and limit
            filtered = [
                t for t in all_tickers 
                if t['volume_24h'] >= min_volume_24h
            ][:100]
            
            # Parallel analysis
            semaphore = asyncio.Semaphore(10)
            
            async def check_breakout(ticker: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                """Check one ticker for BB squeeze"""
                async with semaphore:
                    try:
                        analysis = await self.ta.analyze_asset(
                            ticker['symbol'],
                            timeframes=["4h"],
                            include_patterns=False
                        )
                        
                        h4_data = analysis['timeframes'].get('4h', {})
                        bb = h4_data.get('indicators', {}).get('bollinger_bands', {})
                        
                        # Check BB squeeze
                        if bb.get('squeeze', False):
                            # Generate entry plan before scoring
                            entry_plan = self._generate_entry_plan(analysis, ticker, account_balance)
                            
                            # Calculate score
                            score_data = self._calculate_opportunity_score(analysis, ticker, btc_trend, entry_plan)
                            score = score_data["total"]
                            
                            if score >= 6.0:
                                return {
                                    "symbol": ticker['symbol'],
                                    "current_price": ticker['price'],
                                    "bb_width": bb.get('width', 0),
                                    "score": score,
                                    "score_breakdown": score_data["breakdown"],
                                    "probability": self._estimate_probability(score, analysis),
                                    "entry_plan": entry_plan,
                                    "type": "BB_SQUEEZE_BREAKOUT",
                                    "why": f"BB Squeeze detected (width: {bb.get('width', 0):.2f}%). Готовится к сильному движению."
                                }
                    except Exception as e:
                        logger.warning(f"Error analyzing {ticker['symbol']}: {e}")
                    
                    return None
            
            # Parallel analysis
            tasks = [check_breakout(ticker) for ticker in filtered]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            opportunities = []
            for result in results:
                if isinstance(result, Exception):
                    continue
                if result is not None:
                    opportunities.append(result)
            
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                "success": True,
                "opportunities": opportunities[:10],
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error in find_breakout_opportunities: {e}", exc_info=True)
            return {
                "success": False,
                "opportunities": [],
                "error": str(e)
            }
    
    async def find_trend_reversals(
        self,
        market_type: str = "spot",
        min_volume_24h: float = 1000000
    ) -> Dict[str, Any]:
        """
        Найти возможности разворота тренда (divergence)
        
        Returns:
            Dict с ключами:
            - success: bool
            - opportunities: List[Dict] или []
            - error: Optional[str]
        """
        try:
            logger.info(f"Finding trend reversals on {market_type}")
            
            # TODO: Implement divergence detector
            # For now, use general scan
            criteria = {
                "market_type": market_type,
                "min_volume_24h": min_volume_24h
            }
            
            results = await self.scan_market(criteria, limit=10)
            
            if not isinstance(results, dict):
                return {
                    "success": False,
                    "opportunities": [],
                    "error": "Internal error: scan_market returned invalid response"
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in find_trend_reversals: {e}", exc_info=True)
            return {
                "success": False,
                "opportunities": [],
                "error": str(e)
            }
    
    async def find_orb_opportunities(
        self,
        market_type: str = "spot",
        min_volume_24h: float = 1000000
    ) -> Dict[str, Any]:
        """
        Найти Opening Range Breakout возможности
        
        Best timing: European (08:00-10:00), US (13:30-15:30) UTC
        Win Rate: 65-75%
        
        Returns:
            Dict с ключами:
            - success: bool
            - opportunities: List[Dict] или []
            - error: Optional[str]
        """
        try:
            from .orb_strategy import OpeningRangeBreakout
        except ImportError:
            from orb_strategy import OpeningRangeBreakout
        
        try:
            logger.info(f"Finding ORB opportunities on {market_type}")
            
            orb = OpeningRangeBreakout(self.client, self.ta)
            
            # Получаем все тикеры
            try:
                all_tickers = await self.client.get_all_tickers(market_type)
            except Exception as e:
                logger.error(f"Failed to get tickers: {e}")
                return {
                    "success": False,
                    "opportunities": [],
                    "error": f"Failed to fetch tickers: {str(e)}"
                }
            
            filtered = [t for t in all_tickers if t.get('volume_24h', 0) >= min_volume_24h]
            filtered.sort(key=lambda x: x.get('volume_24h', 0), reverse=True)
            
            opportunities = []
            
            # Проверяем топ-30 по объему
            for ticker in filtered[:30]:
                try:
                    symbol = ticker.get('symbol', '')
                    if not symbol:
                        continue
                    
                    setup = await orb.detect_orb_setup(symbol)
                    
                    if setup.get('has_setup'):
                        opportunities.append({
                            "symbol": symbol,
                            "type": "ORB_BREAKOUT",
                            "score": 11.0 if setup.get('strength') == 'strong' else 9.0,
                            "probability": setup.get('confidence', 0.65),
                            "entry_plan": {
                                "side": setup.get('side'),
                                "entry_price": setup.get('entry_price'),
                                "stop_loss": setup.get('stop_loss'),
                                "take_profit": setup.get('take_profit'),
                                "risk_reward": setup.get('risk_reward')
                            },
                            "orb_details": setup,
                            "price": ticker.get('price', 0),
                            "volume_24h": ticker.get('volume_24h', 0)
                        })
                except Exception as e:
                    logger.warning(f"ORB check failed for {ticker.get('symbol', 'UNKNOWN')}: {e}")
            
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                "success": True,
                "opportunities": opportunities[:10],
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error in find_orb_opportunities: {e}", exc_info=True)
            return {
                "success": False,
                "opportunities": [],
                "error": str(e)
            }
