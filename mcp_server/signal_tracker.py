"""
Signal Tracker
База данных и CRUD операции для отслеживания торговых сигналов
"""

import sqlite3
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger


class SignalTracker:
    """Трекер сигналов для контроля качества"""
    
    def __init__(self, db_path: str = "data/signals.db"):
        """
        Инициализация трекера сигналов
        
        Args:
            db_path: Путь к SQLite базе данных
        """
        # Создаем директорию если не существует
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(db_file)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Для доступа по именам колонок
        
        # Инициализация схемы БД
        self._init_database()
        
        logger.info(f"Signal Tracker initialized: {self.db_path}")
    
    def _init_database(self):
        """Инициализация схемы базы данных"""
        cursor = self.conn.cursor()
        
        # Таблица signals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                risk_reward REAL NOT NULL,
                confluence_score REAL NOT NULL,
                probability REAL NOT NULL,
                expected_value REAL,
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                result TEXT,
                completed_at TIMESTAMP,
                actual_rr REAL,
                max_favorable_excursion REAL,
                max_adverse_excursion REAL,
                time_to_result INTEGER,
                timeframe TEXT,
                pattern_type TEXT,
                pattern_name TEXT,
                telegram_message_ids TEXT
            )
        """)
        
        # Добавляем колонку telegram_message_ids если её нет (для существующих БД)
        try:
            cursor.execute("ALTER TABLE signals ADD COLUMN telegram_message_ids TEXT")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        # Таблица price_snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                distance_to_tp REAL,
                distance_to_sl REAL,
                unrealized_pnl_pct REAL,
                FOREIGN KEY (signal_id) REFERENCES signals(signal_id)
            )
        """)
        
        # Таблица pattern_performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                total_signals INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                avg_confluence REAL,
                avg_actual_rr REAL,
                win_rate REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pattern_type, pattern_name, timeframe)
            )
        """)
        
        # Индексы для производительности
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_signal_id ON price_snapshots(signal_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON price_snapshots(timestamp)")
        
        self.conn.commit()
        logger.info("Database schema initialized")
    
    async def record_signal(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confluence_score: float,
        probability: float,
        analysis_data: Optional[Dict[str, Any]] = None,
        expected_value: Optional[float] = None,
        timeframe: Optional[str] = None,
        pattern_type: Optional[str] = None,
        pattern_name: Optional[str] = None
    ) -> str:
        """
        Записать новый сигнал для отслеживания
        
        Args:
            symbol: Торговая пара (например "BTC/USDT")
            side: Направление ('long' или 'short')
            entry_price: Цена входа
            stop_loss: Стоп-лосс
            take_profit: Тейк-профит
            confluence_score: Confluence score (0-12)
            probability: Вероятность успеха (0-1)
            analysis_data: Полные данные анализа (JSON)
            expected_value: Expected Value
            timeframe: Основной таймфрейм сигнала
            pattern_type: Тип паттерна (если есть)
            pattern_name: Название паттерна (если есть)
            
        Returns:
            signal_id: Уникальный ID сигнала
        """
        signal_id = str(uuid.uuid4())
        
        # Расчет risk_reward
        if side.lower() == "long":
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
        else:  # short
            risk = abs(stop_loss - entry_price)
            reward = abs(entry_price - take_profit)
        
        risk_reward = reward / risk if risk > 0 else 0
        
        # Сериализация analysis_data
        analysis_json = json.dumps(analysis_data) if analysis_data else None
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO signals (
                signal_id, symbol, side, entry_price, stop_loss, take_profit,
                risk_reward, confluence_score, probability, expected_value,
                analysis_data, timeframe, pattern_type, pattern_name, telegram_message_ids
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_id, symbol, side.lower(), entry_price, stop_loss, take_profit,
            risk_reward, confluence_score, probability, expected_value,
            analysis_json, timeframe, pattern_type, pattern_name, None
        ))
        
        self.conn.commit()
        
        logger.info(f"Signal recorded: {signal_id} | {symbol} {side} @ {entry_price} | Confluence: {confluence_score:.1f} | Prob: {probability:.1%}")
        
        return signal_id
    
    async def update_signal_result(
        self,
        signal_id: str,
        result: str,
        actual_rr: Optional[float] = None,
        max_favorable_excursion: Optional[float] = None,
        max_adverse_excursion: Optional[float] = None,
        time_to_result: Optional[int] = None
    ):
        """
        Обновить результат сигнала
        
        Args:
            signal_id: ID сигнала
            result: Результат ('tp_hit', 'sl_hit', 'timeout', 'manual_close')
            actual_rr: Реальный достигнутый R:R
            max_favorable_excursion: Максимальная прибыль в %
            max_adverse_excursion: Максимальный убыток в %
            time_to_result: Время до результата в секундах
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE signals
            SET status = 'completed',
                result = ?,
                completed_at = CURRENT_TIMESTAMP,
                actual_rr = ?,
                max_favorable_excursion = ?,
                max_adverse_excursion = ?,
                time_to_result = ?
            WHERE signal_id = ?
        """, (result, actual_rr, max_favorable_excursion, max_adverse_excursion, time_to_result, signal_id))
        
        self.conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Signal {signal_id} completed: {result}")
            
            # Обновляем статистику паттерна если есть
            await self._update_pattern_stats(signal_id, result)
        else:
            logger.warning(f"Signal {signal_id} not found for update")
    
    async def record_price_snapshot(
        self,
        signal_id: str,
        price: float
    ):
        """
        Записать snapshot цены для сигнала
        
        Args:
            signal_id: ID сигнала
            price: Текущая цена
        """
        # Получаем данные сигнала
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM signals WHERE signal_id = ?", (signal_id,))
        signal_row = cursor.fetchone()
        
        if not signal_row:
            logger.warning(f"Signal {signal_id} not found for snapshot")
            return
        
        signal = dict(signal_row)
        entry_price = signal["entry_price"]
        stop_loss = signal["stop_loss"]
        take_profit = signal["take_profit"]
        side = signal["side"]
        
        # Расчет расстояний и PnL
        if side.lower() == "long":
            distance_to_tp = ((take_profit - price) / price) * 100 if price > 0 else 0
            distance_to_sl = ((price - stop_loss) / price) * 100 if price > 0 else 0
            unrealized_pnl_pct = ((price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        else:  # short
            distance_to_tp = ((price - take_profit) / price) * 100 if price > 0 else 0
            distance_to_sl = ((stop_loss - price) / price) * 100 if price > 0 else 0
            unrealized_pnl_pct = ((entry_price - price) / entry_price) * 100 if entry_price > 0 else 0
        
        # Записываем snapshot
        cursor.execute("""
            INSERT INTO price_snapshots (
                signal_id, price, distance_to_tp, distance_to_sl, unrealized_pnl_pct
            ) VALUES (?, ?, ?, ?, ?)
        """, (signal_id, price, distance_to_tp, distance_to_sl, unrealized_pnl_pct))
        
        self.conn.commit()
        
        # Обновляем max_favorable_excursion и max_adverse_excursion
        if unrealized_pnl_pct > 0:
            current_max_fav = signal.get("max_favorable_excursion") or 0
            if unrealized_pnl_pct > current_max_fav:
                cursor.execute("""
                    UPDATE signals
                    SET max_favorable_excursion = ?
                    WHERE signal_id = ?
                """, (unrealized_pnl_pct, signal_id))
        else:
            current_max_adv = signal.get("max_adverse_excursion") or 0
            if abs(unrealized_pnl_pct) > abs(current_max_adv):
                cursor.execute("""
                    UPDATE signals
                    SET max_adverse_excursion = ?
                    WHERE signal_id = ?
                """, (unrealized_pnl_pct, signal_id))
        
        self.conn.commit()
    
    async def get_active_signals(self) -> List[Dict[str, Any]]:
        """
        Получить все активные сигналы
        
        Returns:
            Список активных сигналов
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM signals
            WHERE status = 'active'
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def get_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить сигнал по ID
        
        Args:
            signal_id: ID сигнала
            
        Returns:
            Данные сигнала или None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM signals WHERE signal_id = ?", (signal_id,))
        row = cursor.fetchone()
        
        if row:
            signal = dict(row)
            # Парсим analysis_data если есть
            if signal.get("analysis_data"):
                try:
                    signal["analysis_data"] = json.loads(signal["analysis_data"])
                except:
                    pass
            return signal
        
        return None
    
    async def get_signal_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Получить статистику сигналов за период
        
        Args:
            days: Количество дней для анализа
            
        Returns:
            Статистика сигналов
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Общая статистика
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN result = 'tp_hit' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'sl_hit' THEN 1 ELSE 0 END) as losses,
                AVG(confluence_score) as avg_confluence,
                AVG(probability) as avg_probability,
                AVG(actual_rr) as avg_actual_rr,
                AVG(risk_reward) as avg_predicted_rr
            FROM signals
            WHERE created_at >= ?
        """, (cutoff_date.isoformat(),))
        
        row = cursor.fetchone()
        
        stats = dict(row) if row else {}
        
        # Расчет win rate
        completed = stats.get("completed") or 0
        wins = stats.get("wins") or 0
        
        if completed > 0:
            stats["win_rate"] = wins / completed
        else:
            stats["win_rate"] = 0.0
        
        return stats
    
    async def get_price_snapshots(
        self,
        signal_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить snapshots цены для сигнала
        
        Args:
            signal_id: ID сигнала
            limit: Максимальное количество snapshots
            
        Returns:
            Список snapshots
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM price_snapshots WHERE signal_id = ? ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (signal_id,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    async def cancel_signal(self, signal_id: str, reason: str = "manual"):
        """
        Отменить сигнал (не отслеживать дальше)
        
        Args:
            signal_id: ID сигнала
            reason: Причина отмены
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE signals
            SET status = 'cancelled',
                result = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE signal_id = ?
        """, (reason, signal_id))
        
        self.conn.commit()
        
        logger.info(f"Signal {signal_id} cancelled: {reason}")
    
    async def _update_pattern_stats(self, signal_id: str, result: str):
        """
        Обновить статистику паттерна после завершения сигнала
        
        Args:
            signal_id: ID сигнала
            result: Результат ('tp_hit', 'sl_hit', etc.)
        """
        # Получаем данные сигнала
        signal = await self.get_signal(signal_id)
        if not signal or not signal.get("pattern_type"):
            return
        
        pattern_type = signal["pattern_type"]
        pattern_name = signal.get("pattern_name") or "unknown"
        timeframe = signal.get("timeframe") or "unknown"
        
        # Проверяем существование записи
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM pattern_performance
            WHERE pattern_type = ? AND pattern_name = ? AND timeframe = ?
        """, (pattern_type, pattern_name, timeframe))
        
        existing = cursor.fetchone()
        
        # Получаем actual_rr
        actual_rr = signal.get("actual_rr") or 0
        confluence = signal.get("confluence_score") or 0
        
        if existing:
            # Обновляем существующую запись
            total = existing["total_signals"] + 1
            wins = existing["wins"] + (1 if result == "tp_hit" else 0)
            losses = existing["losses"] + (1 if result == "sl_hit" else 0)
            
            # Пересчитываем средние
            avg_confluence = ((existing["avg_confluence"] or 0) * existing["total_signals"] + confluence) / total
            avg_rr = ((existing["avg_actual_rr"] or 0) * existing["total_signals"] + actual_rr) / total
            win_rate = wins / total if total > 0 else 0
            
            cursor.execute("""
                UPDATE pattern_performance
                SET total_signals = ?,
                    wins = ?,
                    losses = ?,
                    avg_confluence = ?,
                    avg_actual_rr = ?,
                    win_rate = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE pattern_type = ? AND pattern_name = ? AND timeframe = ?
            """, (total, wins, losses, avg_confluence, avg_rr, win_rate, pattern_type, pattern_name, timeframe))
        else:
            # Создаем новую запись
            win_rate = 1.0 if result == "tp_hit" else 0.0
            cursor.execute("""
                INSERT INTO pattern_performance (
                    pattern_type, pattern_name, timeframe,
                    total_signals, wins, losses,
                    avg_confluence, avg_actual_rr, win_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_type, pattern_name, timeframe,
                1, 1 if result == "tp_hit" else 0, 1 if result == "sl_hit" else 0,
                confluence, actual_rr, win_rate
            ))
        
        self.conn.commit()
    
    async def set_telegram_message_ids(
        self,
        signal_id: str,
        message_ids: Dict[str, int]
    ):
        """
        Сохранить message_id для Telegram постов сигнала
        
        Args:
            signal_id: ID сигнала
            message_ids: Словарь {chat_id: message_id}
        """
        cursor = self.conn.cursor()
        message_ids_json = json.dumps(message_ids)
        
        cursor.execute("""
            UPDATE signals
            SET telegram_message_ids = ?
            WHERE signal_id = ?
        """, (message_ids_json, signal_id))
        
        self.conn.commit()
        logger.debug(f"Telegram message IDs saved for signal {signal_id}")
    
    async def get_telegram_message_ids(self, signal_id: str) -> Dict[str, int]:
        """
        Получить message_id для Telegram постов сигнала
        
        Args:
            signal_id: ID сигнала
            
        Returns:
            Словарь {chat_id: message_id} или пустой словарь
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT telegram_message_ids FROM signals WHERE signal_id = ?", (signal_id,))
        row = cursor.fetchone()
        
        if row and row["telegram_message_ids"]:
            try:
                return json.loads(row["telegram_message_ids"])
            except:
                return {}
        
        return {}
    
    def close(self):
        """Закрыть соединение с БД"""
        if self.conn:
            self.conn.close()
            logger.info("Signal Tracker database connection closed")

