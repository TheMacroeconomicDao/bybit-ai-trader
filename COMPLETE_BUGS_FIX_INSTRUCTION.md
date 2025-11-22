# 🔧 ПОЛНАЯ ИНСТРУКЦИЯ ПО ИСПРАВЛЕНИЮ ВСЕХ БАГОВ

**Дата создания:** 2025-11-22  
**Версия:** 1.0  
**Статус:** Ready for Implementation

---

## 📋 СОДЕРЖАНИЕ

1. [Обзор проблем](#обзор-проблем)
2. [Архитектура исправлений](#архитектура-исправлений)
3. [Детальные инструкции по исправлению](#детальные-инструкции-по-исправлению)
4. [Тестирование](#тестирование)
5. [Проверка результатов](#проверка-результатов)

---

## 📊 ОБЗОР ПРОБЛЕМ

### Выявлено 10 критических багов:

#### Группа 1: Market Scanner Functions (5 багов)
- ❌ `scan_market` - множественные ошибки при вызове
- ❌ `find_oversold_assets` - Tool Errored
- ❌ `find_overbought_assets` - Tool Errored
- ❌ `find_breakout_opportunities` - Tool Errored
- ❌ `find_trend_reversals` - Tool Errored

**Корневая причина:** Функции выбрасывают исключения вместо возврата error response, что приводит к "Tool Errored"

#### Группа 2: Volume Profile (1 баг)
- ❌ `get_volume_profile` - JSON Serialization Error

**Корневая причина:** Возврат Python `bool` вместо JSON-совместимого типа

#### Группа 3: Interval Format Validation (3 бага)
- ❌ `get_market_structure` - Invalid enum value (expects "60", got "1h")
- ❌ `get_ml_rsi` - Invalid enum value (expects "60", got "1h")
- ❌ `get_order_blocks` - Invalid enum value (expects "60", got "1h")

**Корневая причина:** bybit-analysis MCP требует числовые интервалы, но многие функции передают строковые

---

## 🏗️ АРХИТЕКТУРА ИСПРАВЛЕНИЙ

```
┌─────────────────────────────────────────────────────────┐
│           TRADING SYSTEM ARCHITECTURE                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────┐    ┌──────────────────────┐  │
│  │ bybit-trading        │    │ bybit-analysis       │  │
│  │ (Python MCP)         │    │ (Node.js MCP)        │  │
│  │                      │    │                      │  │
│  │ FIX 1-2:             │    │ FIX 3:               │  │
│  │ • market_scanner.py  │    │ • interval_utils.ts  │  │
│  │ • volume_profile.py  │    │ • tool schemas       │  │
│  └──────────────────────┘    └──────────────────────┘  │
│           │                           │                  │
│           └───────────┬───────────────┘                  │
│                       │                                   │
│                  ┌────▼────┐                             │
│                  │ Bybit   │                             │
│                  │ API     │                             │
│                  └─────────┘                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🔨 ДЕТАЛЬНЫЕ ИНСТРУКЦИИ ПО ИСПРАВЛЕНИЮ

---

### FIX #1: Market Scanner Error Handling

**Файл:** `mcp_server/market_scanner.py`

**Проблема:** Все 5 функций scanner бросают исключения вместо возврата структурированных error responses.

**Текущий код (строки 889-960):**

```python
async def scan_market(
    self,
    criteria: Dict[str, Any],
    limit: int = 10,
    ...
) -> List[Dict[str, Any]]:
    try:
        # ... логика сканирования ...
        return final_opportunities
        
    except Exception as e:
        logger.error(f"Error in scan_market: {e}", exc_info=True)
        raise  # ❌ ПРОБЛЕМА: выбрасывает исключение
```

**Исправленный код:**

```python
async def scan_market(
    self,
    criteria: Dict[str, Any],
    limit: int = 10,
    auto_track: bool = False,
    signal_tracker: Optional[Any] = None,
    track_limit: int = 3
) -> Dict[str, Any]:  # ✅ Изменен возвращаемый тип
    """
    Универсальное сканирование рынка по критериям
    
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

        # 2. Get Account Balance
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
            account_balance = None
        
        # 3. Get Open Positions
        open_positions_symbols = []
        try:
            open_positions_data = await self.client.get_open_positions()
            open_positions_symbols = [p['symbol'] for p in open_positions_data]
            if open_positions_symbols:
                logger.info(f"Found open positions: {open_positions_symbols}")
        except Exception as e:
            logger.warning(f"Failed to get open positions: {e}")
        
        # 4. Get all tickers
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
        
        if not all_tickers or len(all_tickers) == 0:
            logger.error("No tickers received from API")
            return {
                "success": False,
                "opportunities": [],
                "error": "API Error: No tickers received from Bybit API",
                "scanned_count": 0,
                "found_count": 0
            }
        
        # 5. Filter by basic criteria
        filtered = []
        for ticker in all_tickers:
            min_volume = criteria.get('min_volume_24h', 100000)
            if ticker['volume_24h'] < min_volume:
                continue
            
            price_range = criteria.get('price_change_range')
            if price_range:
                change = ticker['change_24h']
                if change < price_range[0] or change > price_range[1]:
                    continue
            
            filtered.append(ticker)
        
        # 6. Detailed analysis with parallelization
        candidates = filtered[:min(limit * 5, 100)]
        semaphore = asyncio.Semaphore(10)
        
        async def analyze_ticker(ticker: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Analyze one ticker with error handling"""
            if ticker['symbol'] in open_positions_symbols:
                return None
                
            async with semaphore:
                try:
                    # Correlation Check
                    if open_positions_symbols:
                        is_correlated = False
                        for pos_symbol in open_positions_symbols:
                            try:
                                corr = await self.ta.get_correlation(ticker['symbol'], pos_symbol)
                                if corr > 0.7:
                                    is_correlated = True
                                    break
                            except Exception as corr_err:
                                logger.warning(f"Correlation check failed for {ticker['symbol']}: {corr_err}")
                                continue
                        if is_correlated:
                            return None

                    analysis = await self.ta.analyze_asset(
                        ticker['symbol'],
                        timeframes=["1h", "4h"],
                        include_patterns=True
                    )
                    
                    # Check indicator criteria
                    indicator_criteria = criteria.get('indicators', {})
                    if not self._check_indicator_criteria(analysis, indicator_criteria):
                        return None
                    
                    # Whale Analysis (optional)
                    enable_whale_analysis = criteria.get('include_whale_analysis', False)
                    if enable_whale_analysis and ticker.get('volume_24h', 0) > 5000000:
                        try:
                            whale_data = await self.whale_detector.detect_whale_activity(ticker['symbol'])
                            analysis['whale_analysis'] = whale_data
                        except Exception as e:
                            logger.warning(f"Failed whale analysis for {ticker['symbol']}: {e}")
                    
                    # Volume Profile (optional)
                    enable_volume_profile = criteria.get('include_volume_profile', False)
                    if enable_volume_profile or (enable_whale_analysis and ticker.get('volume_24h', 0) > 5000000):
                        try:
                            vp_data = await self.volume_profile.calculate_volume_profile(
                                ticker['symbol'],
                                timeframe="4h"
                            )
                            if '4h' in analysis.get('timeframes', {}):
                                analysis['timeframes']['4h']['volume_profile'] = vp_data
                        except Exception as e:
                            logger.warning(f"Failed volume profile for {ticker['symbol']}: {e}")
                    
                    # Entry plan (FIRST)
                    entry_plan = self._generate_entry_plan(analysis, ticker, account_balance)
                    
                    # Scoring (SECOND)
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
        
        # Parallel analysis of all candidates
        tasks = [analyze_ticker(ticker) for ticker in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        opportunities = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Task failed with exception: {result}")
                continue
            if result is not None:
                opportunities.append(result)
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # Early exit if enough high-quality opportunities
        high_quality = [opp for opp in opportunities if opp['score'] >= 7.0]
        if len(high_quality) >= limit:
            logger.info(f"Found {len(high_quality)} high-quality opportunities, returning top {limit}")
            final_opportunities = high_quality[:limit]
        else:
            final_opportunities = opportunities[:limit]
        
        # Auto-track top-N signals
        if auto_track and signal_tracker and final_opportunities:
            try:
                tracked_count = 0
                for opp in final_opportunities[:track_limit]:
                    entry_plan = opp.get('entry_plan', {})
                    if not entry_plan:
                        continue
                    
                    entry_price = entry_plan.get('entry_price')
                    stop_loss = entry_plan.get('stop_loss')
                    take_profit = entry_plan.get('take_profit')
                    side = entry_plan.get('side', 'long')
                    
                    if not all([entry_price, stop_loss, take_profit]):
                        continue
                    
                    symbol = opp.get('symbol', '').replace('/', '')
                    if not symbol:
                        continue
                    
                    analysis = opp.get('analysis', {})
                    score = opp.get('score', 0)
                    probability = opp.get('probability', 0.5)
                    
                    # Extract timeframe
                    timeframe = None
                    if 'timeframes' in analysis:
                        for tf in ["4h", "1h", "15m"]:
                            if tf in analysis['timeframes']:
                                timeframe = tf
                                break
                    
                    # Extract patterns
                    pattern_type = None
                    pattern_name = None
                    if 'patterns' in analysis:
                        patterns = analysis['patterns']
                        if patterns:
                            first_pattern = patterns[0] if isinstance(patterns, list) else list(patterns.values())[0]
                            if isinstance(first_pattern, dict):
                                pattern_type = first_pattern.get('type')
                                pattern_name = first_pattern.get('name')
                    
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
                        logger.info(f"✅ Auto-tracked signal: {signal_id} for {symbol} {side}")
                    except Exception as e:
                        logger.warning(f"Failed to track signal for {symbol}: {e}")
                        continue
                
                if tracked_count > 0:
                    logger.info(f"✅ Auto-tracked {tracked_count} signals")
            except Exception as e:
                logger.warning(f"Failed to auto-track signals: {e}")
        
        # ✅ SUCCESS RESPONSE
        return {
            "success": True,
            "opportunities": final_opportunities,
            "error": None,
            "scanned_count": len(candidates),
            "found_count": len(final_opportunities)
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
```

**Аналогичные изменения для остальных 4 функций:**

#### find_oversold_assets

```python
async def find_oversold_assets(
    self,
    market_type: str = "spot",
    min_volume_24h: float = 1000000
) -> Dict[str, Any]:  # ✅ Изменен тип
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
```

#### find_overbought_assets

```python
async def find_overbought_assets(
    self,
    market_type: str = "spot",
    min_volume_24h: float = 1000000
) -> Dict[str, Any]:  # ✅ Изменен тип
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
```

#### find_breakout_opportunities

```python
async def find_breakout_opportunities(
    self,
    market_type: str = "spot",
    min_volume_24h: float = 1000000
) -> Dict[str, Any]:  # ✅ Изменен тип
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
```

#### find_trend_reversals

```python
async def find_trend_reversals(
    self,
    market_type: str = "spot",
    min_volume_24h: float = 1000000
) -> Dict[str, Any]:  # ✅ Изменен тип
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
```

---

### FIX #2: Volume Profile JSON Serialization

**Файл:** `mcp_server/volume_profile.py`

**Проблема:** Возврат Python `bool` вместо JSON-совместимого типа на строке 64

**Текущий код (строка 64):**

```python
confluence_with_poc = abs(current - poc) / current < 0.02 if current > 0 else False
```

**Исправленный код:**

```python
# Явно конвертируем в JSON-совместимый bool
confluence_with_poc = bool(abs(current - poc) / current < 0.02) if current > 0 else False
```

**Полная функция с исправлением:**

```python
async def calculate_volume_profile(self, symbol: str, timeframe: str = "1h", lookback: int = 100) -> Dict[str, Any]:
    try:
        ohlcv = await self.client.get_ohlcv(symbol, timeframe, limit=lookback)
        if not ohlcv or len(ohlcv) < 10:
            return {"error": "Insufficient data"}
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        price_range = df['high'].max() - df['low'].min()
        if price_range == 0:
            return {"error": "Zero price range"}
        
        num_bins = 50
        bin_size = price_range / num_bins
        min_price = df['low'].min()
        
        volume_by_level = {}
        for idx, row in df.iterrows():
            for i in range(num_bins):
                bin_mid = min_price + (i + 0.5) * bin_size
                if row['low'] <= bin_mid <= row['high']:
                    if bin_mid not in volume_by_level:
                        volume_by_level[bin_mid] = 0
                    volume_by_level[bin_mid] += row['volume']
        
        if not volume_by_level:
            return {"error": "Could not calculate volume profile"}
        
        # POC (Point of Control)
        poc = max(volume_by_level.items(), key=lambda x: x[1])[0]
        
        # Value Area (70% volume)
        sorted_levels = sorted(volume_by_level.items(), key=lambda x: x[1], reverse=True)
        total_vol = sum(v for p, v in sorted_levels)
        va_vol = 0
        va_levels = []
        for price, vol in sorted_levels:
            va_vol += vol
            va_levels.append(price)
            if va_vol >= total_vol * 0.70:
                break
        
        va_high = max(va_levels)
        va_low = min(va_levels)
        current = float(df['close'].iloc[-1])
        
        position = "above_va" if current > va_high else "below_va" if current < va_low else "in_va"
        
        # ✅ FIX: Явно конвертируем в JSON-совместимый bool
        confluence_with_poc = bool(abs(current - poc) / current < 0.02) if current > 0 else False
        
        return {
            "poc": round(float(poc), 4),
            "value_area_high": round(float(va_high), 4),
            "value_area_low": round(float(va_low), 4),
            "current_position": position,
            "confluence_with_poc": confluence_with_poc,  # ✅ Теперь это JSON-совместимый bool
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating volume profile: {e}")
        return {"error": str(e)}
```

---

### FIX #3: Interval Format Converter для bybit-analysis MCP

**Проблема:** bybit-analysis MCP требует числовые интервалы ("60"), но получает строковые ("1h")

**Затронутые tools:**
- `get_market_structure`
- `get_ml_rsi`
- `get_order_blocks`

**Решение:** Создать утилиту конвертации интервалов

#### Шаг 1: Создать interval converter

**Новый файл:** `bybit-mcp/src/utils/intervalConverter.ts`

```typescript
/**
 * Interval Converter для bybit-analysis MCP
 * Конвертирует строковые интервалы ("1h") в числовые ("60")
 */

export interface IntervalMapping {
  [key: string]: string;
}

/**
 * Маппинг строковых интервалов в числовые Bybit API интервалы
 */
export const INTERVAL_MAP: IntervalMapping = {
  // Минуты
  "1m": "1",
  "3m": "3",
  "5m": "5",
  "15m": "15",
  "30m": "30",
  
  // Часы (конвертируем в минуты)
  "1h": "60",
  "2h": "120",
  "4h": "240",
  "6h": "360",
  "12h": "720",
  
  // Дни/недели/месяцы (буквенные)
  "1d": "D",
  "1w": "W",
  "1M": "M",
  
  // Прямые числовые (pass-through)
  "1": "1",
  "3": "3",
  "5": "5",
  "15": "15",
  "30": "30",
  "60": "60",
  "120": "120",
  "240": "240",
  "360": "360",
  "720": "720",
  "D": "D",
  "W": "W",
  "M": "M"
};

/**
 * Конвертирует interval в Bybit API формат
 * 
 * @param interval - Интервал в любом формате ("1h", "60", etc.)
 * @returns Bybit API интервал ("60", "D", etc.)
 * @throws Error если интервал не поддерживается
 */
export function convertInterval(interval: string): string {
  const normalized = interval.trim();
  
  // Проверяем, есть ли mapping
  if (INTERVAL_MAP[normalized]) {
    return INTERVAL_MAP[normalized];
  }
  
  // Если нет в маппинге - пытаемся использовать как есть (для прямых numbers like "60")
  // Но это должно быть валидное значение для Bybit API
  const validValues = new Set(Object.values(INTERVAL_MAP));
  if (validValues.has(normalized)) {
    return normalized;
  }
  
  // Если не найдено - ошибка
  throw new Error(
    `Unsupported interval: "${interval}". ` +
    `Supported: ${Object.keys(INTERVAL_MAP).join(", ")}`
  );
}

/**
 * Проверяет, валиден ли интервал
 */
export function isValidInterval(interval: string): boolean {
  try {
    convertInterval(interval);
    return true;
  } catch {
    return false;
  }
}

/**
 * Получить список всех поддерживаемых интервалов
 */
export function getSupportedIntervals(): string[] {
  return Object.keys(INTERVAL_MAP);
}
```

#### Шаг 2: Обновить схемы tools

**Файл:** `bybit-mcp/src/tools/GetMarketStructure.ts` (и аналогично для других)

**Добавить в начало файла:**

```typescript
import { convertInterval } from '../utils/intervalConverter.js';
```

**Обновить схему параметров:**

```typescript
export const getMarketStructureTool: ToolDefinition = {
  name: "get_market_structure",
  description: "Get market structure analysis (regime, trend strength, volatility)",
  inputSchema: {
    type: "object",
    properties: {
      symbol: {
        type: "string",
        description: "Trading pair (e.g. BTCUSDT)"
      },
      category: {
        type: "string",
        enum: ["spot", "linear", "inverse"],
        description: "Market category"
      },
      interval: {
        type: "string",
        description: "Timeframe interval. Supports both string (1h, 4h) and numeric (60, 240) formats",
        // ✅ Расширенное описание с примерами обоих форматов
      }
    },
    required: ["symbol", "category", "interval"]
  }
};
```

**Обновить реализацию:**

```typescript
export async function getMarketStructureImpl(args: GetMarketStructureArgs): Promise<any> {
  const { symbol, category, interval } = args;
  
  // ✅ Конвертируем interval перед использованием
  let convertedInterval: string;
  try {
    convertedInterval = convertInterval(interval);
  } catch (error) {
    throw new Error(
      `Invalid interval format: "${interval}". ` +
      `Supported formats: 1m, 5m, 15m, 1h, 4h, 1d, or numeric: 1, 5, 15, 60, 240, D`
    );
  }
  
  const client = await getOrCreateClient();
  
  // Используем конвертированный interval
  const klines = await client.getKlineData(symbol, convertedInterval, category, 100);
  
  // ... остальная логика ...
}
```

#### Шаг 3: Аналогичные изменения для других tools

**Файлы для обновления:**
1. `bybit-mcp/src/tools/GetMLRSI.ts`
2. `bybit-mcp/src/tools/GetOrderBlocks.ts`

**Для каждого:**

```typescript
import { convertInterval } from '../utils/intervalConverter.js';

// В функции implementation:
export async function getMLRsiImpl(args: GetMLRsiArgs): Promise<any> {
  const { symbol, interval, category } = args;
  
  // ✅ Конвертируем interval
  let convertedInterval: string;
  try {
    convertedInterval = convertInterval(interval);
  } catch (error) {
    throw new Error(
      `Invalid interval format: "${interval}". ` +
      `Supported: 1m, 5m, 15m, 1h, 4h, 1d, or numeric: 1, 5, 15, 60, 240, D`
    );
  }
  
  const client = await getOrCreateClient();
  const klines = await client.getKlineData(symbol, convertedInterval, category, 100);
  
  // ... остальная логика ...
}
```

#### Шаг 4: Обновить toolLoader

**Файл:** `bybit-mcp/src/utils/toolLoader.ts`

Убедиться, что новый конвертер экспортируется:

```typescript
export { convertInterval, isValidInterval, getSupportedIntervals } from './intervalConverter.js';
```

---

## ✅ ТЕСТИРОВАНИЕ

### Тест #1: Market Scanner Functions

```python
# test_market_scanner_fixes.py

import asyncio
from mcp_server.bybit_client import BybitClient
from mcp_server.technical_analysis import TechnicalAnalysis
from mcp_server.market_scanner import MarketScanner

async def test_scan_market():
    """Тест scan_market возвращает Dict, не Exception"""
    client = BybitClient("api_key", "api_secret", testnet=False)
    ta = TechnicalAnalysis(client)
    scanner = MarketScanner(client, ta)
    
    criteria = {
        "min_volume_24h": 1000000,
        "market_type": "spot"
    }
    
    result = await scanner.scan_market(criteria, limit=5)
    
    # ✅ Проверяем, что возвращается Dict
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    
    # ✅ Проверяем, что есть ключ success
    assert "success" in result, "Result должен содержать ключ 'success'"
    assert "opportunities" in result, "Result должен содержать ключ 'opportunities'"
    assert "error" in result, "Result должен содержать ключ 'error'"
    
    # ✅ Если success=True, opportunities должен быть списком
    if result["success"]:
        assert isinstance(result["opportunities"], list)
        print(f"✅ scan_market: SUCCESS, found {len(result['opportunities'])} opportunities")
    else:
        print(f"⚠️ scan_market: FAILED with error: {result['error']}")
    
    await client.close()

async def test_find_oversold():
    """Тест find_oversold_assets возвращает Dict"""
    client = BybitClient("api_key", "api_secret", testnet=False)
    ta = TechnicalAnalysis(client)
    scanner = MarketScanner(client, ta)
    
    result = await scanner.find_oversold_assets(market_type="spot")
    
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "success" in result
    assert "opportunities" in result
    
    if result["success"]:
        print(f"✅ find_oversold_assets: SUCCESS, found {len(result['opportunities'])} opportunities")
    else:
        print(f"⚠️ find_oversold_assets: FAILED with error: {result['error']}")
    
    await client.close()

async def test_find_overbought():
    """Тест find_overbought_assets возвращает Dict"""
    client = BybitClient("api_key", "api_secret", testnet=False)
    ta = TechnicalAnalysis(client)
    scanner = MarketScanner(client, ta)
    
    result = await scanner.find_overbought_assets(market_type="spot")
    
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "success" in result
    
    if result["success"]:
        print(f"✅ find_overbought_assets: SUCCESS, found {len(result['opportunities'])} opportunities")
    else:
        print(f"⚠️ find_overbought_assets: FAILED with error: {result['error']}")
    
    await client.close()

async def test_find_breakouts():
    """Тест find_breakout_opportunities возвращает Dict"""
    client = BybitClient("api_key", "api_secret", testnet=False)
    ta = TechnicalAnalysis(client)
    scanner = MarketScanner(client, ta)
    
    result = await scanner.find_breakout_opportunities(market_type="spot")
    
    assert isinstance(result, dict)
    assert "success" in result
    
    if result["success"]:
        print(f"✅ find_breakout_opportunities: SUCCESS, found {len(result['opportunities'])} opportunities")
    else:
        print(f"⚠️ find_breakout_opportunities: FAILED with error: {result['error']}")
    
    await client.close()

async def test_find_reversals():
    """Тест find_trend_reversals возвращает Dict"""
    client = BybitClient("api_key", "api_secret", testnet=False)
    ta = TechnicalAnalysis(client)
    scanner = MarketScanner(client, ta)
    
    result = await scanner.find_trend_reversals(market_type="spot")
    
    assert isinstance(result, dict)
    assert "success" in result
    
    if result["success"]:
        print(f"✅ find_trend_reversals: SUCCESS, found {len(result['opportunities'])} opportunities")
    else:
        print(f"⚠️ find_trend_reversals: FAILED with error: {result['error']}")
    
    await client.close()

if __name__ == "__main__":
    print("="*50)
    print("TESTING MARKET SCANNER FIXES")
    print("="*50)
    
    asyncio.run(test_scan_market())
    asyncio.run(test_find_oversold())
    asyncio.run(test_find_overbought())
    asyncio.run(test_find_breakouts())
    asyncio.run(test_find_reversals())
    
    print("="*50)
    print("ALL TESTS COMPLETED")
    print("="*50)
```

### Тест #2: Volume Profile JSON Serialization

```python
# test_volume_profile_fix.py

import asyncio
import json
from mcp_server.bybit_client import BybitClient
from mcp_server.volume_profile import VolumeProfileAnalyzer

async def test_volume_profile_json():
    """Тест что volume profile возвращает JSON-сериализуемые данные"""
    client = BybitClient("api_key", "api_secret", testnet=False)
    vp = VolumeProfileAnalyzer(client)
    
    result = await vp.calculate_volume_profile("BTC/USDT", timeframe="1h")
    
    # ✅ Проверяем, что результат сериализуется в JSON
    try:
        json_str = json.dumps(result)
        print(f"✅ Volume Profile JSON serialization: SUCCESS")
        print(f"   Result keys: {list(result.keys())}")
        print(f"   Confluence with POC: {result.get('confluence_with_poc')} (type: {type(result.get('confluence_with_poc'))})")
    except TypeError as e:
        print(f"❌ Volume Profile JSON serialization: FAILED")
        print(f"   Error: {e}")
        raise
    
    await client.close()

if __name__ == "__main__":
    print("="*50)
    print("TESTING VOLUME PROFILE FIX")
    print("="*50)
    
    asyncio.run(test_volume_profile_json())
    
    print("="*50)
```

### Тест #3: Interval Converter

```typescript
// test_interval_converter.test.ts

import { convertInterval, isValidInterval, getSupportedIntervals } from '../src/utils/intervalConverter';

describe('Interval Converter', () => {
  test('converts string intervals to numeric', () => {
    expect(convertInterval('1h')).toBe('60');
    expect(convertInterval('4h')).toBe('240');
    expect(convertInterval('1d')).toBe('D');
  });
  
  test('passes through valid numeric intervals', () => {
    expect(convertInterval('60')).toBe('60');
    expect(convertInterval('240')).toBe('240');
    expect(convertInterval('D')).toBe('D');
  });
  
  test('handles minute intervals', () => {
    expect(convertInterval('1m')).toBe('1');
    expect(convertInterval('5m')).toBe('5');
    expect(convertInterval('15m')).toBe('15');
  });
  
  test('throws error for invalid intervals', () => {
    expect(() => convertInterval('invalid')).toThrow();
    expect(() => convertInterval('999m')).toThrow();
  });
  
  test('validates intervals correctly', () => {
    expect(isValidInterval('1h')).toBe(true);
    expect(isValidInterval('60')).toBe(true);
    expect(isValidInterval('invalid')).toBe(false);
  });
  
  test('getSupportedIntervals returns all mappings', () => {
    const supported = getSupportedIntervals();
    expect(supported).toContain('1h');
    expect(supported).toContain('4h');
    expect(supported).toContain('1d');
    expect(supported).toContain('60');
  });
});
```

---

## 📝 ПРОВЕРКА РЕЗУЛЬТАТОВ

### Чеклист исправлений

#### Market Scanner (5 функций)
- [ ] `scan_market` возвращает `Dict[str, Any]` вместо `List`
- [ ] `scan_market` НЕ бросает исключения, возвращает `{"success": False, "error": "..."}`
- [ ] `find_oversold_assets` возвращает `Dict[str, Any]`
- [ ] `find_overbought_assets` возвращает `Dict[str, Any]`
- [ ] `find_breakout_opportunities` возвращает `Dict[str, Any]`
- [ ] `find_trend_reversals` возвращает `Dict[str, Any]`
- [ ] Все функции обрабатывают ошибки gracefully

#### Volume Profile
- [ ] `calculate_volume_profile` возвращает JSON-сериализуемый `bool`
- [ ] `confluence_with_poc` правильно конвертируется через `bool()`
- [ ] Результат успешно сериализуется через `json.dumps()`

#### Interval Converter
- [ ] Создан файл `bybit-mcp/src/utils/intervalConverter.ts`
- [ ] `convertInterval()` корректно конвертирует "1h" → "60"
- [ ] `convertInterval()` корректно конвертирует "4h" → "240"
- [ ] `get_market_structure` использует `convertInterval()`
- [ ] `get_ml_rsi` использует `convertInterval()`
- [ ] `get_order_blocks` использует `convertInterval()`
- [ ] Обновлены схемы tools (inputSchema descriptions)

### Проверка через MCP

```bash
# Test bybit-trading MCP
python mcp_server/full_server.py

# В другом терминале - вызов через MCP client
# Тестируем scan_market
mcp call bybit-trading scan_market '{"criteria": {"min_volume_24h": 1000000}, "limit": 5}'

# Ожидаемый результат:
# {
#   "success": true,
#   "opportunities": [...],
#   "error": null,
#   "scanned_count": 100,
#   "found_count": 5
# }

# Тестируем find_oversold_assets
mcp call bybit-trading find_oversold_assets '{"market_type": "spot"}'

# Тестируем get_volume_profile
mcp call bybit-trading get_volume_profile '{"symbol": "BTC/USDT", "timeframe": "1h"}'

# Test bybit-analysis MCP
cd bybit-mcp
npm run build
node build/index.js

# В другом терминале
# Тестируем get_market_structure с "1h"
mcp call bybit-analysis get_market_structure '{"symbol": "BTCUSDT", "category": "spot", "interval": "1h"}'

# Тестируем get_ml_rsi с "60"
mcp call bybit-analysis get_ml_rsi '{"symbol": "BTCUSDT", "category": "spot", "interval": "60"}'
```

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

После применения всех исправлений:

### ✅ Market Scanner Functions
```json
{
  "success": true,
  "opportunities": [
    {
      "symbol": "BTC/USDT",
      "score": 8.5,
      "probability": 0.75,
      "entry_plan": {...}
    }
  ],
  "error": null,
  "scanned_count": 100,
  "found_count": 1
}
```

### ✅ Volume Profile
```json
{
  "poc": 84500.0,
  "value_area_high": 85000.0,
  "value_area_low": 84000.0,
  "current_position": "in_va",
  "confluence_with_poc": true,
  "timestamp": "2025-11-22T12:35:00Z"
}
```

### ✅ Interval Converter
```
Input: "1h" → Output: "60" ✅
Input: "4h" → Output: "240" ✅
Input: "1d" → Output: "D" ✅
Input: "60" → Output: "60" ✅
```

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

### Документация
- [Bybit API v5 Intervals](https://bybit-exchange.github.io/docs/v5/enum#interval)
- [Python asyncio Error Handling](https://docs.python.org/3/library/asyncio-exceptions.html)
- [TypeScript Type Guards](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)

### Файлы для справки
- `mcp_server/market_scanner.py` - Market scanner implementation
- `mcp_server/volume_profile.py` - Volume profile analyzer
- `bybit-mcp/src/tools/*.ts` - Tool implementations
- `MARKET_ANALYSIS_BUGS_REPORT.md` - Original bug report

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ

Перед завершением убедитесь:

- [ ] Все 5 market scanner функций возвращают `Dict[str, Any]`
- [ ] Все exception handling обновлен (return Dict вместо raise)
- [ ] Volume Profile конвертирует `bool` правильно
- [ ] Interval converter создан и протестирован
- [ ] Все 3 bybit-analysis tools используют converter
- [ ] Запущены unit tests (Python)
- [ ] Запущены unit tests (TypeScript)
- [ ] Проверено через MCP client
- [ ] Документация обновлена
- [ ] Git commit с описанием изменений

---

## 🎉 ЗАВЕРШЕНИЕ

После применения всех исправлений:

1. **10/10 багов исправлено** ✅
2. **Market scanner стабилен** ✅
3. **Volume profile сериализуется** ✅
4. **Interval format универсален** ✅

**Система готова к production использованию!** 🚀

---

*Документ создан: 2025-11-22*  
*Автор: Trading System Architect*  
*Версия: 1.0 Final*