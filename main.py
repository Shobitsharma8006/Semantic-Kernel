# main.py

import traceback
from fastapi import FastAPI, HTTPException
from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory

# AI Service Imports
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

# Local Imports
from config.settings import settings 
from config.prompts import SYSTEM_PROMPT  # <--- Imported from new file
from kernel.kernel_setup import create_kernel
from models.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Semantic Agent - Assessment First")

kernel: Kernel = None
chat_history: ChatHistory = ChatHistory()

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

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if kernel is None:
        raise HTTPException(status_code=503, detail="Kernel not initialized yet")

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
        # CRITICAL FIX: passed 'kernel=kernel' so it can execute functions
        result = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=execution_settings,
            kernel=kernel 
        )

        final_answer = str(result).strip()

        chat_history.add_assistant_message(final_answer)

        return ChatResponse(
            response=final_answer,
            success=True
        )

    except Exception as e:
        error_detail = traceback.format_exc()
        print("Chat error:", error_detail)
        
        return ChatResponse(
            response=f"Processing error: {str(e)}",
            success=False
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