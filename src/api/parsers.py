from src.models import PokemonAbility, PokemonStats, PokemonType


def _find_name(names: list[dict], language: str) -> str:
    for entry in names:
        if entry["language"]["name"] == language:
            return entry["name"]
    return ""


def _find_genus(genera: list[dict], language: str) -> str:
    for entry in genera:
        if entry["language"]["name"] == language:
            return entry["genus"]
    return ""


def _extract_generation_number(generation_url: str) -> int:
    """Extract generation number from URL like .../generation/1/"""
    parts = generation_url.rstrip("/").split("/")
    try:
        return int(parts[-1])
    except (ValueError, IndexError):
        return 0


def parse_type(data: dict) -> PokemonType:
    names = data.get("names", [])
    return PokemonType(
        id=data["id"],
        name_en=data["name"],
        name_zh_hans=_find_name(names, "zh-hans"),
        name_zh_hant=_find_name(names, "zh-hant"),
    )


def parse_stats(pokemon_data: dict) -> PokemonStats:
    stats_map: dict[str, int] = {}
    for stat_entry in pokemon_data["stats"]:
        stat_name = stat_entry["stat"]["name"]
        stats_map[stat_name] = stat_entry["base_stat"]

    return PokemonStats(
        hp=stats_map.get("hp", 0),
        attack=stats_map.get("attack", 0),
        defense=stats_map.get("defense", 0),
        sp_attack=stats_map.get("special-attack", 0),
        sp_defense=stats_map.get("special-defense", 0),
        speed=stats_map.get("speed", 0),
    )


def parse_ability(data: dict, is_hidden: bool, slot: int) -> PokemonAbility:
    names = data.get("names", [])
    return PokemonAbility(
        id=data["id"],
        name_en=data["name"],
        name_zh_hans=_find_name(names, "zh-hans"),
        name_zh_hant=_find_name(names, "zh-hant"),
        is_hidden=is_hidden,
        slot=slot,
    )


def extract_species_info(species_data: dict) -> dict:
    names = species_data.get("names", [])
    genera = species_data.get("genera", [])
    generation_url = species_data.get("generation", {}).get("url", "")

    return {
        "name_en": species_data["name"],
        "name_zh_hans": _find_name(names, "zh-hans"),
        "name_zh_hant": _find_name(names, "zh-hant"),
        "name_ja": _find_name(names, "ja"),
        "genus_zh": _find_genus(genera, "zh-hans"),
        "generation": _extract_generation_number(generation_url),
    }


def extract_type_ids_from_pokemon(pokemon_data: dict) -> list[dict]:
    """Extract type references from pokemon data for later resolution."""
    result = []
    for type_entry in pokemon_data["types"]:
        url = type_entry["type"]["url"]
        parts = url.rstrip("/").split("/")
        try:
            type_id = int(parts[-1])
        except (ValueError, IndexError):
            continue
        result.append({
            "id": type_id,
            "name": type_entry["type"]["name"],
            "slot": type_entry["slot"],
        })
    return sorted(result, key=lambda x: x["slot"])


def extract_ability_refs_from_pokemon(pokemon_data: dict) -> list[dict]:
    """Extract ability references from pokemon data for later resolution."""
    result = []
    for ab_entry in pokemon_data["abilities"]:
        url = ab_entry["ability"]["url"]
        parts = url.rstrip("/").split("/")
        try:
            ability_id = int(parts[-1])
        except (ValueError, IndexError):
            continue
        result.append({
            "id": ability_id,
            "name": ab_entry["ability"]["name"],
            "is_hidden": ab_entry["is_hidden"],
            "slot": ab_entry["slot"],
        })
    return result
