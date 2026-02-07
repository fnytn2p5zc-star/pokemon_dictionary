from __future__ import annotations

import random

from src.battle.models import BattleConfig, TurnEvent
from src.battle.state import BattlePokemon
from src.battle.damage import calculate_damage


class TurnBattleEngine:
    """Turn-based 1v1 battle engine.

    States: ready -> (waiting_switch) -> ready -> ... -> finished
    """

    def __init__(
        self,
        team1: list[BattlePokemon],
        team2: list[BattlePokemon],
        config: BattleConfig | None = None,
    ) -> None:
        self.team1 = team1
        self.team2 = team2
        self.config = config or BattleConfig()
        self.turn = 0
        self.state = "ready"
        self.finished = False
        self.winner_team: int | None = None

        self.active1: BattlePokemon = team1[0]
        self.active2: BattlePokemon = team2[0]

        self._waiting_switch_team: int | None = None

    def get_active(self, team: int) -> BattlePokemon:
        return self.active1 if team == 1 else self.active2

    def get_team(self, team: int) -> list[BattlePokemon]:
        return self.team1 if team == 1 else self.team2

    def get_alive(self, team: int) -> list[BattlePokemon]:
        return [p for p in self.get_team(team) if p.alive]

    def team_defeated(self, team: int) -> bool:
        return len(self.get_alive(team)) == 0

    def execute_turn(self) -> list[TurnEvent]:
        """Execute one turn: both active pokemon attack in speed order."""
        if self.finished or self.state != "ready":
            return []

        self.turn += 1
        events: list[TurnEvent] = []

        a1 = self.active1
        a2 = self.active2

        speed1 = a1.stats.battle_speed
        speed2 = a2.stats.battle_speed

        if speed1 > speed2:
            first, second = a1, a2
        elif speed2 > speed1:
            first, second = a2, a1
        else:
            first, second = random.choice([(a1, a2), (a2, a1)])

        attack_event = self._do_attack(first, second)
        events.append(attack_event)

        if attack_event.is_fainted:
            fainted_team = second.team
            if self.team_defeated(fainted_team):
                self._finish(first.team)
                return events
            self._waiting_switch_team = fainted_team
            self.state = "waiting_switch"
            return events

        counter_event = self._do_attack(second, first)
        events.append(counter_event)

        if counter_event.is_fainted:
            fainted_team = first.team
            if self.team_defeated(fainted_team):
                self._finish(second.team)
                return events
            self._waiting_switch_team = fainted_team
            self.state = "waiting_switch"

        return events

    def switch_pokemon(self, team: int, index: int) -> BattlePokemon | None:
        """Player selects next pokemon after fainting. Returns the new active."""
        members = self.get_team(team)
        if index < 0 or index >= len(members):
            return None

        chosen = members[index]
        if not chosen.alive:
            return None

        if team == 1:
            self.active1 = chosen
        else:
            self.active2 = chosen

        self._waiting_switch_team = None
        self.state = "ready"
        return chosen

    def auto_switch(self, team: int) -> BattlePokemon | None:
        """Timeout: auto-select first alive pokemon."""
        alive = self.get_alive(team)
        if not alive:
            return None
        return self.switch_pokemon(team, alive[0].index)

    def get_team_summary(self, team: int) -> list[dict]:
        return [p.to_dict() for p in self.get_team(team)]

    @property
    def waiting_switch_team(self) -> int | None:
        return self._waiting_switch_team

    def _do_attack(
        self, attacker: BattlePokemon, defender: BattlePokemon,
    ) -> TurnEvent:
        damage, effectiveness, attack_type = calculate_damage(
            attacker, defender, self.config,
        )
        defender.current_hp = max(0, defender.current_hp - damage)
        fainted = defender.current_hp <= 0
        if fainted:
            defender.alive = False

        return TurnEvent(
            turn=self.turn,
            event_type="attack",
            attacker_name=attacker.stats.name_zh or attacker.stats.name_en,
            defender_name=defender.stats.name_zh or defender.stats.name_en,
            attack_type=attack_type,
            damage=damage,
            effectiveness=effectiveness,
            defender_hp=defender.current_hp,
            defender_max_hp=defender.max_hp,
            is_fainted=fainted,
            attacker_team=attacker.team,
            defender_team=defender.team,
        )

    def _finish(self, winner_team: int) -> None:
        self.finished = True
        self.winner_team = winner_team
        self.state = "finished"
