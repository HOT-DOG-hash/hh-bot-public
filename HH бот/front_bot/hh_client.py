import httpx

BASE = "https://api.hh.ru"

class HHClient:
    def __init__(self, timeout=10):
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        self.client = httpx.AsyncClient(timeout=timeout, limits=limits, base_url=BASE)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.aclose()

    async def search(self, text: str, per_page: int = 5):
        r = await self.client.get("/vacancies", params={"text": text, "per_page": per_page})
        r.raise_for_status()
        return r.json()

    async def vacancy(self, vid: str):
        r = await self.client.get(f"/vacancies/{vid}")
        r.raise_for_status()
        return r.json()
