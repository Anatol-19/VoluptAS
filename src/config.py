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
    DB_DIR = DATA_DIR / "db"
    EXPORT_DIR = DATA_DIR / "export"
    IMPORT_DIR = DATA_DIR / "import"
    
    # База данных
    DB_NAME = "voluptas.db"
    DB_PATH = DB_DIR / DB_NAME
    DB_URI = f"sqlite:///{DB_PATH}"
    
    # Справочники (только для разработки, не редактируются через UI в MVP)
    TYPES = [
        "Module",
        "Epic", 
        "Feature",
        "Page",
        "Service",
        "Element",
        "Story"
    ]
    
    SEGMENTS = [
        "UI",
        "UX/CX",
        "API",
        "Backend",
        "Database",
        "Integration",
        "Security",
        "Performance"
    ]
    
    AUTOMATION_STATUSES = [
        "Not Started",
        "In Progress",
        "Automated",
        "Partially Automated",
        "Not Applicable"
    ]
    
    MATURITY_LEVELS = [
        "Draft",
        "In Review",
        "Approved",
        "Deprecated"
    ]
    
    # UI настройки
    WINDOW_TITLE = "VoluptAS - QA Coverage Tool"
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    
    # Таблица
    TABLE_FONT_SIZE = 10
    TABLE_ROW_HEIGHT = 25
    
    # Цветовые индикаторы
    COLOR_CRIT = "#FF6B6B"      # Красный для критичных
    COLOR_FOCUS = "#FFD93D"     # Желтый для фокусных
    COLOR_COVERED = "#6BCF7F"   # Зеленый для покрытых
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
        for directory in [self.DATA_DIR, self.DB_DIR, self.EXPORT_DIR, self.IMPORT_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_db_uri(self) -> str:
        """
        Получить URI базы данных
        
        Returns:
            str: URI для подключения к БД
        """
        return self.DB_URI
    
    def get_types(self) -> List[str]:
        """
        Получить список типов элементов
        
        Returns:
            List[str]: Список типов
        """
        return self.TYPES.copy()
    
    def get_segments(self) -> List[str]:
        """
        Получить список сегментов
        
        Returns:
            List[str]: Список сегментов
        """
        return self.SEGMENTS.copy()
    
    def get_automation_statuses(self) -> List[str]:
        """
        Получить список статусов автоматизации
        
        Returns:
            List[str]: Список статусов
        """
        return self.AUTOMATION_STATUSES.copy()
    
    def get_maturity_levels(self) -> List[str]:
        """
        Получить список уровней зрелости
        
        Returns:
            List[str]: Список уровней
        """
        return self.MATURITY_LEVELS.copy()
