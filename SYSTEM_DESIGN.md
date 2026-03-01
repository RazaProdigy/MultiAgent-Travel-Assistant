# System Design Decisions — Multi-Agent Travel Assistant (Backend)

This document captures the main system design decisions for the Dubai Travel Assistant backend, with emphasis on **demo suitability** and **production evolution**.

---

## 1. Project Context: Demo vs Production

This project was built as a **demo** to showcase:

- Multi-agent orchestration (Google ADK with a root orchestrator and specialized sub-agents)
- Semantic activity search (ChromaDB + embeddings)
- Conversation persistence and human-in-the-loop (HITL) escalation
- End-to-end flow: chat → activity discovery → booking → escalation when unavailable

Design choices favor **simplicity, fast iteration, and single-instance deployment** over horizontal scaling, cost optimization, and enterprise resilience. The sections below state the current (demo) decisions and what would change for **production** under growing traffic, memory, and reliability requirements.

---

## 2. LLM & Model Choices

### 2.1 Primary LLM: Gemini 2.5 Flash

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **Model** | `gemini-2.5-flash` for all agents (root, activity booking, information) | Single model simplifies configuration and keeps latency low; Flash is cost-effective for a demo. |
| **Provider** | Google AI (Gemini API) | Chosen for Google ADK compatibility and straightforward API key setup. |
| **Usage** | Same model for orchestrator and both sub-agents | Reduces operational complexity; differentiation is via prompts and tools, not model size. |

**Production considerations:**

- **Model tiering**: Use a smaller/cheaper model for the root orchestrator (routing only) and reserve Flash or a larger model for sub-agents that need deeper reasoning (e.g. booking flows, policy explanation).
- **Fallbacks**: Configure fallback models (e.g. another Gemini variant or provider) for rate limits and availability.
- **Caching**: Introduce response or prompt caching for repeated queries (e.g. “what are your cancellation policies?”) to reduce token cost and latency.
- **Rate limits & quotas**: Use per-user or per-tenant rate limiting and monitor token usage to avoid surprise bills.

---

### 2.2 Embeddings: OpenAI `text-embedding-3-small`

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **Model** | OpenAI `text-embedding-3-small` | Used by ChromaDB’s `OpenAIEmbeddingFunction` for activity semantic search; avoids bringing in Chroma’s default embedder (and onnxruntime) for a simpler demo stack. |
| **Provider** | OpenAI | Requires `OPENAI_API_KEY`; keeps embedding and search logic simple. |

**Production considerations:**

- **Cost & latency**: At scale, evaluate self-hosted or vendor embeddings (e.g. Cohere, Voyage, or open-source) for lower cost and data residency.
- **Re-embedding**: If the activity catalog is updated often, plan for incremental re-embedding and versioned collections to avoid full re-seeds on every change.
- **Caching**: Cache embeddings for stable activity text to avoid calling the embedding API on every search.

---

## 3. Databases

### 3.1 MongoDB (Conversation & Bookings)

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **Use case** | Persistent store for chat messages and bookings | Simple document model; easy to add fields (e.g. `session_id`, `role`, `timestamp`, `data`). |
| **Driver** | Motor (async) | Fits FastAPI’s async style and avoids blocking the event loop. |
| **Collections** | `messages`, `bookings` | Flat structure; no sharding or multi-tenancy. |
| **History window** | Last 10 messages fetched, last 6 used in context | Keeps prompt size bounded for the demo; good enough for short conversations. |
| **Limits** | 500 messages per conversation, 100 bookings per session | Hard limits to avoid unbounded reads; sufficient for demo flows. |

**Production considerations:**

- **Indexes**: Add indexes on `session_id`, `timestamp` (and optionally `role`) for messages; on `session_id` and `created_at` for bookings; compound indexes if you filter by tenant or user.
- **Retention & archival**: Define retention for messages and bookings; archive or move old data to cold storage to control size and cost.
- **Sharding**: If traffic grows, shard by `session_id` or a tenant ID.
- **Read/write scaling**: Use replica sets for read scaling; consider separate clusters for analytics vs real-time API.
- **Backup & recovery**: Automated backups, point-in-time recovery, and runbooks for restore.

---

### 3.2 ChromaDB (Activity Catalog & Semantic Search)

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **Use case** | Vector store for activity variations; semantic search + metadata filters | One document per variation; search by natural language (e.g. “skydiving”, “under 2000 AED”) plus filters (price, category, group size). |
| **Storage** | Persistent client with `chroma_data` on disk (or Docker volume) | Survives restarts; no separate vector DB service for the demo. |
| **Embedding** | OpenAI `text-embedding-3-small` via Chroma’s `OpenAIEmbeddingFunction` | Keeps embedding logic inside Chroma; single API key. |
| **Seed** | In-process seed at startup from `DUBAI_ACTIVITIES` if collection empty | Idempotent; demo runs with a fixed, small catalog. |
| **Enrichment** | In-memory `_activity_details` (and `ACTIVITY_MAP` in agents) from mock data | Full activity details (images, policies) live in Python; Chroma holds variation-level docs and metadata. |

