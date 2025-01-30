from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from app.UI.inline import get_calculator_keyboard

router = Router()

@router.message(Command(commands=["calc"]))
async def admin_handler(message: Message) -> None:
  text = "Пожалуйста, выберите тип расчета:\n<code>Экспедирование контейнера\Экспедирование сборки</code> 👇"
  keyboard = get_calculator_keyboard()
  
  await message.answer(
    text=text,
    reply_markup=keyboard,
    parse_mode="HTML"
  )