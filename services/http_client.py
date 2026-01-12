import httpx
from config.settings import settings


async def get_client() -> httpx.AsyncClient:
    """Get shared async HTTP client"""
    return httpx.AsyncClient(
        timeout=settings.REQUEST_TIMEOUT,
        follow_redirects=True
    )