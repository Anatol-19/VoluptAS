from .database import get_engine, get_session_local, Base, get_db, init_db
from .database_manager import DatabaseManager

# Ленивая инициализация — сессия создаётся при первом обращении
def _get_session_local():
    return get_session_local()

SessionLocal = _get_session_local
engine = None  # Инициализируется при первом вызове get_engine()

__all__ = ["engine", "SessionLocal", "Base", "get_db", "init_db", "DatabaseManager"]
