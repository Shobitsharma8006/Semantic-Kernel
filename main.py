
import traceback
import uuid
import asyncio  # Background tasks ke liye zaroori hai
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments

# AI Service Imports
from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

# Local Imports
from config.settings import settings 
from config.prompts import SYSTEM_PROMPT 
from kernel.kernel_setup import create_kernel
from models.schemas import ChatRequest, ChatResponse, QueueRequest 
from plugins.queue_handler import QueuePlugin 
from services.http_client import get_client

app = FastAPI(title="Semantic Agent - Assessment First")

# --- CORS Configuration ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kernel: Kernel = None
chat_history: ChatHistory = ChatHistory()
queue_plugin = QueuePlugin()

@app.on_event("startup")
async def startup_event():
    global kernel
    try:
        kernel = await create_kernel()
        chat_history.add_system_message(SYSTEM_PROMPT)
        print("Application startup complete.")
    except Exception as e:
        print(f"Kernel initialization failed: {str(e)}")
        raise

@app.post("/invoke-batch")
async def invoke_batch(request: QueueRequest, authorization: Optional[str] = Header(None)):
    """
    Turant response deta hai aur processing background mein chalti hai.
    """
    run_id = str(uuid.uuid4())
    user_email = request.email
    token = authorization.replace("Bearer ", "") if authorization else None
    
    print(f"Invoking Batch | Run ID: {run_id} | User: {user_email}")

    project_ids = [item.project_id for item in request.items]
    workbook_ids = [item.workbook_id for item in request.items]

    if not project_ids:
        return {"success": False, "message": "No items provided", "run_id": run_id}

    try:
        # Background task create kiya gaya hai taaki Postman ko turant reply mile
        asyncio.create_task(
            queue_plugin.process_items_queue(
                project_ids=project_ids, 
                workbook_ids=workbook_ids,
                run_id=run_id,
                email=user_email,
                token=token 
            )
        )

        # Postman ko milne wala instant response
        return {
            "success": True,
            "message": "Batch processing started in background",
            "run_id": run_id,
            "processed_count": len(project_ids),
            "user_logged": user_email
        }

    except Exception as e:
        return {"success": False, "run_id": run_id, "error": str(e)}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, authorization: Optional[str] = Header(None)):
    if kernel is None:
        raise HTTPException(status_code=503, detail="Kernel not initialized yet")

    run_id = str(uuid.uuid4())
    token = authorization.replace("Bearer ", "") if authorization else None

    # Inject token into KernelArguments
    args = KernelArguments(token=token)

    try:
        chat_history.add_user_message(request.message)
        chat_service = kernel.get_service("azure-chat")

        execution_settings = OpenAIPromptExecutionSettings(
            service_id="azure-chat",
            model_id=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            temperature=0.0,
            max_tokens=2000,
            function_choice_behavior=FunctionChoiceBehavior.Auto()
        )

        result = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=execution_settings,
            kernel=kernel,
            arguments=args
        )

        final_answer = str(result).strip()
        chat_history.add_assistant_message(final_answer)

        return ChatResponse(response=final_answer, success=True, run_id=run_id)

    except Exception as e:
        return ChatResponse(response=f"Processing error: {str(e)}", success=False, run_id=run_id)

@app.get("/health")
async def health_check():
    return {"status": "ok", "kernel_initialized": kernel is not None}

@app.post("/reset")
async def reset_conversation():
    global chat_history
    chat_history = ChatHistory()
    chat_history.add_system_message(SYSTEM_PROMPT)
    return {"message": "Reset complete"}

if __name__ == "__main__":
    import uvicorn
    # Port 9000 use kiya gaya hai jaisa aapke setup mein tha
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)