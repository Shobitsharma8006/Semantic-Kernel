from semantic_kernel.functions import kernel_function
import httpx
from services.http_client import get_client
from config.settings import settings


class ExternalApisPlugin:
    
    @kernel_function(
        description="Call external user API to get user information",
        name="get_user_info"
    )
    async def get_user_info(self, user_id: str) -> str:
        async with await get_client() as client:
            try:
                resp = await client.get(f"{settings.USER_API_URL}/{user_id}")
                return f"User API response: {resp.text}"
            except Exception as e:
                return f"User API error: {str(e)}"