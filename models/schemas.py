# models/schemas.py

from pydantic import BaseModel
from typing import List

# --- Existing Chat Schemas (Optional, keep if you still want the chat feature) ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    success: bool = True
    run_id: str

# --- NEW Schemas for Queue Processing ---

class QueueItem(BaseModel):
    project_id: str
    workbook_id: str

class QueueRequest(BaseModel):
    # This accepts an array of items
    items: List[QueueItem]