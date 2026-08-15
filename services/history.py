import sqlite3
from typing import List
from datetime import datetime
from config.settings import settings
from services.interfaces import IHistoryBackend
from core.logger import logger

class SQLiteHistory(IHistoryBackend):
    def __init__(self, db_path: str = settings.db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    status TEXT NOT NULL,
                    youtube_url TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def get_recent_topics(self, limit: int = 100) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get successful or pending topics to avoid repeating them
            cursor.execute('''
                SELECT topic FROM history 
                WHERE status IN ('success', 'pending') 
                ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            return [row[0] for row in cursor.fetchall()]

    def record_success(self, topic: str, youtube_url: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO history (topic, status, youtube_url, created_at)
                VALUES (?, 'success', ?, ?)
            ''', (topic, youtube_url, datetime.utcnow()))
            conn.commit()
        logger.info("History recorded success", topic=topic, url=youtube_url)

    def record_failure(self, topic: str, error_message: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO history (topic, status, error_message, created_at)
                VALUES (?, 'failure', ?, ?)
            ''', (topic, error_message, datetime.utcnow()))
            conn.commit()
        logger.warning("History recorded failure", topic=topic, error=error_message)
