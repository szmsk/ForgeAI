from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
RUNS=Counter('forgeai_runs_total','Agent runs',['status'])
RUN_DURATION=Histogram('forgeai_run_duration_seconds','Agent run duration')
LLM_TOKENS=Counter('forgeai_llm_tokens_total','LLM token usage',['direction'])
HTTP_REQUESTS=Counter('forgeai_http_requests_total','HTTP requests',['method','path','status'])
def metrics_response(): return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
