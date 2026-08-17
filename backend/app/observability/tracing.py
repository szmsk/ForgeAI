from contextlib import contextmanager
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
_provider=None

def setup_tracing(enabled=True,endpoint=''):
    global _provider
    if not enabled or _provider:return
    _provider=TracerProvider(resource=Resource.create({'service.name':'forgeai'}))
    _provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_provider)
@contextmanager
def span(name:str,**attrs):
    with trace.get_tracer('forgeai').start_as_current_span(name) as s:
        for k,v in attrs.items(): s.set_attribute(k,str(v))
        yield s
