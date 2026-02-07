from src.config import Config


def pokemon_url(config: Config, pokemon_id: int) -> str:
    return f"{config.base_url}/pokemon/{pokemon_id}"


def species_url(config: Config, pokemon_id: int) -> str:
    return f"{config.base_url}/pokemon-species/{pokemon_id}"


def type_url(config: Config, type_id: int) -> str:
    return f"{config.base_url}/type/{type_id}"


def ability_url(config: Config, ability_id: int) -> str:
    return f"{config.base_url}/ability/{ability_id}"


def artwork_url(config: Config, pokemon_id: int) -> str:
    return config.artwork_url_template.format(id=pokemon_id)


def sprite_url(config: Config, pokemon_id: int) -> str:
    return config.sprite_url_template.format(id=pokemon_id)
