from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, Response
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db, set_tenant_context
from app.db.models import Tenant, User, Run, RunEvent, ApiKey
from app.auth.security import hash_password, verify_password, create_access_token, new_api_key
from app.auth.deps import current_principal
from app.models.schemas import *
from app.queue.client import enqueue_run, rate_limit
from app.core.config import settings

router=APIRouter(prefix='/api/v1',tags=['forgeai'])

def utc(): return datetime.now(timezone.utc)

@router.post('/auth/register',response_model=TokenResponse)
async def register(body:RegisterRequest, db:AsyncSession=Depends(get_db)):
    await db.execute(__import__('sqlalchemy').text("SELECT set_config('app.bootstrap','true',true)"))
    if await db.scalar(select(User).where(User.email==body.email.lower())): raise HTTPException(409,'Email already registered')
    tenant=Tenant(name=body.tenant_name.strip())
    db.add(tenant); await db.flush()
    user=User(tenant_id=tenant.id,email=body.email.lower(),password_hash=hash_password(body.password),role='owner')
    db.add(user); await db.commit(); await db.execute(__import__('sqlalchemy').text("SELECT set_config('app.bootstrap','false',true)"))
    return TokenResponse(access_token=create_access_token(user.id,tenant.id,user.role),expires_in=settings.access_token_minutes*60)

@router.post('/auth/login',response_model=TokenResponse)
async def login(body:LoginRequest, db:AsyncSession=Depends(get_db)):
    await db.execute(__import__('sqlalchemy').text("SELECT set_config('app.bootstrap','true',true)"))
    user=await db.scalar(select(User).where(User.email==body.email.lower()))
    await db.execute(__import__('sqlalchemy').text("SELECT set_config('app.bootstrap','false',true)"))
    if not user or not user.is_active or not verify_password(body.password,user.password_hash): raise HTTPException(401,'Invalid credentials')
    await set_tenant_context(db,user.tenant_id)
    return TokenResponse(access_token=create_access_token(user.id,user.tenant_id,user.role),expires_in=settings.access_token_minutes*60)

@router.get('/me')
async def me(user:User=Depends(current_principal)):
    return {'id':user.id,'email':user.email,'tenant_id':user.tenant_id,'role':user.role}

@router.post('/api-keys',response_model=ApiKeyResponse)
async def create_key(body:ApiKeyCreate,user:User=Depends(current_principal),db:AsyncSession=Depends(get_db)):
    if user.role not in {'owner','admin'}: raise HTTPException(403,'Admin role required')
    raw,prefix,key_hash=new_api_key(); item=ApiKey(tenant_id=user.tenant_id,name=body.name,prefix=prefix,key_hash=key_hash)
    db.add(item); await db.commit(); return ApiKeyResponse(id=item.id,name=item.name,prefix=prefix,key=raw)

@router.delete('/api-keys/{key_id}',status_code=204)
async def revoke_key(key_id:str,user:User=Depends(current_principal),db:AsyncSession=Depends(get_db)):
    item=await db.scalar(select(ApiKey).where(ApiKey.id==key_id,ApiKey.tenant_id==user.tenant_id))
    if not item: raise HTTPException(404,'API key not found')
    item.revoked=True; await db.commit(); return Response(status_code=204)

@router.get('/health',response_model=HealthResponse)
async def health(db:AsyncSession=Depends(get_db)):
    deps={}
    try: await db.execute(select(func.count()).select_from(Tenant)); deps['postgres']='ok'
    except Exception: deps['postgres']='error'
    try:
        from app.queue.client import redis; await redis.ping(); deps['redis']='ok'
    except Exception: deps['redis']='error'
    return HealthResponse(status='ok' if all(v=='ok' for v in deps.values()) else 'degraded',service='forgeai',version='2.0.0',dependencies=deps)

@router.post('/runs',response_model=RunAccepted,status_code=202)
async def create_run(body:RunRequest,user:User=Depends(current_principal),db:AsyncSession=Depends(get_db),idempotency_key:str|None=Header(default=None,alias='X-Idempotency-Key')):
    if not await rate_limit(f'tenant:{user.tenant_id}',settings.rate_limit_per_minute): raise HTTPException(429,'Rate limit exceeded')
    if idempotency_key:
        existing=await db.scalar(select(Run).where(Run.tenant_id==user.tenant_id,Run.idempotency_key==idempotency_key))
        if existing: return RunAccepted(id=existing.id,status=RunStatus(existing.status))
    active=await db.scalar(select(func.count()).select_from(Run).where(Run.tenant_id==user.tenant_id,Run.status.in_(['queued','running'])))
    if active >= settings.run_concurrency_per_tenant: raise HTTPException(429,'Tenant run concurrency limit reached')
    run=Run(tenant_id=user.tenant_id,user_id=user.id,idempotency_key=idempotency_key,repository=body.repository,task=body.task,status='queued')
    db.add(run); await db.commit()
    await enqueue_run({'run_id':run.id,'tenant_id':user.tenant_id,'user_id':user.id,'request':body.model_dump()})
    return RunAccepted(id=run.id,status=RunStatus.queued)

@router.get('/runs/{run_id}',response_model=RunResponse)
async def get_run(run_id:str,user:User=Depends(current_principal),db:AsyncSession=Depends(get_db)):
    run=await db.scalar(select(Run).where(Run.id==run_id,Run.tenant_id==user.tenant_id))
    if not run: raise HTTPException(404,'Run not found')
    events=(await db.scalars(select(RunEvent).where(RunEvent.run_id==run.id,RunEvent.tenant_id==user.tenant_id).order_by(RunEvent.created_at))).all()
    return RunResponse(id=run.id,status=run.status,repository=run.repository,task=run.task,events=[Event(type=e.type,message=e.message,iteration=e.iteration,metadata=e.metadata_json,timestamp=e.created_at.isoformat()) for e in events],files_changed=[],tests_passed=run.tests_passed,tests_total=run.tests_total,iterations=run.iterations,duration_ms=run.duration_ms,cost_usd=run.cost_usd,input_tokens=run.input_tokens,output_tokens=run.output_tokens,pull_request_url=run.pull_request_url,summary=run.summary or run.error or '')

@router.get('/runs')
async def list_runs(user:User=Depends(current_principal),db:AsyncSession=Depends(get_db),limit:int=50):
    limit=max(1,min(limit,100)); rows=(await db.scalars(select(Run).where(Run.tenant_id==user.tenant_id).order_by(desc(Run.created_at)).limit(limit))).all()
    return [{'id':r.id,'status':r.status,'task':r.task,'repository':r.repository,'created_at':r.created_at.isoformat(),'tests':f'{r.tests_passed}/{r.tests_total}','cost_usd':r.cost_usd} for r in rows]
