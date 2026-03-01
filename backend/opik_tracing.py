"""
Opik tracing for the multi-agent backend.
Configures OpenTelemetry to export traces to Opik so agent runs, tool calls,
and ADK instrumentation appear in the Opik dashboard.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Opik Cloud OTLP traces endpoint (HTTP; Opik does not support gRPC)
OPIK_TRACES_ENDPOINT = "https://www.comet.com/opik/api/v1/private/otel/v1/traces"


def setup_opik_tracing() -> bool:
    """
    Set up the global OpenTelemetry TracerProvider to export spans to Opik.
    Call this at application startup, before any agents or runners are used.
    Google ADK uses the global tracer, so its spans will be sent to Opik.

    Returns True if Opik tracing was configured, False if skipped (e.g. no API key).
    """
    api_key = os.environ.get("OPIK_API_KEY", "").strip()
    if not api_key:
        logger.info("OPIK_API_KEY not set; Opik tracing disabled.")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
    except ImportError as e:
        logger.warning("Opik tracing skipped: missing OpenTelemetry packages: %s", e)
        return False

    project_name = os.environ.get("OPIK_PROJECT_NAME", "dubai-travel-assistant")
    workspace = os.environ.get("OPIK_WORKSPACE", "default")

    resource = Resource.create(
        {"service.name": "dubai-travel-assistant", "deployment.environment": os.environ.get("OPIK_ENVIRONMENT", "development")}
    )
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=OPIK_TRACES_ENDPOINT,
            headers={
                "Authorization": api_key,
                "projectName": project_name,
                "Comet-Workspace": workspace,
            },
        )
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    logger.info("Opik tracing enabled (project=%s, workspace=%s).", project_name, workspace)

    # Instrument the OpenAI client so embedding calls (e.g. from ChromaDB) show in traces
    try:
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor
        OpenAIInstrumentor().instrument()
        logger.info("OpenAI instrumentation enabled (embeddings and other API calls will be traced).")
    except ImportError as e:
        logger.debug("OpenAI instrumentation not available: %s", e)
    except Exception as e:
        logger.warning("OpenAI instrumentation failed: %s", e)

    return True
