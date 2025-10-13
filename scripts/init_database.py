"""
Скрипт инициализации базы данных

Создаёт все таблицы на основе моделей SQLAlchemy.
"""

import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.db import init_db, DATABASE_PATH


def main():
    """Инициализирует базу данных"""
    print("🚀 Инициализация базы данных VoluptAS...")
    print(f"📁 Путь к БД: {DATABASE_PATH}")
    
    try:
        init_db()
        print("\n✅ База данных успешно инициализирована!")
        print("📊 Созданные таблицы:")
        print("  - functional_items")
        print("  - users")
    except Exception as e:
        print(f"\n❌ Ошибка при инициализации БД: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
