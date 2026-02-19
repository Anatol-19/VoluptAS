"""
DatabaseManager - Управление подключением к БД проектов

Позволяет динамически переключаться между БД разных проектов
"""

import logging
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер динамического подключения к БД проектов"""

    def __init__(self):
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self.current_db_path: Optional[Path] = None

    def connect_to_database(self, db_path: Path) -> bool:
        """
        Подключение к БД проекта

        Args:
            db_path: Путь к БД проекта

        Returns:
            True если успешно, False при ошибке
        """
        try:
            # Закрываем предыдущее подключение если есть
            if self.engine:
                self.engine.dispose()
                logger.info(f"Закрыто предыдущее подключение: {self.current_db_path}")

            # Создаём новое подключение
            DATABASE_URL = f"sqlite:///{db_path}"
            self.engine = create_engine(
                DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
            )

            # Включаем foreign keys для SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

            # Создаём sessionmaker
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            self.current_db_path = db_path

            logger.info(f"✅ Подключено к БД: {db_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД {db_path}: {e}")
            return False

    def get_session(self) -> Session:
        """
        Получить новую сессию БД

        Returns:
            Session объект

        Raises:
            RuntimeError: Если БД не подключена
        """
        if not self.SessionLocal:
            raise RuntimeError(
                "БД не подключена. Вызовите connect_to_database() сначала."
            )

        return self.SessionLocal()

    def init_database(self):
        """
        Инициализация БД - создание всех таблиц
        Используется при создании нового проекта
        """
        if not self.engine:
            raise RuntimeError(
                "Engine не создан. Вызовите connect_to_database() сначала."
            )

        # Импортируем ВСЕ модели для создания таблиц
        from src.db.database import Base
        from src.models import (
            functional_item,
            user,
            relation,
            dictionary,
            zoho_task,
            report_template,
        )

        Base.metadata.create_all(bind=self.engine)

        logger.info(f"✅ БД инициализирована: {self.current_db_path}")
        logger.info(
            "   Таблицы: functional_items, users, functional_item_relations, "
            "dictionaries, zoho_tasks, report_templates"
        )

    def close(self):
        """Закрыть текущее подключение"""
        if self.engine:
            self.engine.dispose()
            logger.info(f"Закрыто подключение к {self.current_db_path}")
            self.engine = None
            self.SessionLocal = None
            self.current_db_path = None

    def is_connected(self) -> bool:
        """Проверка наличия активного подключения"""
        return self.engine is not None and self.SessionLocal is not None


# Singleton instance для глобального использования
_db_manager_instance: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Получить singleton instance DatabaseManager"""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance


def reset_database_manager():
    """Сброс singleton (для тестирования)"""
    global _db_manager_instance
    if _db_manager_instance:
        _db_manager_instance.close()
    _db_manager_instance = None