**Production considerations:**

- **Dedicated vector DB**: Move to a managed or self-hosted vector store (e.g. Pinecone, Weaviate, Qdrant, or pgvector) for availability, scaling, and backup.
- **High availability**: Chroma’s single-directory persistence is not HA; production needs replication and failover.
- **Scaling**: Separate read replicas or sharding by category/region if catalog and query volume grow.
- **Catalog source**: Replace in-code `DUBAI_ACTIVITIES` with a proper catalog service or DB; sync changes into the vector store via pipelines (with re-embedding as above).
- **Metadata**: Add more metadata (e.g. region, duration, popularity) and expose it in filters and tool parameters for richer search.

---

## 4. Memory & Conversation Context

### 4.1 Agent Runner: In-Memory

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **Runner** | Google ADK `InMemoryRunner` | No extra infra; session state lives in process. |
| **Sessions** | In-process set of `session_id`s; session created on first message | Simple “have we seen this session?” check; creation is best-effort (duplicate creation is tolerated). |

**Production considerations:**

- **Persistence**: Use a **persistent session store** (e.g. ADK’s database-backed runner or a custom store) so that restarting the service or scaling to multiple instances does not lose conversation state.
- **Multi-instance**: With multiple backend replicas, session affinity or a shared session store is required so that a user’s next message hits an instance that has (or can load) their session.
- **TTL & eviction**: Define session TTL and eviction to avoid unbounded memory growth and to align with data retention policy.

---

### 4.2 Conversation History (Context Window)

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **Source** | MongoDB `messages` | Single source of truth for display and for building context. |
| **Fetch** | Last 10 messages by `timestamp` | Small, bounded read per request. |
| **Context to model** | Last 6 messages formatted as “role: content” in the prompt | Keeps token count low and avoids exceeding context limits. |
| **No summarization** | Raw recent messages only | No extra LLM call or summarization pipeline; good for demo. |

**Production considerations:**

- **Sliding window + summarization**: For long conversations, keep a sliding window of recent messages plus an optional summarized “earlier context” to stay within token limits and control cost.
- **Token budgeting**: Explicit token limits per user/tenant and per request; optionally truncate or summarize when approaching the limit.
- **Personalization**: Store and reuse user preferences (e.g. currency, group size) to shorten prompts and improve consistency.

---

## 5. Cost Analysis (Demo vs Production)

### 5.1 Demo Cost Profile

Rough order of magnitude for **low demo usage** (e.g. tens of conversations per day, few messages per conversation):

| Component | Usage | Demo Cost Notes |
|-----------|--------|------------------|
| **Gemini 2.5 Flash** | Input + output tokens per turn (orchestrator + sub-agent calls) | Pay-per-token; typically low for a demo. |
| **OpenAI Embeddings** | One-time seed + per-query embedding for activity search | Seed is fixed; per-query cost scales with number of searches. |
| **MongoDB** | M0 (free) or small shared cluster | Free tier often sufficient for demo. |
| **ChromaDB** | Local disk / Docker volume | No direct SaaS cost. |
| **SendGrid** | Escalation emails only | Free tier usually enough for demo. |
| **Opik** | Traces per request | Depends on Opik plan; can be disabled for demo. |

No formal cost monitoring or budgets are implemented; the demo assumes light, manual use.

### 5.2 Production Cost Considerations

- **Token usage**: Track input/output tokens per model and per user/tenant; set alerts and budgets.
- **Embedding volume**: Monitor embedding API calls; cache and batch where possible.
- **Database**: Size and index usage; consider dedicated clusters and backup cost.
- **Vector DB**: If moving to managed vector DB, factor in storage and query pricing.
- **Email**: SendGrid (or alternative) volume and deliverability; consider queues and retries.
- **Observability**: Opik or other APM/tracing; sampling and retention to control cost while keeping debuggability.

---

## 6. Observability & Tracing

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **Tracing** | Opik via OpenTelemetry (OTLP over HTTP) | Optional (`OPIK_API_KEY`); ADK and app use the global tracer so agent and tool spans show in Opik. |
| **Logging** | Python `logging` to stdout | Simple; no log aggregation. |
| **Metrics** | None | No Prometheus/StatsD or custom metrics. |

