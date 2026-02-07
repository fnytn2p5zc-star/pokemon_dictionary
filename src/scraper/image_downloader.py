from pathlib import Path

from src.api.client import RateLimitedClient
from src.api.endpoints import artwork_url, sprite_url
from src.config import Config


async def download_image(
    client: RateLimitedClient,
    url: str,
    dest: Path,
) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    try:
        data = await client.download_bytes(url)
        dest.write_bytes(data)
        return True
    except Exception as exc:
        print(f"  Failed to download {url}: {exc}")
        return False


async def download_pokemon_images(
    client: RateLimitedClient,
    config: Config,
    pokemon_id: int,
) -> bool:
    art_url = artwork_url(config, pokemon_id)
    spr_url = sprite_url(config, pokemon_id)
    art_dest = config.artwork_dir / f"{pokemon_id}.png"
    spr_dest = config.sprite_dir / f"{pokemon_id}.png"

    art_ok = await download_image(client, art_url, art_dest)
    spr_ok = await download_image(client, spr_url, spr_dest)

    return art_ok and spr_ok
