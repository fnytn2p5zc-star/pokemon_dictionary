import sqlite3

from src.db.repository import get_image_downloaded_ids, get_scraped_ids


def get_pending_pokemon_ids(
    conn: sqlite3.Connection,
    start: int,
    end: int,
) -> list[int]:
    scraped = get_scraped_ids(conn)
    return [pid for pid in range(start, end + 1) if pid not in scraped]


def get_pending_image_ids(
    conn: sqlite3.Connection,
    start: int,
    end: int,
) -> list[int]:
    downloaded = get_image_downloaded_ids(conn)
    return [pid for pid in range(start, end + 1) if pid not in downloaded]
