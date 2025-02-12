from thefuzz import process
import gspread
import logging

from oauth2client.service_account import ServiceAccountCredentials
from app.core.config import CONFIG

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SPREADSHEET_NAME = "Ставки ФОБ 28 12 2024"

# region #&Рассчет Auto


def get_google_sheet(sheet_name):
    logging.info(f"📡 Подключение к Google Sheets: {sheet_name}")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        CONFIG.GOOGLE_CREDENTIALS, scope
    )
    client = gspread.authorize(creds)

    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        logging.info(f"✅ Таблица найдена: {SPREADSHEET_NAME}")
    except gspread.exceptions.SpreadsheetNotFound:
        logging.error(f"❌ Ошибка: Таблица '{SPREADSHEET_NAME}' не найдена! Проверь название и доступы.")
        raise

    sheet = spreadsheet.worksheet(sheet_name)
    return sheet


def get_tariff_before_border(weight, volume):
    logging.info(f"📊 Запрос тарифа ДО ГРАНИЦЫ для веса {weight} кг и объема {volume} м³")

    sheet = get_google_sheet("RAW Сборка Авто")
    headers = sheet.row_values(1)
    logging.info(f"🔍 Заголовки таблицы: {headers}")

    volumetric_weight = volume * 170
    calc_weight = max(weight, volumetric_weight)
    logging.info(f"🔍 Сравнение весов: Фактический: {weight} кг, Объемный: {volumetric_weight} кг → Расчетный: {calc_weight} кг")

    weight_column = None
    volume_column = None

    if calc_weight == weight:
        for i, header in enumerate(headers):
            if "кг" in header:
                clean_header = header.replace(" кг", "").replace(",", ".").strip()
                parts = clean_header.split("-")
                if len(parts) == 2:
                    low, high = map(float, parts)
                    if low <= calc_weight <= high:
                        weight_column = i + 1
                        break
                elif "и более" in header:
                    if float(parts[0]) <= calc_weight:
                        weight_column = i + 1
                        break

    if calc_weight == volumetric_weight and weight_column is None:
        for i, header in enumerate(headers):
            if "м³" in header:
                clean_header = header.replace(" м³", "").replace(",", ".").strip()
                if "до" in header:
                    max_volume = float(clean_header.split(" ")[1])
                    if volume <= max_volume:
                        volume_column = i + 1
                        break
                elif "свыше" in header:
                    volume_column = i + 1
                    break

    if weight_column:
        value = sheet.cell(2, weight_column).value
        logging.info(f"💰 Найден тариф по весу: {value}")
        if value:
            return float(value.replace(",", ".")) * calc_weight

    if volume_column:
        value = sheet.cell(2, volume_column).value
        logging.info(f"💰 Найден тариф по объему: {value}")
        if value:
            return float(value.replace(",", "."))

    raise ValueError("❌ Ошибка: Не удалось найти подходящий тариф в таблице!")


def get_tariff_after_border(destination_city, weight, volume):
    logging.info(f"📊 Запрос тарифа ПОСЛЕ ГРАНИЦЫ для {destination_city}, вес {weight} кг, объем {volume} м³")

    sheet = get_google_sheet("RAW Сборка по РФ")
    cities = sheet.col_values(2)

    if destination_city not in cities:
        raise ValueError(f"❌ Город {destination_city} не найден в тарифах!")

    row_index = cities.index(destination_city) + 1
    headers = sheet.row_values(1)
    weight_column = None
    volume_column = None

    volumetric_weight = volume * 170
    calc_weight = max(weight, volumetric_weight)
    logging.info(f"🔍 Сравнение весов (ПОСЛЕ ГРАНИЦЫ): Фактический: {weight} кг, Объемный: {volumetric_weight} кг → Расчетный: {calc_weight} кг")

    for i, header in enumerate(headers):
        if "кг" in header:
            parts = header.replace(" кг", "").replace(",", ".").split()
            if len(parts) == 2 and "до" in parts:
                if calc_weight <= float(parts[1]):
                    weight_column = i + 1
                    break
            elif "от" in header:
                weight_column = i + 1
                break

    for i, header in enumerate(headers):
        if "м³" in header:
            parts = header.replace(" м³", "").replace(",", ".").split()
            if len(parts) == 2 and "до" in parts:
                if volume <= float(parts[1]):
                    volume_column = i + 1
                    break
            elif "от" in header:
                volume_column = i + 1
                break

    if weight_column:
        value = sheet.cell(row_index, weight_column).value
        logging.info(f"💰 Найден тариф по весу: {value}")
        if value:
            return float(value.replace(",", ".")) * calc_weight
    
    if volume_column:
        value = sheet.cell(row_index, volume_column).value
        logging.info(f"💰 Найден тариф по объему: {value}")
        if value:
            return float(value.replace(",", "."))

    raise ValueError("❌ Ошибка: Не удалось найти подходящий тариф по РФ!")


