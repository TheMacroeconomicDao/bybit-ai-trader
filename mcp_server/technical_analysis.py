"""
Technical Analysis Engine
Полный расчёт всех технических индикаторов для криптовалют
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import ta
from loguru import logger


class TechnicalAnalysis:
    """Движок технического анализа"""
    
    def __init__(self, bybit_client):
        self.client = bybit_client
        logger.info("Technical Analysis engine initialized")
    
    async def analyze_asset(
        self,
        symbol: str,
        timeframes: List[str] = ["5m", "15m", "1h", "4h", "1d"],
        include_patterns: bool = True
    ) -> Dict[str, Any]:
        """
        ПОЛНЫЙ анализ актива на всех таймфреймах
        
        Args:
            symbol: Торговая пара (например "BTC/USDT")
            timeframes: Список таймфреймов для анализа
            include_patterns: Включить распознавание паттернов
            
        Returns:
            Детальный анализ по каждому таймфрейму + composite signal
        """
        logger.info(f"Analyzing {symbol} on timeframes: {timeframes}")
        
        results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "timeframes": {}
        }
        
        # Анализ на каждом таймфрейме
        for tf in timeframes:
            try:
                tf_analysis = await self._analyze_timeframe(symbol, tf, include_patterns)
                results["timeframes"][tf] = tf_analysis
            except Exception as e:
                logger.error(f"Error analyzing {symbol} on {tf}: {e}")
                results["timeframes"][tf] = {"error": str(e)}
        
        # Composite signal (объединённый сигнал)
        results["composite_signal"] = self._generate_composite_signal(results["timeframes"])
        
        return results
    
    async def _analyze_timeframe(
        self,
        symbol: str,
        timeframe: str,
        include_patterns: bool
    ) -> Dict[str, Any]:
        """Анализ на одном таймфрейме"""
        
        # Получаем OHLCV данные
        ohlcv = await self.client.get_ohlcv(symbol, timeframe, limit=200)
        
        # Конвертируем в DataFrame
        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Расчёт всех индикаторов
        indicators = self._calculate_all_indicators(df)
        
        # Анализ тренда
        trend = self._analyze_trend(df, indicators)
        
        # Уровни поддержки/сопротивления
        levels = self._find_support_resistance(df)
        
        # Паттерны (если включено)
        patterns = {}
        if include_patterns:
            patterns = self._detect_patterns(df)
        
        # Генерация сигнала
        signal = self._generate_signal(indicators, trend, levels, patterns)
        
        return {
            "timeframe": timeframe,
            "current_price": float(df['close'].iloc[-1]),
            "ohlcv_summary": {
                "high_24h": float(df['high'].tail(24 if timeframe == "1h" else 10).max()),
                "low_24h": float(df['low'].tail(24 if timeframe == "1h" else 10).min()),
                "volume_avg": float(df['volume'].tail(20).mean())
            },
            "indicators": indicators,
            "trend": trend,
            "levels": levels,
            "patterns": patterns,
            "signal": signal
        }
    
    def _calculate_all_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Расчёт всех технических индикаторов"""
        
        indicators = {}
        
        # RSI (несколько периодов)
        indicators['rsi'] = {
            'rsi_7': float(ta.momentum.rsi(df['close'], window=7).iloc[-1]),
            'rsi_14': float(ta.momentum.rsi(df['close'], window=14).iloc[-1]),
            'rsi_21': float(ta.momentum.rsi(df['close'], window=21).iloc[-1])
        }
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        indicators['macd'] = {
            'macd_line': float(macd.macd().iloc[-1]),
            'signal_line': float(macd.macd_signal().iloc[-1]),
            'histogram': float(macd.macd_diff().iloc[-1]),
            'crossover': 'bullish' if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] else 'bearish'
        }
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'])
        bb_width = (bb.bollinger_hband().iloc[-1] - bb.bollinger_lband().iloc[-1]) / bb.bollinger_mavg().iloc[-1] * 100
        
        indicators['bollinger_bands'] = {
            'upper': float(bb.bollinger_hband().iloc[-1]),
            'middle': float(bb.bollinger_mavg().iloc[-1]),
            'lower': float(bb.bollinger_lband().iloc[-1]),
            'width': float(bb_width),
            'squeeze': bool(bb_width < 2.0)  # Squeeze если ширина < 2% - конвертируем в bool для JSON
        }
        
        # EMA (множественные периоды)
        indicators['ema'] = {
            'ema_9': float(ta.trend.ema_indicator(df['close'], window=9).iloc[-1]),
            'ema_20': float(ta.trend.ema_indicator(df['close'], window=20).iloc[-1]),
            'ema_50': float(ta.trend.ema_indicator(df['close'], window=50).iloc[-1]),
            'ema_100': float(ta.trend.ema_indicator(df['close'], window=100).iloc[-1]),
            'ema_200': float(ta.trend.ema_indicator(df['close'], window=200).iloc[-1])
        }
        
        # EMA alignment
        current_price = df['close'].iloc[-1]
        ema_values = [
            current_price,
            indicators['ema']['ema_9'],
            indicators['ema']['ema_20'],
            indicators['ema']['ema_50'],
            indicators['ema']['ema_200']
        ]
        
        is_bullish_alignment = all(ema_values[i] > ema_values[i+1] for i in range(len(ema_values)-1))
        is_bearish_alignment = all(ema_values[i] < ema_values[i+1] for i in range(len(ema_values)-1))
        
        indicators['ema']['alignment'] = 'bullish' if is_bullish_alignment else 'bearish' if is_bearish_alignment else 'mixed'
        
        # ATR
        atr = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        indicators['atr'] = {
            'atr_14': float(atr.iloc[-1]),
            'atr_7': float(ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=7).iloc[-1])
        }
        
        # ADX
        adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
        indicators['adx'] = {
            'adx': float(adx.adx().iloc[-1]),
            'adx_pos': float(adx.adx_pos().iloc[-1]),
            'adx_neg': float(adx.adx_neg().iloc[-1]),
            'trend_strength': 'strong' if adx.adx().iloc[-1] > 25 else 'weak'
        }
        
        # Stochastic
        stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
        indicators['stochastic'] = {
            'stoch_k': float(stoch.stoch().iloc[-1]),
            'stoch_d': float(stoch.stoch_signal().iloc[-1]),
            'crossover': 'bullish' if stoch.stoch().iloc[-1] > stoch.stoch_signal().iloc[-1] else 'bearish'
        }
        
        # Volume indicators
        indicators['volume'] = {
            'obv': float(ta.volume.on_balance_volume(df['close'], df['volume']).iloc[-1]),
            'volume_sma': float(df['volume'].rolling(20).mean().iloc[-1]),
            'current_volume': float(df['volume'].iloc[-1]),
            'volume_ratio': float(df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1])
        }
        
        # VWAP (для интрадей)
        if len(df) >= 20:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            indicators['vwap'] = float((typical_price * df['volume']).sum() / df['volume'].sum())
        
        return indicators
    
    def _analyze_trend(self, df: pd.DataFrame, indicators: Dict) -> Dict[str, Any]:
        """Анализ тренда"""
        
        current_price = df['close'].iloc[-1]
        ema_50 = indicators['ema']['ema_50']
        ema_200 = indicators['ema']['ema_200']
        adx = indicators['adx']['adx']
        
        # Определение направления
        if current_price > ema_50 > ema_200 and indicators['ema']['alignment'] == 'bullish':
            direction = 'uptrend'
        elif current_price < ema_50 < ema_200 and indicators['ema']['alignment'] == 'bearish':
            direction = 'downtrend'
        else:
            direction = 'sideways'
        
        # Сила тренда
        if adx > 40:
            strength = 'very_strong'
        elif adx > 25:
            strength = 'strong'
        elif adx > 20:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        # Уверенность
        alignment = indicators['ema']['alignment']
        if alignment != 'mixed' and adx > 25:
            confidence = 'high'
        elif alignment != 'mixed' or adx > 20:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            "direction": direction,
            "strength": strength,
            "confidence": confidence,
            "ema_alignment": indicators['ema']['alignment']
        }
    
    def _find_support_resistance(self, df: pd.DataFrame, lookback: int = 50) -> Dict[str, List[float]]:
        """Поиск уровней поддержки и сопротивления"""
        
        # Используем локальные минимумы и максимумы
        recent_df = df.tail(lookback)
        
        # Простой метод: найти локальные экстремумы
        highs = recent_df['high'].nlargest(5).values
        lows = recent_df['low'].nsmallest(5).values
        
        # Кластеризация близких уровней
        resistance_levels = self._cluster_levels(highs, tolerance=0.02)
        support_levels = self._cluster_levels(lows, tolerance=0.02)
        
        return {
            "support": [float(x) for x in support_levels],
            "resistance": [float(x) for x in resistance_levels]
        }
    
    def _cluster_levels(self, levels: np.ndarray, tolerance: float = 0.02) -> List[float]:
        """Кластеризация близких уровней"""
        if len(levels) == 0:
            return []
        
        clustered = []
        sorted_levels = np.sort(levels)
        
        current_cluster = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            if abs(level - current_cluster[0]) / current_cluster[0] < tolerance:
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        
        clustered.append(np.mean(current_cluster))
        
        return clustered
    
    def _detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Детектор свечных паттернов"""
        
        patterns = {
            "candlestick": [],
            "chart": []
        }
        
        # Последние свечи для анализа
        recent = df.tail(5)
        last = recent.iloc[-1]
        prev = recent.iloc[-2] if len(recent) > 1 else None
        
        # Hammer
        body = abs(last['close'] - last['open'])
        lower_shadow = min(last['open'], last['close']) - last['low']
        upper_shadow = last['high'] - max(last['open'], last['close'])
        
        if lower_shadow > body * 2 and upper_shadow < body * 0.5:
            patterns['candlestick'].append({
                "name": "Hammer",
                "type": "bullish",
                "reliability": 0.65,
                "description": "Potential reversal from downtrend"
            })
        
        # Shooting Star
        if upper_shadow > body * 2 and lower_shadow < body * 0.5:
            patterns['candlestick'].append({
                "name": "Shooting Star",
                "type": "bearish",
                "reliability": 0.65,
                "description": "Potential reversal from uptrend"
            })
        
        # Bullish Engulfing
        if prev is not None:
            if (prev['close'] < prev['open'] and  # предыдущая медвежья
                last['close'] > last['open'] and  # текущая бычья
                last['close'] > prev['open'] and  # поглощает
                last['open'] < prev['close']):
                patterns['candlestick'].append({
                    "name": "Bullish Engulfing",
                    "type": "bullish",
                    "reliability": 0.70,
                    "description": "Strong reversal signal"
                })
        
        # Doji
        if body < (last['high'] - last['low']) * 0.1:
            patterns['candlestick'].append({
                "name": "Doji",
                "type": "neutral",
                "reliability": 0.50,
                "description": "Indecision, potential reversal"
            })
        
        return patterns
    
    def _generate_signal(
        self,
        indicators: Dict,
        trend: Dict,
        levels: Dict,
        patterns: Dict
    ) -> Dict[str, Any]:
        """Генерация торгового сигнала"""
        
        score = 0
        max_score = 10
        reasons = []
        warnings = []
        
        # RSI analysis
        rsi_14 = indicators['rsi']['rsi_14']
        if rsi_14 < 30:
            score += 1.5
            reasons.append(f"RSI oversold ({rsi_14:.1f})")
        elif rsi_14 > 70:
            score -= 1.5
            warnings.append(f"RSI overbought ({rsi_14:.1f})")
        elif 40 < rsi_14 < 60:
            score += 0.5
            reasons.append("RSI neutral/healthy")
        
        # MACD
        if indicators['macd']['crossover'] == 'bullish' and indicators['macd']['histogram'] > 0:
            score += 1.5
            reasons.append("MACD bullish crossover")
        elif indicators['macd']['crossover'] == 'bearish' and indicators['macd']['histogram'] < 0:
            score -= 1.5
            warnings.append("MACD bearish crossover")
        
        # EMA alignment
        if indicators['ema']['alignment'] == 'bullish':
            score += 2
            reasons.append("Perfect bullish EMA alignment")
        elif indicators['ema']['alignment'] == 'bearish':
            score -= 2
            warnings.append("Bearish EMA alignment")
        
        # Trend
        if trend['direction'] == 'uptrend' and trend['strength'] in ['strong', 'very_strong']:
            score += 1.5
            reasons.append(f"Strong uptrend (ADX: {indicators['adx']['adx']:.1f})")
        elif trend['direction'] == 'downtrend' and trend['strength'] in ['strong', 'very_strong']:
            score -= 1.5
            warnings.append(f"Strong downtrend (ADX: {indicators['adx']['adx']:.1f})")
        
        # Bollinger Bands
        current_price = indicators.get('current_price', 0)
        bb = indicators['bollinger_bands']
        if current_price < bb['lower']:
            score += 1
            reasons.append("Price below lower BB (oversold)")
        elif current_price > bb['upper']:
            score -= 1
            warnings.append("Price above upper BB (overbought)")
        
        if bb['squeeze']:
            reasons.append("BB Squeeze detected (breakout pending)")
        
        # Volume
        if indicators['volume']['volume_ratio'] > 1.5:
            score += 0.5
            reasons.append(f"High volume ({indicators['volume']['volume_ratio']:.1f}x avg)")
        
        # Patterns
        for pattern in patterns.get('candlestick', []):
            if pattern['type'] == 'bullish':
                score += 0.5
                reasons.append(f"Bullish pattern: {pattern['name']}")
            elif pattern['type'] == 'bearish':
                score -= 0.5
                warnings.append(f"Bearish pattern: {pattern['name']}")
        
        # Нормализация score
        normalized_score = max(0, min(10, (score + 5)))  # Convert -5 to +5 range to 0-10
        
        # Определение сигнала
        if normalized_score >= 7.5:
            signal_type = "BUY"
            strength = "strong"
        elif normalized_score >= 6:
            signal_type = "BUY"
            strength = "moderate"
        elif normalized_score <= 2.5:
            signal_type = "SELL"
            strength = "strong"
        elif normalized_score <= 4:
            signal_type = "SELL"
            strength = "moderate"
        else:
            signal_type = "HOLD"
            strength = "neutral"
        
        # Confidence
        if len(reasons) >= 5 and len(warnings) <= 1:
            confidence = 0.85
        elif len(reasons) >= 3 and len(warnings) <= 2:
            confidence = 0.65
        else:
            confidence = 0.45
        
        return {
            "type": signal_type,
            "strength": strength,
            "confidence": round(confidence, 2),
            "score": round(normalized_score, 1),
            "reasons": reasons,
            "warnings": warnings
        }
    
    def _generate_composite_signal(self, timeframe_results: Dict) -> Dict[str, Any]:
        """Генерация объединённого сигнала по всем таймфреймам"""
        
        signals = []
        confidences = []
        
        # Приоритеты таймфреймов (старшие важнее)
        tf_weights = {
            "1d": 3.0,
            "4h": 2.5,
            "1h": 2.0,
            "15m": 1.0,
            "5m": 0.5
        }
        
        for tf, data in timeframe_results.items():
            if 'error' in data:
                continue
            
            signal = data.get('signal', {})
            weight = tf_weights.get(tf, 1.0)
            
            if signal.get('type') == 'BUY':
                signals.append(signal.get('score', 5) * weight)
            elif signal.get('type') == 'SELL':
                signals.append(-signal.get('score', 5) * weight)
            else:
                signals.append(0)
            
            confidences.append(signal.get('confidence', 0.5) * weight)
        
        # Взвешенный средний
        if signals:
            avg_signal = sum(signals) / sum(tf_weights.values())
            avg_confidence = sum(confidences) / sum(tf_weights.values())
        else:
            avg_signal = 0
            avg_confidence = 0
        
        # Определение итогового сигнала
        if avg_signal >= 6:
            composite_type = "STRONG_BUY"
        elif avg_signal >= 3:
            composite_type = "BUY"
        elif avg_signal <= -6:
            composite_type = "STRONG_SELL"
        elif avg_signal <= -3:
            composite_type = "SELL"
        else:
            composite_type = "HOLD"
        
        # Проверка multi-timeframe alignment
        buy_signals = sum(1 for tf, data in timeframe_results.items() 
                         if not 'error' in data and data.get('signal', {}).get('type') == 'BUY')
        sell_signals = sum(1 for tf, data in timeframe_results.items() 
                          if not 'error' in data and data.get('signal', {}).get('type') == 'SELL')
        total_signals = buy_signals + sell_signals + sum(1 for tf, data in timeframe_results.items() 
                                                          if not 'error' in data and data.get('signal', {}).get('type') == 'HOLD')
        
        alignment = buy_signals / total_signals if total_signals > 0 else 0.5
        
        return {
            "signal": composite_type,
            "confidence": round(avg_confidence, 2),
            "score": round(avg_signal, 1),
            "alignment": round(alignment, 2),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "hold_signals": total_signals - buy_signals - sell_signals,
            "recommendation": self._get_recommendation(composite_type, avg_confidence, alignment)
        }
    
    def _get_recommendation(self, signal: str, confidence: float, alignment: float) -> str:
        """Генерация рекомендации"""
        
        if signal == "STRONG_BUY" and confidence > 0.7 and alignment > 0.7:
            return "ОТЛИЧНАЯ возможность для LONG. Высокая вероятность успеха."
        elif signal == "BUY" and confidence > 0.6:
            return "Хорошая возможность для LONG. Средняя-высокая вероятность."
        elif signal == "STRONG_SELL" and confidence > 0.7:
            return "Сильный сигнал на SELL/SHORT. Высокий риск для longs."
        elif signal == "SELL":
            return "Медвежий сигнал. Избегайте longs или рассмотрите short."
        else:
            return "Нет чёткого сигнала. Лучше подождать более ясной картины."
    
    async def validate_entry(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        risk_pct: float = 0.01
    ) -> Dict[str, Any]:
        """
        Валидация точки входа перед открытием позиции
        
        Returns:
            Детальная оценка качества setup
        """
        logger.info(f"Validating entry: {symbol} {side} @ {entry_price}")
        
        # Получаем текущий анализ
        analysis = await self.analyze_asset(symbol, timeframes=["15m", "1h", "4h", "1d"])
        
        # Расчёт R:R
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        # Проверки
        checks = {}
        
        # Technical checks
        composite = analysis['composite_signal']
        checks['technical'] = {
            "trend_aligned": (side == 'long' and composite['buy_signals'] >= 3) or 
                           (side == 'short' and composite['sell_signals'] >= 3),
            "confidence": composite['confidence'],
            "multi_timeframe_alignment": composite['alignment'] > 0.6
        }
        
        # Risk management checks
        checks['risk_management'] = {
            "risk_reward": risk_reward,
            "risk_reward_acceptable": risk_reward >= 2.0,
            "stop_loss_logical": True,  # Предполагаем что логичен
            "take_profit_realistic": True
        }
        
        # Market conditions
        h4_indicators = analysis['timeframes'].get('4h', {}).get('indicators', {})
        checks['market_conditions'] = {
            "volatility": h4_indicators.get('atr', {}).get('atr_14', 0) if h4_indicators else 0,
            "liquidity": "good",  # TODO: Improve
            "adx": h4_indicators.get('adx', {}).get('adx', 0) if h4_indicators else 0
        }
        
        # Расчёт общего score
        score = 0
        
        if checks['technical']['trend_aligned']:
            score += 3
        if checks['technical']['confidence'] > 0.7:
            score += 2
        if checks['technical']['multi_timeframe_alignment']:
            score += 2
        if checks['risk_management']['risk_reward_acceptable']:
            score += 2
        if checks['market_conditions']['adx'] > 25:
            score += 1
        
        # Валидность
        is_valid = score >= 7 and risk_reward >= 1.5
        
        # Вероятность успеха (эвристика)
        win_probability = min(0.95, 0.5 + (score / 20) + (composite['confidence'] * 0.3))
        
        # Expected Value
        expected_value = (win_probability * reward) - ((1 - win_probability) * risk)
        
        return {
            "is_valid": is_valid,
            "score": score,
            "confidence": round(composite['confidence'], 2),
            "checks": checks,
            "probability_analysis": {
                "win_probability": round(win_probability, 2),
                "expected_value": round(expected_value, 2),
                "risk_reward_ratio": round(risk_reward, 2)
            },
            "warnings": composite.get('warnings', []) if score < 7 else [],
            "recommendations": self._get_entry_recommendations(score, risk_reward, composite)
        }
    
    def _get_entry_recommendations(self, score: int, rr: float, composite: Dict) -> List[str]:
        """Генерация рекомендаций для входа"""
        
        recommendations = []
        
        if score < 7:
            recommendations.append("Confluence score низкий. Подождите лучшего setup.")
        
        if rr < 2.0:
            recommendations.append(f"R:R {rr:.1f} ниже рекомендуемого 2.0. Улучшите targets или SL.")
        
        if composite['confidence'] < 0.6:
            recommendations.append("Низкая уверенность в сигнале. Будьте осторожны.")
        
        if score >= 8 and rr >= 2.5:
            recommendations.append("Отличный setup! Можно входить с confidence.")
        
        return recommendations
    
    async def get_btc_correlation(
        self,
        symbol: str,
        period: int = 24,
        timeframe: str = "1h"
    ) -> Dict[str, Any]:
        """
        Рассчитать корреляцию актива с BTC
        
        Args:
            symbol: Торговая пара (например "ETH/USDT")
            period: Количество периодов для анализа
            timeframe: Таймфрейм для анализа
            
        Returns:
            Корреляция и анализ
        """
        logger.info(f"Calculating BTC correlation for {symbol}")
        
        try:
            # Получаем данные для актива
            alt_data = await self.client.get_ohlcv(symbol, timeframe, limit=period)
            alt_df = pd.DataFrame(alt_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            alt_returns = alt_df['close'].pct_change().dropna()
            
            # Получаем данные для BTC
            btc_data = await self.client.get_ohlcv("BTC/USDT", timeframe, limit=period)
            btc_df = pd.DataFrame(btc_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            btc_returns = btc_df['close'].pct_change().dropna()
            
            # Выравниваем по длине
            min_len = min(len(alt_returns), len(btc_returns))
            alt_returns = alt_returns[-min_len:]
            btc_returns = btc_returns[-min_len:]
            
            # Рассчитываем корреляцию
            correlation = alt_returns.corr(btc_returns) if len(alt_returns) > 1 else 0.0
            
            # Интерпретация
            if correlation > 0.8:
                correlation_level = "very_high"
                interpretation = "Очень высокая корреляция с BTC. Следует за BTC движениями."
                recommendation = "Проверяй BTC перед входом. Если BTC падает - избегай LONG."
            elif correlation > 0.6:
                correlation_level = "high"
                interpretation = "Высокая корреляция с BTC. В основном следует за BTC."
                recommendation = "BTC тренд критичен. Проверяй BTC перед входом."
            elif correlation > 0.4:
                correlation_level = "medium"
                interpretation = "Средняя корреляция. Может двигаться независимо от BTC."
                recommendation = "BTC влияет, но не критично. Проверяй оба актива."
            elif correlation > 0.2:
                correlation_level = "low"
                interpretation = "Низкая корреляция. Движется относительно независимо от BTC."
                recommendation = "BTC влияние минимально. Фокус на технический анализ актива."
            else:
                correlation_level = "very_low"
                interpretation = "Очень низкая или отрицательная корреляция. Независимое движение."
                recommendation = "BTC не влияет. Торгуй по техническому анализу актива."
            
            return {
                "symbol": symbol,
                "btc_symbol": "BTC/USDT",
                "correlation": round(correlation, 3),
                "correlation_level": correlation_level,
                "period": period,
                "timeframe": timeframe,
                "interpretation": interpretation,
                "recommendation": recommendation,
                "alt_avg_return": round(alt_returns.mean() * 100, 2) if len(alt_returns) > 0 else 0,
                "btc_avg_return": round(btc_returns.mean() * 100, 2) if len(btc_returns) > 0 else 0,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating BTC correlation: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_tf_alignment(
        self,
        symbol: str,
        timeframes: List[str] = ["5m", "15m", "1h", "4h", "1d"]
    ) -> Dict[str, Any]:
        """
        Быстрая проверка alignment таймфреймов
        
        Args:
            symbol: Торговая пара
            timeframes: Список таймфреймов для проверки
            
        Returns:
            Alignment анализ
        """
        logger.info(f"Checking TF alignment for {symbol}")
        
        try:
            signals = {}
            trends = {}
            
            for tf in timeframes:
                analysis = await self._analyze_timeframe(symbol, tf, include_patterns=False)
                signal = analysis.get('signal', {})
                trend = analysis.get('trend', {})
                
                signals[tf] = signal.get('type', 'HOLD')
                trends[tf] = trend.get('direction', 'sideways')
            
            # Подсчет согласованности
            buy_count = sum(1 for s in signals.values() if s == 'BUY')
            sell_count = sum(1 for s in signals.values() if s == 'SELL')
            hold_count = sum(1 for s in signals.values() if s == 'HOLD')
            
            uptrend_count = sum(1 for t in trends.values() if t == 'uptrend')
            downtrend_count = sum(1 for t in trends.values() if t == 'downtrend')
            
            # Alignment score
            total_tfs = len(timeframes)
            alignment_score = max(buy_count, sell_count) / total_tfs if total_tfs > 0 else 0
            
            # Определение доминирующего сигнала
            if buy_count > sell_count and buy_count > hold_count:
                dominant_signal = "BUY"
                alignment = "bullish"
            elif sell_count > buy_count and sell_count > hold_count:
                dominant_signal = "SELL"
                alignment = "bearish"
            else:
                dominant_signal = "HOLD"
                alignment = "mixed"
            
            # Интерпретация
            if alignment_score >= 0.8:
                interpretation = "Отличное выравнивание таймфреймов. Сильный сигнал."
                strength = "strong"
            elif alignment_score >= 0.6:
                interpretation = "Хорошее выравнивание. Умеренно сильный сигнал."
                strength = "moderate"
            else:
                interpretation = "Слабое выравнивание. Смешанные сигналы."
                strength = "weak"
            
            return {
                "symbol": symbol,
                "timeframes": timeframes,
                "signals": signals,
                "trends": trends,
                "alignment_score": round(alignment_score, 2),
                "dominant_signal": dominant_signal,
                "alignment": alignment,
                "strength": strength,
                "interpretation": interpretation,
                "buy_signals": buy_count,
                "sell_signals": sell_count,
                "hold_signals": hold_count,
                "uptrend_count": uptrend_count,
                "downtrend_count": downtrend_count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking TF alignment: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_liquidity(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Проверка ликвидности актива на основе orderbook
        
        Args:
            symbol: Торговая пара
            
        Returns:
            Liquidity score и детали
        """
        logger.info(f"Checking liquidity for {symbol}")
        
        try:
            # Получаем orderbook через bybit_client
            orderbook = await self.client.get_orderbook(symbol)
            
            if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
                return {
                    "symbol": symbol,
                    "success": False,
                    "error": "Could not fetch orderbook",
                    "timestamp": datetime.now().isoformat()
                }
            
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            # Рассчитываем ликвидность
            bid_volume = sum(float(bid[1]) for bid in bids[:10]) if len(bids) >= 10 else sum(float(bid[1]) for bid in bids)
            ask_volume = sum(float(ask[1]) for ask in asks[:10]) if len(asks) >= 10 else sum(float(ask[1]) for ask in asks)
            
            total_liquidity = bid_volume + ask_volume
            
            # Рассчитываем spread
            if bids and asks:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                spread = best_ask - best_bid
                spread_pct = (spread / best_bid * 100) if best_bid > 0 else 0
            else:
                spread = 0
                spread_pct = 0
            
            # Liquidity score (0-1)
            # Нормализуем на основе типичных значений
            # Для BTC: ~100-500 BTC в топ-10
            # Для альтов: зависит от объема
            
            if total_liquidity > 1000:
                liquidity_score = 1.0
                liquidity_level = "excellent"
            elif total_liquidity > 500:
                liquidity_score = 0.8
                liquidity_level = "very_good"
            elif total_liquidity > 100:
                liquidity_score = 0.6
                liquidity_level = "good"
            elif total_liquidity > 50:
                liquidity_score = 0.4
                liquidity_level = "moderate"
            elif total_liquidity > 10:
                liquidity_score = 0.2
                liquidity_level = "low"
            else:
                liquidity_score = 0.1
                liquidity_level = "very_low"
            
            # Учитываем spread
            if spread_pct < 0.1:
                spread_score = 1.0
            elif spread_pct < 0.5:
                spread_score = 0.8
            elif spread_pct < 1.0:
                spread_score = 0.6
            elif spread_pct < 2.0:
                spread_score = 0.4
            else:
                spread_score = 0.2
            
            # Финальный score
            final_score = (liquidity_score * 0.7) + (spread_score * 0.3)
            
            # Интерпретация
            if final_score >= 0.8:
                interpretation = "Отличная ликвидность. Можно торговать крупными позициями."
                recommendation = "Безопасно для торговли"
            elif final_score >= 0.6:
                interpretation = "Хорошая ликвидность. Подходит для стандартных позиций."
                recommendation = "Подходит для торговли"
            elif final_score >= 0.4:
                interpretation = "Умеренная ликвидность. Осторожно с крупными позициями."
                recommendation = "Осторожно, используй меньшие размеры"
            else:
                interpretation = "Низкая ликвидность. Высокий риск проскальзывания."
                recommendation = "Избегай или используй очень маленькие позиции"
            
            return {
                "symbol": symbol,
                "liquidity_score": round(final_score, 2),
                "liquidity_level": liquidity_level,
                "bid_volume_top10": round(bid_volume, 2),
                "ask_volume_top10": round(ask_volume, 2),
                "total_liquidity": round(total_liquidity, 2),
                "spread": round(spread, 8),
                "spread_pct": round(spread_pct, 4),
                "spread_score": round(spread_score, 2),
                "interpretation": interpretation,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking liquidity: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }