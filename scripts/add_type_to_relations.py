"""
Миграция: Добавление поля type в таблицу functional_item_relations

Выполняет:
1. Проверка существования столбца type
2. Добавление столбца type (если отсутствует)
3. Установка значения 'hierarchy' для всех существующих связей
"""

import sys
from pathlib import Path

# Добавить корень проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, inspect
from src.db.database import engine, SessionLocal
from src.models.relation import Relation


def check_column_exists(engine, table_name, column_name):
    """Проверяет существование столбца в таблице"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_type_column():
    """Добавляет столбец type в functional_item_relations"""
    
    print("=" * 60)
    print("МИГРАЦИЯ: Добавление поля 'type' в functional_item_relations")
    print("=" * 60)
    
    # Проверка существования столбца
    if check_column_exists(engine, 'functional_item_relations', 'type'):
        print("✅ Столбец 'type' уже существует в таблице")
        
        # Проверка количества записей с type = NULL
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM functional_item_relations WHERE type IS NULL")
            )
            null_count = result.scalar()
            
            if null_count > 0:
                print(f"⚠️  Найдено {null_count} записей с type = NULL")
                print("   Обновляем их на 'hierarchy'...")
                
                conn.execute(
                    text("UPDATE functional_item_relations SET type = 'hierarchy' WHERE type IS NULL")
                )
                conn.commit()
                print(f"✅ Обновлено {null_count} записей")
            else:
                print("✅ Все записи уже имеют значение type")
        
        return
    
    # Добавление столбца
    print("📝 Добавляем столбец 'type' в таблицу...")
    
    try:
        with engine.connect() as conn:
            # Добавить столбец
            conn.execute(
                text("ALTER TABLE functional_item_relations ADD COLUMN type TEXT DEFAULT 'hierarchy'")
            )
            
            # Обновить существующие записи
            result = conn.execute(
                text("UPDATE functional_item_relations SET type = 'hierarchy' WHERE type IS NULL")
            )
            
            # Создать индекс
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_relation_type ON functional_item_relations(type)")
            )
            
            conn.commit()
            
            print("✅ Столбец 'type' успешно добавлен")
            print("✅ Все существующие связи установлены как 'hierarchy'")
            print("✅ Индекс создан")
            
            # Статистика
            result = conn.execute(text("SELECT COUNT(*) FROM functional_item_relations"))
            total_count = result.scalar()
            print(f"\n📊 Всего связей в БД: {total_count}")
            
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        raise


if __name__ == "__main__":
    try:
        add_type_column()
        print("\n" + "=" * 60)
        print("✅ Миграция завершена успешно")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        sys.exit(1)
