"""
Market Scanner
Сканирование рынка для поиска торговых возможностей
"""

from typing import Dict, List, Any, Optional
from loguru import logger
import asyncio


class MarketScanner:
    """Сканер рынка для поиска торговых возможностей"""
    
    def __init__(self, bybit_client, technical_analysis):
        self.client = bybit_client
        self.ta = technical_analysis
        logger.info("Market Scanner initialized")
    
    async def scan_market(
        self,
        criteria: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Универсальное сканирование рынка по критериям
        
        Args:
            criteria: Критерии фильтрации
            limit: Максимальное количество результатов
            
        Returns:
            Список активов, соответствующих критериям
        """
        logger.info(f"Scanning market with criteria: {criteria}")
        
        # Получаем все тикеры
        all_tickers = await self.client.get_all_tickers(
            market_type=criteria.get('market_type', 'spot')
        )
        
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
        
        # Детальный анализ для отфильтрованных
        opportunities = []
        
        for ticker in filtered[:limit * 3]:  # Анализируем больше, чтобы выбрать лучшие
            try:
                analysis = await self.ta.analyze_asset(
                    ticker['symbol'],
                    timeframes=["1h", "4h"],
                    include_patterns=True
                )
                
                # Проверка индикаторных критериев
                indicator_criteria = criteria.get('indicators', {})
                if not self._check_indicator_criteria(analysis, indicator_criteria):
                    continue
                
                # Scoring
                score = self._calculate_opportunity_score(analysis, ticker)
                
                # Entry plan
                entry_plan = self._generate_entry_plan(analysis, ticker)
                
                opportunities.append({
                    "symbol": ticker['symbol'],
                    "current_price": ticker['price'],
                    "change_24h": ticker['change_24h'],
                    "volume_24h": ticker['volume_24h'],
                    "score": score,
                    "probability": self._estimate_probability(score, analysis),
                    "entry_plan": entry_plan,
                    "analysis": analysis,
                    "why": self._generate_reasoning(analysis, score)
                })
                
            except Exception as e:
                logger.warning(f"Error analyzing {ticker['symbol']}: {e}")
                continue
        
        # Сортировка по score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        return opportunities[:limit]
    
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
        """Расчёт scoring возможности (0-10)"""
        
        score = 5.0  # Базовый score
        
        composite = analysis.get('composite_signal', {})
        
        # Composite signal strength
        if composite.get('signal') == 'STRONG_BUY':
            score += 2.5
        elif composite.get('signal') == 'BUY':
            score += 1.5
        elif composite.get('signal') == 'STRONG_SELL':
            score -= 2.5
        elif composite.get('signal') == 'SELL':
            score -= 1.5
        
        # Confidence
        confidence = composite.get('confidence', 0.5)
        score += (confidence - 0.5) * 3  # -1.5 to +1.5
        
        # Alignment
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
        """Генерация плана входа"""
        
        current_price = ticker['price']
        h4_indicators = analysis['timeframes'].get('4h', {}).get('indicators', {})
        atr = h4_indicators.get('atr', {}).get('atr_14', current_price * 0.02)
        
        # Расчёт SL и TP
        stop_loss = current_price - (atr * 2)
        take_profit = current_price + (atr * 4)
        
        risk = current_price - stop_loss
        reward = take_profit - current_price
        risk_reward = reward / risk if risk > 0 else 0
        
        return {
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
        Найти перепроданные активы (RSI < 30)
        
        Args:
            market_type: "spot" или "futures"
            min_volume_24h: Минимальный объём за 24ч
            
        Returns:
            Список перепроданных активов
        """
        logger.info(f"Finding oversold assets on {market_type}")
        
        criteria = {
            "market_type": market_type,
            "min_volume_24h": min_volume_24h,
            "indicators": {
                "rsi_range": [0, 30]
            }
        }
        
        return await self.scan_market(criteria, limit=10)
    
    async def find_breakout_opportunities(
        self,
        market_type: str = "spot",
        min_volume_24h: float = 1000000
    ) -> List[Dict[str, Any]]:
        """
        Найти возможности пробоя (BB squeeze)
        
        Args:
            market_type: "spot" или "futures"
            min_volume_24h: Минимальный объём
            
        Returns:
            Список активов готовых к пробою
        """
        logger.info(f"Finding breakout opportunities on {market_type}")
        
        # Получаем все тикеры
        all_tickers = await self.client.get_all_tickers(market_type)
        
        opportunities = []
        
        for ticker in all_tickers:
            if ticker['volume_24h'] < min_volume_24h:
                continue
            
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
                        opportunities.append({
                            "symbol": ticker['symbol'],
                            "current_price": ticker['price'],
                            "bb_width": bb.get('width', 0),
                            "score": score,
                            "type": "BB_SQUEEZE_BREAKOUT",
                            "why": f"BB Squeeze detected (width: {bb.get('width', 0):.2f}%). Готовится к сильному движению."
                        })
                
            except Exception as e:
                logger.warning(f"Error analyzing {ticker['symbol']}: {e}")
                continue
        
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
