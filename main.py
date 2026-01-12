# main.py

import traceback
import uuid
from typing import List
from fastapi import FastAPI, HTTPException
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory

# AI Service Imports
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

# Local Imports
from config.settings import settings 
from config.prompts import SYSTEM_PROMPT 
from kernel.kernel_setup import create_kernel
# IMPORTANT: Ensure QueueRequest is added to models/schemas.py
from models.schemas import ChatRequest, ChatResponse, QueueRequest 
from plugins.queue_handler import QueuePlugin 

app = FastAPI(title="Semantic Agent - Assessment First")

kernel: Kernel = None
chat_history: ChatHistory = ChatHistory()

# Initialize the plugin for direct use
queue_plugin = QueuePlugin()

@app.on_event("startup")
async def startup_event():
    global kernel
    try:
        # Check if the key is actually loaded (masked for safety)
        key = settings.OPENROUTER_API_KEY
        if not key:
            print("ERROR: OPENROUTER_API_KEY is empty! Check your .env file.")
        else:
            masked_key = f"{key[:10]}...{key[-5:]}"
            print(f"Loaded API Key: {masked_key}")

        kernel = await create_kernel()
        
        # Load the prompt from config/prompts.py
        chat_history.add_system_message(SYSTEM_PROMPT)
        
        print("Kernel initialized successfully")
    except Exception as e:
        print(f"Kernel initialization failed: {str(e)}")
        raise

# --- NEW SHORT & FANCY ENDPOINT ---
@app.post("/invoke-batch")
async def invoke_batch(request: QueueRequest):
    """
    Directly invokes the batch processing queue.
    Short, Semantic Kernel-aligned naming.
    """
    # Generate a run ID for tracking
    run_id = str(uuid.uuid4())
    print(f"Invoking Batch | Run ID: {run_id}")

    # 1. Extract the lists from the request body
    project_ids = [item.project_id for item in request.items]
    workbook_ids = [item.workbook_id for item in request.items]

    if not project_ids:
        return {"success": False, "message": "No items provided for batch invoke", "run_id": run_id}

    try:
        # 2. Call the plugin logic directly
        result_log = await queue_plugin.process_items_queue(
            project_ids=project_ids, 
            workbook_ids=workbook_ids
        )

        print(f"Batch Invocation Complete | Run ID: {run_id}")

        return {
            "success": True,
            "run_id": run_id,
            "processed_count": len(project_ids),
            "log": result_log 
        }

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"Batch Invocation Error [Run ID: {run_id}]:", error_detail)
        return {
            "success": False,
            "run_id": run_id,
            "error": str(e)
        }

# --- EXISTING CHAT ENDPOINT ---
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if kernel is None:
        raise HTTPException(status_code=503, detail="Kernel not initialized yet")

    # Generate a unique Run ID for this execution
    run_id = str(uuid.uuid4())
    print(f"Processing Chat Run ID: {run_id}")

    try:
        chat_history.add_user_message(request.message)

        # Get the chat service (OpenRouter/OpenAI)
        chat_service = kernel.get_service("openrouter-chat", type=OpenAIChatCompletion)

        # Configure execution settings with Auto Tool Calling
        execution_settings = OpenAIPromptExecutionSettings(
            service_id="openrouter-chat",
            model_id="google/gemini-2.0-flash-exp:free", 
            temperature=0.0, 
            max_tokens=2000,
            # This enables the agent to automatically pick and execute tools
            function_choice_behavior=FunctionChoiceBehavior.Auto() 
        )

        # Get response from AI
        result = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=execution_settings,
            kernel=kernel 
        )

        final_answer = str(result).strip()

        chat_history.add_assistant_message(final_answer)

        # Return response with the generated run_id
        return ChatResponse(
            response=final_answer,
            success=True,
            run_id=run_id  # <--- Return Run ID
        )

    except Exception as e:
        error_detail = traceback.format_exc()
        # Log the specific run ID with the error for easier debugging
        print(f"Chat error [Run ID: {run_id}]:", error_detail)
        
        return ChatResponse(
            response=f"Processing error: {str(e)}",
            success=False,
            run_id=run_id  # <--- Return Run ID even on error
        )

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "kernel_initialized": kernel is not None,
        "history_message_count": len(chat_history.messages)
    }

@app.post("/reset")
async def reset_conversation():
    global chat_history
    chat_history = ChatHistory()
    # Re-add the system prompt after reset
    chat_history.add_system_message(SYSTEM_PROMPT)
    return {"message": "Conversation history reset (system prompt preserved)"}

if __name__ == "__main__":
    import uvicorn
    # Running on port 9000 as requested
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)