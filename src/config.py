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
    CREDENTIALS_DIR = DATA_DIR / "credentials"
    CREDENTIALS_EXAMPLES_DIR = CREDENTIALS_DIR / "examples"

    # Текущий проект
    CURRENT_PROJECT = "default"  # Будет обновляться при переключении проекта

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
    COLOR_CRIT = "#FF6B6B"      # Красный для критичных
    COLOR_FOCUS = "#FFD93D"     # Желтый для фокусных
    COLOR_COVERED = "#6BCF7F"   # Зеленый для покрытых
    COLOR_NOT_COVERED = "#E0E0E0"  # Серый для без покрытия
    
    # Экспорт
    EXPORT_FORMATS = ["CSV", "Excel", "Markdown", "Google Sheets"]
    
    # Пути к credentials
    GOOGLE_CREDENTIALS = CREDENTIALS_DIR / "google_credentials.json"
    GOOGLE_SERVICE_ACCOUNT = CREDENTIALS_DIR / "google_service_account.json"
    ZOHO_ENV = CREDENTIALS_DIR / "zoho.env"
    QASE_ENV = CREDENTIALS_DIR / "qase.env"

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
    
    @classmethod
    def get_project_credentials_dir(cls, project_name: str = None) -> Path:
        """
        Получить путь к директории креденшелов проекта

        Args:
            project_name: Имя проекта (если None - используется текущий)

        Returns:
            Path: Абсолютный путь к директории креденшелов проекта
        """
        project = project_name or cls.CURRENT_PROJECT
        return cls.CREDENTIALS_DIR / project

    @classmethod
    def get_credentials_path(cls, filename: str, project_name: str = None) -> Path:
        """
        Получить путь к файлу креденшелов

        Args:
            filename: Имя файла креденшелов (например, 'zoho.env')
            project_name: Имя проекта (если None - используется текущий)

        Returns:
            Path: Абсолютный путь к файлу
        """
        return cls.get_project_credentials_dir(project_name) / filename

    @classmethod
    def get_credentials_example_path(cls, filename: str) -> Path:
        """
        Получить путь к примеру файла креденшелов

        Args:
            filename: Имя файла (например, 'zoho.env.example')

        Returns:
            Path: Абсолютный путь к файлу-примеру
        """
        return cls.CREDENTIALS_EXAMPLES_DIR / filename

    @classmethod
    def set_current_project(cls, project_name: str) -> None:
        """
        Установить текущий проект

        Args:
            project_name: Имя проекта
        """
        cls.CURRENT_PROJECT = project_name
        # Создаем директорию для креденшелов проекта если её нет
        project_creds_dir = cls.get_project_credentials_dir(project_name)
        project_creds_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def init_project_credentials(cls, project_name: str) -> None:
        """
        Инициализация креденшелов для нового проекта

        Args:
            project_name: Имя проекта
        """
        # Создаем директорию
        project_creds_dir = cls.get_project_credentials_dir(project_name)
        project_creds_dir.mkdir(parents=True, exist_ok=True)

        # Копируем примеры файлов
        for example in cls.CREDENTIALS_EXAMPLES_DIR.glob("*.example"):
            target = project_creds_dir / example.name.replace(".example", "")
            if not target.exists():
                import shutil
                shutil.copy2(example, target)

    def get_types(self) -> List[str]:
        """
        Получить список типов элементов (из БД)
        
        Returns:
            List[str]: Список типов
        """
        return self._get_dict_values('type')
    
    def get_segments(self) -> List[str]:
        """
        Получить список сегментов (из БД)
        
        Returns:
            List[str]: Список сегментов
        """
        return self._get_dict_values('segment')
    
    def get_automation_statuses(self) -> List[str]:
        """
        Получить список статусов автоматизации (из БД)
        
        Returns:
            List[str]: Список статусов
        """
        return self._get_dict_values('automation_status')
    
    def get_maturity_levels(self) -> List[str]:
        """
        Получить список уровней зрелости (из БД)
        
        Returns:
            List[str]: Список уровней
        """
        return self._get_dict_values('maturity')
    
    def get_positions(self) -> List[str]:
        """
        Получить список должностей (из БД)
        
        Returns:
            List[str]: Список должностей
        """
        return self._get_dict_values('position')
    
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
            results = session.query(Dictionary.value).filter(
                Dictionary.dict_type == dict_type,
                Dictionary.is_active == True
            ).order_by(Dictionary.display_order).all()
            session.close()
            
            return [r[0] for r in results]
        except Exception as e:
            print(f"⚠️ Ошибка чтения справочника {dict_type}: {e}")
            return []

    @classmethod
    def get_projects_list(cls) -> list[str]:
        """
        Получить список всех проектов

        Returns:
            list[str]: Список имен проектов
        """
        import os
        projects_dir = cls.DATA_DIR / "projects"
        if not projects_dir.exists():
            return ["default"]
        return [d.name for d in projects_dir.iterdir() if d.is_dir()]

    @classmethod
    def switch_project(cls, project_name: str) -> bool:
        """
        Переключить текущий проект

        Args:
            project_name: Имя проекта

        Returns:
            bool: True если переключение успешно, False если проект не существует
        """
        # Проверяем существование проекта
        project_dir = cls.DATA_DIR / "projects" / project_name
        if not project_dir.exists():
            return False

        # Сохраняем текущий проект
        current_project_file = cls.DATA_DIR / "config" / "current_project.txt"
        current_project_file.write_text(project_name)

        # Обновляем текущий проект
        cls.CURRENT_PROJECT = project_name

        # Обновляем пути к БД
        cls.DB_PATH = project_dir / "voluptas.db"
        cls.DB_URI = f"sqlite:///{cls.DB_PATH}"

        return True

    @classmethod
    def create_project(cls, project_name: str) -> bool:
        """
        Создать новый проект

        Args:
            project_name: Имя проекта

        Returns:
            bool: True если создание успешно, False если проект уже существует
        """
        # Проверяем существование проекта
        project_dir = cls.DATA_DIR / "projects" / project_name
        if project_dir.exists():
            return False

        try:
            # Создаем структуру проекта
            project_dir.mkdir(parents=True)
            (project_dir / "bdd_features").mkdir()
            (project_dir / "reports").mkdir()

            # Копируем шаблоны креденшелов
            creds_dir = cls.CREDENTIALS_DIR / project_name
            creds_dir.mkdir(parents=True)

            # Создаем базу данных
            from src.db import init_db
            cls.switch_project(project_name)
            init_db()

            return True

        except Exception as e:
            import logging
            logging.error(f"Ошибка создания проекта {project_name}: {e}")
            if project_dir.exists():
                import shutil
                shutil.rmtree(project_dir)
            return False

    @classmethod
    def delete_project(cls, project_name: str) -> bool:
        """
        Удалить проект

        Args:
            project_name: Имя проекта

        Returns:
            bool: True если удаление успешно, False если проект не существует или это default
        """
        if project_name == "default":
            return False

        project_dir = cls.DATA_DIR / "projects" / project_name
        if not project_dir.exists():
            return False

        try:
            # Удаляем директорию проекта
            import shutil
            shutil.rmtree(project_dir)

            # Удаляем креденшелы
            creds_dir = cls.CREDENTIALS_DIR / project_name
            if creds_dir.exists():
                shutil.rmtree(creds_dir)

            return True

        except Exception as e:
            import logging
            logging.error(f"Ошибка удаления проекта {project_name}: {e}")
            return False
