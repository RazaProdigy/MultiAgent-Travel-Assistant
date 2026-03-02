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
- **Context Management**: Maintains conversation history from last 6 messages
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
│                  │     │ SendGrid (Email)     │     │             │
└──────────────────┘     └──────────────────────┘     └─────────────┘
```

---

## Project Structure

```
/app/
├── backend/
│   ├── agents.py         # Multi-agent system (Google ADK)
│   ├── prompts.py        # Separate prompts file for all agents
│   ├── server.py         # FastAPI endpoints
│   ├── mock_data.py      # 12 Dubai activities database
│   ├── email_service.py  # SendGrid escalation emails
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
| Frontend | React, Tailwind CSS, shadcn/ui, Lucide icons |
| Backend | FastAPI (Python) |
| Agent Framework | Google ADK (Agent Development Kit) |
| LLM | Gemini 2.5 Flash |
| Database | MongoDB (Motor async driver) |
| Email | SendGrid |
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
- MongoDB running locally
- SendGrid API key (optional, for email escalation)
- Google API Key (for Gemini 2.5 Flash)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="dubai_travel_assistant"
CORS_ORIGINS="*"
GOOGLE_API_KEY=your_google_api_key
SENDGRID_API_KEY=your_sendgrid_key
SENDER_EMAIL=your_verified_email@domain.com
SUPERVISOR_EMAIL=supervisor@domain.com
EOF

# Run
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

```bash
cd frontend
yarn install

# Create .env
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF

yarn start
```

### Docker (full stack)

Both frontend and backend run in containers. Env vars are handled as follows:

- **Backend**: Uses `backend/.env` (copy from `backend/.env.example` and fill in values). Required: `MONGO_URL`, `DB_NAME`. Optional: `CORS_ORIGINS`, `GOOGLE_API_KEY`, SendGrid/Opik vars.
- **Frontend**: `REACT_APP_BACKEND_URL` is set at **build time**. Default is `http://localhost:8001` so the browser can reach the API when both services are on the same host. Override with a root `.env` or in `docker-compose`:
  ```bash
  REACT_APP_BACKEND_URL=http://localhost:8001 docker-compose up --build
  ```
  Or create a root `.env` with `REACT_APP_BACKEND_URL=http://localhost:8001`.

**Steps:**

1. Create backend env file:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and set MONGO_URL, DB_NAME, and any optional keys (GOOGLE_API_KEY, etc.)
   ```

2. Build and run:
   ```bash
   docker-compose up --build
   ```

3. Open the app at **http://localhost:3000**. The API is at **http://localhost:8001**.

ChromaDB data is stored in a Docker volume (`backend_chroma_data`) so it persists between runs.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message through multi-agent system |
| GET | `/api/conversations/{session_id}` | Get chat history |
| GET | `/api/activities` | List all 12 activities |
| GET | `/api/activities/{id}` | Activity details |
| POST | `/api/supervisor/reply` | Supervisor HITL reply (panel or API) |
| POST | `/api/webhooks/sendgrid-inbound` | SendGrid Inbound Parse: relay email replies to chat |
| GET | `/api/bookings/{session_id}` | Session bookings |
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
- Queries 12 Dubai activities from mock database
- Handles variations (time slots, group sizes, packages)
- Collects booking info: activity, variation, time slot, group size, customer name
- Processes and saves bookings to MongoDB
- Escalates unavailable activities to human supervisor via email

### Information Agent
- Provides activity images in rich cards
- Shares cancellation and reschedule policies
- Displays pricing for all variations
- Category-based activity discovery (Adventure, Sightseeing, Water Sports, etc.)

### Human-in-the-Loop (HITL)
- SendGrid email sent on escalation with a **Reply to Customer** link to the supervisor panel
- **Reply link**: Set `APP_PUBLIC_URL` in backend (e.g. `https://app.example.com`) so the link in the email opens the correct frontend (otherwise it falls back to CORS origin or `http://localhost:5173`)
- **Supervisor Panel** (`/supervisor/:sessionId`) shows escalation context; supervisor types a reply and it is stored and shown in the customer's chat
- **Reply by email**: Optional. Set `INBOUND_REPLY_DOMAIN` (e.g. `inbound.example.com`) and configure [SendGrid Inbound Parse](https://docs.sendgrid.com/ui/account-and-settings/inbound-parse) to POST to `https://your-api/api/webhooks/sendgrid-inbound`. Escalation emails then use Reply-To `reply-{session_id}@{domain}`; when the supervisor replies to the email, the webhook relays the reply into the customer's chat
- Customer chat polls for new messages (every 2s when there is an escalation, 5s otherwise) so supervisor replies appear seamlessly

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

## Mock Database

12 Dubai activities with full details in `/backend/mock_data.py`:

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

The system uses Google ADK's `LlmAgent` and `InMemoryRunner`:

```python
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner

# Create specialized agents
activity_booking_agent = LlmAgent(
    name="activity_booking_agent",
    model="gemini-2.5-flash",
    instruction=ACTIVITY_BOOKING_AGENT_PROMPT,
)

information_agent = LlmAgent(
    name="information_agent",
    model="gemini-2.5-flash",
    instruction=INFORMATION_AGENT_PROMPT,
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

## Rate Limits

Google Gemini API free tier has rate limits:
- 5 requests per minute
- 20 requests per day (free tier)

For production use, consider upgrading to a paid tier.

---

## License

MIT