def calculate_delivery_cost(origin_city, destination_city, weight, volume):
    logging.info(f"🚀 Начало расчета стоимости для {origin_city} -> {destination_city}, {weight} кг, {volume} м³")

    try:
        cost_before_border = get_tariff_before_border(weight, volume)
        logging.info(f"💰 Стоимость до границы: {cost_before_border} руб.")

        cost_after_border = get_tariff_after_border(destination_city, weight, volume)
        logging.info(f"💰 Стоимость после границы: {cost_after_border} руб.")

        total_cost = cost_before_border + cost_after_border

        result = {
            "origin_city": origin_city,
            "destination_city": destination_city,
            "weight": weight,
            "volume": volume,
            "cost_before_border": cost_before_border,
            "cost_after_border": cost_after_border,
            "total_cost": total_cost,
        }

        logging.info(f"✅ Итоговый расчет: {result}")
        return result

    except Exception as e:
        logging.error(f"❌ Ошибка в calculate_delivery_cost: {e}")
        raise e


# endregion


# region #&Расчет ЖД


def get_tariff_zhd(origin_city, destination_city, weight, volume):
    logging.info(f"📊 Запрос тарифа ЖД для {origin_city} -> {destination_city}, вес {weight} кг, объем {volume} м³")

    sheet = get_google_sheet("RAW Сборка ЖД")
    headers = sheet.row_values(1)
    cities = sheet.col_values(2)

    if destination_city not in cities:
        raise ValueError(f"❌ Город назначения {destination_city} не соответствует данным в таблице!")

    row_index = cities.index(destination_city) + 1

    volume_brackets = ["0 - 3", "3.1 - 5", "5.1 - 10"]
    volume_column = None

    for i, header in enumerate(headers):
        header_clean = header.replace(",", ".").replace("м3", "").strip()
        for bracket in volume_brackets:
            if bracket in header_clean:
                low, high = map(float, bracket.split(" - "))
                if low <= volume <= high:
                    volume_column = i + 1
                    break
        if volume_column:
            break

    if volume_column is None:
        raise ValueError("❌ Ошибка: Не удалось найти подходящий тариф по объему!")

    def clean_numeric(value):
        return float(value.replace("$", "").strip().replace(",", "."))

    try:
        tariff = clean_numeric(sheet.cell(row_index, volume_column).value)  # 🛠 Чистим `$`
        export_declaration = clean_numeric(sheet.cell(row_index, headers.index("Экспортная декларация") + 1).value)
        transit_time = sheet.cell(row_index, headers.index("Транзитное время") + 1).value.strip()
        additional_conditions = sheet.cell(row_index, headers.index("Доп.Условия") + 1).value.strip()
        warehouse_costs = sheet.cell(row_index, headers.index("Расходы на СВХ") + 1).value.strip()
    except Exception as e:
        raise ValueError(f"❌ Ошибка при обработке данных: {e}")

    total_cost = tariff * volume + export_declaration

    result = {
        "origin_city": origin_city,
        "destination_city": destination_city,
        "weight": weight,
        "volume": volume,
        "tariff": tariff,
        "export_declaration": export_declaration,
        "transit_time": transit_time,
        "additional_conditions": additional_conditions,
        "warehouse_costs": warehouse_costs,
        "total_cost": total_cost,
    }

    logging.info(f"✅ Итоговый расчет ЖД: {result}")
    return result


# endregion

