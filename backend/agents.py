"""
Multi-Agent Travel Assistant using Google ADK with Gemini 2.5 Flash.
Implements a multi-agent architecture with specialized agents:
- Root Orchestrator: Routes requests to appropriate sub-agents
- Activity Booking Agent: Handles booking flows and escalation
- Information Agent: Provides activity details, policies, and pricing
"""
import os
import json
import logging
import uuid
from datetime import datetime, timezone

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

from mock_data import DUBAI_ACTIVITIES
from chroma_activities import search_activities
from email_service import send_escalation_email
from prompts import (
    ROOT_AGENT_PROMPT,
    ACTIVITY_BOOKING_AGENT_PROMPT,
    INFORMATION_AGENT_PROMPT,
)

logger = logging.getLogger(__name__)

# Quick lookup by ID for enrichment
ACTIVITY_MAP = {a["id"]: a for a in DUBAI_ACTIVITIES}


# ──────────────────────────────────────────────
# Define Specialized Agents using Google ADK
# ──────────────────────────────────────────────

# Activity Booking Agent - Handles bookings and escalation
activity_booking_agent = LlmAgent(
    name="activity_booking_agent",
    model="gemini-2.5-flash",
    description="Specialized agent for handling activity bookings, reservations, and escalations when activities are unavailable.",
    instruction=ACTIVITY_BOOKING_AGENT_PROMPT,
    tools=[search_activities],
)

# Information Agent - Provides activity info, policies, pricing
information_agent = LlmAgent(
    name="information_agent",
    model="gemini-2.5-flash",
    description="Specialized agent for providing activity information, images, cancellation policies, reschedule policies, and pricing details.",
    instruction=INFORMATION_AGENT_PROMPT,
    tools=[search_activities],
)

# Root Orchestrator Agent - Routes to sub-agents
root_agent = LlmAgent(
    name="dubai_travel_orchestrator",
    model="gemini-2.5-flash",
    description="Root orchestrator that routes user requests to specialized agents for the Dubai Travel Assistant.",
    instruction=ROOT_AGENT_PROMPT,
    sub_agents=[activity_booking_agent, information_agent],
)


