import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from zoneinfo import ZoneInfo

DB_PATH = os.getenv("DB_PATH", "moodbot.db")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.DatabaseError:
        pass
    try:
        conn.execute("PRAGMA foreign_keys=ON")
    except sqlite3.DatabaseError:
        pass
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id  INTEGER PRIMARY KEY,
                timezone TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage (
                user_id    INTEGER NOT NULL,
                local_date TEXT    NOT NULL,
                count      INTEGER NOT NULL,
                PRIMARY KEY (user_id, local_date)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkins (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                created_at_utc  TEXT    NOT NULL,
                local_date      TEXT    NOT NULL,
                mood            INTEGER NOT NULL,
                energy          INTEGER NOT NULL,
                stress          INTEGER NOT NULL,
                sleep           REAL,
                note            TEXT,
                tags            TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_checkins_user_date ON checkins(user_id, local_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_checkins_user_created ON checkins(user_id, created_at_utc)")
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
        _migrate_records_to_checkins(conn)


def _get_schema_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM schema_meta WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    return str(row["value"])


def _set_schema_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO schema_meta (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )


def _migrate_records_to_checkins(conn: sqlite3.Connection) -> None:
    if _get_schema_meta(conn, "migrated_records_to_checkins") == "1":
        return

    rows = conn.execute(
        "SELECT user_id, date, mood, energy, stress, sleep, note, tags FROM records"
    ).fetchall()
    if rows:
        conn.executemany(
            """
            INSERT INTO checkins (
                user_id, created_at_utc, local_date, mood, energy, stress, sleep, note, tags
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    int(r["user_id"]),
                    f"{r['date']}T12:00:00Z",
                    str(r["date"]),
                    int(r["mood"]),
                    int(r["energy"]),
                    int(r["stress"]),
                    float(r["sleep"]) if r["sleep"] is not None else None,
                    r["note"],
                    r["tags"],
                )
                for r in rows
            ],
        )

    _set_schema_meta(conn, "migrated_records_to_checkins", "1")
    conn.commit()


def _local_today(tz_name: str) -> date:
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo(DEFAULT_TIMEZONE)
    return datetime.now(timezone.utc).astimezone(tz).date()


def get_user_timezone(user_id: int) -> str:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT timezone FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row:
            return str(row["timezone"])

        conn.execute(
            "INSERT OR IGNORE INTO user_settings (user_id, timezone) VALUES (?, ?)",
            (user_id, DEFAULT_TIMEZONE),
        )
        conn.commit()
        return DEFAULT_TIMEZONE


def set_user_timezone(user_id: int, tz_name: str) -> None:
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO user_settings (user_id, timezone)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET timezone = excluded.timezone
            """,
            (user_id, tz_name),
        )
        conn.commit()


def add_checkin(
    user_id: int,
    created_at_utc: str,
    local_date: str,
    mood: int,
    energy: int,
    stress: int,
    sleep: float | None,
    note: Optional[str],
    tags: Optional[str],
) -> None:
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO checkins (
                user_id, created_at_utc, local_date, mood, energy, stress, sleep, note, tags
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                created_at_utc,
                local_date,
                mood,
                energy,
                stress,
                sleep,
                note,
                tags,
            ),
        )
        conn.commit()


def has_sleep_for_date(user_id: int, local_date: str) -> bool:
    with _get_conn() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM checkins
            WHERE user_id = ? AND local_date = ? AND sleep IS NOT NULL
            LIMIT 1
            """,
            (user_id, local_date),
        ).fetchone()
        return row is not None


def count_checkins_for_date(user_id: int, local_date: str) -> int:
    with _get_conn() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM checkins
            WHERE user_id = ? AND local_date = ?
            """,
            (user_id, local_date),
        ).fetchone()
        if not row:
            return 0
        return int(row["cnt"])


def get_checkins_in_period(user_id: int, period: str, tz_name: str) -> List[sqlite3.Row]:
    with _get_conn() as conn:
        if period == "0":
            return conn.execute(
                """
                SELECT * FROM checkins
                WHERE user_id = ?
                ORDER BY local_date ASC, created_at_utc ASC
                """,
                (user_id,),
            ).fetchall()

        days = 7 if period == "7" else 30
        since = (_local_today(tz_name) - timedelta(days=days - 1)).isoformat()
        return conn.execute(
            """
            SELECT * FROM checkins
            WHERE user_id = ? AND local_date >= ?
            ORDER BY local_date ASC, created_at_utc ASC
            """,
            (user_id, since),
        ).fetchall()


def get_daily_history(user_id: int, tz_name: str, days: int = 7) -> List[dict]:
    checkins = get_checkins_in_period(user_id, str(days) if days in (7, 30) else "0", tz_name)
    if days in (7, 30):
        checkins = checkins[-(days * 10):]

    daily = _aggregate_daily(checkins)
    return list(reversed(daily[-days:]))


def get_daily_series(user_id: int, tz_name: str, period: str) -> List[dict]:
    checkins = get_checkins_in_period(user_id, period, tz_name)
    return _aggregate_daily(checkins)


def get_ai_usage_count(user_id: int, local_date: str) -> int:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT count FROM ai_usage WHERE user_id = ? AND local_date = ?",
            (user_id, local_date),
        ).fetchone()
        if not row:
            return 0
        return int(row["count"])


def increment_ai_usage(user_id: int, local_date: str) -> int:
    with _get_conn() as conn:
        row = conn.execute(
            """
            INSERT INTO ai_usage (user_id, local_date, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, local_date) DO UPDATE SET count = ai_usage.count + 1
            RETURNING count
            """,
            (user_id, local_date),
        ).fetchone()
        conn.commit()
        return int(row["count"])


def _aggregate_daily(checkins: List[sqlite3.Row]) -> List[dict]:
    if not checkins:
        return []

    daily: list[dict] = []
    current_date: str | None = None
    bucket: list[sqlite3.Row] = []

    def flush() -> None:
        nonlocal bucket, current_date, daily
        if not bucket or current_date is None:
            return

        moods = [int(r["mood"]) for r in bucket]
        energies = [int(r["energy"]) for r in bucket]
        stresses = [int(r["stress"]) for r in bucket]

        sleep_value: float | None = None
        for r in bucket:
            if r["sleep"] is not None:
                try:
                    sleep_value = float(r["sleep"])
                except Exception:
                    sleep_value = None
                break

        notes = [str(r["note"]).strip() for r in bucket if r["note"]]
        note_text = "\n\n———\n\n".join(n for n in notes if n)
        if len(note_text) > 900:
            note_text = note_text[:900].rstrip() + "…"

        tags_set: set[str] = set()
        for r in bucket:
            if not r["tags"]:
                continue
            for t in str(r["tags"]).split(","):
                t = t.strip()
                if t:
                    tags_set.add(t)
        tags_text = ",".join(sorted(tags_set)) if tags_set else None

        daily.append(
            {
                "date": current_date,
                "count": len(bucket),
                "mood": sum(moods) / len(moods),
                "energy": sum(energies) / len(energies),
                "stress": sum(stresses) / len(stresses),
                "sleep": sleep_value,
                "note": note_text or None,
                "tags": tags_text,
            }
        )

    for r in checkins:
        ld = str(r["local_date"])
        if current_date is None:
            current_date = ld
            bucket = [r]
            continue
        if ld == current_date:
            bucket.append(r)
            continue
        flush()
        current_date = ld
        bucket = [r]

    flush()
    return daily