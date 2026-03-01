# Dubai Travel Assistant — Multi-Agent System

A full-stack multi-agent travel assistant for discovering and booking Dubai activities, built with **Google ADK** (Agent Development Kit), React (WhatsApp-themed UI), and Gemini 2.5 Flash.

## Architecture

### Multi-Agent Design (Google ADK)

The system uses Google ADK's native `sub_agents` pattern for agent orchestration:

```
┌─────────────────────────────────────────────────────────────┐
│                    Root Orchestrator Agent                   │
│                 (dubai_travel_orchestrator)                  │
│                                                              │
│   • Analyzes user intent and routes to specialized agents    │
│   • Handles greetings directly                               │
│   • Uses Google ADK's transfer_to_agent for delegation       │
├──────────────────────────┬───────────────────────────────────┤
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
┌───────────────────────┐     ┌───────────────────────┐
│  Activity Booking     │     │   Information         │
│       Agent           │     │      Agent            │
│                       │     │                       │
│ • Query activities    │     │ • Activity pictures   │
│ • Handle variations   │     │ • Cancellation policy │
│ • Process bookings    │     │ • Reschedule policy   │
│ • Save reservations   │     │ • Pricing details     │
│ • Escalate via email  │     │ • List activities     │
│   when unavailable    │     │ • Category discovery  │
└───────────────────────┘     └───────────────────────┘
```

### Conversation Handler (TravelAssistant Class)

The `TravelAssistant` class wraps the multi-agent system and provides:
- **Context Management**: Maintains conversation history from last 10 messages
- **Message Aggregation**: Supports rapid user messages (sent as batch)
- **Response Enrichment**: Injects full activity data (images, policies) post-LLM response
- **Booking Persistence**: Saves confirmed bookings to MongoDB
- **Escalation Handling**: Triggers SendGrid email for unavailable activities

### Human-in-the-Loop (HITL)

Handled via the `/api/supervisor/reply` endpoint:
- Escalation emails sent via SendGrid with reply link
- Supervisor Panel at `/supervisor/:sessionId` for context and reply
- Supervisor messages appear seamlessly in customer chat

### System Architecture

```
┌──────────────────┐     ┌──────────────────────┐     ┌─────────────┐
│   React Frontend │────▶│   FastAPI Backend    │────▶│   MongoDB   │
│                  │     │                      │     │             │
│ • WhatsApp Chat  │     │ • /api/chat          │     │ • messages  │
│ • Activity Cards │     │ • /api/activities    │     │ • bookings  │
│ • Supervisor     │     │ • /api/supervisor    │     │             │
│   Panel          │     │ • /api/conversations │     │             │
│ • Message        │     │                      │     │             │
│   Aggregation    │     │ Google ADK Runner    │     │             │
│                  │     │ Gemini 2.5 Flash     │     │             │
│                  │     │ ChromaDB + OpenAI   │     │             │
│                  │     │   embeddings         │     │             │
│                  │     │ SendGrid (Email)     │     │             │
│                  │     │ Opik (optional)      │     │             │
└──────────────────┘     └──────────────────────┘     └─────────────┘
```

---

## Project Structure

