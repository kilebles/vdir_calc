import asyncio
import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.utils.states import FreightCalculationState
from app.utils.google_sheets import calculate_delivery_cost
from app.UI.inline import (
    get_calculator_keyboard,
    get_build_keyboard,
    get_confirm_keyboard,
)
from app.handlers.callbacks.callback_data import (
    ContinueStartCallback,
    CalcBuildCallback,
    CalcBackToMenu,
    CalcAutoCallback,
    CalcAviaCallback,
    CalcZdCallback,
    CalcConteinersCallback,
    CalcConfirmCallback,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

router = Router()


# region #&Вызов клав
# ^ Вызов клавиатуры калькулей
@router.callback_query(ContinueStartCallback.filter())
async def Continue_handler(callback: CallbackQuery):
    text = "Пожалуйста, выберите тип расчета:\n<code>Экспедирование контейнера\Экспедирование сборки</code> 👇"
    keyboard = get_calculator_keyboard()

    await callback.message.edit_text(
        text=text, reply_markup=keyboard, parse_mode="HTML"
    )

    await callback.answer()


# ^ Вызов клавиатуры сборки
@router.callback_query(CalcBuildCallback.filter())
async def Build_handler(callback: CallbackQuery):
    text = "<b>Выберите метод доставки 👇🏻</b>"
    keyboard = get_build_keyboard()

    await callback.message.edit_text(
        text=text, reply_markup=keyboard, parse_mode="HTML"
    )

    await callback.answer()


# ^ Обработка кнопки назад в клавиатуру калькулей
@router.callback_query(CalcBackToMenu.filter())
async def Back_to_calc_menu_handler(callback: CallbackQuery):
    text = "Пожалуйста, выберите тип расчета:\n<code>Экспедирование контейнера\Экспедирование сборки</code> 👇🏻"
    keyboard = get_calculator_keyboard()

    await callback.message.edit_text(
        text=text, reply_markup=keyboard, parse_mode="HTML"
    )

    await callback.answer()


# endregion


# region #&auto
# ^ Старт ввода данных
@router.callback_query(CalcAutoCallback.filter())
async def start_calculation(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FreightCalculationState.entering_origin_city)
    await callback.message.answer(
        text="<b>🚚 Введите город отправления:</b>", parse_mode="HTML"
    )
    await callback.answer()


# ^ Ввод города отправления
@router.message(FreightCalculationState.entering_origin_city)
async def enter_origin_city(message: Message, state: FSMContext):
    await state.update_data(origin_city=message.text)
    data = await state.get_data()
    logging.info(f"🚚 Введен город отправления: {data}")
    await state.set_state(FreightCalculationState.entering_destination_city)
    await message.answer(text="<b>🏙 Введите город доставки:</b>", parse_mode="HTML")


# ^ Ввод города доставки
@router.message(FreightCalculationState.entering_destination_city)
async def enter_destination_sity(message: Message, state: FSMContext):
    await state.update_data(destination_city=message.text)
    data = await state.get_data()
    logging.info(f"🏙 Введен город доставки: {data}")
    await state.set_state(FreightCalculationState.entering_weight)
    await message.answer(text="<b>⚖ Введите вес груза (кг):</b>", parse_mode="HTML")


# ^ Ввод веса груза
@router.message(FreightCalculationState.entering_weight)
async def enter_weigth(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        await state.update_data(weight=weight)
        await state.set_state(FreightCalculationState.entering_volume)
        await message.answer(
            text="<b>📦 Введите объем груза (м³):</b>", parse_mode="HTML"
        )
    except ValueError:
        error_message = await message.answer("❌ Введите число!")
        await asyncio.sleep(3)
        await error_message.delete()


# ^ Ввод объема гурза
@router.message(FreightCalculationState.entering_volume)
async def enter_volume(message: Message, state: FSMContext):
    try:
        volume = float(message.text)
        await state.update_data(volume=volume)
        await state.set_state(FreightCalculationState.confirming_data)

        data = await state.get_data()
        response = (
            f"<b>Вы ввели:</b>\n\n"
            f"🚚 <b>Город отправления: <code>{data['origin_city']}</code></b>\n"
            f"🏙 <b>Город доставки: <code>{data['destination_city']}</code></b>\n"
            f"⚖ <b>Вес: <code>{data['weight']} кг</code></b>\n"
            f"📦 <b>Объем: <code>{data['volume']} м³</code></b>\n"
        )

        keyboard = get_confirm_keyboard()

        await message.answer(response, reply_markup=keyboard, parse_mode="HTML")

    except ValueError:
        error_message = await message.answer("❌ Введите число!")
        await asyncio.sleep(3)
        await error_message.delete()


#^ Подтверждение и расчет стоимости доставки
@router.callback_query(CalcConfirmCallback.filter())
async def confirm_calculation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Проверяем, что все данные на месте
    required_keys = ["origin_city", "destination_city", "weight", "volume"]
    missing_keys = [key for key in required_keys if key not in data]

    if missing_keys:
        await callback.message.answer(f"❌ Ошибка: отсутствуют данные {', '.join(missing_keys)}. Повторите ввод.")
        await state.clear()
        return

    try:
        result = calculate_delivery_cost(
            origin_city=data["origin_city"],
            destination_city=data["destination_city"],
            weight=data["weight"],
            volume=data["volume"]
        )

        response = (
            f"✅ <b>Расчет стоимости доставки:</b>\n\n"
            f"🚚 <b>Город отправления:</b> <code>{result['origin_city']}</code>\n"
            f"🏙 <b>Город доставки:</b> <code>{result['destination_city']}</code>\n"
            f"⚖ <b>Вес груза:</b> <code>{result['weight']} кг</code>\n"
            f"📦 <b>Объем груза:</b> <code>{result['volume']} м³</code>\n\n"
            f"💰 <b>Стоимость до границы:</b> <code>{result['cost_before_border']:.2f} руб.</code>\n"
            f"💰 <b>Стоимость после границы:</b> <code>{result['cost_after_border']:.2f} руб.</code>\n"
            f"💰 <u><b>Общая стоимость доставки:</b> <code>{result['total_cost']:.2f} руб.</code></u>\n"
        )

        await callback.message.answer(response, parse_mode="HTML")
        await state.clear()

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при расчете: {e}")
        await state.clear()

# endregion