from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class Lead(Base):
    __tablename__ = "leads"

    id           = Column(Integer, primary_key=True, index=True)
    email        = Column(String, unique=True, index=True, nullable=False)
    name         = Column(String, nullable=True)
    phone        = Column(String, nullable=True)
    company      = Column(String, nullable=True)
    source       = Column(String, default="chat")       # "chat" | "api" | "import"
    status       = Column(String, default="new")        # "new" | "contacted" | "qualified" | "closed"
    deal_value   = Column(Float, nullable=True)
    assigned_to  = Column(String, nullable=True)        # user_id of owner
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
