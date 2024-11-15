import logging
from typing import TYPE_CHECKING

# ? General imports for common labels in OTEL
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_INSTANCE_ID, Resource

# ? Imports for setting up traces and exporting them to the OTLP endpoint
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# ? Imports for setting up metrics and exporting them to the OTLP endpoint
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# ? Imports for setting up logs and exporting them to the OTLP endpoint
from opentelemetry._logs import set_logger_provider
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

# ? Import for instrumenting HTTPX client
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# ? Import for instrumenting FastAPI app
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

#? Import for instrumenting Mysql
from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

from config import ProjectSettings, OTELSettings

if TYPE_CHECKING:
    from fastapi import FastAPI

project_settings = ProjectSettings()
otel_settings = OTELSettings()

logger = logging.getLogger(__name__)


def setup_otel() -> None:
    # ? Service name is required for most backends
    resource = Resource(
        attributes={
            SERVICE_NAME: project_settings.service_name,
            SERVICE_INSTANCE_ID: project_settings.service_instance_id,
            "service.environment": project_settings.env,
        }
    )

    # ? Setting up the TraceProvider for exporting traces to the OTLP endpoint
    trace_provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=f"{otel_settings.otel_exporter_otlp_endpoint}/v1/traces"
        )
    )
    trace_provider.add_span_processor(processor)
    trace.set_tracer_provider(trace_provider)

    # ? Setting up the MeterProvider for exporting metrics to the OTLP endpoint
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=f"{otel_settings.otel_exporter_otlp_endpoint}/v1/metrics"
        )
    )
    metric_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(metric_provider)

    # ? Setting up the LoggingInstrumentor for log, and log export to the OTLP endpoint
    LoggingInstrumentor().instrument(set_logging_format=True)
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)

    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=f"{otel_settings.otel_exporter_otlp_endpoint}/v1/logs"
            )
        )
    )
    otlp_logging_handler = LoggingHandler(
        level=logging.NOTSET, logger_provider=logger_provider
    )

    # Attach OTLP handler to root logger
    logging.getLogger().addHandler(otlp_logging_handler)

    logger.info("OTEL instrumentation setup complete")


def setup_pymysql_instrumentation() -> None:
    PyMySQLInstrumentor().instrument()

def setup_httpx_instrumentation() -> None:
    HTTPXClientInstrumentor().instrument()


def setup_fastapi_instrumentation(app: "FastAPI") -> None:
    FastAPIInstrumentor.instrument_app(app)