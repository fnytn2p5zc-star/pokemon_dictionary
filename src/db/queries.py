import sqlite3

_BASE_QUERY = """
SELECT p.id, p.name_en, p.name_zh_hans, p.name_zh_hant, p.name_ja,
       p.genus_zh, p.height, p.weight, p.generation,
       p.artwork_path, p.sprite_path,
       t1.id AS type1_id, t1.name_en AS type1_en,
       t1.name_zh_hans AS type1_zh_hans, t1.name_zh_hant AS type1_zh_hant,
       t2.id AS type2_id, t2.name_en AS type2_en,
       t2.name_zh_hans AS type2_zh_hans, t2.name_zh_hant AS type2_zh_hant,
       s.hp, s.attack, s.defense, s.sp_attack, s.sp_defense, s.speed, s.total
FROM pokemon p
JOIN types t1 ON p.type1_id = t1.id
LEFT JOIN types t2 ON p.type2_id = t2.id
JOIN pokemon_stats s ON p.id = s.pokemon_id
"""

_VALID_SORT_COLUMNS = {
    "id": ("p.id", "ASC"),
    "total": ("s.total", "DESC"),
    "hp": ("s.hp", "DESC"),
    "attack": ("s.attack", "DESC"),
    "defense": ("s.defense", "DESC"),
    "sp_attack": ("s.sp_attack", "DESC"),
    "sp_defense": ("s.sp_defense", "DESC"),
    "speed": ("s.speed", "DESC"),
}

_VALID_STATS = {"hp", "attack", "defense", "sp_attack", "sp_defense", "speed", "total"}


def get_total_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM pokemon").fetchone()
    return row["c"]


def fetch_pokemon_page(
    conn: sqlite3.Connection,
    offset: int = 0,
    limit: int = 20,
) -> list[sqlite3.Row]:
    sql = _BASE_QUERY + "ORDER BY p.id LIMIT ? OFFSET ?"
    return conn.execute(sql, (limit, offset)).fetchall()


def search_pokemon(
    conn: sqlite3.Connection,
    term: str,
) -> list[sqlite3.Row]:
    pattern = f"%{term}%"
    sql = _BASE_QUERY + """
    WHERE p.name_zh_hans LIKE ?
       OR p.name_zh_hant LIKE ?
       OR p.name_en LIKE ?
       OR p.name_ja LIKE ?
    ORDER BY p.id LIMIT 50
    """
    return conn.execute(sql, (pattern, pattern, pattern, pattern)).fetchall()


def fetch_pokemon_detail(
    conn: sqlite3.Connection,
    id_or_name: str,
) -> tuple[sqlite3.Row | None, list[sqlite3.Row]]:
    if id_or_name.isdigit():
        sql = _BASE_QUERY + "WHERE p.id = ?"
        row = conn.execute(sql, (int(id_or_name),)).fetchone()
    else:
        sql = _BASE_QUERY + """
        WHERE LOWER(p.name_en) = LOWER(?)
           OR p.name_zh_hans = ?
           OR p.name_zh_hant = ?
        """
        row = conn.execute(sql, (id_or_name, id_or_name, id_or_name)).fetchone()

    if row is None:
        return None, []

    abilities = conn.execute(
        """
        SELECT ability_id, name_en, name_zh_hans, name_zh_hant,
               is_hidden, slot, flavor_text_zh
        FROM pokemon_abilities
        WHERE pokemon_id = ?
        ORDER BY slot
        """,
        (row["id"],),
    ).fetchall()

    return row, abilities


def filter_pokemon(
    conn: sqlite3.Connection,
    *,
    type_name: str | None = None,
    gen: int | None = None,
    min_total: int | None = None,
    sort_by: str = "id",
    limit: int = 20,
) -> list[sqlite3.Row]:
    conditions = []
    params: list[object] = []

    if type_name is not None:
        conditions.append(
            "(t1.name_en = ? OR t2.name_en = ? "
            "OR t1.name_zh_hans = ? OR t2.name_zh_hans = ?)"
        )
        params.extend([type_name, type_name, type_name, type_name])

    if gen is not None:
        conditions.append("p.generation = ?")
        params.append(gen)

    if min_total is not None:
        conditions.append("s.total >= ?")
        params.append(min_total)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    col, direction = _VALID_SORT_COLUMNS.get(sort_by, ("p.id", "ASC"))

    sql = f"{_BASE_QUERY}{where_clause} ORDER BY {col} {direction} LIMIT ?"
    params.append(limit)

    return conn.execute(sql, params).fetchall()


def fetch_top_by_stat(
    conn: sqlite3.Connection,
    stat: str,
    *,
    type_name: str | None = None,
    gen: int | None = None,
    limit: int = 5,
) -> list[sqlite3.Row]:
    if stat not in _VALID_STATS:
        raise ValueError(f"Invalid stat: {stat}. Must be one of {_VALID_STATS}")

    return filter_pokemon(
        conn,
        type_name=type_name,
        gen=gen,
        sort_by=stat,
        limit=limit,
    )


def get_type_by_name(
    conn: sqlite3.Connection,
    name: str,
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT * FROM types
        WHERE LOWER(name_en) = LOWER(?)
           OR name_zh_hans = ?
           OR name_zh_hant = ?
        """,
        (name, name, name),
    ).fetchone()


def fetch_all_types(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM types ORDER BY id").fetchall()


def search_by_ability(
    conn: sqlite3.Connection,
    ability_name: str,
) -> list[sqlite3.Row]:
    pattern = f"%{ability_name}%"
    ability_rows = conn.execute(
        """
        SELECT DISTINCT pokemon_id FROM pokemon_abilities
        WHERE name_zh_hans LIKE ? OR name_en LIKE ?
        """,
        (pattern, pattern),
    ).fetchall()

    if not ability_rows:
        return []

    ids = [row["pokemon_id"] for row in ability_rows]
    placeholders = ",".join("?" for _ in ids)
    sql = f"{_BASE_QUERY}WHERE p.id IN ({placeholders}) ORDER BY p.id LIMIT 50"
    return conn.execute(sql, ids).fetchall()
