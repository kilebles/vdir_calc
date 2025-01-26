from datetime import time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import CONFIG
from app.database.models import Base, Post

engine = create_async_engine(CONFIG.DATABASE_URL, echo=True)

async_session = sessionmaker(
  bind=engine,
  expire_on_commit=False,
  class_=AsyncSession
)

#^ Инициализируем БД 
async def init_db():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)


#^ Получаем все посты из БД 
async def get_all_posts():
  async with async_session() as session:
    query = select(Post.id, Post.title)
    result = await session.execute(query)
    posts = [{"id": row.id, "title": row.title} for row in result.fetchall()]
  return posts


#^ Добавление нового поста в БД
async def add_post(title: str, content: str, media_content: str, schedule_time: time):
    async with async_session() as session:
        try:
            post = Post(
                title=title,
                content=content,
                media_content=media_content,
                schedule_time=schedule_time,
            )
            session.add(post)
            await session.commit()
            return post
        except Exception as e:
            await session.rollback()
            raise e
  

#^ Удаление поста
async def delete_post(post_id: int):
  async with async_session() as session:
    post = await session.get(Post, post_id)
    if post:
      await session.delete(post)
      await session.commit()
      return True
    return False
  

#^ Просмотр поста
async def get_post_by_id(post_id: int):
  async with async_session() as session:
    query = select(Post).where(Post.id == post_id)
    result = await session.execute(query)
    post = result.scalar_one_or_none()
    return post