# AI Sales Assistant v2.0

A production-grade AI assistant for B2B sales teams with JWT auth, LLM intent detection, HubSpot CRM integration, conversation memory, and an analytics dashboard.

---

## Project Structure

```
ai-sales-assistant/
│
├── app/                          # Backend (FastAPI)
│   ├── api/v1/
│   │   ├── auth.py               # Register, Login, Refresh
│   │   ├── chat.py               # Chat endpoint (LLM intent + entity)
│   │   └── analytics.py          # Analytics dashboard API
│   ├── core/
│   │   ├── config.py             # All env vars + startup validation
│   │   ├── security.py           # bcrypt + JWT (access + refresh tokens)
│   │   └── logger.py
│   ├── db/session.py             # SQLAlchemy + get_db dependency
│   ├── models/                   # User, Lead, Conversation, PendingApproval
│   ├── services/
│   │   ├── intent_service.py     # LLM intent classification (regex fallback)
│   │   ├── entity_service.py     # Entity extraction (email, phone, company...)
│   │   ├── action_service.py     # CRUD actions: create/update/delete/show leads
│   │   ├── crm_service.py        # HubSpot CRM (create + update contact)
│   │   ├── vector_service.py     # Conversation memory (ChromaDB / SQLite FTS5)
│   │   └── approval_service.py   # Human-in-the-loop (DB-persisted approvals)
│   ├── schemas/                  # Pydantic request/response models
│   └── main.py                   # App entry point (CORS, rate limiting)
│
├── migrations/                   # Alembic database migrations
├── .env.example                  # All environment variables documented
├── requirements.txt
├── start.ps1                     # ← Recommended startup script
├── start.bat
└── Dockerfile
```

---

## Prerequisites

- **Python 3.9–3.13** (Python 3.14 supported but some packages have limited wheels)
- **pip**, **Git**
- **Node.js 18+** (for frontend)

---

## ⚡ Quick Start (Recommended)

### 1. Clone & set up environment

```powershell
git clone <repository-url>
cd ai-sales-assistant

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```powershell
copy .env.example .env
```

Edit `.env` — at minimum set `SECRET_KEY`:
```bash
# Generate a secure key:
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start the server

```powershell
# Option A — Smart startup script (auto-detects port, runs migrations)
.\start.ps1

# Option B — Direct
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Access API docs

```
http://127.0.0.1:8000/docs
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/register` | ❌ | Create account |
| POST | `/api/v1/login` | ❌ | Get access + refresh tokens |
| POST | `/api/v1/refresh` | ❌ | Renew access token |
| POST | `/api/v1/chat` | ✅ Bearer | Natural language lead commands |
| GET | `/api/v1/analytics/summary` | ✅ Bearer | KPI overview |
| GET | `/api/v1/analytics/intent-distribution` | ✅ Bearer | Chat intent breakdown |
| GET | `/api/v1/analytics/leads-over-time` | ✅ Bearer | Daily lead creation |
| GET | `/health` | ❌ | Health check |

### Sample Chat Commands

```json
POST /api/v1/chat
Authorization: Bearer <token>

{"user_id": "1", "channel": "chat", "message": "Create a lead with email john@acme.com"}
{"user_id": "1", "channel": "chat", "message": "Show me all leads"}
{"user_id": "1", "channel": "chat", "message": "Update john@acme.com status to qualified"}
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | JWT signing key (generate with `secrets.token_hex(32)`) |
| `DATABASE_URL` | ✅ | SQLite: `sqlite:///./aisales.db` · PostgreSQL for production |
| `HUBSPOT_API_KEY` | ⚪ | HubSpot Private App key for CRM sync |
| `OPENAI_API_KEY` | ⚪ | OpenAI key for LLM intent classification (regex fallback if absent) |
| `ALLOWED_ORIGINS` | ⚪ | Comma-separated CORS origins (default: localhost:3000,localhost:5173) |

---

## Database Migrations (Alembic)

```powershell
# Apply all migrations (done automatically by start.ps1)
.\venv\Scripts\alembic.exe upgrade head

# After changing a model — generate new migration
.\venv\Scripts\alembic.exe revision --autogenerate -m "describe change"
.\venv\Scripts\alembic.exe upgrade head

# Rollback one step
.\venv\Scripts\alembic.exe downgrade -1
```

---

## Frontend Setup (React)

```powershell
cd ai-sales-assistant-frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## Docker (Optional)

```bash
docker build -t ai-sales-assistant .
docker run -p 8000:8000 --env-file .env ai-sales-assistant
```

---

## Key Features

| Feature | Status |
|---------|--------|
| JWT auth (access + refresh tokens) | ✅ |
| bcrypt password hashing | ✅ |
| LLM intent classification (OpenAI / regex fallback) | ✅ |
| Entity extraction (email, phone, company, deal value) | ✅ |
| Lead CRUD (create / update / delete / show) | ✅ |
| HubSpot CRM sync (create + update contact) | ✅ |
| Conversation memory (ChromaDB / SQLite FTS5 fallback) | ✅ |
| Human-in-the-loop approval (DB-persisted) | ✅ |
| Analytics dashboard API (4 endpoints) | ✅ |
| Rate limiting (slowapi) | ✅ |
| Alembic DB migrations | ✅ |
| Docker-ready | ✅ |

---

## Port Conflict Resolution

If port 8000 is in use from a previous session:
```powershell
# Use start.ps1 — it auto-detects and switches to port 8001
.\start.ps1

# Or explicitly use port 8001
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Port 8000 will be automatically freed when you restart your IDE/terminal.