**Production considerations:**

- **Sampling**: Trace sampling (e.g. 10–20%) to control volume and cost while retaining visibility.
- **Metrics**: Add request rate, latency (p50/p95/p99), error rate, token usage, and queue depth; expose via Prometheus and dashboards.
- **Logging**: Structured logs (JSON) and central aggregation (e.g. ELK, Datadog) with retention and search.
- **Alerting**: Alerts on errors, latency SLOs, and cost thresholds.

---

## 7. Email (Escalation / HITL)

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **Provider** | SendGrid | Simple API; HTML template with reply link to supervisor panel. |
| **Trigger** | When agent returns `type: "escalation"` (e.g. activity unavailable) | Single code path; no queue. |
| **Config** | Optional; missing key/email disables sending | Demo can run without email. |

**Production considerations:**

- **Queue**: Put escalation events in a queue (e.g. SQS, Redis); worker sends email and records outcome. Decouples API from SendGrid and allows retries.
- **Templates & i18n**: Template storage and localization for subject/body.
- **Deliverability**: Domain authentication, rate limits, and bounce/complaint handling.
- **Audit**: Log all escalation emails and supervisor actions for compliance and support.

---

## 8. Activity Data & Seeding

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **Source** | In-code `DUBAI_ACTIVITIES` in `mock_data.py` | No external CMS or DB; easy to demo with fixed data. |
| **Chroma seed** | `chroma_activities.ensure_seeded(DUBAI_ACTIVITIES)` at startup | Idempotent; fills Chroma if empty. |
| **Enrichment** | `ACTIVITY_MAP` and `_activity_details` in memory | Fast lookup for enriching agent responses with images, policies, etc. |

**Production considerations:**

- **Catalog source**: Activities and variations from a proper database or product/CMS API; sync pipeline into vector store and (if needed) into caches.
- **Versioning**: Version activity and variation data; support A/B or gradual rollout of catalog changes.
- **Seed/refresh**: No longer “seed once at startup”; use scheduled or event-driven refresh and re-embedding.

---

## 9. API & Deployment (Demo)

| Aspect | Demo Decision | Rationale |
|--------|----------------|-----------|
| **API** | FastAPI; single process | Simple and sufficient for demo concurrency. |
| **CORS** | Configurable via `CORS_ORIGINS` (e.g. `*` for dev) | Flexible for local and demo frontends. |
| **Docker** | Backend + frontend in Docker Compose; backend chroma volume | Single-node deployment; Chroma data persisted in a named volume. |
| **Secrets** | `.env` (and env_file in Compose) | No secret manager; acceptable for demo. |

**Production considerations:**

- **Scaling**: Multiple backend replicas behind a load balancer; session/store and Chroma alternatives as above.
- **Secrets**: Use a secret manager (e.g. AWS Secrets Manager, Vault); rotate API keys and DB credentials.
- **TLS & auth**: TLS termination; API authentication and authorization (e.g. JWT, API keys, OAuth).
- **Rate limiting**: Global and per-user/tenant rate limits to protect LLM and embedding APIs and backend.

---

## 10. Summary Table: Demo vs Production

| Area | Demo | Production (when traffic/memory/cost grow) |
|------|------|-------------------------------------------|
| **LLM** | Single Gemini 2.5 Flash for all agents | Tiered models; fallbacks; caching; rate limits |
| **Embeddings** | OpenAI text-embedding-3-small, no cache | Consider alternatives; cache; batch/re-embed pipeline |
| **MongoDB** | Single instance; minimal indexes | Indexes; retention; sharding; replicas; backups |
| **Vector store** | ChromaDB on disk / volume | Managed vector DB; HA; catalog sync pipeline |
| **Memory/sessions** | InMemoryRunner; in-process session set | Persistent session store; multi-instance safe; TTL |
| **Conversation** | Last 6 of 10 messages | Sliding window; optional summarization; token budget |
| **Activity data** | In-code mock; seed at startup | Catalog DB/CMS; sync and re-embed; versioning |
| **Email** | SendGrid direct send | Queue; retries; templates; deliverability; audit |
| **Observability** | Optional Opik; stdout logs | Sampling; metrics; structured logs; alerts |
| **Cost** | Unmonitored | Token/embedding/DB monitoring; budgets; alerts |
| **Deployment** | Single Compose stack; .env | Multi-replica; secrets manager; TLS; auth; rate limiting |

---

This document reflects the system as implemented for the demo and the intended direction for production hardening and scaling. Decisions are documented so that future changes (e.g. moving to a persistent runner, a managed vector DB, or a formal catalog pipeline) can be made consistently with the original design intent.
