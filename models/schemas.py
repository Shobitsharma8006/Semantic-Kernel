from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    # You can add more fields later: conversation_id, user_id, etc.


class ChatResponse(BaseModel):
    response: str
    success: bool = True