from __future__ import annotations

import random
import string

from src.battle.models import BattlePokemonStats


class BattlePokemon:
    def __init__(self, stats: BattlePokemonStats, team: int, index: int) -> None:
        self.stats = stats
        self.team = team
        self.index = index
        self.max_hp = stats.battle_hp
        self.current_hp = stats.battle_hp
        self.alive = True

    def to_dict(self) -> dict:
        return {
            "pokemon_id": self.stats.pokemon_id,
            "name_zh": self.stats.name_zh,
            "name_en": self.stats.name_en,
            "sprite_path": self.stats.sprite_path,
            "team": self.team,
            "index": self.index,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "alive": self.alive,
            "type1_en": self.stats.type1_en,
            "type2_en": self.stats.type2_en,
            "speed": self.stats.battle_speed,
        }


class Player:
    def __init__(self, sid: str, nickname: str) -> None:
        self.sid = sid
        self.nickname = nickname
        self.team_ids: list[int] = []
        self.ready = False

    def to_dict(self) -> dict:
        return {
            "sid": self.sid,
            "nickname": self.nickname,
            "team_size": len(self.team_ids),
            "ready": self.ready,
        }


class Room:
    def __init__(self, code: str, host: Player) -> None:
        self.code = code
        self.players: list[Player] = [host]
        self.status = "waiting"
        self.turn = 0

    @property
    def is_full(self) -> bool:
        return len(self.players) >= 2

    @property
    def all_ready(self) -> bool:
        return (
            len(self.players) == 2
            and all(p.ready for p in self.players)
            and all(len(p.team_ids) >= 1 for p in self.players)
        )

    def get_player(self, sid: str) -> Player | None:
        for player in self.players:
            if player.sid == sid:
                return player
        return None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "status": self.status,
            "players": [p.to_dict() for p in self.players],
        }

    @staticmethod
    def generate_code() -> str:
        return "".join(random.choices(string.digits, k=4))


def create_team(
    stats_list: list[BattlePokemonStats],
    team: int,
) -> list[BattlePokemon]:
    return [
        BattlePokemon(stats=stats, team=team, index=i)
        for i, stats in enumerate(stats_list)
    ]
