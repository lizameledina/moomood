import sqlite3
from datetime import date, timedelta
from typing import List, Optional

DB_PATH = "moodbot.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date    TEXT    NOT NULL,
                mood    INTEGER NOT NULL,
                energy  INTEGER NOT NULL,
                stress  INTEGER NOT NULL,
                sleep   REAL    NOT NULL,
                note    TEXT,
                tags    TEXT,
                UNIQUE (user_id, date)
            )
        """)
        conn.commit()


def upsert_record(
    user_id: int,
    mood: int,
    energy: int,
    stress: int,
    sleep: float,
    note: Optional[str],
    tags: Optional[str],
) -> None:
    today = date.today().isoformat()
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO records (user_id, date, mood, energy, stress, sleep, note, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                mood   = excluded.mood,
                energy = excluded.energy,
                stress = excluded.stress,
                sleep  = excluded.sleep,
                note   = excluded.note,
                tags   = excluded.tags
        """, (user_id, today, mood, energy, stress, sleep, note, tags))
        conn.commit()


def get_history(user_id: int, limit: int = 7) -> List[sqlite3.Row]:
    with _get_conn() as conn:
        return conn.execute("""
            SELECT * FROM records
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()


def get_stats_7d(user_id: int) -> Optional[sqlite3.Row]:
    since = (date.today() - timedelta(days=6)).isoformat()
    with _get_conn() as conn:
        return conn.execute("""
            SELECT
                COUNT(*)    AS count,
                AVG(mood)   AS avg_mood,
                AVG(energy) AS avg_energy,
                AVG(stress) AS avg_stress,
                AVG(sleep)  AS avg_sleep
            FROM records
            WHERE user_id = ? AND date >= ?
        """, (user_id, since)).fetchone()


def get_records_in_period(user_id: int, period: str) -> List[sqlite3.Row]:
    """
    Записи пользователя за период, по возрастанию даты.
    period: '7' — последние 7 дней, '30' — 30 дней, '0' — всё время.
    """
    with _get_conn() as conn:
        if period == "0":
            return conn.execute("""
                SELECT * FROM records
                WHERE user_id = ?
                ORDER BY date ASC
            """, (user_id,)).fetchall()
        days = 7 if period == "7" else 30
        since = (date.today() - timedelta(days=days - 1)).isoformat()
        return conn.execute("""
            SELECT * FROM records
            WHERE user_id = ? AND date >= ?
            ORDER BY date ASC
        """, (user_id, since)).fetchall()
