from semantic_kernel.functions import kernel_function
import httpx
from config.settings import settings
from services.http_client import get_client

class ParsingPlugin:
    
    @kernel_function(
        name="parse_xml_data",
        description="""
        Call this function ONLY AFTER the assessment is successful.
        It sends the project_id and workbook_id to the parsing API.
        """
    )
    async def parse_xml_data(
        self,
        project_id: str,
        workbook_id: str
    ) -> str:
        """
        Sends request to /parse-xml endpoint.
        """
        payload = {
            "project_id": project_id,
            "workbook_id": workbook_id
        }

        try:
            # We use the shared http client
            async with await get_client() as client:
                response = await client.post(
                    settings.PARSING_API_URL + "/parse-xml",
                    json=payload,
                    timeout=60.0,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                
                # SUCCESS: Only show status, NO response text
                return f"PARSING SUCCESS! Status: {response.status_code}"

        except httpx.HTTPStatusError as e:
            # FAILED: Only show status, NO error body
            return f"PARSING FAILED: HTTP {e.response.status_code}"

        except Exception as e:
            return f"PARSING ERROR: {str(e)}"

    @kernel_function(name="clean_response")
    async def clean_response(self, raw_text: str) -> str:
        return raw_text.strip()