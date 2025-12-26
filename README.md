# Disha – Mini AI Health Coach

Production-ready AI health coach with a WhatsApp-style chat, long-term memory, health protocol matching, and real WhatsApp Cloud API integration. Built for the Curelink Backend Engineer assignment.

> Repo is **public** as requested. A real WhatsApp bot is configured; testing requires adding allowed recipient numbers (not published to marketplace).

---

## Live Deployment
- Backend (FastAPI): `https://<your-backend-domain>` (update after deploy)
- Frontend: `https://<your-frontend-domain>` (update after deploy)
- WhatsApp Webhook: `https://<your-backend-domain>/api/webhooks/whatsapp`

To test WhatsApp:
1) Add your phone to the allowed/test list in Meta (since the number is not yet published).  
2) Send “Hi” to the configured WhatsApp number.  
3) Webhook verify token is in env (`WA_VERIFY_TOKEN`), and the bot uses the permanent access token from env.  
4) CTAs are rendered as WhatsApp interactive buttons; custom goals supported via “Other”.

---

## Quick Start (Local)
1) Prereqs: Docker + Docker Compose, Python 3.11+.  
2) Backend env: `cd backend && cp .env.example .env` (fill LLM keys, Mongo URI, WA keys).  
3) Run stack: `docker-compose up -d` (starts Mongo + FastAPI).  
4) Seed protocols: `cd backend && python scripts/seed_db.py`.  
5) Frontend: `cd frontend && python -m http.server 3000` → open `http://localhost:3000`.  
6) Swagger: `http://localhost:8000/docs` | Health: `http://localhost:8000/health`.

---

## Architecture (High Level)
- **Frontend**: Vanilla JS, WhatsApp-like UI, infinite scroll, typing indicator, quick replies, voice input.  
- **Backend (FastAPI)**:  
  - `ChatOrchestrator`: orchestrates onboarding, memory, protocol match, LLM calls.  
  - `ContextBuilder`: token-aware prompt assembly (profile, memories, protocols, sliding window).  
  - `MemoryManager`: Mem0-inspired long-term facts extraction.  
  - `ProtocolMatcher`: keyword/RAG-light health protocols.  
  - `WhatsApp webhook`: inbound via `/api/webhooks/whatsapp`; replies via Graph API with interactive buttons.  
  - `RateLimiter` and `ErrorHandler` middleware.  
- **Data**: MongoDB (user, messages, memories, protocols).  
- **LLM**: Pluggable (Gemini / OpenAI / Azure OpenAI) via factory + env.  
- **WebSocket**: `/ws/chat/{user_id}` for typing indicator.

### User Flow (Web/WhatsApp)
1) New user → onboarding: name → gender → age → goal (includes “Other” for custom goals) → weight/height if relevant.  
2) Messages persisted; cursor-based pagination for history.  
3) Context built with profile + memories + matched protocols + sliding window of recent chat.  
4) LLM generates reply; CTAs rendered as quick replies (web) or interactive buttons (WhatsApp).  
5) Long-term memories auto-extracted for personalization.

### Trade-offs vs PDF guidelines
- Database: Used MongoDB (flexible schema for evolving memories) instead of Postgres/SQLite. Rationale: faster iteration for document-like memories; acknowledge deviation from PDF preference.  
- Redis: Not added; can be introduced for protocol cache later.  
- Embeddings: Keyword/RAG-light today; semantic vector search is a future enhancement.  
- Streaming: Not implemented; responses returned whole for simplicity.

---

## API Surface (Core Endpoints)
- `POST /api/users` – create session user.  
- `GET /api/users/{user_id}` – profile/onboarding state.  
- `POST /api/messages` – send message, get AI reply.  
- `GET /api/messages` – cursor-based history (`before` cursor).  
- `GET /api/messages/latest` – latest batch for initial load.  
- `GET /health` – health check.  
- `WS /ws/chat/{user_id}` – typing indicator.  
- `GET|POST /api/webhooks/whatsapp` – Meta verify + inbound messages.

---

## Repo Structure
```
curelink/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, middleware, routers
│   │   ├── config.py             # Pydantic settings
│   │   ├── database.py           # Mongo (Motor) connection
│   │   ├── api/routes/           # chat, user, health, websocket, whatsapp_webhook
│   │   ├── services/             # chat_orchestrator, context_builder, memory_manager, protocol_matcher, onboarding, whatsapp
│   │   ├── models/               # user, message, memory, protocol
│   │   ├── schemas/              # Pydantic I/O schemas
│   │   ├── middleware/           # rate limiter, error handler
│   │   └── utils/                # token counter, validators
│   ├── scripts/                  # seed_db, reset_user, send_outbound, test_whatsapp, fix_subscription
│   ├── seeds/protocols.json
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── css/ (styles, chat, animations)
│   ├── js/  (app, api, chat, websocket, scroll, utils)
│   └── assets/ disha-avatar.svg
└── README.md
```

---

## Environment Variables (backend/.env.example)
- `MONGODB_URL` (Atlas URI)  
- `DATABASE_NAME`  
- `LLM_PROVIDER` = azure|openai|gemini  
- `AZURE_OPENAI_*` or `OPENAI_API_KEY` or `GEMINI_API_KEY`  
- `WA_ACCESS_TOKEN` (permanent, keep secret)  
- `WA_PHONE_NUMBER_ID`  
- `WA_VERIFY_TOKEN`  
- `CORS_ORIGINS`, `RATE_LIMIT_PER_MINUTE`, `MAX_CONTEXT_TOKENS`, etc.

---

## WhatsApp Bot (Live, not marketplace-published)
- Real WhatsApp Cloud API webhook wired to `/api/webhooks/whatsapp`.  
- Uses permanent access token from env; verify token from env.  
- Interactive buttons map from `[CTA: ...]` tags.  
- Testing: add your phone as an allowed recipient in Meta, then send “Hi” to the configured number.  
- Not published to marketplace yet; only allowed/test numbers can message the bot.

---

## Deployment Notes
1) Backend: Render/Railway/Fly/etc. Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.  
2) Env vars: set all secrets in host env (no secrets in repo).  
3) Webhook: set callback to `https://<your-backend-domain>/api/webhooks/whatsapp`; verify token matches env.  
4) DB: Use MongoDB Atlas (recommended).  
5) Frontend: host statically (Vercel/Netlify/Render static); set API base URL to backend.  
6) Health check: `/health`; docs: `/docs`.

---

## Testing
- Manual: Onboarding flow (name-first, gender, age, goal with “Other”), WhatsApp CTA buttons, long messages, rate limit.  
- Suggested (time-permitting): add pytest for onboarding extractors and chat happy-path.

---

## Future Enhancements
- Streaming responses (SSE).  
- Semantic memory with embeddings.  
- Redis caching for protocol/memory lookups.  
- Additional languages and transliteration.  
- Proactive nudges and analytics.

---

## License
For assignment purposes.
