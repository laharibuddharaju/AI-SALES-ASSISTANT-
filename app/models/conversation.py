from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(String, index=True, nullable=False)
    role       = Column(String, default="user")   # "user" | "assistant"
    message    = Column(Text, nullable=False)
    response   = Column(Text, nullable=True)       # AI response stored alongside
    intent     = Column(String, nullable=True)     # detected intent for analytics
    created_at = Column(DateTime(timezone=True), server_default=func.now())
