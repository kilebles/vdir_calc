import asyncio
import logging

from aiogram import Router
from thefuzz import process
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.utils.states import FreightCalculationState, FreightContainerState
from app.utils.google_sheets import calculate_container_cost, calculate_delivery_cost, get_google_sheet, get_tariff_zhd
from app.UI.inline import (
    get_calculator_keyboard,
    get_build_keyboard,
    get_confirm_keyboard,
    get_confirm_keyboard_for_containers,
    get_confirm_keyboard_for_zhd,
)
from app.handlers.callbacks.callback_data import (
    CalcConfirmZhdCallback,
    CalcContainersCallback,
    ContinueStartCallback,
    CalcBuildCallback,
    CalcBackToMenu,
    CalcAutoCallback,
    CalcAviaCallback,
    CalcZdCallback,
    CalcConfirmCallback,
    CalcConfirmContainersCallback
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

router = Router()


# region #& Исправлеие городов


def get_available_cities(sheet_name, column_index):
    sheet = get_google_sheet(sheet_name)
    cities = sheet.col_values(column_index)
    clean_cities = [city.strip().lower() for city in cities if city.strip()]
    
    logging.info(f"📜 Доступные города в {sheet_name}: {clean_cities}")
    return clean_cities


def find_closest_city(city, available_cities):
    match, score = process.extractOne(city, available_cities)
    logging.info(f"🔍 Ближайшее совпадение для '{city}': {match} (Точность: {score}%)")
    return match if score > 75 else None


def get_available_ports(sheet_name, column_index=3):
    sheet = get_google_sheet(sheet_name)
    ports = sheet.col_values(column_index)
    clean_ports = [port.strip() for port in ports if port.strip()]
    logging.info(f"📜 Доступные порты в {sheet_name}: {clean_ports}")
    return clean_ports


def get_available_cities_rw(sheet_name, column_index=4):
    sheet = get_google_sheet(sheet_name)
    cities = sheet.col_values(column_index)
    clean_cities = [city.strip() for city in cities if city.strip()]
    logging.info(f"📜 Доступные города в {sheet_name}: {clean_cities}")
    return clean_cities


def find_closest_location(location, available_locations):
    match, score = process.extractOne(location, available_locations)
    logging.info(f"🔍 Ближайшее совпадение для '{location}': {match} (Точность: {score}%)")
    return match if score > 75 else None


# endregion


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


# ^ Ввод города отправителя
@router.message(FreightCalculationState.entering_origin_city)
async def enter_origin_city(message: Message, state: FSMContext):
    city = message.text.strip().lower()
    
    available_cities = get_available_cities("RAW Сборка Авто", 1)  # Берем POL City

    if city in available_cities:
        sheet = get_google_sheet("RAW Сборка Авто")
        row_index = available_cities.index(city) + 1
        pod_city = sheet.cell(row_index, 2).value  # Берем POD City

        if pod_city and pod_city.strip():
            pod_city = pod_city.strip()
            await state.update_data(origin_city=city.capitalize(), intermediate_city=pod_city)
            logging.info(f"🚚 Введен город отправления: {city.capitalize()}, промежуточный город: {pod_city}")

            await state.set_state(FreightCalculationState.entering_destination_city)
            await message.answer(
                f"<b>🏙 Введите конечный город доставки в РФ:</b>", parse_mode="HTML"
            )
        else:
            logging.error(f"❌ Ошибка: Не найден POD City для {city} в таблице RAW Сборка Авто!")
            await message.answer(
                f"❌ Ошибка: Не найден промежуточный город для {city}. Проверьте данные."
            )
    else:
        corrected_city = find_closest_city(city, available_cities)
        if corrected_city:
            await message.answer(
                f"🔍 Вы имели в виду <b>{corrected_city.capitalize()}</b>? (Исправлено автоматически)",
                parse_mode="HTML"
            )
            
            sheet = get_google_sheet("RAW Сборка Авто")
            row_index = available_cities.index(corrected_city) + 1
            pod_city = sheet.cell(row_index, 2).value.strip()

            await state.update_data(origin_city=corrected_city.capitalize(), intermediate_city=pod_city)
            logging.info(f"🚚 Введен город отправления: {corrected_city.capitalize()}, промежуточный город: {pod_city}")

            await state.set_state(FreightCalculationState.entering_destination_city)
            await message.answer(
                f"<b>🏙 Введите конечный город доставки в РФ:</b>", parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ Город не найден в базе. Проверьте правильность написания и попробуйте снова.\n\n"
                f"📜 Список доступных городов: {', '.join(available_cities[:10])}..."
            )
            

# ^ Ввод города доставки
@router.message(FreightCalculationState.entering_destination_city)
async def enter_destination_city(message: Message, state: FSMContext):
    city = message.text.strip().lower()
    data = await state.get_data()
    pod_city = data.get("intermediate_city")

    available_cities = get_available_cities("RAW Сборка по РФ", 2)

    if city in available_cities:
        await state.update_data(destination_city=city.capitalize())
        logging.info(f"🏙 Введен конечный город доставки: {city}")

        await state.set_state(FreightCalculationState.entering_weight)
        await message.answer("<b>⚖ Введите вес груза (кг):</b>", parse_mode="HTML")
    else:
        corrected_city = find_closest_city(city, available_cities)
        if corrected_city:
            await message.answer(f"🔍 Вы имели в виду <b>{corrected_city.capitalize()}</b>? (Исправлено автоматически)",
                                 parse_mode="HTML")
            await state.update_data(destination_city=corrected_city.capitalize()) 
            await state.set_state(FreightCalculationState.entering_weight) 
            await message.answer("<b>⚖ Введите вес груза (кг):</b>", parse_mode="HTML") 
        else:
            await message.answer(f"❌ Город не найден в базе. Проверьте правильность написания и попробуйте снова.\n\n"
                                 f"📜 Список доступных городов: {', '.join(available_cities[:10])}...")


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


# ^ Подтверждение и расчет стоимости доставки
@router.callback_query(CalcConfirmCallback.filter())
async def confirm_calculation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    required_keys = ["origin_city", "destination_city", "weight", "volume"]
    missing_keys = [key for key in required_keys if key not in data]

    if missing_keys:
        await callback.message.edit_text(
            f"❌ Ошибка: отсутствуют данные {', '.join(missing_keys)}. Повторите ввод."
        )
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

        await callback.message.edit_text(response, parse_mode="HTML")
        await state.clear()

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при расчете: {e}")
        await state.clear()


# endregion


# region #&ZHD


# ^ Старт ввода данных для ЖД
@router.callback_query(CalcZdCallback.filter())
async def start_calculation_zhd(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FreightCalculationState.entering_origin_city_zhd)
    await callback.message.answer(
        text="<b>🚂 Введите город отправления (ЖД):</b>", parse_mode="HTML"
    )
    await callback.answer()


# ^ Ввод города отправителя для ЖД
@router.message(FreightCalculationState.entering_origin_city_zhd)
async def enter_origin_city_zhd(message: Message, state: FSMContext):
    city = message.text.strip().lower()
    available_cities = get_available_cities("RAW Сборка ЖД", 1)

    if city in available_cities:
        await state.update_data(origin_city=city.capitalize())
        logging.info(f"🚂 Введен город отправления: {city.capitalize()}")

        await state.set_state(FreightCalculationState.entering_destination_city_zhd)
        await message.answer("<b>🏙 Введите конечный город доставки в РФ:</b>", parse_mode="HTML")
    else:
        corrected_city = find_closest_city(city, available_cities)
        if corrected_city:
            await message.answer(f"🔍 Вы имели в виду <b>{corrected_city.capitalize()}</b>? (Исправлено автоматически)",
                                 parse_mode="HTML")
            await state.update_data(origin_city=corrected_city.capitalize())
            await state.set_state(FreightCalculationState.entering_destination_city_zhd)
            await message.answer("<b>🏙 Введите конечный город доставки в РФ:</b>", parse_mode="HTML")
        else:
            await message.answer(f"❌ Город не найден в базе. Проверьте правильность написания и попробуйте снова.\n\n"
                                 f"📜 Список доступных городов: {', '.join(available_cities[:10])}...")


# ^ Ввод города доставки для ЖД
@router.message(FreightCalculationState.entering_destination_city_zhd)
async def enter_destination_city_zhd(message: Message, state: FSMContext):
    city = message.text.strip().lower()
    available_cities = get_available_cities("RAW Сборка ЖД", 2)

    if city in available_cities:
        await state.update_data(destination_city=city.capitalize())
        logging.info(f"🏙 Введен конечный город доставки (ЖД): {city}")

        await state.set_state(FreightCalculationState.entering_weight_zhd)
        await message.answer("<b>⚖ Введите вес груза (кг):</b>", parse_mode="HTML")
    else:
        corrected_city = find_closest_city(city, available_cities)
        if corrected_city:
            await message.answer(f"🔍 Вы имели в виду <b>{corrected_city.capitalize()}</b>? (Исправлено автоматически)",
                                 parse_mode="HTML")
            await state.update_data(destination_city=corrected_city.capitalize())
            await state.set_state(FreightCalculationState.entering_weight_zhd)
            await message.answer("<b>⚖ Введите вес груза (кг):</b>", parse_mode="HTML")
        else:
            await message.answer(f"❌ Город не найден в базе. Проверьте правильность написания и попробуйте снова.\n\n"
                                 f"📜 Список доступных городов: {', '.join(available_cities[:10])}...")


# ^ Ввод веса груза для ЖД
@router.message(FreightCalculationState.entering_weight_zhd)
async def enter_weight_zhd(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        await state.update_data(weight=weight)
        await state.set_state(FreightCalculationState.entering_volume_zhd)
        await message.answer("<b>📦 Введите объем груза (м³):</b>", parse_mode="HTML")
    except ValueError:
        error_message = await message.answer("❌ Введите число!")
        await asyncio.sleep(3)
        await error_message.delete()
        

# ^ Ввод объема груза для ЖД
@router.message(FreightCalculationState.entering_volume_zhd)
async def enter_volume_zhd(message: Message, state: FSMContext):
    try:
        volume = float(message.text)
        await state.update_data(volume=volume)
        await state.set_state(FreightCalculationState.confirming_data_zhd)

        data = await state.get_data()
        response = (
            f"<b>Вы ввели (ЖД):</b>\n\n"
            f"🚂 <b>Город отправления: <code>{data['origin_city']}</code></b>\n"
            f"🏙 <b>Город доставки: <code>{data['destination_city']}</code></b>\n"
            f"⚖ <b>Вес: <code>{data['weight']} кг</code></b>\n"
            f"📦 <b>Объем: <code>{data['volume']} м³</code></b>\n"
        )

        keyboard = get_confirm_keyboard_for_zhd()
        await message.answer(response, reply_markup=keyboard, parse_mode="HTML")

    except ValueError:
        error_message = await message.answer("❌ Введите число!")
        await asyncio.sleep(3)
        await error_message.delete()
        
        
# ^ Подтверждение формы ЖД
@router.callback_query(CalcConfirmZhdCallback.filter())
async def confirm_calculation_zhd(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    required_keys = ["origin_city", "destination_city", "weight", "volume"]
    missing_keys = [key for key in required_keys if key not in data]

    if missing_keys:
        await callback.message.edit_text(
            f"❌ Ошибка: отсутствуют данные {', '.join(missing_keys)}. Повторите ввод."
        )
        await state.clear()
        return

    try:
        result = get_tariff_zhd(
            origin_city=data["origin_city"],
            destination_city=data["destination_city"],
            weight=data["weight"],
            volume=data["volume"]
        )

        response = (
            f"✅ <b>Расчет стоимости ЖД-доставки:</b>\n\n"
            f"🚂 <b>Город отправления:</b> <code>{result['origin_city']}</code>\n"
            f"🏙 <b>Город доставки:</b> <code>{result['destination_city']}</code>\n"
            f"⚖ <b>Вес груза:</b> <code>{result['weight']} кг</code>\n"
            f"📦 <b>Объем груза:</b> <code>{result['volume']} м³</code>\n\n"
            f"💰 <b>Тариф по объёму:</b> <code>{result['tariff_rub']} руб.</code>\n"
            f"📜 <b>Экспортная декларация:</b> <code>{result['export_declaration_rub']} руб.</code>\n"
            f"🕒 <b>Транзитное время:</b> <code>{result['transit_time']}</code>\n"
            f"ℹ️ <b>Доп. условия:</b> <code>{result['additional_conditions']}</code>\n"
            f"📦 <b>Расходы на СВХ:</b> <code>{result['warehouse_costs']}</code>\n\n"
            f"💰 <u><b>Общая стоимость доставки:</b> <code>{result['total_cost_rub']:.2f} руб.</code></u>\n"
        )

        await callback.message.edit_text(response, parse_mode="HTML")
        await state.clear()

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при расчете: {e}")
        await state.clear()
    
    
# endregion


# region #&Conteiners


# ^ Старт ввода данных для контейнеров
@router.callback_query(CalcContainersCallback.filter())
async def start_calculation_containers(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FreightContainerState.entering_port)
    await callback.message.answer("<b>🚢 Введите порт отправления:</b>", parse_mode="HTML")
    await callback.answer()


# ^ Ввод порта отправления для контейнеров
@router.message(FreightContainerState.entering_port)
async def enter_port_container(message: Message, state: FSMContext):
    user_input = message.text.strip().lower()
    available_ports = get_available_ports("RAW SEA", 3)

    corrected_port = None
    for port in available_ports:
        if user_input in port.lower():
            corrected_port = port
            break

    if corrected_port:
        await state.update_data(port=corrected_port)
        logging.info(f"🚢 Введен порт отправления (исправлен): {corrected_port}")
        await state.set_state(FreightContainerState.entering_city)
        await message.answer(f"🔍 Порт исправлен автоматически: <b>{corrected_port}</b>\n\n"
                             "<b>🏙 Введите город доставки в РФ:</b>", parse_mode="HTML")
    else:
        await message.answer(f"❌ Порт не найден. Проверьте правильность и попробуйте снова.\n\n"
                             f"📜 Список портов: {', '.join(available_ports[:10])}...")




# ^ Ввод города доставки для контейнеров
@router.message(FreightContainerState.entering_city)
async def enter_city_container(message: Message, state: FSMContext):
    city = message.text.strip().lower()
    available_cities = get_available_cities_rw("RAW RW", 4)

    if city in available_cities:
        await state.update_data(destination_city=city.capitalize())
        logging.info(f"🏙 Введен город доставки: {city.capitalize()}")
        await state.set_state(FreightContainerState.entering_weight)
        await message.answer("<b>⚖ Введите вес груза (кг):</b>", parse_mode="HTML")
    else:
        corrected_city = find_closest_location(city, available_cities)
        if corrected_city:
            await state.update_data(destination_city=corrected_city.capitalize())
            await state.set_state(FreightContainerState.entering_weight)
            await message.answer("<b>⚖ Введите вес груза (кг):</b>", parse_mode="HTML")
        else:
            await message.answer(f"❌ Город не найден в базе. Проверьте правильность и попробуйте снова.\n\n"
                                 f"📜 Список городов: {', '.join(available_cities[:10])}...")


# ^ Ввод веса
@router.message(FreightContainerState.entering_weight)
async def enter_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        await state.update_data(weight=weight)
        await state.set_state(FreightContainerState.entering_container_type)
        await message.answer("<b>📦 Введите тип контейнера (20DC, 40HC и т.д.):</b>", parse_mode="HTML")
    except ValueError:
        await message.answer("❌ Введите корректное число!")


# ^ Ввод типа контейнера
@router.message(FreightContainerState.entering_container_type)
async def enter_container_type(message: Message, state: FSMContext):
    await state.update_data(container_type=message.text.strip().upper())
    await state.set_state(FreightContainerState.confirming_data)

    data = await state.get_data()
    response = (
        f"<b>Вы ввели:</b>\n\n"
        f"🚢 <b>Порт отправления:</b> <code>{data['port']}</code>\n"
        f"🏙 <b>Город доставки:</b> <code>{data['destination_city']}</code>\n"
        f"⚖ <b>Вес:</b> <code>{data['weight']} тонн</code>\n"
        f"📦 <b>Тип контейнера:</b> <code>{data['container_type']}</code>\n"
    )

    keyboard = get_confirm_keyboard_for_containers()
    await message.answer(response, reply_markup=keyboard, parse_mode="HTML")


# ^ Подтверждение и вывод данных
@router.callback_query(CalcConfirmContainersCallback.filter())
async def confirm_calculation_containers(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    required_keys = ["port", "destination_city", "weight", "container_type"]
    missing_keys = [key for key in required_keys if key not in data]

    if missing_keys:
        await callback.message.answer(f"❌ Ошибка: отсутствуют данные {', '.join(missing_keys)}. Повторите ввод.")
        await state.clear()
        return

    try:
        result = calculate_container_cost(
            port=data["port"],
            city=data["destination_city"],
            weight=data["weight"],
            container_type=data["container_type"]
        )

        response = (
            f"✅ <b>Расчет стоимости контейнерной доставки:</b>\n\n"
            f"🚢 <b>Порт отправления:</b> <code>{result['port']}</code>\n"
            f"🏙 <b>Город доставки:</b> <code>{result['city']}</code>\n"
            f"⚖ <b>Вес груза:</b> <code>{result['weight']} тонн</code>\n"
            f"📦 <b>Тип контейнера:</b> <code>{result['container_type']}</code>\n\n"
            f"💰 <b>Морской фрахт:</b> <code>{result['sea_freight']:.2f} руб.</code>\n"
            f"🚂 <b>ЖД фрахт:</b> <code>{result['rail_freight']:.2f} руб.</code>\n"
            f"🔒 <b>Охрана:</b> <code>{result['security']:.2f} руб.</code>\n"
            f"🏗 <b>Погрузка-разгрузка:</b> <code>{result['prr']:.2f} руб.</code>\n\n"
            f"💰 <u><b>Итоговая стоимость:</b> <code>{result['total_cost']:.2f} руб.</code></u>\n"
        )

        await callback.message.edit_text(response, parse_mode="HTML")
        await state.clear()

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при расчете: {e}")
        await state.clear()

    
# endregion


@router.callback_query(CalcAviaCallback.filter())
async def start_calculating_avia(callback: CallbackQuery):
    await callback.answer("Данная функция в разработке ⚙", show_alert=True)