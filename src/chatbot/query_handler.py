import sqlite3

from src.db.queries import (
    fetch_pokemon_detail,
    fetch_top_by_stat,
    filter_pokemon,
    search_by_ability,
    search_pokemon,
)
from src.chatbot.rules import ParsedQuery, QueryType


def handle_query(
    parsed: ParsedQuery,
    conn: sqlite3.Connection,
) -> dict:
    handler = _HANDLERS.get(parsed.query_type, _handle_unknown)
    return handler(parsed, conn)


def _handle_pokemon_info(parsed: ParsedQuery, conn: sqlite3.Connection) -> dict:
    row, abilities = fetch_pokemon_detail(conn, parsed.pokemon_name)
    if row is None:
        results = search_pokemon(conn, parsed.pokemon_name)
        return {"type": "search_results", "rows": results, "term": parsed.pokemon_name}
    return {"type": "detail", "row": row, "abilities": abilities}


def _handle_top_by_stat(parsed: ParsedQuery, conn: sqlite3.Connection) -> dict:
    rows = fetch_top_by_stat(
        conn,
        parsed.stat,
        type_name=parsed.type_name or None,
        gen=parsed.generation or None,
        limit=parsed.limit,
    )
    return {
        "type": "ranking",
        "rows": rows,
        "stat": parsed.stat,
        "type_name": parsed.type_name,
        "generation": parsed.generation,
    }


def _handle_filter_type(parsed: ParsedQuery, conn: sqlite3.Connection) -> dict:
    rows = filter_pokemon(
        conn,
        type_name=parsed.type_name or None,
        gen=parsed.generation or None,
        limit=parsed.limit,
    )
    return {
        "type": "filter",
        "rows": rows,
        "type_name": parsed.type_name,
        "generation": parsed.generation,
    }


def _handle_filter_ability(parsed: ParsedQuery, conn: sqlite3.Connection) -> dict:
    rows = search_by_ability(conn, parsed.ability_name)
    return {"type": "ability", "rows": rows, "ability_name": parsed.ability_name}


def _handle_unknown(_parsed: ParsedQuery, _conn: sqlite3.Connection) -> dict:
    return {"type": "unknown"}


_HANDLERS = {
    QueryType.POKEMON_INFO: _handle_pokemon_info,
    QueryType.TOP_BY_STAT: _handle_top_by_stat,
    QueryType.FILTER_TYPE: _handle_filter_type,
    QueryType.FILTER_ABILITY: _handle_filter_ability,
    QueryType.UNKNOWN: _handle_unknown,
}
