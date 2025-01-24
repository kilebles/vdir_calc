from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

async def register_admin_handler(dp: Dispatcher) -> None:
  @dp.message(Command(commands=["admin"]))
  async def admin_handler(message: Message) -> None:
    await message.answer("Это админская команда")