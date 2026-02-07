import csv
import sqlite3
from pathlib import Path

from src.db.repository import fetch_all_pokemon


def export_csv(conn: sqlite3.Connection, output_path: Path) -> None:
    pokemon_list = fetch_all_pokemon(conn)

    fieldnames = [
        "id", "name_en", "name_zh_hans", "name_zh_hant", "name_ja",
        "genus_zh", "type1_en", "type1_zh_hans", "type2_en", "type2_zh_hans",
        "height", "weight", "generation",
        "hp", "attack", "defense", "sp_attack", "sp_defense", "speed", "total",
        "abilities_en", "abilities_zh",
        "artwork_path", "sprite_path",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in pokemon_list:
            abilities_en = "; ".join(
                a["name_en"] for a in row["abilities"]
            )
            abilities_zh = "; ".join(
                a["name_zh_hans"] for a in row["abilities"]
            )

            writer.writerow({
                "id": row["id"],
                "name_en": row["name_en"],
                "name_zh_hans": row["name_zh_hans"],
                "name_zh_hant": row["name_zh_hant"],
                "name_ja": row["name_ja"],
                "genus_zh": row["genus_zh"],
                "type1_en": row["type1_en"],
                "type1_zh_hans": row["type1_zh_hans"],
                "type2_en": row.get("type2_en", ""),
                "type2_zh_hans": row.get("type2_zh_hans", ""),
                "height": row["height"],
                "weight": row["weight"],
                "generation": row["generation"],
                "hp": row["hp"],
                "attack": row["attack"],
                "defense": row["defense"],
                "sp_attack": row["sp_attack"],
                "sp_defense": row["sp_defense"],
                "speed": row["speed"],
                "total": row["total"],
                "abilities_en": abilities_en,
                "abilities_zh": abilities_zh,
                "artwork_path": row["artwork_path"],
                "sprite_path": row["sprite_path"],
            })

    print(f"Exported {len(pokemon_list)} Pokemon to {output_path}")
