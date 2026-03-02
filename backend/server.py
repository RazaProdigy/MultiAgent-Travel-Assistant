import re
from fastapi import FastAPI, APIRouter, HTTPException, Form
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

def _store_supervisor_reply(session_id: str, message: str):
    """Store a supervisor reply so it appears in the customer's chat (shared helper)."""
    doc = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "supervisor",
        "content": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "supervisor",
        "data": {"type": "supervisor", "message": message},
    }
    return doc


@api_router.post("/supervisor/reply")
async def supervisor_reply(body: SupervisorReply):
    """Supervisor replies via the panel (or API). Message is stored and shown in the customer's chat."""
    session_id = body.session_id
    message = body.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Reply cannot be empty")

    doc = _store_supervisor_reply(session_id, message)
    await db.messages.insert_one(doc)
    return {"status": "ok", "message": "Supervisor reply recorded"}


@api_router.post("/webhooks/sendgrid-inbound")
async def sendgrid_inbound_webhook(
    from_email: str = Form(None, alias="from"),
    to_email: str = Form(None, alias="to"),
    subject: str = Form(""),
    text: str = Form(""),
    html: str = Form(""),
):
    """
    SendGrid Inbound Parse webhook: when the supervisor replies to an escalation email,
    the reply is POSTed here. We extract session_id from the 'to' address (reply-{session_id}@domain)
    or from the subject, then store the reply so it appears in the customer's chat.
    """
    # Prefer session from Reply-To recipient: reply-sess-xxx@inbound.example.com
    session_id = None
    if to_email:
        match = re.match(r"reply-(.+?)@", to_email, re.IGNORECASE)
        if match:
            session_id = match.group(1).strip()
    if not session_id and subject:
        # Fallback: "Re: ... Session sess-xxx" or "Session sess-xxx"
        match = re.search(r"Session\s+([a-zA-Z0-9\-]+)", subject, re.IGNORECASE)
        if match:
            session_id = match.group(1).strip()
        if not session_id:
            match = re.search(r"(sess-[a-f0-9\-]+)", subject, re.IGNORECASE)
            if match:
                session_id = match.group(1).strip()

    if not session_id:
        logger.warning("Inbound email: could not determine session_id from to=%r subject=%r", to_email, subject)
        return {"status": "ignored", "reason": "no_session_id"}

    body_text = (text or "").strip() or (html or "").strip()
    if not body_text:
        return {"status": "ignored", "reason": "empty_body"}
    # If we only have HTML, strip tags
    if not text and html:
        body_text = re.sub(r"<[^>]+>", " ", body_text)
        body_text = re.sub(r"\s+", " ", body_text).strip()

    # Strip quoted reply and signature (simple: take first paragraph or first 2000 chars)
    if len(body_text) > 2000:
        body_text = body_text[:2000].rstrip() + "..."
    # Remove common reply prefixes
    for prefix in ("On .+ wrote:", "From:.*?", "To:.*?", "Sent:.*?", "Reply to this email"):
        body_text = re.sub(prefix, "", body_text, flags=re.IGNORECASE | re.DOTALL)
    body_text = re.sub(r"\n{3,}", "\n\n", body_text).strip()

    if not body_text:
        return {"status": "ignored", "reason": "empty_after_clean"}

    doc = _store_supervisor_reply(session_id, body_text)
    await db.messages.insert_one(doc)
    logger.info("Inbound email relayed to chat for session_id=%s", session_id)
    return {"status": "ok", "session_id": session_id}


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
