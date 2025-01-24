from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

async def register_start_handler(dp: Dispatcher) -> None:
  @dp.message(CommandStart())
  async def start_handler(message: Message) -> None:
    await message.answer(f"Привет, {message.from_user.full_name}!")