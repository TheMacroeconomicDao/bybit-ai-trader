"""Whale Detection & Large Order Tracking"""
from typing import Dict, List, Any
import numpy as np
from loguru import logger
from datetime import datetime


class WhaleDetector:
    def __init__(self, bybit_client):
        self.client = bybit_client
        self.whale_threshold_multiplier = 10.0
        logger.info("Whale Detector initialized")
    
    async def detect_whale_activity(self, symbol: str, lookback_trades: int = 1000) -> Dict[str, Any]:
        try:
            trades = await self.client.get_public_trade_history(symbol, limit=lookback_trades)
            if not trades:
                return {"whale_activity": "unknown", "error": "No data"}
            
            large_orders = self._detect_large_orders(trades)
            orderbook = await self.client.get_orderbook(symbol, limit=50)
            walls = self._detect_orderbook_walls(orderbook)
            flow = self._analyze_whale_flow(large_orders, walls)
            activity_pattern = self._detect_activity_pattern(large_orders, trades)
            signals = self._generate_whale_signals(activity_pattern, flow, walls)
            
            return {
                "whale_activity": activity_pattern,
                "large_orders": large_orders,
                "orderbook_walls": walls,
                "flow_direction": flow,
                "confidence": self._calculate_confidence(large_orders, walls),
                "signals": signals,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error detecting whale activity: {e}")
            return {"whale_activity": "error", "error": str(e)}
    
    def _detect_large_orders(self, trades: List[Dict]) -> Dict[str, Any]:
        if not trades:
            return {
                "count_large_buys": 0,
                "count_large_sells": 0,
                "whale_buy_percentage": 0,
                "whale_sell_percentage": 0,
                "net_direction": "neutral"
            }
        
        # Получаем amount из разных возможных полей
        amounts = []
        for t in trades:
            amount = t.get('amount') or t.get('size') or t.get('quantity') or 0
            if amount:
                amounts.append(float(amount))
        
        if not amounts:
            return {
                "count_large_buys": 0,
                "count_large_sells": 0,
                "whale_buy_percentage": 0,
                "whale_sell_percentage": 0,
                "net_direction": "neutral"
            }
        
        avg_size = np.mean(amounts)
        whale_threshold = avg_size * self.whale_threshold_multiplier
        
        large_buys = []
        large_sells = []
        
        for t in trades:
            amount = float(t.get('amount') or t.get('size') or t.get('quantity') or 0)
            if amount > whale_threshold:
                side = t.get('side', '').lower()
                if side == 'buy':
                    large_buys.append(t)
                elif side == 'sell':
                    large_sells.append(t)
        
        total_volume = sum(amounts)
        whale_buy_vol = sum(float(t.get('amount') or t.get('size') or t.get('quantity') or 0) for t in large_buys)
        whale_sell_vol = sum(float(t.get('amount') or t.get('size') or t.get('quantity') or 0) for t in large_sells)
        
        net_direction = "bullish" if len(large_buys) > len(large_sells) * 1.5 else "bearish" if len(large_sells) > len(large_buys) * 1.5 else "neutral"
        
        return {
            "count_large_buys": len(large_buys),
            "count_large_sells": len(large_sells),
            "whale_buy_percentage": round(whale_buy_vol / total_volume * 100, 2) if total_volume > 0 else 0,
            "whale_sell_percentage": round(whale_sell_vol / total_volume * 100, 2) if total_volume > 0 else 0,
            "net_direction": net_direction
        }
    
    def _detect_orderbook_walls(self, orderbook: Dict) -> Dict[str, Any]:
        if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
            return {"bid_walls": [], "ask_walls": [], "imbalance_direction": "neutral", "imbalance": 0.0}
        
        bids = orderbook['bids'][:20]
        asks = orderbook['asks'][:20]
        
        if not bids or not asks:
            return {"bid_walls": [], "ask_walls": [], "imbalance_direction": "neutral", "imbalance": 0.0}
        
        bid_sizes = [float(b[1]) for b in bids]
        ask_sizes = [float(a[1]) for a in asks]
        
        avg_bid = np.mean(bid_sizes) if bid_sizes else 0
        avg_ask = np.mean(ask_sizes) if ask_sizes else 0
        
        bid_walls = [{"price": float(b[0]), "size": float(b[1])} for b in bids if float(b[1]) > avg_bid * 3]
        ask_walls = [{"price": float(a[0]), "size": float(a[1])} for a in asks if float(a[1]) > avg_ask * 3]
        
        total_bid = sum(bid_sizes)
        total_ask = sum(ask_sizes)
        total_volume = total_bid + total_ask
        
        imbalance = (total_bid - total_ask) / total_volume if total_volume > 0 else 0.0
        
        return {
            "bid_walls": bid_walls,
            "ask_walls": ask_walls,
            "imbalance": round(imbalance, 3),
            "imbalance_direction": "bullish" if imbalance > 0.15 else "bearish" if imbalance < -0.15 else "neutral"
        }
    
    def _analyze_whale_flow(self, large_orders: Dict, walls: Dict) -> str:
        net = large_orders.get('net_direction', 'neutral')
        imb = walls.get('imbalance_direction', 'neutral')
        
        if net == "bullish" and imb == "bullish":
            return "strong_bullish"
        elif net == "bearish" and imb == "bearish":
            return "strong_bearish"
        elif net == "bullish" or imb == "bullish":
            return "bullish"
        elif net == "bearish" or imb == "bearish":
            return "bearish"
        return "neutral"
    
    def _detect_activity_pattern(self, large_orders: Dict, trades: List) -> str:
        buy_pct = large_orders.get('whale_buy_percentage', 0)
        sell_pct = large_orders.get('whale_sell_percentage', 0)
        
        if buy_pct > 15:
            return "accumulation"
        elif sell_pct > 15:
            return "distribution"
        return "neutral"
    
    def _generate_whale_signals(self, activity: str, flow: str, walls: Dict) -> List[str]:
        signals = []
        if activity == "accumulation":
            signals.append("🐋 WHALE ACCUMULATION - Strong bullish")
        elif activity == "distribution":
            signals.append("🐋 WHALE DISTRIBUTION - Strong bearish")
        
        if flow == "strong_bullish":
            signals.append("💰 Whales + Orderbook aligned BULLISH")
        elif flow == "strong_bearish":
            signals.append("💰 Whales + Orderbook aligned BEARISH")
        
        return signals
    
    def _calculate_confidence(self, orders: Dict, walls: Dict) -> float:
        conf = 0.5
        if orders.get('count_large_buys', 0) > orders.get('count_large_sells', 0) * 2:
            conf += 0.2
        if abs(walls.get('imbalance', 0)) > 0.25:
            conf += 0.2
        return min(0.95, conf)






