import json
import sqlite3
from pathlib import Path

from src.db.repository import fetch_all_pokemon


def export_json(conn: sqlite3.Connection, output_path: Path) -> None:
    pokemon_list = fetch_all_pokemon(conn)

    records = []
    for row in pokemon_list:
        types = [row["type1_en"]]
        types_zh = [row["type1_zh_hans"]]
        if row.get("type2_en"):
            types.append(row["type2_en"])
            types_zh.append(row["type2_zh_hans"])

        record = {
            "id": row["id"],
            "name_en": row["name_en"],
            "name_zh_hans": row["name_zh_hans"],
            "name_zh_hant": row["name_zh_hant"],
            "name_ja": row["name_ja"],
            "genus_zh": row["genus_zh"],
            "types_en": types,
            "types_zh": types_zh,
            "height": row["height"],
            "weight": row["weight"],
            "generation": row["generation"],
            "stats": {
                "hp": row["hp"],
                "attack": row["attack"],
                "defense": row["defense"],
                "sp_attack": row["sp_attack"],
                "sp_defense": row["sp_defense"],
                "speed": row["speed"],
                "total": row["total"],
            },
            "abilities": [
                {
                    "name_en": a["name_en"],
                    "name_zh_hans": a["name_zh_hans"],
                    "name_zh_hant": a["name_zh_hant"],
                    "is_hidden": bool(a["is_hidden"]),
                }
                for a in row["abilities"]
            ],
            "artwork_path": row["artwork_path"],
            "sprite_path": row["sprite_path"],
        }
        records.append(record)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(records)} Pokemon to {output_path}")
