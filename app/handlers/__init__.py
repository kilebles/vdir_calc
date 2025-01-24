from aiogram import Dispatcher
from .start_handler import register_start_handler
from .admin_handler import register_admin_handler

async def register_handlers(dp: Dispatcher) -> None:
  await register_start_handler(dp)
  await register_admin_handler(dp)