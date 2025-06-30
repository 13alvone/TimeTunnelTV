from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Optional, List


DB_PATH = Path("curator.db")


@contextmanager
def get_connection(db_path: Path = DB_PATH) -> Iterable[sqlite3.Connection]:
    """Yield a SQLite connection with WAL mode enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    mode = conn.execute("PRAGMA journal_mode=WAL;").fetchone()[0]
    if str(mode).lower() != "wal":
        raise RuntimeError("WAL mode could not be enabled")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DB_PATH) -> None:
    """Initialise the database schema."""
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                duration INTEGER,
                url TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS ratings (
                item_id TEXT REFERENCES items(id),
                rating INTEGER,
                rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS downloads (
                item_id TEXT REFERENCES items(id),
                size_bytes INTEGER,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def insert_item(
    item_id: str,
    title: str,
    description: str,
    duration: int,
    url: str,
    added_at: Optional[str] = None,
    db_path: Path = DB_PATH,
) -> None:
    """Insert a new item into the ``items`` table."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO items (id, title, description, duration, url, added_at)
            VALUES (?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
            """,
            (item_id, title, description, duration, url, added_at),
        )


def record_rating(
    item_id: str,
    rating: int,
    rated_at: Optional[str] = None,
    db_path: Path = DB_PATH,
) -> None:
    """Record a rating for an item."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO ratings (item_id, rating, rated_at)
            VALUES (?, ?, COALESCE(?, CURRENT_TIMESTAMP))
            """,
            (item_id, rating, rated_at),
        )


def record_download(
    item_id: str,
    size_bytes: int,
    downloaded_at: Optional[str] = None,
    db_path: Path = DB_PATH,
) -> None:
    """Record a download for an item."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO downloads (item_id, size_bytes, downloaded_at)
            VALUES (?, ?, COALESCE(?, CURRENT_TIMESTAMP))
            """,
            (item_id, size_bytes, downloaded_at),
        )


def list_items(limit: int = 100, db_path: Path = DB_PATH) -> List[sqlite3.Row]:
    """Return a list of items ordered by ``added_at`` descending."""
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            SELECT * FROM items ORDER BY added_at DESC LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()


def list_items_today(limit: int = 100, db_path: Path = DB_PATH) -> List[sqlite3.Row]:
    """Return today's items ordered by ``added_at`` descending."""
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            SELECT * FROM items
            WHERE date(added_at, 'utc') = date('now','utc')
            ORDER BY added_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()


def list_ratings(item_id: str, db_path: Path = DB_PATH) -> List[sqlite3.Row]:
    """Return all ratings for a given ``item_id``."""
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            SELECT rating, rated_at FROM ratings WHERE item_id = ? ORDER BY rated_at
            """,
            (item_id,),
        )
        return cur.fetchall()
