from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    POKEMON_INFO = "pokemon_info"
    TOP_BY_STAT = "top_by_stat"
    FILTER_TYPE = "filter_type"
    FILTER_ABILITY = "filter_ability"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ParsedQuery:
    query_type: QueryType
    pokemon_name: str = ""
    stat: str = ""
    type_name: str = ""
    generation: int = 0
    ability_name: str = ""
    limit: int = 5


EXIT_WORDS = frozenset({"quit", "exit", "退出", "再见", "bye"})

STAT_KEYWORDS: dict[str, str] = {
    "最强": "total",
    "最厉害": "total",
    "种族值最高": "total",
    "strongest": "total",
    "最快": "speed",
    "速度最快": "speed",
    "fastest": "speed",
    "攻击最高": "attack",
    "物攻最高": "attack",
    "物攻": "attack",
    "特攻最高": "sp_attack",
    "特攻": "sp_attack",
    "防御最高": "defense",
    "最硬": "defense",
    "物防": "defense",
    "特防最高": "sp_defense",
    "特防": "sp_defense",
    "血最厚": "hp",
    "HP最高": "hp",
    "hp最高": "hp",
    "血量最高": "hp",
}

TYPE_KEYWORDS: dict[str, str] = {
    "一般": "normal",
    "普通": "normal",
    "格斗": "fighting",
    "飞行": "flying",
    "毒": "poison",
    "地面": "ground",
    "岩石": "rock",
    "虫": "bug",
    "幽灵": "ghost",
    "钢": "steel",
    "火": "fire",
    "火系": "fire",
    "水": "water",
    "水系": "water",
    "草": "grass",
    "草系": "grass",
    "电": "electric",
    "电系": "electric",
    "超能力": "psychic",
    "冰": "ice",
    "冰系": "ice",
    "龙": "dragon",
    "龙系": "dragon",
    "恶": "dark",
    "妖精": "fairy",
    "仙": "fairy",
    "normal": "normal",
    "fighting": "fighting",
    "flying": "flying",
    "poison": "poison",
    "ground": "ground",
    "rock": "rock",
    "bug": "bug",
    "ghost": "ghost",
    "steel": "steel",
    "fire": "fire",
    "water": "water",
    "grass": "grass",
    "electric": "electric",
    "psychic": "psychic",
    "ice": "ice",
    "dragon": "dragon",
    "dark": "dark",
    "fairy": "fairy",
}

GEN_KEYWORDS: dict[str, int] = {
    "第一世代": 1, "一代": 1, "gen1": 1, "第1世代": 1,
    "第二世代": 2, "二代": 2, "gen2": 2, "第2世代": 2,
    "第三世代": 3, "三代": 3, "gen3": 3, "第3世代": 3,
    "第四世代": 4, "四代": 4, "gen4": 4, "第4世代": 4,
    "第五世代": 5, "五代": 5, "gen5": 5, "第5世代": 5,
    "第六世代": 6, "六代": 6, "gen6": 6, "第6世代": 6,
    "第七世代": 7, "七代": 7, "gen7": 7, "第7世代": 7,
    "第八世代": 8, "八代": 8, "gen8": 8, "第8世代": 8,
    "第九世代": 9, "九代": 9, "gen9": 9, "第9世代": 9,
}

INTENT_INFO_KEYWORDS = frozenset({
    "的属性", "的种族值", "的数据", "的信息", "是什么", "stats", "info",
})

INTENT_FILTER_KEYWORDS = frozenset({
    "有哪些", "列出", "有多少", "which", "有什么",
})

INTENT_ABILITY_KEYWORDS = frozenset({
    "特性", "ability", "拥有", "会什么技能",
})
