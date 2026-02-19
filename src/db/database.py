import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from src.models.project_config import ProjectManager
from src.db.base import Base

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "data" / "config"
project_manager = ProjectManager(CONFIG_DIR)


# Получаем путь к БД текущего проекта
def get_database_url():
    current_project = project_manager.get_current_project()
    if not current_project:
        raise RuntimeError("Не выбран активный проект!")
    db_path = current_project.database_path
    return f"sqlite:///{db_path}"


def get_engine():
    return create_engine(
        get_database_url(), echo=False, connect_args={"check_same_thread": False}
    )


def get_session_local():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация базы данных - создание всех таблиц для текущего проекта"""
    from src.models import (
        functional_item,
        user,
        relation,
        dictionary,
        zoho_task,
        report_template,
    )

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print(f"✅ База данных инициализирована: {get_database_url()}")
    print(
        f"   Таблицы: functional_items, users, functional_item_relations, dictionaries, zoho_tasks, report_templates"
    )
