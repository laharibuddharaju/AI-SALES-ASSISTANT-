from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.db.session import Base, engine
from app.models import user, lead, conversation  # noqa: F401 — ensure models registered
from app.api.v1.chat import router as chat_router
from app.api.v1.auth import router as auth_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.leads import router as leads_router
from app.core.config import ALLOWED_ORIGINS

# NOTE: Schema is managed by Alembic migrations.
# Run: alembic upgrade head
# (Base.metadata.create_all is intentionally removed)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AI Sales Assistant",
    version="2.0.0",
    description="AI-powered sales assistant with JWT auth, LLM intent detection, and HubSpot CRM integration.",
)

# Rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — loaded from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": "2.0.0"}

# Root
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "AI Sales Assistant Backend Running"}

# Routers
app.include_router(auth_router,      prefix="/api/v1", tags=["Auth"])
app.include_router(chat_router,      prefix="/api/v1", tags=["Chat"])
app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])
app.include_router(approvals_router, prefix="/api/v1", tags=["Approvals"])
app.include_router(leads_router, prefix="/api/v1", tags=["Leads"])