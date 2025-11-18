"""
Quality Metrics
Расчет метрик качества сигналов для анализа эффективности
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
from loguru import logger

from mcp_server.signal_tracker import SignalTracker


class QualityMetrics:
    """Расчет метрик качества сигналов"""
    
    def __init__(self, signal_tracker: SignalTracker):
        """
        Инициализация калькулятора метрик
        
        Args:
            signal_tracker: Экземпляр SignalTracker
        """
        self.tracker = signal_tracker
        logger.info("Quality Metrics calculator initialized")
    
    async def calculate_overall_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Рассчитать общие метрики качества
        
        Args:
            days: Количество дней для анализа
            
        Returns:
            Словарь с метриками:
            {
                "total_signals": int,
                "completed_signals": int,
                "win_rate": float,
                "avg_confluence": float,
                "avg_predicted_probability": float,
                "avg_actual_rr": float,
                "avg_predicted_rr": float,
                "accuracy_by_confluence": Dict,
                "accuracy_by_probability": Dict
            }
        """
        cursor = self.tracker.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Базовая статистика
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN result = 'tp_hit' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'sl_hit' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result LIKE 'timeout%' THEN 1 ELSE 0 END) as timeouts,
                AVG(confluence_score) as avg_confluence,
                AVG(probability) as avg_probability,
                AVG(actual_rr) as avg_actual_rr,
                AVG(risk_reward) as avg_predicted_rr,
                AVG(time_to_result) as avg_time_to_result
            FROM signals
            WHERE created_at >= ?
        """, (cutoff_date.isoformat(),))
        
        row = cursor.fetchone()
        stats = dict(row) if row else {}
        
        total_signals = stats.get("total") or 0
        completed_signals = stats.get("completed") or 0
        wins = stats.get("wins") or 0
        
        # Win rate
        win_rate = wins / completed_signals if completed_signals > 0 else 0.0
        
        # Accuracy by confluence ranges
        accuracy_by_confluence = await self._calculate_accuracy_by_confluence(days)
        
        # Accuracy by probability ranges
        accuracy_by_probability = await self._calculate_accuracy_by_probability(days)
        
        return {
            "total_signals": total_signals,
            "completed_signals": completed_signals,
            "active_signals": total_signals - completed_signals,
            "wins": wins,
            "losses": stats.get("losses") or 0,
            "timeouts": stats.get("timeouts") or 0,
            "win_rate": round(win_rate, 4),
            "avg_confluence": round(stats.get("avg_confluence") or 0, 2),
            "avg_predicted_probability": round(stats.get("avg_probability") or 0, 4),
            "avg_actual_rr": round(stats.get("avg_actual_rr") or 0, 2),
            "avg_predicted_rr": round(stats.get("avg_predicted_rr") or 0, 2),
            "avg_time_to_result_hours": round((stats.get("avg_time_to_result") or 0) / 3600, 2),
            "accuracy_by_confluence": accuracy_by_confluence,
            "accuracy_by_probability": accuracy_by_probability
        }
    
    async def _calculate_accuracy_by_confluence(self, days: int) -> Dict[str, Any]:
        """Расчет точности по диапазонам confluence"""
        cursor = self.tracker.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        ranges = [
            ("8.0-8.5", 8.0, 8.5),
            ("8.5-9.0", 8.5, 9.0),
            ("9.0-9.5", 9.0, 9.5),
            ("9.5+", 9.5, 100.0)
        ]
        
        result = {}
        
        for range_name, min_score, max_score in ranges:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN result = 'tp_hit' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = 'sl_hit' THEN 1 ELSE 0 END) as losses,
                    AVG(actual_rr) as avg_rr
                FROM signals
                WHERE created_at >= ?
                AND status = 'completed'
                AND confluence_score >= ?
                AND confluence_score < ?
            """, (cutoff_date.isoformat(), min_score, max_score))
            
            row = cursor.fetchone()
            if row:
                total = row["total"] or 0
                wins = row["wins"] or 0
                
                if total > 0:
                    result[range_name] = {
                        "total": total,
                        "wins": wins,
                        "losses": row["losses"] or 0,
                        "win_rate": round(wins / total, 4),
                        "avg_actual_rr": round(row["avg_rr"] or 0, 2)
                    }
                else:
                    result[range_name] = {
                        "total": 0,
                        "wins": 0,
                        "losses": 0,
                        "win_rate": 0.0,
                        "avg_actual_rr": 0.0
                    }
        
        return result
    
    async def _calculate_accuracy_by_probability(self, days: int) -> Dict[str, Any]:
        """Расчет точности по диапазонам вероятности"""
        cursor = self.tracker.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        ranges = [
            ("65-70%", 0.65, 0.70),
            ("70-75%", 0.70, 0.75),
            ("75-80%", 0.75, 0.80),
            ("80%+", 0.80, 1.0)
        ]
        
        result = {}
        
        for range_name, min_prob, max_prob in ranges:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN result = 'tp_hit' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = 'sl_hit' THEN 1 ELSE 0 END) as losses,
                    AVG(actual_rr) as avg_rr
                FROM signals
                WHERE created_at >= ?
                AND status = 'completed'
                AND probability >= ?
                AND probability < ?
            """, (cutoff_date.isoformat(), min_prob, max_prob))
            
            row = cursor.fetchone()
            if row:
                total = row["total"] or 0
                wins = row["wins"] or 0
                
                if total > 0:
                    result[range_name] = {
                        "total": total,
                        "wins": wins,
                        "losses": row["losses"] or 0,
                        "win_rate": round(wins / total, 4),
                        "avg_actual_rr": round(row["avg_rr"] or 0, 2)
                    }
                else:
                    result[range_name] = {
                        "total": 0,
                        "wins": 0,
                        "losses": 0,
                        "win_rate": 0.0,
                        "avg_actual_rr": 0.0
                    }
        
        return result
    
    async def analyze_pattern_performance(self) -> Dict[str, Any]:
        """
        Анализ эффективности паттернов
        
        Returns:
            Статистика по паттернам
        """
        cursor = self.tracker.conn.cursor()
        cursor.execute("""
            SELECT 
                pattern_type,
                pattern_name,
                timeframe,
                total_signals,
                wins,
                losses,
                win_rate,
                avg_confluence,
                avg_actual_rr
            FROM pattern_performance
            WHERE total_signals > 0
            ORDER BY win_rate DESC, total_signals DESC
        """)
        
        rows = cursor.fetchall()
        
        patterns = []
        for row in rows:
            patterns.append({
                "pattern_type": row["pattern_type"],
                "pattern_name": row["pattern_name"],
                "timeframe": row["timeframe"],
                "total_signals": row["total_signals"],
                "wins": row["wins"],
                "losses": row["losses"],
                "win_rate": round(row["win_rate"] or 0, 4),
                "avg_confluence": round(row["avg_confluence"] or 0, 2),
                "avg_actual_rr": round(row["avg_actual_rr"] or 0, 2)
            })
        
        # Группировка по типам паттернов
        by_type = {}
        for pattern in patterns:
            ptype = pattern["pattern_type"]
            if ptype not in by_type:
                by_type[ptype] = {
                    "total_signals": 0,
                    "total_wins": 0,
                    "total_losses": 0,
                    "patterns": []
                }
            
            by_type[ptype]["total_signals"] += pattern["total_signals"]
            by_type[ptype]["total_wins"] += pattern["wins"]
            by_type[ptype]["total_losses"] += pattern["losses"]
            by_type[ptype]["patterns"].append(pattern)
        
        # Расчет win rate по типам
        for ptype, data in by_type.items():
            total = data["total_signals"]
            if total > 0:
                data["win_rate"] = round(data["total_wins"] / total, 4)
            else:
                data["win_rate"] = 0.0
        
        return {
            "by_pattern": patterns,
            "by_type": by_type,
            "total_patterns": len(patterns)
        }
    
    async def analyze_timeframe_performance(self) -> Dict[str, Any]:
        """
        Анализ эффективности по таймфреймам
        
        Returns:
            Статистика по таймфреймам
        """
        cursor = self.tracker.conn.cursor()
        cursor.execute("""
            SELECT 
                timeframe,
                COUNT(*) as total,
                SUM(CASE WHEN result = 'tp_hit' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'sl_hit' THEN 1 ELSE 0 END) as losses,
                AVG(confluence_score) as avg_confluence,
                AVG(probability) as avg_probability,
                AVG(actual_rr) as avg_actual_rr,
                AVG(time_to_result) as avg_time_to_result
            FROM signals
            WHERE status = 'completed'
            AND timeframe IS NOT NULL
            GROUP BY timeframe
            ORDER BY win_rate DESC
        """)
        
        rows = cursor.fetchall()
        
        timeframes = []
        for row in rows:
            total = row["total"] or 0
            wins = row["wins"] or 0
            win_rate = wins / total if total > 0 else 0.0
            
            timeframes.append({
                "timeframe": row["timeframe"],
                "total_signals": total,
                "wins": wins,
                "losses": row["losses"] or 0,
                "win_rate": round(win_rate, 4),
                "avg_confluence": round(row["avg_confluence"] or 0, 2),
                "avg_probability": round(row["avg_probability"] or 0, 4),
                "avg_actual_rr": round(row["avg_actual_rr"] or 0, 2),
                "avg_time_to_result_hours": round((row["avg_time_to_result"] or 0) / 3600, 2)
            })
        
        return {
            "by_timeframe": timeframes,
            "total_timeframes": len(timeframes)
        }
    
    async def calculate_confluence_accuracy(self) -> Dict[str, Any]:
        """
        Анализ точности confluence scores
        
        Returns:
            Анализ калибровки confluence
        """
        cursor = self.tracker.conn.cursor()
        
        # Получаем все завершенные сигналы
        cursor.execute("""
            SELECT 
                confluence_score,
                probability,
                result,
                actual_rr,
                risk_reward
            FROM signals
            WHERE status = 'completed'
            AND result IN ('tp_hit', 'sl_hit')
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            return {
                "total_samples": 0,
                "message": "Недостаточно данных для анализа"
            }
        
        # Группировка по confluence ranges
        ranges = {
            "8.0-8.5": {"predicted_wins": 0, "actual_wins": 0, "total": 0},
            "8.5-9.0": {"predicted_wins": 0, "actual_wins": 0, "total": 0},
            "9.0-9.5": {"predicted_wins": 0, "actual_wins": 0, "total": 0},
            "9.5+": {"predicted_wins": 0, "actual_wins": 0, "total": 0}
        }
        
        for row in rows:
            confluence = row["confluence_score"] or 0
            probability = row["probability"] or 0
            result = row["result"]
            
            # Определяем диапазон
            if 8.0 <= confluence < 8.5:
                range_key = "8.0-8.5"
            elif 8.5 <= confluence < 9.0:
                range_key = "8.5-9.0"
            elif 9.0 <= confluence < 9.5:
                range_key = "9.0-9.5"
            elif confluence >= 9.5:
                range_key = "9.5+"
            else:
                continue
            
            ranges[range_key]["total"] += 1
            ranges[range_key]["predicted_wins"] += probability
            if result == "tp_hit":
                ranges[range_key]["actual_wins"] += 1
        
        # Расчет калибровки
        calibration = {}
        for range_key, data in ranges.items():
            if data["total"] > 0:
                predicted_rate = data["predicted_wins"] / data["total"]
                actual_rate = data["actual_wins"] / data["total"]
                calibration_error = abs(predicted_rate - actual_rate)
                
                calibration[range_key] = {
                    "total": data["total"],
                    "predicted_win_rate": round(predicted_rate, 4),
                    "actual_win_rate": round(actual_rate, 4),
                    "calibration_error": round(calibration_error, 4),
                    "well_calibrated": calibration_error < 0.1  # Ошибка < 10%
                }
        
        return {
            "total_samples": len(rows),
            "calibration_by_confluence": calibration,
            "summary": {
                "well_calibrated_ranges": sum(1 for c in calibration.values() if c.get("well_calibrated", False)),
                "total_ranges": len(calibration)
            }
        }
    
    async def get_improvement_suggestions(self) -> List[str]:
        """
        Получить рекомендации по улучшению на основе анализа
        
        Returns:
            Список рекомендаций
        """
        suggestions = []
        
        # Анализ confluence accuracy
        confluence_analysis = await self.calculate_confluence_accuracy()
        
        if confluence_analysis.get("total_samples", 0) > 10:
            calibration = confluence_analysis.get("calibration_by_confluence", {})
            
            for range_key, data in calibration.items():
                error = data.get("calibration_error", 0)
                if error > 0.15:  # Ошибка > 15%
                    predicted = data.get("predicted_win_rate", 0)
                    actual = data.get("actual_win_rate", 0)
                    
                    if predicted > actual:
                        suggestions.append(
                            f"Confluence range {range_key}: Прогнозируемая вероятность ({predicted:.1%}) "
                            f"завышена относительно реальной ({actual:.1%}). "
                            f"Рекомендуется снизить scoring для этого диапазона."
                        )
                    else:
                        suggestions.append(
                            f"Confluence range {range_key}: Прогнозируемая вероятность ({predicted:.1%}) "
                            f"занижена относительно реальной ({actual:.1%}). "
                            f"Рекомендуется повысить scoring для этого диапазона."
                        )
        
        # Анализ паттернов
        pattern_perf = await self.analyze_pattern_performance()
        
        if pattern_perf.get("total_patterns", 0) > 0:
            # Ищем паттерны с низким win rate но высоким confluence
            for pattern in pattern_perf.get("by_pattern", []):
                if pattern["total_signals"] >= 5:  # Минимум 5 сигналов для статистики
                    win_rate = pattern["win_rate"]
                    confluence = pattern["avg_confluence"]
                    
                    if win_rate < 0.5 and confluence >= 8.5:
                        suggestions.append(
                            f"Паттерн {pattern['pattern_name']} ({pattern['timeframe']}): "
                            f"Высокий confluence ({confluence:.1f}) но низкий win rate ({win_rate:.1%}). "
                            f"Возможно, паттерн переоценен или требует дополнительных фильтров."
                        )
        
        # Анализ таймфреймов
        tf_perf = await self.analyze_timeframe_performance()
        
        if tf_perf.get("total_timeframes", 0) > 0:
            # Ищем таймфреймы с низкой эффективностью
            for tf_data in tf_perf.get("by_timeframe", []):
                if tf_data["total_signals"] >= 5:
                    win_rate = tf_data["win_rate"]
                    
                    if win_rate < 0.4:
                        suggestions.append(
                            f"Таймфрейм {tf_data['timeframe']}: Низкий win rate ({win_rate:.1%}). "
                            f"Рекомендуется пересмотреть критерии анализа для этого таймфрейма."
                        )
        
        # Общие рекомендации
        overall = await self.calculate_overall_metrics(days=30)
        
        if overall.get("completed_signals", 0) >= 20:
            win_rate = overall.get("win_rate", 0)
            
            if win_rate < 0.5:
                suggestions.append(
                    f"Общий win rate ({win_rate:.1%}) ниже целевого (50%+). "
                    f"Рекомендуется повысить минимальный threshold confluence с 8.0 до 8.5."
                )
            
            # Проверка R:R
            avg_actual_rr = overall.get("avg_actual_rr", 0)
            avg_predicted_rr = overall.get("avg_predicted_rr", 0)
            
            if avg_actual_rr < avg_predicted_rr * 0.7:  # Реальный R:R на 30% ниже прогнозируемого
                suggestions.append(
                    f"Реальный R:R ({avg_actual_rr:.2f}) значительно ниже прогнозируемого ({avg_predicted_rr:.2f}). "
                    f"Рекомендуется пересмотреть расчет take_profit уровней."
                )
        
        if not suggestions:
            suggestions.append("Недостаточно данных для конкретных рекомендаций. Продолжайте собирать статистику.")
        
        return suggestions

