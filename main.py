from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import traceback

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
from semantic_kernel.contents import ChatHistory

from kernel.kernel_setup import create_kernel
from models.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Semantic Agent - Assessment First")

kernel: Kernel = None
chat_history: ChatHistory = ChatHistory()

SYSTEM_PROMPT = """
You are a strict workflow agent. Follow these rules EXACTLY and in this order:

1. YOU MUST HAVE BOTH project_id and workbook_id BEFORE doing ANYTHING else
   - They are UUID format like: c1e2cc14-0fce-436c-bc2d-d13c928fec4d
   - If user didn't give both IDs → ASK for them clearly, do NOT guess
   - Do NOT make up IDs, do NOT use defaults

2. FIRST STEP - ALWAYS run assessment first
   - Use function: run_assessment(project_id, workbook_id)
   - This MUST be the very first function call

3. ONLY AFTER successful assessment
   - You may proceed to parsing, other APIs or final answer

4. If assessment fails → stop immediately and tell user clearly what went wrong
   - Do NOT continue to other steps

5. Be very clear in your responses about:
   - Which step you are performing
   - What IDs you are using
   - Whether assessment succeeded or failed

Never skip steps. Never assume missing information.
"""

@app.on_event("startup")
async def startup_event():
    global kernel
    try:
        kernel = await create_kernel()
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

        chat_service = kernel.get_service("openrouter-chat", type=OpenAIChatCompletion)

        execution_settings = OpenAIPromptExecutionSettings(
            service_id="openrouter-chat",
            model="openai/gpt-4o-mini",  # change here if you want different model
            temperature=0.3,
            max_tokens=1800,
            tool_call_behavior="auto_invoke_kernel_functions"
        )

        result = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=execution_settings
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
    chat_history.add_system_message(SYSTEM_PROMPT)
    return {"message": "Conversation history reset (system prompt preserved)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)