class TravelAssistant:
    """
    Root orchestrator that manages conversation and delegates to appropriate agents via Google ADK.
    Handles:
    - Conversation context management
    - Message aggregation (for rapid user messages)
    - Agent response processing
    - Booking persistence
    - Escalation email sending
    """

    def __init__(self, db):
        self.db = db
        self._runner = InMemoryRunner(
            agent=root_agent,
            app_name="dubai_travel_assistant",
        )
        self._sessions: set[str] = set()

    async def _ensure_session(self, session_id: str):
        """Create a new ADK session if one doesn't exist for this session_id."""
        if session_id not in self._sessions:
            try:
                await self._runner.session_service.create_session(
                    app_name="dubai_travel_assistant",
                    user_id=session_id,
                    session_id=session_id,
                )
                self._sessions.add(session_id)
            except Exception as e:
                # Session might already exist (e.g. from a previous run)
                logger.warning(f"Session creation note: {e}")
                self._sessions.add(session_id)

    async def process_message(self, session_id: str, user_message: str, message_history: list = None) -> dict:
        """
        Process a user message through the multi-agent system.
        
        Conversation Handler responsibilities:
        - Maintains conversation context from history
        - Supports message aggregation (multiple rapid messages)
        - Routes through the agent orchestration system
        """
        await self._ensure_session(session_id)

        # Build context from recent history (Conversation Handler: maintain context)
        context_str = ""
        if message_history and len(message_history) > 0:
            recent = message_history[-6:]  # last 6 messages for context
            context_parts = []
            for msg in recent:
                role = msg.get("role", "user")
                text = msg.get("content", "")
                if isinstance(text, str) and len(text) > 0:
                    context_parts.append(f"{role}: {text}")
            if context_parts:
                context_str = "\n".join(context_parts)

        prompt = user_message
        if context_str:
            prompt = f"Recent conversation context:\n{context_str}\n\nUser's new message: {user_message}"

        try:
            # Create user message content for Google ADK
            user_content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=prompt)]
            )

            # Run through multi-agent system via ADK runner
            response_text = ""
            async for event in self._runner.run_async(
                user_id=session_id,
                session_id=session_id,
                new_message=user_content,
            ):
                if event.is_final_response() and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text

            if not response_text:
                return {
                    "type": "text",
                    "message": "I apologize, I didn't get a proper response. Could you please try again?"
                }

            # Parse the JSON response
            parsed = self._parse_response(response_text)

            # Handle escalation — send email (Activity Booking Agent escalation)
            if parsed.get("type") == "escalation":
                escalation_data = parsed.get("escalation", {})
                email_sent = send_escalation_email(
                    user_query=escalation_data.get("query", user_message),
                    session_id=session_id,
                    context=escalation_data.get("reason", "Activity/variation unavailable"),
                )
                parsed["email_sent"] = email_sent

            # Handle booking — save to db (Activity Booking Agent confirmation)
            if parsed.get("type") == "booking":
                booking_data = parsed.get("booking", {})
                if booking_data:
                    booking_doc = {
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "activity_id": booking_data.get("activity_id"),
                        "activity_name": booking_data.get("activity_name"),
                        "variation_id": booking_data.get("variation_id"),
                        "variation_name": booking_data.get("variation_name"),
                        "time_slot": booking_data.get("time_slot"),
                        "group_size": booking_data.get("group_size"),
                        "customer_name": booking_data.get("customer_name"),
                        "total_price": booking_data.get("total_price"),
                        "currency": booking_data.get("currency", "AED"),
                        "status": "confirmed",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    await self.db.bookings.insert_one(booking_doc)
                    parsed["booking"]["booking_id"] = booking_doc["id"]

            return parsed

        except Exception as e:
            logger.error(f"Multi-agent system error: {e}")
            return {
                "type": "text",
                "message": "I apologize, I'm having a moment. Could you please rephrase your question? I'm here to help you explore amazing Dubai activities!"
            }

    def _parse_response(self, raw: str) -> dict:
        """Parse the LLM response, extracting JSON from potential markdown wrapping."""
        text = raw.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    parsed = json.loads(text[start:end])
                except json.JSONDecodeError:
                    return {"type": "text", "message": text}
            else:
                return {"type": "text", "message": text}

        # Enrich activities with full data from mock DB
        return self._enrich_response(parsed)

    def _enrich_response(self, parsed: dict) -> dict:
        """Enrich LLM response with full activity data (images, descriptions, etc.)."""
        resp_type = parsed.get("type")

        if resp_type == "activity_list" and "activities" in parsed:
            enriched = []
            for act in parsed["activities"]:
                aid = act.get("id", "")
                if aid in ACTIVITY_MAP:
                    source = ACTIVITY_MAP[aid]
                    act["image"] = source["image"]
                    act["description"] = act.get("description") or source["description"]
                    act["category"] = act.get("category") or source["category"]
                    act["price_from"] = act.get("price_from") or min(v["price"] for v in source["variations"])
                    act["currency"] = act.get("currency") or source["variations"][0]["currency"]
                    act["available"] = source["available"]
                enriched.append(act)
            parsed["activities"] = enriched

        if resp_type == "activity_info" and "activity" in parsed:
            act = parsed["activity"]
            aid = act.get("id", "")
            if aid in ACTIVITY_MAP:
                source = ACTIVITY_MAP[aid]
                act["image"] = source["image"]
                act["description"] = act.get("description") or source["description"]
                act["variations"] = act.get("variations") or source["variations"]
                act["cancellation_policy"] = act.get("cancellation_policy") or source["cancellation_policy"]
                act["reschedule_policy"] = act.get("reschedule_policy") or source["reschedule_policy"]
                act["category"] = act.get("category") or source["category"]
                act["currency"] = act.get("currency", "AED")
                act["price_from"] = act.get("price_from") or min(v["price"] for v in source["variations"])
            parsed["activity"] = act

        return parsed
