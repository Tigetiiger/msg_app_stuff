from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://app:app@127.0.0.1:5432/appdb"

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"server_settings": {"search_path": "app,public"}},
)

Session = async_sessionmaker(engine, expire_on_commit=False)


async def ping():
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
