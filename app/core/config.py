import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
    SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
    CONTEINERS_LIST1 = os.getenv("CONTEINERS_LIST1")
    CONTEINERS_LIST2 = os.getenv("CONTEINERS_LIST2")
    BUILD_AUTO_LIST = os.getenv("BUILD_AUTO_LIST")
    BUILD_RAILWAY_LIST = os.getenv("BUILD_RAILWAY_LIST")
    BUILD_RUSSIA_LIST = os.getenv("BUILD_RUSSIA_LIST")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


CONFIG = Config()
