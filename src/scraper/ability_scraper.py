import asyncio
import sqlite3

from tqdm import tqdm

from src.api.client import RateLimitedClient
from src.api.endpoints import ability_url
from src.config import Config


def _get_pending_ability_ids(conn: sqlite3.Connection) -> list[int]:
    rows = conn.execute(
        "SELECT DISTINCT ability_id FROM pokemon_abilities WHERE flavor_text_zh = ''"
    ).fetchall()
    return [row["ability_id"] for row in rows]


def _extract_flavor_text_zh(data: dict) -> str:
    entries = data.get("flavor_text_entries", [])
    zh_entries = [
        e for e in entries
        if e.get("language", {}).get("name") == "zh-hans"
    ]
    if not zh_entries:
        return ""
    return zh_entries[-1].get("flavor_text", "").strip()


async def _scrape_abilities(config: Config, conn: sqlite3.Connection) -> None:
    ability_ids = _get_pending_ability_ids(conn)
    if not ability_ids:
        print("All abilities already have flavor text. Nothing to do.")
        return

    print(f"Found {len(ability_ids)} abilities to scrape.")

    async with RateLimitedClient(config) as client:
        progress = tqdm(ability_ids, desc="Abilities", unit="ability")
        for aid in progress:
            url = ability_url(config, aid)
            try:
                data = await client.get_json(url)
                flavor_text = _extract_flavor_text_zh(data)
                conn.execute(
                    "UPDATE pokemon_abilities SET flavor_text_zh = ? WHERE ability_id = ?",
                    (flavor_text, aid),
                )
                conn.commit()
                progress.set_postfix(id=aid)
            except Exception as exc:
                tqdm.write(f"Failed ability {aid}: {exc}")

    total = conn.execute(
        "SELECT COUNT(DISTINCT ability_id) AS c FROM pokemon_abilities WHERE flavor_text_zh != ''"
    ).fetchone()["c"]
    print(f"Done. {total} abilities now have Chinese flavor text.")


def run_ability_scraper() -> None:
    from src.db.connection import create_connection

    config = Config()
    if not config.db_path.exists():
        print("No database found. Run 'scrape' first.")
        return

    conn = create_connection(config.db_path)
    try:
        asyncio.run(_scrape_abilities(config, conn))
    finally:
        conn.close()
