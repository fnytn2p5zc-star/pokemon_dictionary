from dataclasses import dataclass


@dataclass(frozen=True)
class PokemonStats:
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int

    @property
    def total(self) -> int:
        return (
            self.hp + self.attack + self.defense
            + self.sp_attack + self.sp_defense + self.speed
        )


@dataclass(frozen=True)
class PokemonType:
    id: int
    name_en: str
    name_zh_hans: str
    name_zh_hant: str


@dataclass(frozen=True)
class PokemonAbility:
    id: int
    name_en: str
    name_zh_hans: str
    name_zh_hant: str
    is_hidden: bool
    slot: int


@dataclass(frozen=True)
class Pokemon:
    id: int
    name_en: str
    name_zh_hans: str
    name_zh_hant: str
    name_ja: str
    genus_zh: str
    types: tuple[PokemonType, ...]
    stats: PokemonStats
    abilities: tuple[PokemonAbility, ...]
    height: int
    weight: int
    generation: int
    artwork_path: str
    sprite_path: str