```
All-out/
├── backend/
│   ├── agents.py           # Multi-agent system (Google ADK)
│   ├── prompts.py          # Separate prompts file for all agents
│   ├── server.py           # FastAPI endpoints
│   ├── mock_data.py        # 12 Dubai activities source data
│   ├── chroma_activities.py # ChromaDB catalog + semantic search (OpenAI embeddings)
│   ├── email_service.py    # SendGrid escalation emails
│   ├── opik_tracing.py     # Optional Opik/OpenTelemetry tracing
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.js
│       └── components/
│           ├── ChatInterface.js
│           ├── MessageBubble.js
│           ├── ActivityCard.js
│           ├── BookingConfirmation.js
│           ├── EscalationNotice.js
│           ├── SupervisorPanel.js
│           └── TypingIndicator.js
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Tailwind CSS, shadcn/ui, Lucide icons, Craco |
| Backend | FastAPI (Python) |
| Agent Framework | Google ADK (Agent Development Kit) |
| LLM | Gemini 2.5 Flash |
| Activity Search | ChromaDB + OpenAI embeddings (text-embedding-3-small) |
| Database | MongoDB (Motor async driver) |
| Email | SendGrid |
| Tracing | Opik (optional, OpenTelemetry) |
| Styling | WhatsApp-themed (custom CSS) |

---

## Agent Prompts

All agent prompts are separated into `/backend/prompts.py` for maintainability:

| Prompt | Agent | Purpose |
|--------|-------|---------|
| `ROOT_AGENT_PROMPT` | Root Orchestrator | Routes requests to specialized agents |
| `ACTIVITY_BOOKING_AGENT_PROMPT` | Activity Booking Agent | Handles booking flows, escalation |
| `INFORMATION_AGENT_PROMPT` | Information Agent | Provides activity info, policies, pricing |

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas connection string)
- **Google API Key** (for Gemini 2.5 Flash)
- **OpenAI API Key** (for ChromaDB semantic search — text-embedding-3-small)
- SendGrid API key (optional, for email escalation)
- Opik API key (optional, for tracing)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Create .env file (no .env.example in repo — use this template)
# Required: MONGO_URL, DB_NAME, GOOGLE_API_KEY, OPENAI_API_KEY
cat > .env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="dubai_travel_assistant"
CORS_ORIGINS="*"
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
SENDGRID_API_KEY=your_sendgrid_key
SENDER_EMAIL=your_verified_email@domain.com
SUPERVISOR_EMAIL=supervisor@domain.com
# Optional: Opik tracing
# OPIK_API_KEY=
# OPIK_PROJECT_NAME=dubai-travel-assistant
# OPIK_WORKSPACE=default
EOF

# Run
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

On first run, the backend seeds ChromaDB from `mock_data.py` (calls OpenAI embeddings). Data is stored in `backend/chroma_data` (or `CHROMA_PERSIST_DIR` in Docker).

### Frontend Setup

```bash
cd frontend
yarn install

# Create .env
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

yarn start
```

### Docker (full stack)

Both frontend and backend run in containers.

- **Backend**: Uses `backend/.env`. Create it from the Backend Setup template above. Required: `MONGO_URL`, `DB_NAME`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`. Optional: `CORS_ORIGINS`, SendGrid vars, Opik vars (`OPIK_API_KEY`, `OPIK_PROJECT_NAME`, `OPIK_WORKSPACE`). Chroma data is persisted in volume `backend_chroma_data`.
- **Frontend**: `REACT_APP_BACKEND_URL` is set at **build time** (default: `http://localhost:8001`). Override with a root `.env`: `REACT_APP_BACKEND_URL=http://localhost:8001`.

**Steps:**

1. Create backend env file:
   ```bash
   # Create backend/.env with MONGO_URL, DB_NAME, GOOGLE_API_KEY, OPENAI_API_KEY (see Backend Setup)
   ```

2. Build and run:
   ```bash
   docker-compose up --build
   ```

3. Open the app at **http://localhost:3000**. The API is at **http://localhost:8001**.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message through multi-agent system |
| GET | `/api/conversations/{session_id}` | Get chat history |
| GET | `/api/activities` | List all activities (from ChromaDB) |
| GET | `/api/activities/{id}` | Activity details |
| POST | `/api/supervisor/reply` | Supervisor HITL reply |
| GET | `/api/bookings/{session_id}` | Session bookings |
| POST | `/api/seed` | Seed info (activities count; Chroma seeded at startup) |
| GET | `/api/health` | Health check |

### Chat Response Types

The multi-agent system returns structured JSON responses:

```json
// Text response
{"type": "text", "message": "Hello! How can I help you?"}

// Activity list
{"type": "activity_list", "message": "...", "activities": [...]}

// Single activity with details
{"type": "activity_info", "message": "...", "activity": {...}}

// Booking confirmation
{"type": "booking", "message": "...", "booking": {...}}

// Escalation to human
{"type": "escalation", "message": "...", "escalation": {...}}
```

