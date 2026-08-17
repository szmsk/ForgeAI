import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.queue.client import next_run
from app.db.session import SessionLocal, set_tenant_context
from app.db.models import Run, RunEvent
from app.models.schemas import RunRequest
from app.agent.engine import ForgeAgent

def utc(): return datetime.now(timezone.utc)

async def process(job:dict):
    async with SessionLocal() as db:
        await db.execute(__import__('sqlalchemy').text("SELECT set_config('app.bootstrap','true',true)"))
        run=await db.scalar(select(Run).where(Run.id==job['run_id'],Run.tenant_id==job['tenant_id']))
        if not run: return
        await set_tenant_context(db,run.tenant_id); await db.execute(__import__('sqlalchemy').text("SELECT set_config('app.bootstrap','false',true)"))
        run.status='running'; run.started_at=utc(); await db.commit()
        try:
            result=await asyncio.to_thread(ForgeAgent(job['request']['max_iterations']).run,RunRequest(**job['request']))
            run.status=result.status.value; run.iterations=result.iterations; run.tests_passed=result.tests_passed; run.tests_total=result.tests_total
            run.duration_ms=result.duration_ms; run.cost_usd=result.cost_usd; run.input_tokens=result.input_tokens; run.output_tokens=result.output_tokens
            run.summary=result.summary; run.pull_request_url=result.pull_request_url; run.finished_at=utc()
            for e in result.events:
                db.add(RunEvent(tenant_id=run.tenant_id,run_id=run.id,type=e.type,message=e.message,iteration=e.iteration,metadata_json=e.metadata))
            await db.commit()
        except Exception as exc:
            run.status='failed'; run.error=str(exc)[:4000]; run.finished_at=utc(); await db.commit()

async def main():
    while True:
        job=await next_run(5)
        if job:
            await process(job)

if __name__=='__main__': asyncio.run(main())
