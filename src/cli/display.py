RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

TYPE_COLORS = {
    "normal": "\033[38;5;255m",
    "fire": "\033[38;5;196m",
    "water": "\033[38;5;33m",
    "grass": "\033[38;5;34m",
    "electric": "\033[38;5;226m",
    "ice": "\033[38;5;51m",
    "fighting": "\033[38;5;166m",
    "poison": "\033[38;5;129m",
    "ground": "\033[38;5;215m",
    "flying": "\033[38;5;117m",
    "psychic": "\033[38;5;205m",
    "bug": "\033[38;5;142m",
    "rock": "\033[38;5;137m",
    "ghost": "\033[38;5;99m",
    "dragon": "\033[38;5;57m",
    "dark": "\033[38;5;240m",
    "steel": "\033[38;5;249m",
    "fairy": "\033[38;5;218m",
}

GREEN = "\033[38;5;34m"
YELLOW = "\033[38;5;226m"
RED = "\033[38;5;196m"

BAR_WIDTH = 30
STAT_MAX = 255

STAT_LABELS = {
    "hp": "HP",
    "attack": "攻击",
    "defense": "防御",
    "sp_attack": "特攻",
    "sp_defense": "特防",
    "speed": "速度",
}


def colorize(text: str, type_en: str) -> str:
    color = TYPE_COLORS.get(type_en.lower(), "")
    if not color:
        return text
    return f"{color}{text}{RESET}"


def format_type_badge(type_en: str, type_zh: str) -> str:
    return colorize(f"[{type_zh}]", type_en)


def _type_badges(row) -> str:
    badges = format_type_badge(row["type1_en"], row["type1_zh_hans"])
    if row["type2_en"]:
        badges += format_type_badge(row["type2_en"], row["type2_zh_hans"])
    return badges


def format_pokemon_row(row) -> str:
    pid = f"#{row['id']:04d}"
    name_zh = row["name_zh_hans"] or row["name_en"]
    name_en = row["name_en"]
    badges = _type_badges(row)
    total = row["total"]
    return f"  {BOLD}{pid}{RESET} {name_zh} ({name_en})  {badges}  总:{total}"


def format_pokemon_table(rows, page_info: str | None = None) -> str:
    if not rows:
        return "  未找到匹配的宝可梦"

    lines = [f"  {DIM}{'─' * 54}{RESET}"]
    for row in rows:
        lines.append(format_pokemon_row(row))
    lines.append(f"  {DIM}{'─' * 54}{RESET}")

    if page_info:
        lines.append(f"  {DIM}{page_info}{RESET}")

    return "\n".join(lines)


def _stat_color(value: int) -> str:
    if value >= 100:
        return GREEN
    if value >= 60:
        return YELLOW
    return RED


def format_stat_bar(label: str, value: int, max_val: int = STAT_MAX) -> str:
    filled = round(value / max_val * BAR_WIDTH)
    empty = BAR_WIDTH - filled
    color = _stat_color(value)
    bar = f"{color}{'█' * filled}{DIM}{'░' * empty}{RESET}"
    return f"   {label}:{value:>5}  {bar}"


def format_pokemon_detail(row, abilities) -> str:
    sep_double = f"  {'═' * 40}"
    sep_single = f"  {'─' * 40}"

    pid = f"#{row['id']:04d}"
    name_zh = row["name_zh_hans"] or row["name_en"]
    name_en = row["name_en"]
    name_ja = row["name_ja"] or ""

    header = f"   {BOLD}{pid} {name_zh} ({name_en}){RESET}"
    if name_ja:
        header += f"  {name_ja}"

    genus_line = f"   分类: {row['genus_zh']}" if row["genus_zh"] else ""
    type_line = f"   属性: {_type_badges(row)}"
    meta_line = (
        f"   世代: {row['generation']}    "
        f"身高: {row['height'] / 10:.1f}m    "
        f"体重: {row['weight'] / 10:.1f}kg"
    )

    stat_header = f"   {BOLD}种族值 (总计: {row['total']}){RESET}"
    stat_lines = [
        format_stat_bar(STAT_LABELS["hp"], row["hp"]),
        format_stat_bar(STAT_LABELS["attack"], row["attack"]),
        format_stat_bar(STAT_LABELS["defense"], row["defense"]),
        format_stat_bar(STAT_LABELS["sp_attack"], row["sp_attack"]),
        format_stat_bar(STAT_LABELS["sp_defense"], row["sp_defense"]),
        format_stat_bar(STAT_LABELS["speed"], row["speed"]),
    ]

    ability_parts = []
    for ab in abilities:
        name = ab["name_zh_hans"] or ab["name_en"]
        if ab["is_hidden"]:
            ability_parts.append(f"{name} (隐藏)")
        else:
            ability_parts.append(name)
    ability_line = f"   特性: {' | '.join(ability_parts)}" if ability_parts else ""

    sections = [sep_double, header]
    if genus_line:
        sections.append(genus_line)
    sections.extend([type_line, meta_line, sep_single, stat_header])
    sections.extend(stat_lines)
    sections.append(sep_single)
    if ability_line:
        sections.append(ability_line)
    sections.append(sep_double)

    return "\n".join(sections)
