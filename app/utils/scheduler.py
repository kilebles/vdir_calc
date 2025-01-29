import logging
import asyncio
from aiogram import Bot
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database.requests import get_all_posts, get_all_users, get_post_by_id

async def send_post(bot: Bot, post_id: int):
    post = await get_post_by_id(post_id)
    
    if not post:
        return
    
    users = await get_all_users()
    
    for user_id in users:
        try:
            if post.media_content:
                if post.media_content.startswith("AgAC"):
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=post.media_content,
                        caption=f"{post.title}\n\n{post.content}",
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_video(
                        chat_id=user_id,
                        video=post.media_content,
                        caption=f"{post.title}\n\n{post.content}",
                        parse_mode="HTML"
                    )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"{post.title}\n\n{post.content}",
                    parse_mode="HTML"
                )
        except Exception as e:
            logging.error(f"Ошибка при отправке поста пользователю {user_id}: {e}")


async def schedule_posts(bot: Bot, scheduler: AsyncIOScheduler):
    posts = await get_all_posts()
    now = datetime.now()

    for post in posts:
        if not post.get("is_active") or not post.get("schedule_time"):
            continue

        schedule_time = datetime.combine(now.date(), post["schedule_time"])

        if schedule_time < now:
            schedule_time += timedelta(days=1)

        job_id = f"post_{post['id']}"
        
        if scheduler.get_job(job_id) is None:
            scheduler.add_job(
                send_post,
                "date",
                run_date=schedule_time,
                args=[bot, post["id"]],
                id=job_id,
                replace_existing=True
            )
            logging.info(f"Задача для поста {post['id']} запланирована на {schedule_time}")


async def background_task(bot: Bot, scheduler: AsyncIOScheduler):
    while True:
        await schedule_posts(bot, scheduler)
        await asyncio.sleep(60)


def start_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    scheduler.start()
    asyncio.create_task(background_task(bot, scheduler))
    return scheduler