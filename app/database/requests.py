from datetime import time
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import CONFIG
from app.database.models import Base, Post, User

engine = create_async_engine(CONFIG.DATABASE_URL, echo=True)

async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


# ^ Инициализируем БД
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# region #&Posts
# ^ Получаем все посты из БД
async def get_all_posts():
    async with async_session() as session:
        query = select(Post.id, Post.title, Post.is_active, Post.schedule_time)
        result = await session.execute(query)
        posts = [
            {
                "id": row.id,
                "title": row.title,
                "is_active": row.is_active,
                "schedule_time": row.schedule_time,
            }
            for row in result.fetchall()
        ]
    return posts


# ^ Добавление нового поста в БД
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


# ^ Удаление поста
async def delete_post(post_id: int):
    async with async_session() as session:
        post = await session.get(Post, post_id)
        if post:
            await session.delete(post)
            await session.commit()
            return True
        return False


# ^ Просмотр поста
async def get_post_by_id(post_id: int):
    async with async_session() as session:
        query = select(Post).where(Post.id == post_id)
        result = await session.execute(query)
        post = result.scalar_one_or_none()
        return post


# ^ Обновление описания поста
async def update_post_description(post_id: id, new_description: str):
    async with async_session() as session:
        await session.execute(
            update(Post).where(Post.id == post_id).values(content=new_description)
        )
        await session.commit()


# ^ Обновление медиа поста
async def update_post_media(post_id: int, media_file_id: str):
    async with async_session() as session:
        await session.execute(
            update(Post).where(Post.id == post_id).values(media_content=media_file_id)
        )
        await session.commit()


# ^ Обновление времени рассылки поста
async def update_post_time(post_id: int, schedule_time: time):
    async with async_session() as session:
        await session.execute(
            update(Post).where(Post.id == post_id).values(schedule_time=schedule_time)
        )
        await session.commit()


# ^ Переключение активности поста
async def toggle_post_active(post_id: int, is_active: bool):
    async with async_session() as session:
        stmt = update(Post).where(Post.id == post_id).values(is_active=is_active)
        await session.execute(stmt)
        await session.commit()


# endregion


# region #&Users
# ^ Регаем юзера
async def add_user(tg_id: int, username: str):
    async with async_session() as session:
        user = await session.execute(select(User).where(User.tg_id == tg_id))
        if user.scalar_one_or_none() is None:
            new_user = User(tg_id=tg_id, username=username)
            session.add(new_user)
            await session.commit()
            return new_user


# ^ Получаем всех юзеров
async def get_all_users():
    async with async_session() as session:
        query = select(User.tg_id)
        result = await session.execute(query)
        users = [row.tg_id for row in result.fetchall()]
        return users
