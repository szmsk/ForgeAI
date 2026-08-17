from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.db.models import Base
from app.core.config import settings
config=context.config
config.set_main_option('sqlalchemy.url',settings.database_url)
if config.config_file_name:fileConfig(config.config_file_name)
target_metadata=Base.metadata
async def run_migrations_online():
    connectable=async_engine_from_config(config.get_section(config.config_ini_section,{}),prefix='sqlalchemy.',poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(lambda conn: context.configure(connection=conn,target_metadata=target_metadata))
        await connection.run_sync(lambda conn: context.run_migrations())
    await connectable.dispose()
import asyncio
asyncio.run(run_migrations_online())
