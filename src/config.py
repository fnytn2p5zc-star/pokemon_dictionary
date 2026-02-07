from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    base_url: str = "https://pokeapi.co/api/v2"
    artwork_url_template: str = (
        "https://raw.githubusercontent.com/PokeAPI/sprites"
        "/master/sprites/pokemon/other/official-artwork/{id}.png"
    )
    sprite_url_template: str = (
        "https://raw.githubusercontent.com/PokeAPI/sprites"
        "/master/sprites/pokemon/{id}.png"
    )
    data_dir: Path = Path("data")
    db_path: Path = Path("data/pokemon.db")
    artwork_dir: Path = Path("data/images/artwork")
    sprite_dir: Path = Path("data/images/sprites")
    requests_per_second: float = 2.0
    max_retries: int = 3
    retry_base_delay: float = 1.0
    max_concurrent_downloads: int = 5
    total_pokemon: int = 1025
    http_timeout: float = 30.0

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.artwork_dir.mkdir(parents=True, exist_ok=True)
        self.sprite_dir.mkdir(parents=True, exist_ok=True)