---

## Features

### Activity Booking Agent
- Queries Dubai activities via ChromaDB semantic search (tool: `search_activities`)
- Handles variations (time slots, group sizes, packages)
- Collects booking info: activity, variation, time slot, group size, customer name
- Processes and saves bookings to MongoDB
- Escalates unavailable activities to human supervisor via email

### Information Agent
- Uses ChromaDB search (`search_activities`) for activity discovery
- Provides activity images in rich cards
- Shares cancellation and reschedule policies
- Displays pricing for all variations
- Category-based activity discovery (Adventure, Sightseeing, Water Sports, etc.)

### Human-in-the-Loop (HITL)
- SendGrid email sent on escalation with reply link
- Supervisor Panel (`/supervisor/:sessionId`) for viewing context and replying
- Supervisor replies appear seamlessly in customer chat via polling

### Conversation Handler
- Message interruption support (user can send while bot processes)
- Aggregates rapid messages (2.5s window) into single request
- Maintains conversation context across messages
- Persistent chat history in MongoDB

### WhatsApp-Themed UI
- Authentic green header with avatar and status
- Message bubbles with timestamps and read receipts
- Activity cards with images, pricing, and Book Now buttons
- Typing indicator animation
- Chat background pattern
- Responsive mobile-first design

---

## Activity Data & ChromaDB

Activity source: **12 Dubai activities** in `/backend/mock_data.py`. On startup, the backend seeds **ChromaDB** from this data (one document per variation, embedded with OpenAI `text-embedding-3-small`). The agents use the `search_activities` tool to query ChromaDB; `/api/activities` and `/api/activities/{id}` also read from Chroma.

Activities:

1. Burj Khalifa At The Top
2. Desert Safari Adventure
3. Dubai Marina Luxury Cruise
4. Skydiving over Palm Jumeirah
5. Jet Ski Experience
6. Dubai Frame
7. Aquaventure Waterpark
8. Hot Air Balloon Ride
9. Old Dubai Heritage Walking Tour
10. Dubai Miracle Garden
11. Deep Dive Dubai
12. Helicopter Tour of Dubai (**unavailable** — triggers escalation)

Each activity includes: name, description, image, category, multiple variations with pricing, cancellation policy, and reschedule policy.

---

## Google ADK Integration

The system uses Google ADK's `LlmAgent` and `InMemoryRunner`. Both sub-agents have the `search_activities` tool (ChromaDB semantic search):

```python
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from chroma_activities import search_activities

# Specialized agents with ChromaDB search tool
activity_booking_agent = LlmAgent(
    name="activity_booking_agent",
    model="gemini-2.5-flash",
    instruction=ACTIVITY_BOOKING_AGENT_PROMPT,
    tools=[search_activities],
)

information_agent = LlmAgent(
    name="information_agent",
    model="gemini-2.5-flash",
    instruction=INFORMATION_AGENT_PROMPT,
    tools=[search_activities],
)

# Root orchestrator with sub-agents
root_agent = LlmAgent(
    name="dubai_travel_orchestrator",
    model="gemini-2.5-flash",
    instruction=ROOT_AGENT_PROMPT,
    sub_agents=[activity_booking_agent, information_agent],
)

# Runner for executing agent conversations
runner = InMemoryRunner(agent=root_agent, app_name="dubai_travel_assistant")
```

---

## Optional: Opik Tracing

The backend supports **Opik** for observability. Set `OPIK_API_KEY` (and optionally `OPIK_PROJECT_NAME`, `OPIK_WORKSPACE`) in `backend/.env`. `opik_tracing.py` configures OpenTelemetry so agent runs, tool calls, and OpenAI embedding usage appear in the Opik dashboard. If `OPIK_API_KEY` is unset, tracing is disabled.

---

## Rate Limits

Google Gemini API free tier has rate limits:
- 5 requests per minute
- 20 requests per day (free tier)

For production use, consider upgrading to a paid tier.

---

## License

MIT
