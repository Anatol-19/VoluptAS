"""
Конфигурация приложения VoluptAS

Содержит настройки базы данных, путей, справочников и другие параметры
"""

import os
from pathlib import Path
from typing import List, Dict


class Config:
    """
    Класс конфигурации приложения
    Все настройки в одном месте для удобного управления
    """

    # Базовые пути
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    EXPORT_DIR = DATA_DIR / "export"
    IMPORT_DIR = DATA_DIR / "import"
    CREDENTIALS_DIR = BASE_DIR / "credentials"

    # База данных (унифицированный путь с database.py)
    DB_NAME = "voluptas.db"
    DB_PATH = DATA_DIR / DB_NAME
    DB_URI = f"sqlite:///{DB_PATH}"

    # Справочники теперь хранятся в БД (таблица dictionaries)
    # Эти константы — только fallback на случай проблем с БД

    # UI настройки
    WINDOW_TITLE = "VoluptAS - QA Coverage Tool"
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900

    # Таблица
    TABLE_FONT_SIZE = 10
    TABLE_ROW_HEIGHT = 25

    # Цветовые индикаторы
    COLOR_CRIT = "#FF6B6B"  # Красный для критичных
    COLOR_FOCUS = "#FFD93D"  # Желтый для фокусных
    COLOR_COVERED = "#6BCF7F"  # Зеленый для покрытых
    COLOR_NOT_COVERED = "#E0E0E0"  # Серый для без покрытия

    # Экспорт
    EXPORT_FORMATS = ["CSV", "Excel", "Markdown", "Google Sheets"]

    def __init__(self):
        """
        Инициализация конфигурации
        Создание необходимых директорий
        """
        self._ensure_directories()

    def _ensure_directories(self):
        """
        Создание необходимых директорий если их нет
        """
        for directory in [self.DATA_DIR, self.EXPORT_DIR, self.IMPORT_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_db_uri(self) -> str:
        """
        Получить URI базы данных

        Returns:
            str: URI для подключения к БД
        """
        return self.DB_URI

    @staticmethod
    def get_credentials_path(filename: str = None) -> Path:
        """
        Получить путь к файлу credentials (относительно корня проекта)

        Args:
            filename: имя файла в папке credentials (необязательно)

        Returns:
            Path: полный путь к credentials или к файлу

        Example:
            >>> Config.get_credentials_path()  # Путь к папке
            Path('C:/project/credentials')
            >>> Config.get_credentials_path('zoho.env')  # Путь к файлу
            Path('C:/project/credentials/zoho.env')
        """
        base_dir = Path(__file__).parent.parent
        credentials_dir = base_dir / "credentials"

        if filename:
            return credentials_dir / filename
        return credentials_dir

    def get_types(self) -> List[str]:
        """
        Получить список типов элементов (из БД)

        Returns:
            List[str]: Список типов
        """
        return self._get_dict_values("type")

    def get_segments(self) -> List[str]:
        """
        Получить список сегментов (из БД)

        Returns:
            List[str]: Список сегментов
        """
        return self._get_dict_values("segment")

    def get_automation_statuses(self) -> List[str]:
        """
        Получить список статусов автоматизации (из БД)

        Returns:
            List[str]: Список статусов
        """
        return self._get_dict_values("automation_status")

    def get_maturity_levels(self) -> List[str]:
        """
        Получить список уровней зрелости (из БД)

        Returns:
            List[str]: Список уровней
        """
        return self._get_dict_values("maturity")

    def get_positions(self) -> List[str]:
        """
        Получить список должностей (из БД)

        Returns:
            List[str]: Список должностей
        """
        return self._get_dict_values("position")

    def _get_dict_values(self, dict_type: str) -> List[str]:
        """
        Универсальный метод для чтения справочников из БД

        Args:
            dict_type: тип справочника

        Returns:
            List[str]: список значений
        """
        try:
            from src.db import SessionLocal
            from src.models import Dictionary

            session = SessionLocal()
            results = (
                session.query(Dictionary.value)
                .filter(Dictionary.dict_type == dict_type, Dictionary.is_active == True)
                .order_by(Dictionary.display_order)
                .all()
            )
            session.close()

            return [r[0] for r in results]
        except Exception as e:
            print(f"⚠️ Ошибка чтения справочника {dict_type}: {e}")
            return []
