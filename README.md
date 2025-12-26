# Disha – Mini AI Health Coach

Production-ready AI health coach with a WhatsApp-style chat, long-term memory, health protocol matching, and real WhatsApp Cloud API integration. Built for the Curelink Backend Engineer assignment.

> Repo is **public** as requested. A real WhatsApp bot is configured; testing requires adding allowed recipient numbers (not published to marketplace).

---

## Live Deployment
- Backend (FastAPI): `https://curelink-disha.onrender.com`
- Frontend: `https://curelink-disha-frontend.onrender.com` (Update with your actual frontend URL)
- WhatsApp Webhook: `https://curelink-disha.onrender.com/api/webhooks/whatsapp`

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
  - `ChatOrchestrator`: orchestrates onboarding, memory, protocol match, LLM calls. Includes **Emergency Detection** (detects medical emergencies and redirects to hospital/ambulance).
  - `ContextBuilder`: token-aware prompt assembly (profile, memories, protocols, sliding window).  
  - `MemoryManager`: Mem0-inspired long-term facts extraction.  
  - `ProtocolMatcher`: keyword/RAG-light health protocols.  
  - `WhatsApp webhook`: inbound via `/api/webhooks/whatsapp`; replies via Graph API with interactive buttons.  
  - `RateLimiter` and `ErrorHandler` middleware.  
- **Data**: MongoDB (user, messages, memories, protocols).  
- **LLM**: Pluggable (Gemini / OpenAI / Azure OpenAI) via factory + env. **Hinglish** support included.
- **WebSocket**: `/ws/chat/{user_id}` for typing indicator.

## LLM & Prompting Strategy
- **Providers**: Supports Google Gemini (default), OpenAI, and Azure OpenAI via a Factory pattern.
- **System Prompt**: A carefully crafted persona (Disha) that balances professional health guidance with warm, Hinglish-friendly WhatsApp communication.
- **Context Construction**:
  - **Dynamic Profile**: User data (age, weight, etc.) is injected into the system prompt to prevent redundant questions.
  - **Mem0-inspired Memory**: Facts like "allergic to peanuts" or "prefers evening workouts" are extracted and prioritized in the prompt.
  - **Protocol Injection**: Relevant health guidelines are injected only when keywords match, keeping the prompt clean.
  - **Sliding Window**: History is token-capped to maintain speed and cost-efficiency.

## Design Decisions
1. **MongoDB over SQL**: Chosen for the flexible `User` profile and `Memory` schema. As the bot learns more about a user, the data structure evolves; MongoDB handles this without complex migrations.
2. **Greedy Onboarding**: Instead of a rigid step-by-step form, the bot uses LLM-powered extraction to "catch" multiple details in one message (e.g., "I'm Niketan, 28, looking to lose weight").
3. **Safety Guardrails**: A dedicated emergency detector runs *before* the LLM to catch keywords like "chest pain" or "suicide" and provides immediate, non-AI medical instructions.

## Trade-offs & "If I had more time..."
- **Redis**: Currently using MongoDB for everything. With more time, I'd add Redis for session caching and rate-limit tracking.
- **Vector Search**: Using keyword-based protocol matching. For a larger knowledge base, I would implement ChromaDB/Pinecone for semantic RAG.
- **Streaming**: Responses are delivered as a single block. Implementing Server-Sent Events (SSE) would improve the "real-time" feel on the web UI.
- **Automated Testing**: While manually tested, I'd add a full suite of integration tests for the `ChatOrchestrator` using `pytest-asyncio`.

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
