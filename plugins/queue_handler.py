import asyncio
import random
from typing import List, Dict, Any
from datetime import datetime

import httpx
from semantic_kernel.functions import kernel_function

from config.settings import settings
from services.http_client import get_client


class QueuePlugin:
    async def _post_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        json_data: Dict[str, Any],
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> httpx.Response:
        """
        Helper method to perform POST requests with exponential backoff retry logic.
        """
        for attempt in range(max_retries + 1):
            try:
                response = await client.post(url, json=json_data)
                response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if attempt == max_retries:
                    print(f"Final attempt failed for {url}. Error: {e}")
                    raise

                # Exponential backoff calculation: 1s, 2s, 4s...
                wait_time = base_delay * (2**attempt)
                print(
                    f"Attempt {attempt + 1} failed for {url}. Retrying in {wait_time}s... Error: {e}"
                )
                await asyncio.sleep(wait_time)

    @kernel_function(
        name="process_items_queue",
        description="Process items concurrently (bounded) and log results to CosmosDB and Monitoring Agent.",
    )
    async def process_items_queue(
        self,
        project_ids: List[str],
        workbook_ids: List[str],
        run_id: str,
        email: str,
        token: str = None,
    ) -> List[Dict[str, Any]]:
        detailed_results: List[Dict[str, Any]] = []
        log_lines: List[str] = []

        if not project_ids or not workbook_ids:
            return [{"error": "Missing ID lists"}]

        # Safety: keep the pairs aligned to the shortest list
        pairs = list(zip(project_ids, workbook_ids))
        if not pairs:
            return [{"error": "No valid project/workbook pairs found"}]

        # Concurrency controls (fallbacks if settings not present)
        max_concurrent = getattr(settings, "MAX_CONCURRENT_WORKBOOKS", 5)
        start_jitter = getattr(settings, "START_JITTER_SECONDS", 0.25)

        async with await get_client(token=token) as client:
            sem = asyncio.Semaphore(max_concurrent)

            async def process_one(i: int, pid: str, wid: str) -> Dict[str, Any]:
                """
                One workbook pipeline:
                Assessment -> Parsing -> Mapping
                Runs under a semaphore (bounded concurrency) and starts with a small jitter.
                """
                # Stagger start so all tasks don't hit downstream services at the exact same moment
                if start_jitter and start_jitter > 0:
                    await asyncio.sleep(random.uniform(0, start_jitter))

                async with sem:
                    project_status = {
                        "project_id": pid,
                        "workbook_id": wid,
                        "steps": {
                            "assessment": "PENDING",
                            "parsing": "SKIPPED",
                            "mapping": "SKIPPED",
                        },
                        "final_status": "PENDING",
                    }

                    file_label = f"file {i+1} ({pid})"
                    current_chain = [file_label]

                    # Step 1: Assessment
                    try:
                        await self._post_with_retry(
                            client,
                            f"{settings.ASSESSMENT_API_URL}/api/assessment",
                            {"project_id": pid, "workbook_id": wid, "run_id": run_id},
                        )
                        project_status["steps"]["assessment"] = "COMPLETED"
                        current_chain.append("assessment pass")

                        # Step 2: Parsing
                        try:
                            await self._post_with_retry(
                                client,
                                f"{settings.PARSING_API_URL}/parse-xml",
                                {"project_id": pid, "workbook_id": wid, "run_id": run_id},
                            )
                            project_status["steps"]["parsing"] = "COMPLETED"
                            current_chain.append("parsing pass")

                            # Step 3: Mapping
                            try:
                                await self._post_with_retry(
                                    client,
                                    f"{settings.MAPPING_API_URL}/mapping",
                                    {"project_id": pid, "workbook_id": wid, "run_id": run_id},
                                )
                                project_status["steps"]["mapping"] = "COMPLETED"
                                project_status["final_status"] = "SUCCESS"
                                current_chain.append("mapping pass")
                            except Exception as e:
                                # Mapping failed but previous steps succeeded
                                project_status["final_status"] = "WARNING"
                                current_chain.append(f"mapping error: {str(e)}")

                        except Exception as e:
                            # Parsing failed
                            project_status["final_status"] = "FAILED"
                            current_chain.append(f"parsing error: {str(e)}")

                    except Exception as e:
                        # Assessment failed
                        project_status["final_status"] = "FAILED"
                        current_chain.append(f"assessment error: {str(e)}")

                    # Notify monitoring agent per workbook (bounded + retry)
                    try:
                        await self._post_with_retry(
                            client,
                            settings.MONITORING_AGENT_URL + "/monitor/report",
                            {
                                "project_id": pid,
                                "workbook_id": wid,
                                "run_id": run_id,
                                "status": project_status["final_status"],
                            },
                        )
                    except Exception as monitor_err:
                        print(
                            f"Monitoring Agent notification failed for {pid} after retries: {monitor_err}"
                        )

                    return {
                        "project_status": project_status,
                        "log_line": " -> ".join(current_chain),
                    }

            # Create tasks for all selected workbooks
            tasks = [
                asyncio.create_task(process_one(i, pid, wid))
                for i, (pid, wid) in enumerate(pairs)
            ]

            # Run concurrently (bounded by semaphore). One failure won't stop others.
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in results:
                if isinstance(r, Exception):
                    # Unhandled task-level error
                    detailed_results.append({"error": str(r)})
                    log_lines.append(f"unhandled task error: {str(r)}")
                else:
                    detailed_results.append(r["project_status"])
                    log_lines.append(r["log_line"])

            # --- CosmosDB LOGGING (with retry) ---
            final_log_content = "\n".join(log_lines)
            log_payload = {
                "project_name": "Semantic-Kernel-Agent",
                "run_id": run_id,
                "status": "completed",
                "payload": {
                    "user_email": email,
                    "full_console_output": final_log_content,
                    "processed_items": detailed_results,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            try:
                await self._post_with_retry(
                    client,
                    f"{settings.COSMOSDB_API_URL}/api/records/semantic-kernel",
                    log_payload,
                )
            except Exception as e:
                print(f"Critical Logging Error after retries: {e}")

        return detailed_results
