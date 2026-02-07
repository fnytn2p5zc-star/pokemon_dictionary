import sqlite3
from pathlib import Path

from .schema import init_database


def create_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    init_database(conn)
    return conn


def ensure_evolution_data(conn: sqlite3.Connection) -> None:
    """Auto-backfill evolution data if pokemon exist but fields are empty."""
    total = conn.execute("SELECT COUNT(*) as cnt FROM pokemon").fetchone()["cnt"]
    if total == 0:
        return

    fully_evolved = conn.execute(
        "SELECT COUNT(*) as cnt FROM pokemon WHERE is_fully_evolved = 1"
    ).fetchone()["cnt"]

    if fully_evolved > 0:
        return

    print("Evolution data missing — running CSV backfill...")
    try:
        from src.scraper.evolution_backfill import backfill_from_csv
        backfill_from_csv(conn)
    except Exception as exc:
        print(f"Auto-backfill failed: {exc}")
