import sqlite3
from pathlib import Path

from papermind.config import settings


def _db_path() -> Path:
    return Path(settings.data_dir) / "memory.db"


def get_connection() -> sqlite3.Connection:
    db_path = _db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_papers (
            paper_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            indexed_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS briefing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            briefing_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_briefing_topic ON briefing_history(topic)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_extractions (
            paper_id TEXT PRIMARY KEY,
            extraction_json TEXT NOT NULL,
            extracted_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()
