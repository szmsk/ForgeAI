from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from app.core.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    async with SessionLocal() as session:
        yield session

async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    # PostgreSQL RLS reads this transaction-local setting.
    await session.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {'tenant_id': tenant_id})
