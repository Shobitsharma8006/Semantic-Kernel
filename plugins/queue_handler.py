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
        # INITIALIZE final_log here to prevent NameError
        final_log = "No items processed" 
        
        async with await get_client() as client:
            for pid, wid in zip(project_ids, workbook_ids):
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
                    res = await client.post(
                        f"{settings.ASSESSMENT_API_URL}/api/assessment", 
                        json={"project_id": pid, "workbook_id": wid, "run_id": run_id},
                        timeout=60.0
                    )
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
                    res = await client.post(
                        f"{settings.PARSING_API_URL}/parse-xml", 
                        json={"project_id": pid, "workbook_id": wid, "run_id": run_id},
                        timeout=60.0
                    )
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
                    res = await client.post(
                        f"{settings.MAPPING_API_URL}/mapping", 
                        json={"project_id": pid, "workbook_id": wid, "run_id": run_id},
                        timeout=60.0
                    )
                    res.raise_for_status()
                    project_status["steps"]["mapping"] = "COMPLETED"
                    project_status["final_status"] = "SUCCESS"
                except Exception as e:
                    project_status["steps"]["mapping"] = "FAILED"
                    project_status["final_status"] = "WARNING"
                    project_status["error_details"] = f"Mapping Error: {str(e)}"

                detailed_results.append(project_status)

            # --- CONSTRUCT FINAL LOG TEXT AFTER LOOP ---
            if detailed_results:
                log_lines = []
                for res in detailed_results:
                    icon = "✅" if res["final_status"] == "SUCCESS" else "❌"
                    if res["final_status"] == "WARNING": icon = "⚠️"
                    log_lines.append(f"{icon} Project {res['project_id']}: {res['final_status']}")
                final_log = "\n".join(log_lines)

            # --- LOG TO MONGODB ---
            log_payload = {
                "project_name": project_ids[0] if project_ids else "Batch",
                "run_id": run_id,
                "agent_name": "Semantic Kernel Queue Agent",
                "log_level": "INFO",
                "message": "Batch process summary",
                "project_id": project_ids[0] if project_ids else "",
                "workbook_id": workbook_ids[0] if workbook_ids else "",
                "details": {
                    "log_content": final_log, # Now guaranteed to be defined
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "COMPLETED"
                }
            }
            
            try:
                # Update endpoint to /logs
                await client.post(f"{settings.MONGODB_LOG_API_URL}/api/records/logs", json=log_payload)
            except Exception as e:
                print(f"Logging Error: {e}")

        return detailed_results