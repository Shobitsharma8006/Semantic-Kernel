# plugins/queue_handler.py

from typing import List, Dict, Any
from datetime import datetime
from semantic_kernel.functions import kernel_function
from config.settings import settings
from services.http_client import get_client

class QueuePlugin:
    
    @kernel_function(
        name="process_items_queue",
        description="Process a list of items sequentially and log structured results."
    )
    async def process_items_queue(
        self,
        project_ids: List[str],
        workbook_ids: List[str],
        run_id: str
    ) -> List[Dict[str, Any]]:
        detailed_results = []
        
        async with await get_client() as client:
            for pid, wid in zip(project_ids, workbook_ids):
                # Initialize structured tracking for this specific project
                project_status = {
                    "project_id": pid,
                    "workbook_id": wid,
                    "steps": {
                        "assessment": "PENDING",
                        "parsing": "SKIPPED",
                        "mapping": "SKIPPED"
                    },
                    "final_status": "PENDING",
                    "error_details": None
                }

                # --- STEP 1: ASSESSMENT ---
                try:
                    res = await client.post(f"{settings.ASSESSMENT_API_URL}/api/assessment", 
                                            json={"project_id": pid, "workbook_id": wid, "run_id": run_id})
                    res.raise_for_status()
                    project_status["steps"]["assessment"] = "COMPLETED"
                except Exception as e:
                    project_status["steps"]["assessment"] = "FAILED"
                    project_status["final_status"] = "FAILED"
                    project_status["error_details"] = f"Assessment Error: {str(e)}"
                    detailed_results.append(project_status)
                    continue

                # --- STEP 2: PARSING ---
                project_status["steps"]["parsing"] = "PENDING"
                try:
                    res = await client.post(f"{settings.PARSING_API_URL}/parse-xml", 
                                            json={"project_id": pid, "workbook_id": wid, "run_id": run_id})
                    res.raise_for_status()
                    project_status["steps"]["parsing"] = "COMPLETED"
                except Exception as e:
                    project_status["steps"]["parsing"] = "FAILED"
                    project_status["final_status"] = "FAILED"
                    project_status["error_details"] = f"Parsing Error: {str(e)}"
                    detailed_results.append(project_status)
                    continue

                # --- STEP 3: MAPPING ---
                project_status["steps"]["mapping"] = "PENDING"
                try:
                    res = await client.post(f"{settings.MAPPING_API_URL}/mapping", 
                                            json={"project_id": pid, "workbook_id": wid, "run_id": run_id})
                    res.raise_for_status()
                    project_status["steps"]["mapping"] = "COMPLETED"
                    project_status["final_status"] = "SUCCESS"
                except Exception as e:
                    project_status["steps"]["mapping"] = "FAILED"
                    project_status["final_status"] = "WARNING"
                    project_status["error_details"] = f"Mapping Error: {str(e)}"

                detailed_results.append(project_status)

            # --- LOG TO MONGODB ---
            log_payload = {
                "project_name": "Semantic-Kernel-Agent",
                "run_id": run_id,
                "status": "completed",
                "payload": {
                    "total_projects": len(project_ids),
                    "execution_summary": detailed_results, # Each project is now its own object
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            try:
                await client.post(f"{settings.MONGODB_LOG_API_URL}/api/records/validation", json=log_payload)
            except Exception as e:
                print(f"Logging Error: {e}")

        return detailed_results