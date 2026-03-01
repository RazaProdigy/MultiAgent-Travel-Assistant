"""
ChromaDB-backed activity catalog: one document per variation.
Supports metadata filtering (price, category, available) and semantic search.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Compatibility: google-adk requires opentelemetry <1.39, but ChromaDB's telemetry
# imports ReadableLogRecord (added in 1.39). Stub it if missing so chromadb can load.
def _ensure_readable_log_record():
    try:
        from opentelemetry.sdk._logs import ReadableLogRecord  # noqa: F401
    except ImportError:
        import opentelemetry.sdk._logs as _logs_mod
        if not hasattr(_logs_mod, "ReadableLogRecord"):
            from typing import Any

            class ReadableLogRecord:
                """Minimal stub for OpenTelemetry <1.39 compatibility with ChromaDB."""

                def __init__(self, **kwargs: Any) -> None:
                    pass

            _logs_mod.ReadableLogRecord = ReadableLogRecord


_ensure_readable_log_record()

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# Persistent storage under backend; fallback to in-memory for tests
ROOT_DIR = Path(__file__).parent
DEFAULT_PERSIST_DIR = str(ROOT_DIR / "chroma_data")

# OpenAI embeddings for ChromaDB (avoids onnxruntime from default embedder).
# Requires OPENAI_API_KEY in environment.
# If you had previously used the default embedder, delete chroma_data and restart to re-seed.
_openai_ef = OpenAIEmbeddingFunction(
    api_key_env_var="OPENAI_API_KEY",
    model_name="text-embedding-3-small",
)


class _LoggedOpenAIEmbeddingFunction:
    """Wraps OpenAI embedder to log every call so we can confirm OpenAI embeddings are invoked."""

    def __init__(self, inner):
        self._inner = inner

    def name(self) -> str:
        """ChromaDB uses this to validate embedding function; must match inner."""
        if hasattr(self._inner, "name") and callable(self._inner.name):
            return self._inner.name()
        if hasattr(self._inner.__class__, "name") and callable(getattr(self._inner.__class__, "name")):
            return self._inner.__class__.name()
        return "openai"

    def get_config(self) -> dict:
        """ChromaDB may persist config; delegate to inner so stored config matches."""
        if hasattr(self._inner, "get_config") and callable(self._inner.get_config):
            return self._inner.get_config()
        return {"name": self.name()}

    def embed_query(self, input: str, **kwargs):
        """ChromaDB calls this for single-query embedding (e.g. search). Delegate and log."""
        logger.info(
            "ChromaDB invoking OpenAI embeddings (embed_query): model=text-embedding-3-small, query_len=%d",
            len(input) if input else 0,
        )
        inner = self._inner
        if hasattr(inner, "embed_query") and callable(inner.embed_query):
            result = inner.embed_query(input)
        else:
            # Fallback: some ChromaDB embedders only have __call__(documents)
            result = inner([input])[0] if input else []
        logger.info("OpenAI embeddings returned (embed_query): vector_len=%d", len(result) if result else 0)
        return result

    def __call__(self, input: list) -> list:
        logger.info(
            "ChromaDB invoking OpenAI embeddings: model=text-embedding-3-small, num_texts=%d",
            len(input) if input else 0,
        )
        result = self._inner(input)
        logger.info("OpenAI embeddings returned: num_vectors=%d", len(result) if result else 0)
        return result

_collection = None
_activity_details = {}  # activity_id -> { image, description, cancellation_policy, reschedule_policy }


def _get_client(persist_directory: Optional[str] = None):
    persist = persist_directory or os.environ.get("CHROMA_PERSIST_DIR", DEFAULT_PERSIST_DIR)
    return chromadb.PersistentClient(path=persist, settings=Settings(anonymized_telemetry=False))


def _get_collection():
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name="activity_variations",
            embedding_function=_LoggedOpenAIEmbeddingFunction(_openai_ef),
            metadata={"description": "Dubai activity variations for semantic search"},
        )
    return _collection


def _build_activity_details(activities: list) -> dict:
    """Build activity_id -> { image, description, cancellation_policy, reschedule_policy } from mock_data."""
    details = {}
    for a in activities:
        details[a["id"]] = {
            "image": a.get("image"),
            "description": a.get("description"),
            "cancellation_policy": a.get("cancellation_policy"),
            "reschedule_policy": a.get("reschedule_policy"),
        }
    return details


def ensure_seeded(activities: list) -> None:
    """Seed the Chroma collection from activities list if empty. Idempotent."""
    global _activity_details
    _activity_details = _build_activity_details(activities)
    coll = _get_collection()
    existing = coll.count()
    if existing > 0:
        logger.info("ChromaDB already seeded (%d docs); skipping seed (no OpenAI embedding call).", existing)
        return

    logger.info("ChromaDB collection empty; will seed and call OpenAI embeddings for each document.")
    ids = []
    documents = []
    metadatas = []

    for activity in activities:
        activity_id = activity["id"]
        name = activity["name"]
        description = activity.get("description", "")
        category = activity.get("category", "")
        available = activity.get("available", True)

        for v in activity.get("variations", []):
            var_id = v["id"]
            var_name = v.get("name", "")
            doc_text = f"{name} {description} {var_name}"
            ids.append(var_id)
            documents.append(doc_text)
            group_sizes_str = ",".join(str(x) for x in v.get("group_sizes", []))
            time_slots_str = ",".join(v.get("time_slots", []))
            metadatas.append({
                "activity_id": activity_id,
                "variation_id": var_id,
                "activity_name": name,
                "variation_name": var_name,
                "category": category,
                "price": int(v.get("price", 0)),
                "currency": v.get("currency", "AED"),
                "available": available,
                "group_sizes": group_sizes_str,
                "time_slots": time_slots_str,
            })

    if ids:
        logger.info("Calling ChromaDB coll.add with %d documents (triggers OpenAI embeddings).", len(ids))
        coll.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("ChromaDB seed completed.")


def _variation_doc_to_variation(meta: dict) -> dict:
    """Build a variation dict for API/agent response from Chroma metadata."""
    time_slots = meta.get("time_slots", "")
    return {
        "id": meta.get("variation_id"),
        "name": meta.get("variation_name"),
        "price": meta.get("price"),
        "currency": meta.get("currency", "AED"),
        "time_slots": time_slots.split(",") if time_slots else [],
        "group_sizes": [int(x) for x in meta.get("group_sizes", "").split(",") if x.strip()],
    }


def _enrich_activity(activity_id: str, name: str, category: str, available: bool, variations: list) -> dict:
    """Build full activity dict with enrichment from _activity_details."""
    details = _activity_details.get(activity_id, {})
    prices = [v["price"] for v in variations if isinstance(v.get("price"), (int, float))]
    return {
        "id": activity_id,
        "name": name,
        "description": details.get("description", ""),
        "image": details.get("image"),
        "category": category,
        "available": available,
        "price_from": min(prices) if prices else None,
        "currency": variations[0].get("currency", "AED") if variations else "AED",
        "variations": variations,
        "cancellation_policy": details.get("cancellation_policy"),
        "reschedule_policy": details.get("reschedule_policy"),
    }


def search_activities(
    query_text: str = "",
    group_size: Optional[int] = None,
    max_price: Optional[float] = None,
    category: Optional[str] = None,
) -> list:
    """
    Search Dubai activities by semantic query and/or filters. Returns a list of activities
    (with only matching variations) for display. Use this to find activities when the user
    asks for things like "skydiving", "group of 2", "under 2000 AED", or by category.

    Args:
        query_text: Natural language search (e.g. "skydiving", "desert safari"). Leave empty for filter-only.
        group_size: Filter to variations that support this group size (e.g. 2 for "group of 2").
        max_price: Maximum price in AED (e.g. 2000 for "under 2000").
        category: Filter by category (e.g. "Adventure", "Sightseeing", "Cultural").
    """
    coll = _get_collection()
    if not _activity_details:
        return []

    # Build Chroma where filter
    where_conditions = []
    if max_price is not None:
        where_conditions.append({"price": {"$lte": int(max_price)}})
    if category is not None and category.strip():
        where_conditions.append({"category": category.strip()})
    # Optionally filter by available; plan said e.g. available True - we can show all or only available
    # where_conditions.append({"available": True})  # uncomment to hide unavailable

    if where_conditions:
        where = {"$and": where_conditions} if len(where_conditions) > 1 else where_conditions[0]
    else:
        where = None

    if query_text and query_text.strip():
        logger.info(
            "Semantic search: query_text=%r (this will call OpenAI embeddings for the query).",
            query_text.strip()[:80],
        )
        result = coll.query(
            query_texts=[query_text.strip()],
            n_results=50,
            where=where,
            include=["metadatas"],
        )
        # result["metadatas"] is list of lists (one per query)
        metadatas = result["metadatas"][0] if result.get("metadatas") else []
    else:
        logger.debug("Filter-only search (no query_text); no OpenAI embedding call.")
        get_result = coll.get(where=where, include=["metadatas"])
        metadatas = get_result.get("metadatas") or []

    # Post-filter by group_sizes (Chroma can't do "value in list" for stored list)
    if group_size is not None:
        gs_str = str(group_size)
        metadatas = [m for m in metadatas if m and gs_str in (m.get("group_sizes") or "").split(",")]

    # Group by activity_id and build activity list
    by_activity = {}
    for m in metadatas:
        if not m:
            continue
        aid = m.get("activity_id")
        if aid not in by_activity:
            by_activity[aid] = {
                "activity_id": aid,
                "activity_name": m.get("activity_name"),
                "category": m.get("category"),
                "available": m.get("available", True),
                "variations": [],
            }
        by_activity[aid]["variations"].append(_variation_doc_to_variation(m))

    out = []
    for aid, data in by_activity.items():
        variations = data["variations"]
        if not variations:
            continue
        act = _enrich_activity(
            activity_id=aid,
            name=data["activity_name"],
            category=data["category"],
            available=data["available"],
            variations=variations,
        )
        out.append(act)

    return out


def get_all_activities() -> list:
    """Return all activities (unique by activity_id) with all variations, for GET /api/activities."""
    coll = _get_collection()
    if not _activity_details:
        return []
    result = coll.get(include=["metadatas"])
    metadatas = result.get("metadatas") or []
    by_activity = {}
    for m in metadatas:
        if not m:
            continue
        aid = m.get("activity_id")
        if aid not in by_activity:
            by_activity[aid] = {
                "activity_id": aid,
                "activity_name": m.get("activity_name"),
                "category": m.get("category"),
                "available": m.get("available", True),
                "variations": [],
            }
        by_activity[aid]["variations"].append(_variation_doc_to_variation(m))

    out = []
    for aid, data in by_activity.items():
        act = _enrich_activity(
            activity_id=aid,
            name=data["activity_name"],
            category=data["category"],
            available=data["available"],
            variations=data["variations"],
        )
        out.append(act)
    return out


def get_activity_by_id(activity_id: str) -> Optional[dict]:
    """Return one activity with all its variations, or None. For GET /api/activities/{id}."""
    coll = _get_collection()
    if not _activity_details:
        return None
    result = coll.get(where={"activity_id": activity_id}, include=["metadatas"])
    metadatas = result.get("metadatas") or []
    if not metadatas:
        return None
    m0 = metadatas[0]
    variations = [_variation_doc_to_variation(m) for m in metadatas]
    return _enrich_activity(
        activity_id=activity_id,
        name=m0.get("activity_name", ""),
        category=m0.get("category", ""),
        available=m0.get("available", True),
        variations=variations,
    )
