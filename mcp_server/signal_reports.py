"""
Signal Reports
Генерация отчетов о качестве сигналов
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from mcp_server.signal_tracker import SignalTracker
from mcp_server.quality_metrics import QualityMetrics


class SignalReports:
    """Генератор отчетов о качестве сигналов"""
    
    def __init__(self, signal_tracker: SignalTracker, quality_metrics: QualityMetrics):
        """
        Инициализация генератора отчетов
        
        Args:
            signal_tracker: Экземпляр SignalTracker
            quality_metrics: Экземпляр QualityMetrics
        """
        self.tracker = signal_tracker
        self.metrics = quality_metrics
        
        # Создаем директорию для отчетов
        self.reports_dir = Path("data/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Signal Reports generator initialized")
    
    async def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Генерация ежедневного отчета
        
        Args:
            date: Дата отчета (по умолчанию сегодня)
            
        Returns:
            Ежедневный отчет
        """
        if not date:
            date = datetime.now()
        
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        cursor = self.tracker.conn.cursor()
        
        # Новые сигналы за день
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM signals
            WHERE created_at >= ? AND created_at < ?
        """, (start_date.isoformat(), end_date.isoformat()))
        
        new_signals_count = cursor.fetchone()["count"] or 0
        
        # Завершенные сигналы за день
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN result = 'tp_hit' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'sl_hit' THEN 1 ELSE 0 END) as losses
            FROM signals
            WHERE completed_at >= ? AND completed_at < ?
            AND status = 'completed'
        """, (start_date.isoformat(), end_date.isoformat()))
        
        completed_row = cursor.fetchone()
        completed_total = completed_row["total"] or 0
        completed_wins = completed_row["wins"] or 0
        completed_losses = completed_row["losses"] or 0
        
        # Топ-3 лучших сигналов за день
        cursor.execute("""
            SELECT 
                signal_id, symbol, side, entry_price, take_profit,
                confluence_score, probability, actual_rr, result
            FROM signals
            WHERE completed_at >= ? AND completed_at < ?
            AND status = 'completed'
            AND result = 'tp_hit'
            ORDER BY actual_rr DESC
            LIMIT 3
        """, (start_date.isoformat(), end_date.isoformat()))
        
        best_signals = [dict(row) for row in cursor.fetchall()]
        
        # Топ-3 худших сигналов за день
        cursor.execute("""
            SELECT 
                signal_id, symbol, side, entry_price, stop_loss,
                confluence_score, probability, actual_rr, result
            FROM signals
            WHERE completed_at >= ? AND completed_at < ?
            AND status = 'completed'
            AND result = 'sl_hit'
            ORDER BY actual_rr ASC
            LIMIT 3
        """, (start_date.isoformat(), end_date.isoformat()))
        
        worst_signals = [dict(row) for row in cursor.fetchall()]
        
        # Текущая статистика (за последние 30 дней)
        overall_stats = await self.metrics.calculate_overall_metrics(days=30)
        
        report = {
            "date": date.strftime("%Y-%m-%d"),
            "new_signals": new_signals_count,
            "completed_signals": {
                "total": completed_total,
                "wins": completed_wins,
                "losses": completed_losses,
                "win_rate": round(completed_wins / completed_total, 4) if completed_total > 0 else 0.0
            },
            "best_signals": best_signals,
            "worst_signals": worst_signals,
            "overall_stats_30d": overall_stats,
            "generated_at": datetime.now().isoformat()
        }
        
        # Сохранение отчета
        await self._save_report("daily", report, date)
        
        return report
    
    async def generate_weekly_report(self, week_start: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Генерация недельного отчета
        
        Args:
            week_start: Начало недели (по умолчанию начало текущей недели)
            
        Returns:
            Недельный отчет
        """
        if not week_start:
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        week_end = week_start + timedelta(days=7)
        
        cursor = self.tracker.conn.cursor()
        
        # Статистика за неделю
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN result = 'tp_hit' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'sl_hit' THEN 1 ELSE 0 END) as losses,
                AVG(confluence_score) as avg_confluence,
                AVG(probability) as avg_probability,
                AVG(actual_rr) as avg_actual_rr
            FROM signals
            WHERE created_at >= ? AND created_at < ?
            AND status = 'completed'
        """, (week_start.isoformat(), week_end.isoformat()))
        
        week_row = cursor.fetchone()
        week_total = week_row["total"] or 0
        week_wins = week_row["wins"] or 0
        
        # Анализ эффективности по паттернам
        pattern_perf = await self.metrics.analyze_pattern_performance()
        
        # Анализ по таймфреймам
        tf_perf = await self.metrics.analyze_timeframe_performance()
        
        # Рекомендации по улучшению
        suggestions = await self.metrics.get_improvement_suggestions()
        
        # Тренд качества (сравнение с предыдущей неделей)
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN result = 'tp_hit' THEN 1 ELSE 0 END) as wins
            FROM signals
            WHERE created_at >= ? AND created_at < ?
            AND status = 'completed'
        """, (prev_week_start.isoformat(), prev_week_end.isoformat()))
        
        prev_week_row = cursor.fetchone()
        prev_week_total = prev_week_row["total"] or 0
        prev_week_wins = prev_week_row["wins"] or 0
        
        prev_week_win_rate = prev_week_wins / prev_week_total if prev_week_total > 0 else 0.0
        current_week_win_rate = week_wins / week_total if week_total > 0 else 0.0
        
        quality_trend = "improving" if current_week_win_rate > prev_week_win_rate else "declining" if current_week_win_rate < prev_week_win_rate else "stable"
        
        report = {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": (week_end - timedelta(days=1)).strftime("%Y-%m-%d"),
            "statistics": {
                "total_signals": week_total,
                "wins": week_wins,
                "losses": week_row["losses"] or 0,
                "win_rate": round(current_week_win_rate, 4),
                "avg_confluence": round(week_row["avg_confluence"] or 0, 2),
                "avg_probability": round(week_row["avg_probability"] or 0, 4),
                "avg_actual_rr": round(week_row["avg_actual_rr"] or 0, 2)
            },
            "pattern_performance": pattern_perf,
            "timeframe_performance": tf_perf,
            "quality_trend": quality_trend,
            "previous_week_win_rate": round(prev_week_win_rate, 4),
            "improvement_suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        }
        
        # Сохранение отчета
        await self._save_report("weekly", report, week_start)
        
        return report
    
    async def generate_monthly_report(self, month_start: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Генерация месячного отчета
        
        Args:
            month_start: Начало месяца (по умолчанию начало текущего месяца)
            
        Returns:
            Месячный отчет
        """
        if not month_start:
            today = datetime.now()
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Конец месяца
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        
        # Полная статистика за месяц
        overall_stats = await self.metrics.calculate_overall_metrics(days=31)
        
        # Анализ калибровки confluence
        confluence_accuracy = await self.metrics.calculate_confluence_accuracy()
        
        # Анализ паттернов
        pattern_perf = await self.metrics.analyze_pattern_performance()
        
        # Анализ таймфреймов
        tf_perf = await self.metrics.analyze_timeframe_performance()
        
        # Рекомендации
        suggestions = await self.metrics.get_improvement_suggestions()
        
        # Детальная статистика по дням месяца
        daily_stats = []
        current_date = month_start
        while current_date < month_end:
            day_end = current_date + timedelta(days=1)
            
            cursor = self.tracker.conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN result = 'tp_hit' THEN 1 ELSE 0 END) as wins
                FROM signals
                WHERE created_at >= ? AND created_at < ?
                AND status = 'completed'
            """, (current_date.isoformat(), day_end.isoformat()))
            
            day_row = cursor.fetchone()
            day_total = day_row["total"] or 0
            day_wins = day_row["wins"] or 0
            
            if day_total > 0:
                daily_stats.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "total": day_total,
                    "wins": day_wins,
                    "win_rate": round(day_wins / day_total, 4)
                })
            
            current_date = day_end
        
        report = {
            "month": month_start.strftime("%Y-%m"),
            "month_start": month_start.strftime("%Y-%m-%d"),
            "month_end": (month_end - timedelta(days=1)).strftime("%Y-%m-%d"),
            "overall_statistics": overall_stats,
            "confluence_calibration": confluence_accuracy,
            "pattern_performance": pattern_perf,
            "timeframe_performance": tf_perf,
            "daily_statistics": daily_stats,
            "improvement_suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        }
        
        # Сохранение отчета
        await self._save_report("monthly", report, month_start)
        
        return report
    
    async def generate_summary_report(self, days: int = 30, format: str = "summary") -> Dict[str, Any]:
        """
        Генерация сводного отчета
        
        Args:
            days: Количество дней для анализа
            format: Формат отчета ('summary' или 'json')
            
        Returns:
            Сводный отчет
        """
        overall_stats = await self.metrics.calculate_overall_metrics(days=days)
        pattern_perf = await self.metrics.analyze_pattern_performance()
        tf_perf = await self.metrics.analyze_timeframe_performance()
        confluence_accuracy = await self.metrics.calculate_confluence_accuracy()
        suggestions = await self.metrics.get_improvement_suggestions()
        
        report = {
            "period_days": days,
            "overall_metrics": overall_stats,
            "pattern_performance": pattern_perf,
            "timeframe_performance": tf_perf,
            "confluence_accuracy": confluence_accuracy,
            "improvement_suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        }
        
        if format == "summary":
            # Форматированный текстовый отчет
            return self._format_summary_report(report)
        else:
            return report
    
    def _format_summary_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Форматирование сводного отчета в читаемый вид"""
        overall = report.get("overall_metrics", {})
        
        summary_text = f"""
═══════════════════════════════════════════════════════
ОТЧЕТ О КАЧЕСТВЕ СИГНАЛОВ
Период: {report.get('period_days', 30)} дней
Дата: {report.get('generated_at', 'N/A')}
═══════════════════════════════════════════════════════

📊 ОБЩАЯ СТАТИСТИКА:
• Всего сигналов: {overall.get('total_signals', 0)}
• Завершено: {overall.get('completed_signals', 0)}
• Активных: {overall.get('active_signals', 0)}
• Win Rate: {overall.get('win_rate', 0):.1%}
• Средний Confluence: {overall.get('avg_confluence', 0):.2f}
• Средний R:R (реальный): {overall.get('avg_actual_rr', 0):.2f}
• Средний R:R (прогноз): {overall.get('avg_predicted_rr', 0):.2f}

📈 ТОЧНОСТЬ ПО CONFLUENCE:
"""
        
        accuracy_by_conf = overall.get("accuracy_by_confluence", {})
        for range_key, data in accuracy_by_conf.items():
            summary_text += f"• {range_key}: Win Rate {data.get('win_rate', 0):.1%} ({data.get('total', 0)} сигналов)\n"
        
        summary_text += "\n📊 ТОЧНОСТЬ ПО ВЕРОЯТНОСТИ:\n"
        accuracy_by_prob = overall.get("accuracy_by_probability", {})
        for range_key, data in accuracy_by_prob.items():
            summary_text += f"• {range_key}: Win Rate {data.get('win_rate', 0):.1%} ({data.get('total', 0)} сигналов)\n"
        
        summary_text += "\n💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:\n"
        suggestions = report.get("improvement_suggestions", [])
        if suggestions:
            for i, suggestion in enumerate(suggestions[:5], 1):  # Топ-5 рекомендаций
                summary_text += f"{i}. {suggestion}\n"
        else:
            summary_text += "Недостаточно данных для рекомендаций.\n"
        
        summary_text += "\n═══════════════════════════════════════════════════════\n"
        
        return {
            "summary_text": summary_text,
            "full_data": report
        }
    
    async def _save_report(self, report_type: str, report: Dict[str, Any], date: datetime):
        """
        Сохранение отчета в файл
        
        Args:
            report_type: Тип отчета ('daily', 'weekly', 'monthly')
            report: Данные отчета
            date: Дата отчета
        """
        # Создаем поддиректорию для типа отчета
        type_dir = self.reports_dir / report_type
        type_dir.mkdir(exist_ok=True)
        
        # Имя файла
        if report_type == "daily":
            filename = f"daily_{date.strftime('%Y-%m-%d')}.json"
        elif report_type == "weekly":
            filename = f"weekly_{date.strftime('%Y-%W')}.json"
        else:  # monthly
            filename = f"monthly_{date.strftime('%Y-%m')}.json"
        
        filepath = type_dir / filename
        
        # Сохранение
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Report saved: {filepath}")
    
    async def export_to_csv(self, days: int = 30, output_path: Optional[str] = None) -> str:
        """
        Экспорт данных сигналов в CSV
        
        Args:
            days: Количество дней для экспорта
            output_path: Путь к выходному файлу
            
        Returns:
            Путь к созданному файлу
        """
        import csv
        
        if not output_path:
            output_path = f"data/reports/signals_export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor = self.tracker.conn.cursor()
        cursor.execute("""
            SELECT 
                signal_id, symbol, side, entry_price, stop_loss, take_profit,
                confluence_score, probability, risk_reward, expected_value,
                created_at, status, result, actual_rr,
                max_favorable_excursion, max_adverse_excursion, time_to_result
            FROM signals
            WHERE created_at >= ?
            ORDER BY created_at DESC
        """, (cutoff_date.isoformat(),))
        
        rows = cursor.fetchall()
        
        # Записываем в CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows([dict(row) for row in rows])
        
        logger.info(f"Data exported to CSV: {output_path}")
        
        return output_path

