"""
OpenTelemetry Integration dla Distributed Tracing
Zgodnie z regułami MDC dla monitoringu i observability
"""

from collections.abc import Awaitable, Callable
from functools import wraps
import logging
import os
from types import TracebackType
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from prometheus_client import start_http_server

logger = logging.getLogger(__name__)

from settings import settings

# Global tracer
tracer: trace.Tracer | None = None


def setup_telemetry(
    service_name: str = "foodsave-ai-backend",
    enable_jaeger: bool = True,
    enable_prometheus: bool = True,
    enable_console: bool = False,
) -> None:
    """Setup OpenTelemetry dla distributed tracing i metrics"""
    # Resource configuration
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )

    # Trace provider setup
    trace_provider = TracerProvider(resource=resource)

    # Jaeger exporter
    if enable_jaeger:
        jaeger_endpoint = os.getenv(
            "JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
        )
        jaeger_exporter = JaegerExporter(
            collector_endpoint=jaeger_endpoint,
        )
        trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    # Console exporter (for development)
    if enable_console or settings.ENVIRONMENT == "development":
        console_exporter = ConsoleSpanExporter()
        trace_provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set global trace provider
    trace.set_tracer_provider(trace_provider)
    get_tracer._instance = trace.get_tracer(__name__)

    # Metrics setup
    if enable_prometheus:
        setup_prometheus_metrics()


def setup_prometheus_metrics(port: int = 8001) -> None:
    """Setup Prometheus metrics exporter"""
    try:
        # Start Prometheus HTTP server
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start Prometheus server: {e}")


def instrument_sqlalchemy(engine: Any) -> None:
    """Instrument SQLAlchemy engine z OpenTelemetry"""
    SQLAlchemyInstrumentor.instrument(engine=engine)


def instrument_httpx() -> None:
    """Instrument HTTPX client z OpenTelemetry"""
    HTTPXClientInstrumentor.instrument()


def get_tracer() -> trace.Tracer:
    """Get global tracer instance"""
    if not hasattr(get_tracer, "_instance"):
        get_tracer._instance = trace.get_tracer(__name__)
    return get_tracer._instance


def create_span(name: str, attributes: dict | None = None) -> trace.Span:
    """Create a new span with given name and attributes"""
    current_tracer = get_tracer()
    span = current_tracer.start_span(name, attributes=attributes or {})
    return span


def add_span_event(span: trace.Span, name: str, attributes: dict | None = None) -> None:
    """Add event to span"""
    span.add_event(name, attributes=attributes or {})


def set_span_attribute(span: trace.Span, key: str, value: Any) -> None:
    """Set attribute on span"""
    span.set_attribute(key, value)


def record_exception(span: trace.Span, exception: Exception) -> None:
    """Record exception in span"""
    span.record_exception(exception)
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))


# Context managers dla spans
class SpanContext:
    """Context manager dla spans"""

    def __init__(self, name: str, attributes: dict | None = None) -> None:
        self.name = name
        self.attributes = attributes or {}
        self.span = None

    def __enter__(self) -> "SpanContext":
        self.span = create_span(self.name, self.attributes)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.span:
            if exc_type and isinstance(exc_val, Exception):
                record_exception(self.span, exc_val)
            self.span.end()


# Decorator dla funkcji z tracing
def traced_function(
    name: str | None = None, attributes: dict | None = None
) -> Callable[..., Any]:
    """Decorator to add tracing to functions"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            span_name = name or f"{func.__module__}.{func.__name__}"
            with SpanContext(span_name, attributes):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Async decorator
def traced_async_function(
    name: str | None = None, attributes: dict[str, Any] | None = None
) -> Callable[..., Any]:
    """Decorator to add tracing to async functions"""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            span_name = name or f"{func.__module__}.{func.__name__}"
            with SpanContext(span_name, attributes):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
