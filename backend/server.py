from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Opik tracing (must run before agents/runner so ADK uses this tracer)
from opik_tracing import setup_opik_tracing
setup_opik_tracing()

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Import agents (after db init)
from agents import TravelAssistant
from mock_data import DUBAI_ACTIVITIES
import chroma_activities

assistant = TravelAssistant(db)

# Seed Chroma with activity variations before handling requests
chroma_activities.ensure_seeded(DUBAI_ACTIVITIES)

# ──────────────────────────────────
# Models
# ──────────────────────────────────

class ChatMessage(BaseModel):
    session_id: str
    message: str

class SupervisorReply(BaseModel):
    session_id: str
    message: str

# ──────────────────────────────────
# Chat Endpoints
# ──────────────────────────────────

@api_router.post("/chat")
async def chat(body: ChatMessage):
    """Process a chat message through the multi-agent system.
    Supports aggregated messages (multiple lines = multiple user messages sent rapidly).
    """
    session_id = body.session_id
    user_msg = body.message.strip()

    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check if this is an aggregated message (multiple lines)
    lines = [l.strip() for l in user_msg.split("\n") if l.strip()]
    is_aggregated = len(lines) > 1

    # Store each line as a separate user message (for history display)
    for line in lines:
        user_doc = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": "user",
            "content": line,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "text",
        }
        await db.messages.insert_one(user_doc)

    # Get recent history for context
    history_cursor = db.messages.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(10)
    history = await history_cursor.to_list(10)
    history.reverse()

    # If aggregated, tell the agent these are multiple rapid messages
    prompt = user_msg
    if is_aggregated:
        prompt = f"[The user sent these messages rapidly in succession, please address all of them]\n{user_msg}"

    # Process through agent
    response = await assistant.process_message(session_id, prompt, history)

    # Store assistant response
    bot_doc = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "assistant",
        "content": response.get("message", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": response.get("type", "text"),
        "data": response,
    }
    await db.messages.insert_one(bot_doc)

    return {"status": "ok", "response": response}


@api_router.get("/conversations/{session_id}")
async def get_conversation(session_id: str):
    """Get all messages for a session."""
    messages = await db.messages.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(500)
    return {"messages": messages}


# ──────────────────────────────────
# Activity Endpoints
# ──────────────────────────────────

@api_router.get("/activities")
async def list_activities():
    """List all available activities (from Chroma)."""
    all_activities = chroma_activities.get_all_activities()
    activities = [
        {
            "id": a["id"],
            "name": a["name"],
            "description": a["description"],
            "image": a["image"],
            "category": a["category"],
            "available": a["available"],
            "price_from": a.get("price_from"),
            "currency": a.get("currency", "AED"),
        }
        for a in all_activities
    ]
    return {"activities": activities}


@api_router.get("/activities/{activity_id}")
async def get_activity(activity_id: str):
    """Get full details for a single activity (from Chroma)."""
    activity = chroma_activities.get_activity_by_id(activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"activity": activity}


# ──────────────────────────────────
# Supervisor / HITL Endpoints
# ──────────────────────────────────

@api_router.post("/supervisor/reply")
async def supervisor_reply(body: SupervisorReply):
    """Simulate supervisor replying to an escalation."""
    session_id = body.session_id
    message = body.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Reply cannot be empty")

    doc = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "supervisor",
        "content": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "supervisor",
        "data": {"type": "supervisor", "message": message},
    }
    await db.messages.insert_one(doc)
    return {"status": "ok", "message": "Supervisor reply recorded"}


# ──────────────────────────────────
# Bookings
# ──────────────────────────────────

@api_router.get("/bookings/{session_id}")
async def get_bookings(session_id: str):
    """Get bookings for a session."""
    bookings = await db.bookings.find(
        {"session_id": session_id},
        {"_id": 0}
    ).to_list(100)
    return {"bookings": bookings}


# ──────────────────────────────────
# Seed & Health
# ──────────────────────────────────

@api_router.post("/seed")
async def seed_data():
    """Seed the activities into MongoDB (optional, we use in-memory mock)."""
    return {"status": "ok", "activities_count": len(DUBAI_ACTIVITIES)}


@api_router.get("/health")
async def health():
    return {"status": "healthy", "service": "dubai-travel-assistant"}


@api_router.get("/")
async def root():
    return {"message": "Dubai Travel Assistant API"}


# ──────────────────────────────────
# App Config
# ──────────────────────────────────
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
