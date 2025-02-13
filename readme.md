# Telegram Bot для расчета стоимости доставки контейнеров

Этот бот позволяет автоматически рассчитывать стоимость доставки контейнеров различными способами (авто, ЖД, морем), используя данные из Google Sheets и актуальный курс валют.

## Основной функционал

### Калькулятор доставки
- Авто, ЖД, морские перевозки.
- Автоматический подбор тарифов на основе данных из Google Sheets.
- Учет актуального курса USD → RUB.

### Автоматическое исправление данных
- Коррекция названий портов, городов и типов контейнеров.
- Поиск ближайшего соответствия при вводе.

### Google Sheets API
- Получение актуальных тарифов.
- Автоматическое обновление данных.

### FSM-логика
- Последовательный ввод данных.
- Подтверждение перед расчетом.

### Автоматизированная рассылка постов
- Запланированная отправка сообщений пользователям.
- Работа с фото/видео-контентом.

## Требования
Pyhton 3.10+
Зависимости (requirements.txt)
Сервисный аккаунт Google (service_account.json)
