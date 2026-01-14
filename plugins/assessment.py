from semantic_kernel.functions import kernel_function
import httpx
from config.settings import settings
from services.http_client import get_client


class AssessmentPlugin:
    
    @kernel_function(
        name="run_assessment",
        description="""
        VERY IMPORTANT: This must be the FIRST step before any other actions.
        Call this function ONLY when you have BOTH project_id and workbook_id.
        This function calls the assessment API first.
        Only continue to other steps if this succeeds.
        """
    )
    async def run_assessment(
        self,
        project_id: str,
        workbook_id: str,
        run_id: str  # Add run_id parameter
    ) -> str:
        """
        Required parameters:
        - project_id: must be valid UUID
        - workbook_id: must be valid UUID
        - run_id: must be valid UUID
        Returns success message or detailed error
        """
        if not project_id or not workbook_id:
            return "ERROR: Both project_id and workbook_id are required. Ask user to provide them."
        
        payload = {
            "project_id": project_id,
            "workbook_id": workbook_id,
            "run_id": run_id  
        }
        
        try:
            async with await get_client() as client:
                response = await client.post(
                    settings.ASSESSMENT_API_URL + "/api/assessment",
                    json=payload,
                    timeout=60.0,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                
                # SUCCESS: Only show status, NO result body
                return f"ASSESSMENT SUCCESS! Status: {response.status_code}"
                    
        except httpx.HTTPStatusError as e:
            # FAILED: Only show status, NO error body
            return f"ASSESSMENT FAILED: HTTP {e.response.status_code}"
            
        except Exception as e:
            return f"ASSESSMENT CRITICAL ERROR: {str(e)}"