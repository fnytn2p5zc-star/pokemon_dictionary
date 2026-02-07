import sqlite3

from src.db.queries import search_pokemon
from src.chatbot.rules import (
    EXIT_WORDS,
    GEN_KEYWORDS,
    INTENT_ABILITY_KEYWORDS,
    INTENT_FILTER_KEYWORDS,
    INTENT_INFO_KEYWORDS,
    STAT_KEYWORDS,
    TYPE_KEYWORDS,
    ParsedQuery,
    QueryType,
)


def parse_query(text: str, conn: sqlite3.Connection) -> ParsedQuery | None:
    text = text.strip()
    if not text:
        return None

    lower = text.lower()
    if lower in EXIT_WORDS:
        return None

    stat = _extract_stat(text)
    type_name = _extract_type(text)
    generation = _extract_gen(text)
    ability_name = _extract_ability(text)
    query_type = _detect_intent(text)

    if stat:
        return ParsedQuery(
            query_type=QueryType.TOP_BY_STAT,
            stat=stat,
            type_name=type_name,
            generation=generation,
        )

    if ability_name and not type_name:
        return ParsedQuery(
            query_type=QueryType.FILTER_ABILITY,
            ability_name=ability_name,
        )

    if query_type == QueryType.FILTER_TYPE and type_name:
        return ParsedQuery(
            query_type=QueryType.FILTER_TYPE,
            type_name=type_name,
            generation=generation,
            limit=20,
        )

    if type_name and (generation or _has_filter_intent(text)):
        return ParsedQuery(
            query_type=QueryType.FILTER_TYPE,
            type_name=type_name,
            generation=generation,
            limit=20,
        )

    name = _extract_pokemon_name(text, conn)
    if name:
        return ParsedQuery(
            query_type=QueryType.POKEMON_INFO,
            pokemon_name=name,
        )

    if type_name:
        return ParsedQuery(
            query_type=QueryType.FILTER_TYPE,
            type_name=type_name,
            generation=generation,
            limit=20,
        )

    return ParsedQuery(query_type=QueryType.UNKNOWN)


def _extract_stat(text: str) -> str:
    for keyword, stat in sorted(
        STAT_KEYWORDS.items(), key=lambda kv: len(kv[0]), reverse=True,
    ):
        if keyword in text:
            return stat
    return ""


def _extract_type(text: str) -> str:
    for keyword, type_en in sorted(
        TYPE_KEYWORDS.items(), key=lambda kv: len(kv[0]), reverse=True,
    ):
        if keyword in text:
            return type_en
    return ""


def _extract_gen(text: str) -> int:
    lower = text.lower()
    for keyword, gen in sorted(
        GEN_KEYWORDS.items(), key=lambda kv: len(kv[0]), reverse=True,
    ):
        if keyword in lower:
            return gen
    return 0


def _extract_ability(text: str) -> str:
    for keyword in INTENT_ABILITY_KEYWORDS:
        if keyword in text:
            cleaned = text
            for k in INTENT_ABILITY_KEYWORDS:
                cleaned = cleaned.replace(k, "")
            for k in ("的", "有", "宝可梦", "pokemon"):
                cleaned = cleaned.replace(k, "")
            cleaned = cleaned.strip()
            if cleaned:
                return cleaned
    return ""


def _detect_intent(text: str) -> QueryType:
    for keyword in INTENT_INFO_KEYWORDS:
        if keyword in text:
            return QueryType.POKEMON_INFO
    for keyword in INTENT_FILTER_KEYWORDS:
        if keyword in text:
            return QueryType.FILTER_TYPE
    return QueryType.UNKNOWN


def _has_filter_intent(text: str) -> bool:
    for keyword in INTENT_FILTER_KEYWORDS:
        if keyword in text:
            return True
    return False


def _extract_pokemon_name(text: str, conn: sqlite3.Connection) -> str:
    cleaned = text
    for keywords in (
        STAT_KEYWORDS, TYPE_KEYWORDS, GEN_KEYWORDS,
    ):
        for k in sorted(keywords, key=len, reverse=True):
            cleaned = cleaned.replace(k, "")

    for keyword in INTENT_INFO_KEYWORDS | INTENT_FILTER_KEYWORDS:
        cleaned = cleaned.replace(keyword, "")

    for filler in ("的", "是", "什么", "呢", "吗", "啊"):
        cleaned = cleaned.replace(filler, "")

    cleaned = cleaned.strip()
    if not cleaned:
        return ""

    results = search_pokemon(conn, cleaned)
    if not results:
        return ""

    for row in results:
        if (
            row["name_zh_hans"] == cleaned
            or row["name_zh_hant"] == cleaned
            or row["name_en"].lower() == cleaned.lower()
            or row["name_ja"] == cleaned
        ):
            return cleaned

    if len(results) == 1:
        return cleaned

    return cleaned
