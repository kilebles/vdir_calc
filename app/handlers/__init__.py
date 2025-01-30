from aiogram import Dispatcher
from .calc_handler import router as calc_command_router
from .start_handler import router as start_router
from .admin_handler import router as admin_router
from .callbacks.post_callbacks import router as post_router
from .callbacks.calc_callbacks import router as calc_router

async def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(calc_command_router)
    dp.include_router(post_router)
    dp.include_router(calc_router)