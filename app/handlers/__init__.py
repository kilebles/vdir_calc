from aiogram import Dispatcher
from .start_handler import router as start_router
from .admin_handler import router as admin_router
from .callbacks.post_callbacks import router as post_router

async def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(post_router)