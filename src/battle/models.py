from dataclasses import dataclass


@dataclass(frozen=True)
class BattleConfig:
    level: int = 50
    move_power: int = 80
    stab_bonus: float = 1.5
    random_min: float = 0.85
    random_max: float = 1.0
    team_min: int = 1
    team_max: int = 6
    turn_delay: float = 3.5
    switch_timeout: float = 30.0


@dataclass(frozen=True)
class BattlePokemonStats:
    pokemon_id: int
    name_zh: str
    name_en: str
    sprite_path: str
    base_hp: int
    base_attack: int
    base_defense: int
    base_sp_attack: int
    base_sp_defense: int
    base_speed: int
    type1_id: int
    type1_en: str
    type2_id: int | None
    type2_en: str | None

    @property
    def battle_hp(self) -> int:
        return self.base_hp * 2 + 110

    @property
    def battle_attack(self) -> int:
        return self.base_attack * 2 + 5

    @property
    def battle_defense(self) -> int:
        return self.base_defense * 2 + 5

    @property
    def battle_sp_attack(self) -> int:
        return self.base_sp_attack * 2 + 5

    @property
    def battle_sp_defense(self) -> int:
        return self.base_sp_defense * 2 + 5

    @property
    def battle_speed(self) -> int:
        return self.base_speed * 2 + 5


@dataclass(frozen=True)
class TurnEvent:
    turn: int
    event_type: str
    attacker_name: str = ""
    defender_name: str = ""
    attack_type: str = ""
    damage: int = 0
    effectiveness: float = 1.0
    defender_hp: int = 0
    defender_max_hp: int = 0
    is_fainted: bool = False
    attacker_team: int = 0
    defender_team: int = 0

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "type": self.event_type,
            "attacker_name": self.attacker_name,
            "defender_name": self.defender_name,
            "attack_type": self.attack_type,
            "damage": self.damage,
            "effectiveness": self.effectiveness,
            "defender_hp": self.defender_hp,
            "defender_max_hp": self.defender_max_hp,
            "is_fainted": self.is_fainted,
            "attacker_team": self.attacker_team,
            "defender_team": self.defender_team,
        }
