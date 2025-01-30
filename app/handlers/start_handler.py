from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.database import add_user
from app.UI.inline import get_continue_keyboard

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message) -> None:
  tg_id = message.from_user.id
  username = message.from_user.username
  text = f"""
<b>👋 Добро пожаловать, {username or 'друг'}!</b>

Я — ваш персональный помощник по расчёту стоимости доставки грузов. 
Готов помочь быстро и точно рассчитать доставку любым удобным для вас способом: 
<code>✈️ авиа, 🚛 авто или 🚂 ж/д</code>

Что я умею?
✔️ <i>Рассчитать стоимость доставки для любого типа груза.
✔️ Подсказать подходящий тариф, учитывая вес, объём и пункты отправки/доставки.
✔️ Проверить корректность введённых данных и помочь исправить ошибки.
✔️ Предоставить понятный результат в считанные секунды.</i>

<b>Как это работает?</b>
1️⃣ Выберите подходящий <u>способ доставки</u>.
2️⃣ Укажите <u>данные о грузе</u>, следуя простым шагам.
3️⃣ Получите <u>готовый расчёт</u> и начните планировать перевозку!

<b>Если вы готовы, нажмите кнопку ниже, чтобы начать:</b>
"""

  keyboard = get_continue_keyboard()
  
  await add_user(tg_id, username)
  await message.answer(
    text=text,
    reply_markup=keyboard,
    parse_mode="HTML"
  )