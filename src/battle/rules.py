"""Battle room rules: presets, parsing, and team validation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoomRules:
    max_legendary: int | None = None
    max_stat_total: int | None = None
    fully_evolved_only: bool = False
    preset_name: str = "无限制"

    def to_dict(self) -> dict:
        return {
            "max_legendary": self.max_legendary,
            "max_stat_total": self.max_stat_total,
            "fully_evolved_only": self.fully_evolved_only,
            "preset_name": self.preset_name,
        }


DEFAULT_RULES = RoomRules()

PRESETS: dict[str, RoomRules] = {
    "无限制": DEFAULT_RULES,
    "标准": RoomRules(
        max_legendary=2,
        max_stat_total=600,
        preset_name="标准",
    ),
    "严格": RoomRules(
        max_legendary=0,
        max_stat_total=540,
        fully_evolved_only=True,
        preset_name="严格",
    ),
}

_MAX_LEGENDARY_VALUES = {None, 0, 1, 2}
_MAX_STAT_VALUES = {None, 500, 540, 600}


def parse_rules_from_data(data: dict) -> RoomRules:
    """Parse rules from client-submitted data. Returns DEFAULT_RULES on invalid input."""
    if not isinstance(data, dict):
        return DEFAULT_RULES

    preset = data.get("preset")
    if isinstance(preset, str) and preset in PRESETS:
        return PRESETS[preset]

    max_legendary = data.get("max_legendary")
    if max_legendary is not None:
        try:
            max_legendary = int(max_legendary)
        except (ValueError, TypeError):
            max_legendary = None
        if max_legendary not in _MAX_LEGENDARY_VALUES:
            max_legendary = None

    max_stat_total = data.get("max_stat_total")
    if max_stat_total is not None:
        try:
            max_stat_total = int(max_stat_total)
        except (ValueError, TypeError):
            max_stat_total = None
        if max_stat_total not in _MAX_STAT_VALUES:
            max_stat_total = None

    fully_evolved_only = bool(data.get("fully_evolved_only", False))

    return RoomRules(
        max_legendary=max_legendary,
        max_stat_total=max_stat_total,
        fully_evolved_only=fully_evolved_only,
        preset_name="自定义",
    )


def validate_team(
    rules: RoomRules,
    team_data: list[dict],
) -> list[str]:
    """Validate a team against room rules. Returns list of error messages (empty = pass)."""
    errors: list[str] = []

    if rules.max_legendary is not None:
        legendary_count = sum(
            1 for p in team_data
            if p.get("is_legendary") or p.get("is_mythical")
        )
        if legendary_count > rules.max_legendary:
            if rules.max_legendary == 0:
                errors.append("本房间禁止使用传说/幻之宝可梦")
            else:
                errors.append(
                    f"传说/幻之宝可梦最多 {rules.max_legendary} 只"
                    f"（当前 {legendary_count} 只）"
                )

    if rules.max_stat_total is not None:
        for p in team_data:
            total = p.get("total", 0)
            if total > rules.max_stat_total:
                errors.append(
                    f"#{p.get('id', '?')} 种族值 {total} 超过上限 {rules.max_stat_total}"
                )

    if rules.fully_evolved_only:
        for p in team_data:
            if not p.get("is_fully_evolved"):
                errors.append(
                    f"#{p.get('id', '?')} 不是最终进化形态"
                )

    return errors
