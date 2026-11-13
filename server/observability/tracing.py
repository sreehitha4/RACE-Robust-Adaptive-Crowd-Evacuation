"""Optional OpenTelemetry setup. The service remains runnable without an OTLP collector."""
import logging
import os

logger = logging.getLogger(__name__)


def configure_tracing(app):
    if os.getenv("RACE_OTEL_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": "race-api"}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        return True
    except Exception:
        logger.exception("OpenTelemetry could not be initialized; continuing without tracing")
        return False
