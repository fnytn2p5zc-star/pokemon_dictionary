from src.cli.display import format_pokemon_detail, format_pokemon_table

STAT_NAMES_ZH = {
    "total": "种族值",
    "hp": "HP",
    "attack": "攻击",
    "defense": "防御",
    "sp_attack": "特攻",
    "sp_defense": "特防",
    "speed": "速度",
}

TYPE_NAMES_ZH = {
    "normal": "一般",
    "fire": "火",
    "water": "水",
    "grass": "草",
    "electric": "电",
    "ice": "冰",
    "fighting": "格斗",
    "poison": "毒",
    "ground": "地面",
    "flying": "飞行",
    "psychic": "超能力",
    "bug": "虫",
    "rock": "岩石",
    "ghost": "幽灵",
    "dragon": "龙",
    "dark": "恶",
    "steel": "钢",
    "fairy": "妖精",
}

HELP_TEXT = (
    "抱歉，我不太理解你的问题。你可以试试：\n"
    '  - 查询宝可梦：「皮卡丘」\n'
    '  - 排行：「最强的水系」\n'
    '  - 筛选：「第一世代火系」\n'
    '  - 特性：「特性 威吓」'
)


def format_response(result: dict) -> str:
    formatter = _FORMATTERS.get(result["type"], _format_unknown)
    return formatter(result)


def _format_detail(result: dict) -> str:
    return format_pokemon_detail(result["row"], result["abilities"])


def _format_search_results(result: dict) -> str:
    rows = result["rows"]
    term = result["term"]
    if not rows:
        return f"  未找到匹配「{term}」的宝可梦"
    header = f"  找到 {len(rows)} 个与「{term}」相关的结果：\n"
    return header + format_pokemon_table(rows)


def _format_ranking(result: dict) -> str:
    rows = result["rows"]
    stat = result["stat"]
    type_name = result.get("type_name", "")
    generation = result.get("generation", 0)

    stat_zh = STAT_NAMES_ZH.get(stat, stat)
    type_zh = TYPE_NAMES_ZH.get(type_name, type_name) if type_name else ""

    parts = []
    if type_zh:
        parts.append(f"{type_zh}系")
    if generation:
        parts.append(f"第{generation}世代")

    scope = "".join(parts)
    header = f"  {scope}{stat_zh}最高的宝可梦：\n" if scope else f"  {stat_zh}最高的宝可梦：\n"

    if not rows:
        return header + "  未找到符合条件的宝可梦"

    lines = []
    for i, row in enumerate(rows, 1):
        name = row["name_zh_hans"] or row["name_en"]
        value = row[stat] if stat != "total" else row["total"]
        lines.append(f"  {i}. {name} ({row['name_en']}) — {stat_zh}: {value}")

    return header + "\n".join(lines)


def _format_filter(result: dict) -> str:
    rows = result["rows"]
    type_name = result.get("type_name", "")
    generation = result.get("generation", 0)

    type_zh = TYPE_NAMES_ZH.get(type_name, type_name) if type_name else ""

    parts = []
    if generation:
        parts.append(f"第{generation}世代")
    if type_zh:
        parts.append(f"{type_zh}系")

    scope = "".join(parts)

    if not rows:
        return f"  未找到{scope}宝可梦"

    header = f"  找到 {len(rows)} 只{scope}宝可梦：\n"
    return header + format_pokemon_table(rows)


def _format_ability(result: dict) -> str:
    rows = result["rows"]
    ability = result["ability_name"]

    if not rows:
        return f"  未找到拥有特性「{ability}」的宝可梦"

    header = f"  以下宝可梦拥有特性「{ability}」：\n"
    return header + format_pokemon_table(rows)


def _format_unknown(_result: dict) -> str:
    return HELP_TEXT


_FORMATTERS = {
    "detail": _format_detail,
    "search_results": _format_search_results,
    "ranking": _format_ranking,
    "filter": _format_filter,
    "ability": _format_ability,
    "unknown": _format_unknown,
}
