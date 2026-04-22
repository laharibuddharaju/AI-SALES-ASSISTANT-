from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: str
    channel: str
    message: str