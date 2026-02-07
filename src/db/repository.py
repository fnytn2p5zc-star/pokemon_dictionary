import sqlite3

from src.models import Pokemon, PokemonAbility, PokemonStats, PokemonType


def upsert_type(conn: sqlite3.Connection, ptype: PokemonType) -> None:
    conn.execute(
        """
        INSERT INTO types (id, name_en, name_zh_hans, name_zh_hant)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name_en=excluded.name_en,
            name_zh_hans=excluded.name_zh_hans,
            name_zh_hant=excluded.name_zh_hant
        """,
        (ptype.id, ptype.name_en, ptype.name_zh_hans, ptype.name_zh_hant),
    )
    conn.commit()


def upsert_pokemon(conn: sqlite3.Connection, pokemon: Pokemon) -> None:
    type2_id = pokemon.types[1].id if len(pokemon.types) > 1 else None

    conn.execute(
        """
        INSERT INTO pokemon (
            id, name_en, name_zh_hans, name_zh_hant, name_ja,
            genus_zh, type1_id, type2_id, height, weight,
            generation, artwork_path, sprite_path,
            is_legendary, is_mythical, evolves_from_species_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name_en=excluded.name_en,
            name_zh_hans=excluded.name_zh_hans,
            name_zh_hant=excluded.name_zh_hant,
            name_ja=excluded.name_ja,
            genus_zh=excluded.genus_zh,
            type1_id=excluded.type1_id,
            type2_id=excluded.type2_id,
            height=excluded.height,
            weight=excluded.weight,
            generation=excluded.generation,
            artwork_path=excluded.artwork_path,
            sprite_path=excluded.sprite_path,
            is_legendary=excluded.is_legendary,
            is_mythical=excluded.is_mythical,
            evolves_from_species_id=excluded.evolves_from_species_id
        """,
        (
            pokemon.id, pokemon.name_en, pokemon.name_zh_hans,
            pokemon.name_zh_hant, pokemon.name_ja, pokemon.genus_zh,
            pokemon.types[0].id, type2_id,
            pokemon.height, pokemon.weight, pokemon.generation,
            pokemon.artwork_path, pokemon.sprite_path,
            int(pokemon.is_legendary), int(pokemon.is_mythical),
            pokemon.evolves_from_species_id,
        ),
    )

    conn.execute(
        """
        INSERT INTO pokemon_stats (
            pokemon_id, hp, attack, defense,
            sp_attack, sp_defense, speed, total
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(pokemon_id) DO UPDATE SET
            hp=excluded.hp,
            attack=excluded.attack,
            defense=excluded.defense,
            sp_attack=excluded.sp_attack,
            sp_defense=excluded.sp_defense,
            speed=excluded.speed,
            total=excluded.total
        """,
        (
            pokemon.id,
            pokemon.stats.hp, pokemon.stats.attack, pokemon.stats.defense,
            pokemon.stats.sp_attack, pokemon.stats.sp_defense,
            pokemon.stats.speed, pokemon.stats.total,
        ),
    )

    conn.execute(
        "DELETE FROM pokemon_abilities WHERE pokemon_id = ?",
        (pokemon.id,),
    )
    for ability in pokemon.abilities:
        conn.execute(
            """
            INSERT INTO pokemon_abilities (
                pokemon_id, ability_id, name_en,
                name_zh_hans, name_zh_hant, is_hidden, slot
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pokemon.id, ability.id, ability.name_en,
                ability.name_zh_hans, ability.name_zh_hant,
                int(ability.is_hidden), ability.slot,
            ),
        )

    conn.commit()


def mark_data_scraped(conn: sqlite3.Connection, pokemon_id: int) -> None:
    conn.execute(
        """
        INSERT INTO scrape_log (pokemon_id, data_scraped, images_downloaded)
        VALUES (?, 1, 0)
        ON CONFLICT(pokemon_id) DO UPDATE SET data_scraped=1
        """,
        (pokemon_id,),
    )
    conn.commit()


def mark_images_downloaded(conn: sqlite3.Connection, pokemon_id: int) -> None:
    conn.execute(
        """
        INSERT INTO scrape_log (pokemon_id, data_scraped, images_downloaded)
        VALUES (?, 1, 1)
        ON CONFLICT(pokemon_id) DO UPDATE SET images_downloaded=1
        """,
        (pokemon_id,),
    )
    conn.commit()


def get_scraped_ids(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute(
        "SELECT pokemon_id FROM scrape_log WHERE data_scraped = 1"
    ).fetchall()
    return {row["pokemon_id"] for row in rows}


def get_image_downloaded_ids(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute(
        "SELECT pokemon_id FROM scrape_log WHERE images_downloaded = 1"
    ).fetchall()
    return {row["pokemon_id"] for row in rows}


def get_scrape_status(conn: sqlite3.Connection) -> dict[str, int]:
    total_data = conn.execute(
        "SELECT COUNT(*) as c FROM scrape_log WHERE data_scraped = 1"
    ).fetchone()["c"]
    total_images = conn.execute(
        "SELECT COUNT(*) as c FROM scrape_log WHERE images_downloaded = 1"
    ).fetchone()["c"]
    total_pokemon = conn.execute(
        "SELECT COUNT(*) as c FROM pokemon"
    ).fetchone()["c"]
    return {
        "total_pokemon": total_pokemon,
        "data_scraped": total_data,
        "images_downloaded": total_images,
    }


def fetch_all_pokemon(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            p.id, p.name_en, p.name_zh_hans, p.name_zh_hant, p.name_ja,
            p.genus_zh, p.height, p.weight, p.generation,
            p.artwork_path, p.sprite_path,
            t1.name_en as type1_en, t1.name_zh_hans as type1_zh_hans,
            t2.name_en as type2_en, t2.name_zh_hans as type2_zh_hans,
            s.hp, s.attack, s.defense, s.sp_attack, s.sp_defense,
            s.speed, s.total
        FROM pokemon p
        JOIN types t1 ON p.type1_id = t1.id
        LEFT JOIN types t2 ON p.type2_id = t2.id
        JOIN pokemon_stats s ON p.id = s.pokemon_id
        ORDER BY p.id
        """
    ).fetchall()

    result = []
    for row in rows:
        pokemon_dict = dict(row)
        abilities = conn.execute(
            """
            SELECT name_en, name_zh_hans, name_zh_hant, is_hidden, slot
            FROM pokemon_abilities
            WHERE pokemon_id = ?
            ORDER BY slot
            """,
            (row["id"],),
        ).fetchall()
        pokemon_dict["abilities"] = [dict(a) for a in abilities]
        result.append(pokemon_dict)

    return result
