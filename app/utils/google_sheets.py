import gspread
import logging
import requests

from xml.etree import ElementTree as ET
from oauth2client.service_account import ServiceAccountCredentials

from app.core.config import CONFIG

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_usd_to_rub_rate():
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    response = requests.get(url)
    tree = ET.fromstring(response.content)

    for valute in tree.findall("Valute"):
        if valute.find("CharCode").text == "USD":
            rate = valute.find("Value").text
            return float(rate.replace(",", "."))
    raise ValueError("❌ Не удалось получить курс USD к RUB")


# region #&Расчет Auto


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
        spreadsheet = client.open(CONFIG.SPREADSHEET_NAME)
        logging.info(f"✅ Таблица найдена: {CONFIG.SPREADSHEET_NAME}")
    except gspread.exceptions.SpreadsheetNotFound:
        logging.error(f"❌ Ошибка: Таблица '{CONFIG.SPREADSHEET_NAME}' не найдена! Проверь название и доступы.")
        raise

    sheet = spreadsheet.worksheet(sheet_name)
    return sheet


def get_tariff_before_border(weight, volume):
    logging.info(f"📊 Запрос тарифа ДО ГРАНИЦЫ для веса {weight} кг и объема {volume} м³")

    sheet = get_google_sheet(CONFIG.BUILD_AUTO_LIST)
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

    sheet = get_google_sheet(CONFIG.BUILD_RUSSIA_LIST)
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

    sheet = get_google_sheet(CONFIG.BUILD_RAILWAY_LIST)
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
        tariff_usd = clean_numeric(sheet.cell(row_index, volume_column).value)
        export_declaration_usd = clean_numeric(sheet.cell(row_index, headers.index("Экспортная декларация") + 1).value)
        transit_time = sheet.cell(row_index, headers.index("Транзитное время") + 1).value.strip()
        additional_conditions = sheet.cell(row_index, headers.index("Доп.Условия") + 1).value.strip()
        warehouse_costs = sheet.cell(row_index, headers.index("Расходы на СВХ") + 1).value.strip()
    except Exception as e:
        raise ValueError(f"❌ Ошибка при обработке данных: {e}")

    usd_to_rub_rate = get_usd_to_rub_rate()

    tariff_rub = tariff_usd * usd_to_rub_rate
    export_declaration_rub = export_declaration_usd * usd_to_rub_rate
    total_cost_usd = tariff_usd * volume + export_declaration_usd
    total_cost_rub = total_cost_usd * usd_to_rub_rate

    result = {
        "origin_city": origin_city,
        "destination_city": destination_city,
        "weight": weight,
        "volume": volume,
        "tariff_usd": tariff_usd,
        "tariff_rub": tariff_rub,
        "export_declaration_usd": export_declaration_usd,
        "export_declaration_rub": export_declaration_rub,
        "transit_time": transit_time,
        "additional_conditions": additional_conditions,
        "warehouse_costs": warehouse_costs,
        "total_cost_usd": total_cost_usd,
        "total_cost_rub": total_cost_rub,
    }

    logging.info(f"✅ Итоговый расчет ЖД: {result}")
    return result


# endregion


# region #&Расчет Контейнеров


def calculate_container_cost(port, city, weight, container_type):
    logging.info(f"🚢 Расчет стоимости контейнера: {port} -> {city}, Вес: {weight} кг, Контейнер: {container_type}")

    usd_to_rub_rate = get_usd_to_rub_rate()
    logging.info(f"💱 Актуальный курс USD → RUB: {usd_to_rub_rate}")

    if "20DC" in container_type:
        sea_container = "20DC - COC"
    elif "40HC" in container_type:
        sea_container = "40HC - COC"

    if "20DC" in container_type:
        if weight <= 24000:
            rw_container = "20DC (till 24 tonns)"
            security_container = "Security 20DC (till 24 tonns)"
        else:
            rw_container = "20DC (24-28 tonns)"
            security_container = "Security 20DC (24-28 tonns)"
    elif "40HC" in container_type:
        rw_container = "40HC - COC"
        security_container = "Security 40HC"

    sheet_sea = get_google_sheet(CONFIG.CONTEINERS_LIST1)
    sea_data = sheet_sea.get_all_records()

    sea_cost_usd = None
    pod_sea = None
    for row in sea_data:
        if row["POL SEA"].strip() == port.strip():
            pod_sea = row["POD SEA"].strip()
            sea_cost_usd = float(str(row.get(sea_container, 0)).replace('\xa0', '').replace("$", "").strip())
            break

    if not sea_cost_usd or not pod_sea:
        raise ValueError(f"❌ Морской фрахт для {port} не найден!")
    
    sea_cost_rub = sea_cost_usd * usd_to_rub_rate
    logging.info(f"💰 Морской фрахт: {sea_cost_usd} USD → {sea_cost_rub} RUB")

    sheet_rw = get_google_sheet(CONFIG.CONTEINERS_LIST2)
    rw_data = sheet_rw.get_all_records()

    rail_cost, security_cost, prr_cost = None, None, None
    for row in rw_data:
        if row["POL SEA"].strip() == pod_sea.strip() and row["POD City"].strip() == city.strip():
            rail_cost = float(str(row.get(rw_container, 0)).replace('\xa0', '').replace("$", "").strip())
            security_cost = float(str(row.get(security_container, 0)).replace('\xa0', '').replace("$", "").strip())
            prr_cost = float(str(row.get("PRR", 0)).replace('\xa0', '').replace("$", "").strip())
            break

    if not all([rail_cost, security_cost, prr_cost]):
        raise ValueError("❌ Не удалось найти тарифы в RAW RW!")

    logging.info(f"🚂 ЖД: {rail_cost} RUB, 🔒 Охрана: {security_cost} RUB, 🏗 Погрузка: {prr_cost} RUB")

    sum_rw = rail_cost + security_cost + prr_cost
    logging.info(f"🧮 Сумма ЖД + Охрана + Погрузка: {sum_rw} RUB")

    total_cost = sea_cost_rub + sum_rw
    logging.info(f"💰 Итого: {total_cost} RUB")

    return {
        "port": port,
        "city": city,
        "weight": weight,
        "container_type": container_type,
        "sea_freight": sea_cost_rub,
        "rail_freight": rail_cost,
        "security": security_cost,
        "prr": prr_cost,
        "total_cost": total_cost,
    }


# endregion