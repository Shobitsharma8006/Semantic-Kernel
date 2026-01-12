# plugins/queue_handler.py

from typing import List
from semantic_kernel.functions import kernel_function
import httpx
from config.settings import settings
from services.http_client import get_client

class QueuePlugin:
    
    @kernel_function(
        name="process_items_queue",
        description="""
        Process a list (queue) of items sequentially. 
        For each project/workbook pair, it strictly follows the flow: 
        1. Run Assessment 
        2. If Assessment succeeds, Run Parsing.
        """
    )
    async def process_items_queue(
        self,
        project_ids: List[str],
        workbook_ids: List[str]
    ) -> str:
        """
        Takes lists of IDs and processes them one by one in order.
        """
        if not project_ids or not workbook_ids:
            return "ERROR: Missing ID lists."
            
        if len(project_ids) != len(workbook_ids):
            return "ERROR: Mismatch in number of project_ids and workbook_ids."

        results = []
        
        # Open one client session for the whole queue processing
        async with await get_client() as client:
            for i, (pid, wid) in enumerate(zip(project_ids, workbook_ids)):
                item_label = f"Item {i+1} ({pid})"
                
                # --- STEP 1: ASSESSMENT ---
                try:
                    assess_res = await client.post(
                        settings.ASSESSMENT_API_URL + "/api/assessment",
                        json={"project_id": pid, "workbook_id": wid},
                        timeout=60.0
                    )
                    assess_res.raise_for_status()
                except Exception as e:
                    results.append(f"❌ {item_label}: Assessment Failed ({str(e)}) - Skipping Parsing")
                    continue # Skip to next item in loop

                # --- STEP 2: PARSING (Only runs if Assessment passed) ---
                try:
                    parse_res = await client.post(
                        settings.PARSING_API_URL + "/parse-xml",
                        json={"project_id": pid, "workbook_id": wid},
                        timeout=60.0
                    )
                    parse_res.raise_for_status()
                    results.append(f"✅ {item_label}: Assessment OK -> Parsing OK")
                except Exception as e:
                    results.append(f"⚠️ {item_label}: Assessment OK -> Parsing Failed ({str(e)})")

        return "\n".join(results)