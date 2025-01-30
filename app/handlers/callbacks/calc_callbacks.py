import asyncio
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.UI.inline import get_calculator_keyboard
from app.handlers.callbacks.callback_data import(
  ContinueStartCallback,
  CalcBuildCallback,
  CalcConteinersCallback,
)

router = Router()

@router.callback_query(ContinueStartCallback.filter())
async def Continue_handler(callback: CallbackQuery):
  text = "Пожалуйста, выберите тип расчета:\n<code>Экспедирование контейнера\Экспедирование сборки</code> 👇"
  keyboard = get_calculator_keyboard()
  
  await callback.message.edit_text(
    text=text,
    reply_markup=keyboard,
    parse_mode="HTML"
  )
  
  await callback.answer()