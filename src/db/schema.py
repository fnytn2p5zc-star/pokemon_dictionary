import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS types (
    id INTEGER PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_zh_hans TEXT NOT NULL DEFAULT '',
    name_zh_hant TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pokemon (
    id INTEGER PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_zh_hans TEXT NOT NULL DEFAULT '',
    name_zh_hant TEXT NOT NULL DEFAULT '',
    name_ja TEXT NOT NULL DEFAULT '',
    genus_zh TEXT NOT NULL DEFAULT '',
    type1_id INTEGER NOT NULL REFERENCES types(id),
    type2_id INTEGER REFERENCES types(id),
    height INTEGER NOT NULL DEFAULT 0,
    weight INTEGER NOT NULL DEFAULT 0,
    generation INTEGER NOT NULL DEFAULT 0,
    artwork_path TEXT NOT NULL DEFAULT '',
    sprite_path TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pokemon_stats (
    pokemon_id INTEGER PRIMARY KEY REFERENCES pokemon(id),
    hp INTEGER NOT NULL,
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL,
    sp_attack INTEGER NOT NULL,
    sp_defense INTEGER NOT NULL,
    speed INTEGER NOT NULL,
    total INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id INTEGER NOT NULL REFERENCES pokemon(id),
    ability_id INTEGER NOT NULL,
    name_en TEXT NOT NULL,
    name_zh_hans TEXT NOT NULL DEFAULT '',
    name_zh_hant TEXT NOT NULL DEFAULT '',
    is_hidden INTEGER NOT NULL DEFAULT 0,
    slot INTEGER NOT NULL,
    PRIMARY KEY (pokemon_id, slot)
);

CREATE TABLE IF NOT EXISTS scrape_log (
    pokemon_id INTEGER PRIMARY KEY,
    data_scraped INTEGER NOT NULL DEFAULT 0,
    images_downloaded INTEGER NOT NULL DEFAULT 0
);
"""


_MIGRATIONS = [
    (
        "pokemon_abilities",
        "flavor_text_zh",
        "ALTER TABLE pokemon_abilities ADD COLUMN flavor_text_zh TEXT NOT NULL DEFAULT ''",
    ),
    (
        "pokemon",
        "is_legendary",
        "ALTER TABLE pokemon ADD COLUMN is_legendary INTEGER NOT NULL DEFAULT 0",
    ),
    (
        "pokemon",
        "is_mythical",
        "ALTER TABLE pokemon ADD COLUMN is_mythical INTEGER NOT NULL DEFAULT 0",
    ),
    (
        "pokemon",
        "evolves_from_species_id",
        "ALTER TABLE pokemon ADD COLUMN evolves_from_species_id INTEGER",
    ),
    (
        "pokemon",
        "evolution_stage",
        "ALTER TABLE pokemon ADD COLUMN evolution_stage INTEGER NOT NULL DEFAULT 0",
    ),
    (
        "pokemon",
        "is_fully_evolved",
        "ALTER TABLE pokemon ADD COLUMN is_fully_evolved INTEGER NOT NULL DEFAULT 0",
    ),
]


def _run_migrations(conn: sqlite3.Connection) -> None:
    for table, column, sql in _MIGRATIONS:
        columns = [
            row[1]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        ]
        if column not in columns:
            conn.execute(sql)
    conn.commit()


def init_database(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    _run_migrations(conn)
    conn.commit()
