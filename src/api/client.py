import asyncio

import httpx

from src.config import Config


class RateLimitedClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._semaphore = asyncio.Semaphore(1)
        self._interval = 1.0 / config.requests_per_second
        self._last_request_time = 0.0
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "RateLimitedClient":
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._config.http_timeout),
            follow_redirects=True,
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
            ),
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _wait_for_rate_limit(self) -> None:
        async with self._semaphore:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self._interval:
                await asyncio.sleep(self._interval - elapsed)
            self._last_request_time = asyncio.get_event_loop().time()

    async def get_json(self, url: str) -> dict:
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with.")

        for attempt in range(self._config.max_retries):
            await self._wait_for_rate_limit()
            try:
                response = await self._client.get(url)
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                if attempt == self._config.max_retries - 1:
                    raise
                delay = self._config.retry_base_delay * (2 ** attempt)
                print(f"  Retry {attempt + 1}/{self._config.max_retries} "
                      f"for {url}: {exc}")
                await asyncio.sleep(delay)

        raise RuntimeError(f"Failed after {self._config.max_retries} retries")

    async def download_bytes(self, url: str) -> bytes:
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with.")

        for attempt in range(self._config.max_retries):
            await self._wait_for_rate_limit()
            try:
                response = await self._client.get(url)
                response.raise_for_status()
                return response.content
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                if attempt == self._config.max_retries - 1:
                    raise
                delay = self._config.retry_base_delay * (2 ** attempt)
                print(f"  Retry {attempt + 1}/{self._config.max_retries} "
                      f"for {url}: {exc}")
                await asyncio.sleep(delay)

        raise RuntimeError(f"Failed after {self._config.max_retries} retries")
