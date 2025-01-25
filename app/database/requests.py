from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import CONFIG
from app.database.models import Base

engine = create_async_engine(CONFIG.DATABASE_URL, echo=True)

async_session = sessionmaker(
  bind=engine,
  expire_on_commit=False,
  class_=AsyncSession
)

async def init_db():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)