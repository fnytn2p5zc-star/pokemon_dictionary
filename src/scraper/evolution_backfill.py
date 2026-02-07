"""Backfill is_legendary, is_mythical, evolves_from_species_id from PokeAPI,
then compute evolution_stage and is_fully_evolved via SQL."""

from __future__ import annotations

import asyncio
import csv
import io
import sqlite3

import httpx
from tqdm import tqdm

from src.api.client import RateLimitedClient
from src.api.endpoints import species_url
from src.api.parsers import extract_species_id
from src.config import Config

CSV_URL = (
    "https://raw.githubusercontent.com/PokeAPI/pokeapi/"
    "master/data/v2/csv/pokemon_species.csv"
)


async def backfill_species_fields(
    config: Config,
    conn: sqlite3.Connection,
) -> None:
    """Fetch species data for every pokemon in DB and update new columns."""
    rows = conn.execute("SELECT id FROM pokemon ORDER BY id").fetchall()
    if not rows:
        print("No pokemon in database to backfill.")
        return

    pokemon_ids = [row["id"] for row in rows]
    print(f"Backfilling species fields for {len(pokemon_ids)} pokemon...")

    async with RateLimitedClient(config) as client:
        progress = tqdm(pokemon_ids, desc="Backfill species", unit="pokemon")
        for pid in progress:
            progress.set_postfix(id=pid)
            try:
                url = species_url(config, pid)
                data = await client.get_json(url)

                is_legendary = int(data.get("is_legendary", False))
                is_mythical = int(data.get("is_mythical", False))
                evolves_from = extract_species_id(
                    data.get("evolves_from_species"),
                )

                conn.execute(
                    """
                    UPDATE pokemon
                    SET is_legendary = ?,
                        is_mythical = ?,
                        evolves_from_species_id = ?
                    WHERE id = ?
                    """,
                    (is_legendary, is_mythical, evolves_from, pid),
                )
                conn.commit()
            except Exception as exc:
                print(f"  Error backfilling #{pid}: {exc}")

    print("Species fields backfill complete.")


def backfill_from_csv(conn: sqlite3.Connection) -> None:
    """Fast backfill using PokeAPI's CSV data from GitHub (single HTTP request)."""
    existing = conn.execute("SELECT COUNT(*) as cnt FROM pokemon").fetchone()
    if existing["cnt"] == 0:
        print("No pokemon in database to backfill.")
        return

    print("Fetching species CSV from PokeAPI GitHub...")
    resp = httpx.get(CSV_URL, timeout=30, follow_redirects=True)
    resp.raise_for_status()

    reader = csv.DictReader(io.StringIO(resp.text))
    updated = 0
    for row in reader:
        species_id = int(row["id"])
        is_legendary = int(row["is_legendary"])
        is_mythical = int(row["is_mythical"])
        evolves_from = (
            int(row["evolves_from_species_id"])
            if row["evolves_from_species_id"]
            else None
        )

        result = conn.execute(
            """
            UPDATE pokemon
            SET is_legendary = ?,
                is_mythical = ?,
                evolves_from_species_id = ?
            WHERE id = ?
            """,
            (is_legendary, is_mythical, evolves_from, species_id),
        )
        if result.rowcount > 0:
            updated += 1

    conn.commit()
    print(f"CSV backfill complete: {updated} pokemon updated.")
    compute_evolution_fields(conn)


def compute_evolution_fields(conn: sqlite3.Connection) -> None:
    """Compute evolution_stage and is_fully_evolved from evolves_from_species_id."""
    print("Computing evolution stages...")

    # Each UPDATE below is visible to subsequent queries within the same
    # SQLite transaction (SQLite reads see uncommitted writes from the
    # same connection), so the stage-1 and stage-2 queries correctly
    # reference previously updated rows.

    # Stage 0: base forms (no evolves_from)
    conn.execute(
        """
        UPDATE pokemon
        SET evolution_stage = 0
        WHERE evolves_from_species_id IS NULL
        """
    )

    # Stage 1: evolves from a base form
    conn.execute(
        """
        UPDATE pokemon
        SET evolution_stage = 1
        WHERE evolves_from_species_id IS NOT NULL
          AND evolves_from_species_id IN (
              SELECT id FROM pokemon WHERE evolves_from_species_id IS NULL
          )
        """
    )

    # Stage 2: evolves from a stage-1 pokemon
    conn.execute(
        """
        UPDATE pokemon
        SET evolution_stage = 2
        WHERE evolves_from_species_id IS NOT NULL
          AND evolves_from_species_id IN (
              SELECT id FROM pokemon WHERE evolution_stage = 1
          )
        """
    )

    # is_fully_evolved: no other pokemon evolves from this one
    conn.execute(
        """
        UPDATE pokemon
        SET is_fully_evolved = CASE
            WHEN id NOT IN (
                SELECT DISTINCT evolves_from_species_id
                FROM pokemon
                WHERE evolves_from_species_id IS NOT NULL
            ) THEN 1
            ELSE 0
        END
        """
    )

    conn.commit()
    print("Evolution fields computed.")

    stats = conn.execute(
        """
        SELECT evolution_stage, COUNT(*) as cnt
        FROM pokemon
        GROUP BY evolution_stage
        ORDER BY evolution_stage
        """
    ).fetchall()
    for row in stats:
        print(f"  Stage {row['evolution_stage']}: {row['cnt']} pokemon")

    fully = conn.execute(
        "SELECT COUNT(*) as cnt FROM pokemon WHERE is_fully_evolved = 1"
    ).fetchone()
    print(f"  Fully evolved: {fully['cnt']} pokemon")
