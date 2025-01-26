from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from app.database.requests import get_all_posts
from app.UI.inline import get_admin_keyboard
from app.handlers.callbacks.post_callbacks import register_post_callbacks

async def register_admin_handler(dp: Dispatcher) -> None:
  @dp.message(Command(commands=["admin"]))
  async def admin_handler(message: Message) -> None:
    posts = await get_all_posts()
    keyboard = get_admin_keyboard(posts)
    await message.answer(
      text="<b>Вы можете создать новый пост для рассылки,\nили <code>изменить\отключить\удалить</code> существующий 👇🏻</b>",
      reply_markup=keyboard,
      parse_mode="HTML"
    )
    
  register_post_callbacks(dp)