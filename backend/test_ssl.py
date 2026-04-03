import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
async def test():
    engine = create_async_engine(
        settings.async_database_url,
        connect_args={"ssl": "require"}
    )
    async with engine.connect() as conn:
        print("Connected!")
asyncio.run(test())
