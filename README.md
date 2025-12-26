# Disha - Mini AI Health Coach 🩺🤖

Disha is a production-grade AI Health Coach designed like a WhatsApp chat interface. It provides personalized health advice, remembers user facts over long periods (Mem0-inspired), and follows common health protocols.

Built for the Curelink Backend Engineer assignment.

![Disha Chat UI](frontend/assets/disha-avatar.svg) <!-- Note: Replace with actual screenshot if available -->

## ✨ Key Features

- **WhatsApp-style UI**: Familiar, mobile-first chat interface with autoscrolling, typing indicators, and message timestamps.
- **Smart Context Management**: Handles context overflow using a sliding window strategy and token-aware context assembly.
- **Multi-Provider LLM Support**: Configurable to use **Google Gemini 1.5**, **OpenAI GPT-4o**, or **Azure OpenAI**.
- **Long-Term Memory (Mem0-inspired)**: Automatically extracts and stores key facts about the user (conditions, goals, preferences) to provide personalized advice in future sessions.
- **Health Protocol Matching**: Maps user queries to specific health guidelines (Fever, PCOS, Diabetes, etc.) using a RAG-light keyword matching system.
- **Conversational Onboarding**: A friendly 4-step flow to get to know the user before diving into coaching.
- **Robust Backend**: Built with FastAPI, MongoDB (Motor), and Pydantic for high performance and type safety.
- **Pagination**: Efficient cursor-based infinite scrolling for message history.

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+ (if running locally without Docker)
- API Key for Gemini, OpenAI, or Azure OpenAI

### 2. Setup Environment
Copy the `.env.example` to `.env` in the `backend` folder and fill in your credentials.

```bash
cd backend
cp .env.example .env
# Edit .env with your LLM API keys
```

### 3. Run with Docker (Recommended)
This will start MongoDB and the FastAPI backend.

```bash
docker-compose up -d
```

### 4. Seed Protocol Data
Populate the database with initial health guidelines:

```bash
cd backend
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python scripts/seed_db.py
```

### 5. Launch Frontend
Since the frontend is Vanilla JS/HTML, you can serve it with any static server.

**Using Python:**
```bash
cd frontend
python -m http.server 3000
```
Then open `http://localhost:3000` in your browser.

---

## 🏗️ Architecture & Design Decisions

### **Memory Management**
Instead of just sending a raw chat history, Disha uses a multi-level memory system:
1. **User Profile**: Structured facts (Name, Age, Gender, Weight, Height, Primary Goals).
2. **Semantic Memories**: LLM-extracted facts about health conditions, allergies, and lifestyle patterns.
3. **Conversation History**: Recent messages managed with a token-capped sliding window (approx. 8,000 tokens context).

### **Clean Architecture**
The project follows a modular service-oriented architecture:
- **Orchestration Layer**: `ChatOrchestrator` manages the complex flow between LLM, Memory, and Protocols.
- **Service Layer**: Dedicated services for `MemoryManager`, `ProtocolMatcher`, `ContextBuilder`, and `OnboardingService`.
- **API Layer**: Clean FastAPI routes with Pydantic validation and global error handling.
- **Frontend**: Modular ES6 JavaScript with a clean separation of UI rendering and API logic.

### **Database Choice: MongoDB**
I chose MongoDB for its flexibility with document schemas. As an AI coach evolves, the "memories" we store about a user will change. Document-based storage handles this much better than strict relational schemas.

### **LLM abstraction**
The backend uses a Factory Pattern for LLM providers. This allows the system to switch between Gemini, OpenAI, or Azure OpenAI seamlessly via environment variables without changing core logic.

### **Prompt Engineering**
The system prompt defines "Disha" as a warm, Indian AI health coach. It includes specific instructions on tone, empathy, and safety (NEVER giving emergency advice).

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python), Motor (Async MongoDB), Pydantic V2
- **Frontend**: Vanilla JavaScript, HTML5, CSS3 (No heavy frameworks for speed and simplicity)
- **Database**: MongoDB 7.0
- **AI/LLM**: Google Generative AI (Gemini), OpenAI SDK, Tiktoken
- **Infrastructure**: Docker, Docker Compose

---

## 📋 API Documentation

Once the backend is running, you can access the interactive Swagger docs at:
- `http://localhost:8000/docs`

### Key Endpoints:
- `POST /api/messages`: Send a message and get a coached response.
- `GET /api/messages`: Fetch message history with cursor-based pagination.
- `GET /api/users/{user_id}`: Retrieve user profile and onboarding state.
- `GET /health`: Check system and database status.

---

## 🔮 Future Enhancements (If I had more time)

1. **Streaming Responses**: Implement Server-Sent Events (SSE) for "typing" effect as tokens are generated.
2. **Semantic Search for Memories**: Use Vector Embeddings (MongoDB Atlas Vector Search) for memory retrieval instead of simple category/recency filters.
3. **Voice Interface**: Add speech-to-text and text-to-speech for hands-free coaching.
4. **Integration with Health Devices**: Connect with Apple Health or Google Fit to fetch real-time activity data.
5. **Multilingual Support**: Support for Hindi, Tamil, and other regional languages using LLM translation capabilities.

---

## 📄 License
This project is for assignment purposes.

**Developed with ❤️ for Curelink.**
