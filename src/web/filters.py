from markupsafe import Markup

TYPE_COLORS_HEX = {
    "normal": "#A8A878",
    "fire": "#F08030",
    "water": "#6890F0",
    "grass": "#78C850",
    "electric": "#F8D030",
    "ice": "#98D8D8",
    "fighting": "#C03028",
    "poison": "#A040A0",
    "ground": "#E0C068",
    "flying": "#A890F0",
    "psychic": "#F85888",
    "bug": "#A8B820",
    "rock": "#B8A038",
    "ghost": "#705898",
    "dragon": "#7038F8",
    "dark": "#705848",
    "steel": "#B8B8D0",
    "fairy": "#EE99AC",
}

STAT_LABELS = {
    "hp": "HP",
    "attack": "攻击",
    "defense": "防御",
    "sp_attack": "特攻",
    "sp_defense": "特防",
    "speed": "速度",
}


def type_color(type_name_en: str) -> str:
    return TYPE_COLORS_HEX.get(type_name_en.lower(), "#888888")


def type_badge(name_zh: str, name_en: str) -> str:
    color = type_color(name_en)
    return Markup(
        f'<span class="type-badge" style="background:{color}">{name_zh}</span>'
    )


def stat_percent(value: int) -> int:
    return min(int(value / 255 * 100), 100)


def stat_color(value: int) -> str:
    if value >= 100:
        return "#4CAF50"
    if value >= 60:
        return "#FFC107"
    return "#F44336"


def pokemon_id_str(pid: int) -> str:
    return f"#{pid:04d}"


def register_filters(app: object) -> None:
    app.jinja_env.filters["type_color"] = type_color
    app.jinja_env.filters["type_badge"] = type_badge
    app.jinja_env.filters["stat_percent"] = stat_percent
    app.jinja_env.filters["stat_color"] = stat_color
    app.jinja_env.filters["pokemon_id_str"] = pokemon_id_str
