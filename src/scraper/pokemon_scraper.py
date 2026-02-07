import asyncio
import sqlite3
from typing import Any

from tqdm import tqdm

from src.api.client import RateLimitedClient
from src.api.endpoints import ability_url, pokemon_url, species_url, type_url
from src.api.parsers import (
    extract_ability_refs_from_pokemon,
    extract_species_info,
    extract_type_ids_from_pokemon,
    parse_ability,
    parse_stats,
    parse_type,
)
from src.config import Config
from src.db.repository import (
    mark_data_scraped,
    mark_images_downloaded,
    upsert_pokemon,
    upsert_type,
)
from src.models import Pokemon, PokemonAbility, PokemonType
from src.scraper.image_downloader import download_pokemon_images
from src.scraper.progress import get_pending_image_ids, get_pending_pokemon_ids


class PokemonScraper:
    def __init__(self, config: Config, conn: sqlite3.Connection) -> None:
        self._config = config
        self._conn = conn
        self._type_cache: dict[int, PokemonType] = {}
        self._ability_cache: dict[int, dict[str, Any]] = {}
        self._interrupted = False

    def request_stop(self) -> None:
        self._interrupted = True

    async def _fetch_type(
        self,
        client: RateLimitedClient,
        type_id: int,
    ) -> PokemonType:
        if type_id in self._type_cache:
            return self._type_cache[type_id]

        url = type_url(self._config, type_id)
        data = await client.get_json(url)
        ptype = parse_type(data)
        self._type_cache[type_id] = ptype
        upsert_type(self._conn, ptype)
        return ptype

    async def _fetch_ability(
        self,
        client: RateLimitedClient,
        ability_id: int,
    ) -> dict:
        if ability_id in self._ability_cache:
            return self._ability_cache[ability_id]

        url = ability_url(self._config, ability_id)
        data = await client.get_json(url)
        self._ability_cache[ability_id] = data
        return data

    async def _scrape_single(
        self,
        client: RateLimitedClient,
        pokemon_id: int,
    ) -> Pokemon | None:
        try:
            poke_url = pokemon_url(self._config, pokemon_id)
            poke_data = await client.get_json(poke_url)

            spec_url = species_url(self._config, pokemon_id)
            species_data = await client.get_json(spec_url)
            species_info = extract_species_info(species_data)

            type_refs = extract_type_ids_from_pokemon(poke_data)
            types: list[PokemonType] = []
            for ref in type_refs:
                ptype = await self._fetch_type(client, ref["id"])
                types.append(ptype)

            ability_refs = extract_ability_refs_from_pokemon(poke_data)
            abilities: list[PokemonAbility] = []
            for ref in ability_refs:
                ab_data = await self._fetch_ability(client, ref["id"])
                ability = parse_ability(
                    ab_data, ref["is_hidden"], ref["slot"],
                )
                abilities.append(ability)

            stats = parse_stats(poke_data)

            return Pokemon(
                id=pokemon_id,
                name_en=species_info["name_en"],
                name_zh_hans=species_info["name_zh_hans"],
                name_zh_hant=species_info["name_zh_hant"],
                name_ja=species_info["name_ja"],
                genus_zh=species_info["genus_zh"],
                types=tuple(types),
                stats=stats,
                abilities=tuple(abilities),
                height=poke_data.get("height", 0),
                weight=poke_data.get("weight", 0),
                generation=species_info["generation"],
                artwork_path=f"images/artwork/{pokemon_id}.png",
                sprite_path=f"images/sprites/{pokemon_id}.png",
            )
        except Exception as exc:
            print(f"  Error scraping Pokemon #{pokemon_id}: {exc}")
            return None

    async def scrape_data(
        self,
        start: int,
        end: int,
    ) -> None:
        pending = get_pending_pokemon_ids(self._conn, start, end)
        if not pending:
            print("All Pokemon data already scraped in this range.")
            return

        print(f"Scraping data for {len(pending)} Pokemon "
              f"({start}-{end}, {end - start + 1 - len(pending)} cached)...")

        async with RateLimitedClient(self._config) as client:
            progress = tqdm(pending, desc="Fetching data", unit="pokemon")
            for pokemon_id in progress:
                if self._interrupted:
                    print("\nInterrupted. Progress saved.")
                    break

                progress.set_postfix(id=pokemon_id)
                pokemon = await self._scrape_single(client, pokemon_id)
                if pokemon:
                    upsert_pokemon(self._conn, pokemon)
                    mark_data_scraped(self._conn, pokemon_id)

    async def download_images(
        self,
        start: int,
        end: int,
    ) -> None:
        pending = get_pending_image_ids(self._conn, start, end)
        if not pending:
            print("All images already downloaded in this range.")
            return

        print(f"Downloading images for {len(pending)} Pokemon...")

        async with RateLimitedClient(self._config) as client:
            progress = tqdm(pending, desc="Downloading images", unit="pokemon")
            for pokemon_id in progress:
                if self._interrupted:
                    print("\nInterrupted. Progress saved.")
                    break

                progress.set_postfix(id=pokemon_id)
                success = await download_pokemon_images(
                    client, self._config, pokemon_id,
                )
                if success:
                    mark_images_downloaded(self._conn, pokemon_id)

    async def run(
        self,
        start: int = 1,
        end: int | None = None,
        skip_images: bool = False,
    ) -> None:
        actual_end = end or self._config.total_pokemon
        self._config.ensure_dirs()

        await self.scrape_data(start, actual_end)

        if not skip_images and not self._interrupted:
            await self.download_images(start, actual_end)

        if not self._interrupted:
            print("Done!")
