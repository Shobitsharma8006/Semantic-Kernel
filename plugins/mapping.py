# plugins/mapping.py

from semantic_kernel.functions import kernel_function
import httpx
from config.settings import settings
from services.http_client import get_client

class MappingPlugin:
    
    @kernel_function(
        name="run_mapping",
        description="""
        Call this function ONLY AFTER parsing is successful.
        It sends the project_id and workbook_id to the mapping API.
        """
    )
    async def run_mapping(
        self,
        project_id: str,
        workbook_id: str,
        run_id: str
    ) -> str:
        """
        Sends request to /mapping endpoint.
        """
        payload = {
            "project_id": project_id,
            "workbook_id": workbook_id,
            "run_id": run_id 
        }

        try:
            async with await get_client() as client:
                # Assuming base URL is handled in settings, or use the direct 127.0.0.1:9000
                response = await client.post(
                    settings.MAPPING_API_URL + "/mapping",
                    json=payload,
                    timeout=60.0,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                return f"MAPPING SUCCESS! Status: {response.status_code}"

        except httpx.HTTPStatusError as e:
            return f"MAPPING FAILED: HTTP {e.response.status_code}"
        except Exception as e:
            return f"MAPPING ERROR: {str(e)}"