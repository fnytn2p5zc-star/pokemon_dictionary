import math
import random

from src.battle.models import BattleConfig
from src.battle.state import BattlePokemon
from src.battle.type_chart import best_attack_type


def calculate_damage(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    config: BattleConfig,
) -> tuple[int, float, str]:
    a_stats = attacker.stats
    d_stats = defender.stats

    attack_type, type_mult = best_attack_type(
        a_stats.type1_en,
        a_stats.type2_en,
        d_stats.type1_en,
        d_stats.type2_en,
    )

    if a_stats.base_attack >= a_stats.base_sp_attack:
        atk_val = a_stats.battle_attack
        def_val = d_stats.battle_defense
    else:
        atk_val = a_stats.battle_sp_attack
        def_val = d_stats.battle_sp_defense

    level = config.level
    power = config.move_power
    raw = math.floor(
        (2 * level / 5 + 2) * power * atk_val / (def_val * 50) + 2
    )

    stab = config.stab_bonus if _is_stab(attack_type, a_stats) else 1.0
    rand_factor = random.uniform(config.random_min, config.random_max)

    damage = max(1, math.floor(raw * type_mult * stab * rand_factor))
    return damage, type_mult, attack_type


def _is_stab(attack_type: str, stats) -> bool:
    if attack_type.lower() == stats.type1_en.lower():
        return True
    if stats.type2_en and attack_type.lower() == stats.type2_en.lower():
        return True
    return False
