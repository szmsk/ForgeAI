from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uuid, time
from app.api.routes import router
from app.core.config import settings
from app.observability.tracing import setup_tracing
setup_tracing(settings.otel_enabled,settings.otel_endpoint)
app=FastAPI(title='ForgeAI',version='2.0.0',description='Multi-tenant autonomous AI software engineering platform')
app.add_middleware(TrustedHostMiddleware,allowed_hosts=settings.allowed_hosts_list)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_list,allow_methods=['GET','POST','DELETE'],allow_headers=['Authorization','Content-Type','X-Idempotency-Key'])
class SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        rid=request.headers.get('X-Request-ID') or str(uuid.uuid4()); response=await call_next(request); response.headers['X-Request-ID']=rid; response.headers['X-Content-Type-Options']='nosniff'; response.headers['X-Frame-Options']='DENY'; response.headers['Referrer-Policy']='no-referrer'; response.headers['Content-Security-Policy']="default-src 'none'; frame-ancestors 'none'"; return response
app.add_middleware(SecurityHeaders)
app.include_router(router)
@app.get('/metrics',include_in_schema=False)
def metrics():
    from app.observability.metrics import metrics_response
    return metrics_response()
