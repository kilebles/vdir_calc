from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.database import add_user

router = Router()

@router.message()
async def start_handler(message: Message) -> None:
  tg_id = message.from_user.id
  username = message.from_user.username
  
  await add_user(tg_id, username)
  await message.answer(f"Привет, ты успешно зарегистрирован")