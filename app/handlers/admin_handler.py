import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.database.requests import get_all_posts
from app.UI.inline import get_admin_keyboard
from app.core.config import CONFIG

router = Router()

@router.message(Command(commands=["admin"]))
async def admin_handler(message: Message) -> None:
  print(f"User ID: {message.from_user.id}")
  print(f"Admin IDs: {CONFIG.ADMIN_IDS}")
  
  if message.from_user.id not in CONFIG.ADMIN_IDS:
    error_message = await message.answer("❗ У вас нет доступа к этой команде")
    await asyncio.sleep(3)
    await error_message.delete()
    return
  
  posts = await get_all_posts()
  keyboard = get_admin_keyboard(posts)
  await message.answer(
    text="<b>Вы можете создать новый пост для рассылки,\nили <code>изменить\отключить\удалить</code> существующий 👇🏻</b>",
    reply_markup=keyboard,
    parse_mode="HTML"
  )
    
  