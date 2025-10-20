import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / 'voluptas.db'
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

engine = create_engine(DATABASE_URL, echo=False, connect_args={'check_same_thread': False})

@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """ Инициализация базы данных - создание всех таблиц """
    # Импортируем ВСЕ модели для создания таблиц
    from src.models import functional_item, user, relation, dictionary, zoho_task
    Base.metadata.create_all(bind=engine)
    print(f'✅ База данных инициализирована: {DATABASE_PATH}')
    print(f'   Таблицы: functional_items, users, functional_item_relations, dictionaries, zoho_tasks')

