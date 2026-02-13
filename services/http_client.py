# services/http_client.py
import httpx
from config.settings import settings

async def get_client(token: str = None) -> httpx.AsyncClient:
    """Get shared async HTTP client with optional Bearer Token"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    return httpx.AsyncClient(
        timeout=settings.REQUEST_TIMEOUT,
        follow_redirects=True,
        headers=headers
    )