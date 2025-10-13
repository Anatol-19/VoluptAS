"""
Модуль для работы с базой данных

Настройка SQLAlchemy, создание сессий, инициализация БД
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from typing import Generator

# Базовый класс для моделей
Base = declarative_base()

# Глобальные переменные для engine и session
engine = None
SessionLocal = None


def init_database(db_uri: str):
    """
    Инициализация базы данных
    
    Args:
        db_uri: URI подключения к базе данных
    
    Создаёт engine, sessionmaker и все таблицы
    """
    global engine, SessionLocal
    
    # Создание engine
    engine = create_engine(
        db_uri,
        connect_args={"check_same_thread": False},  # Для SQLite
        echo=False  # True для отладки SQL запросов
    )
    
    # Создание sessionmaker
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    # Создание всех таблиц
    Base.metadata.create_all(bind=engine)
    
    print(f"✓ База данных инициализирована: {db_uri}")


def get_session() -> Generator[Session, None, None]:
    """
    Получить сессию для работы с БД
    
    Yields:
        Session: Сессия SQLAlchemy
        
    Использование:
        with get_session() as session:
            # работа с БД
            pass
    """
    if SessionLocal is None:
        raise RuntimeError("База данных не инициализирована. Вызовите init_database() сначала.")
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_session() -> Session:
    """
    Создать новую сессию для работы с БД
    
    Returns:
        Session: Сессия SQLAlchemy
        
    ВАЖНО: Не забыть закрыть сессию после использования!
    """
    if SessionLocal is None:
        raise RuntimeError("База данных не инициализирована. Вызовите init_database() сначала.")
    
    return SessionLocal()
