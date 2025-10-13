"""
Одноразовый импортёр данных из CSV → SQLite

Импортирует начальные данные из voluptas_data.csv в базу данных.
После первого импорта - вся работа через UI!
"""

import sys
import csv
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.db import SessionLocal, init_db
from src.models import FunctionalItem


def parse_boolean(value: str) -> bool:
    """Парсит строку в boolean"""
    if not value:
        return False
    return value.strip().upper() in ['TRUE', '1', 'YES', 'Y']


def import_csv_data(csv_path: Path):
    """
    Импортирует данные из CSV в БД
    
    Args:
        csv_path: Путь к CSV файлу
    """
    print(f"📂 Чтение CSV: {csv_path}")
    
    session = SessionLocal()
    imported_count = 0
    skipped_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Пропускаем пустые строки
                functional_id = row.get('Functional ID', '').strip()
                if not functional_id:
                    skipped_count += 1
                    continue
                
                # Проверяем, не существует ли уже
                existing = session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
                if existing:
                    print(f"  ⏭️  Пропущено (уже существует): {functional_id}")
                    skipped_count += 1
                    continue
                
                # Создаём новый элемент
                item = FunctionalItem(
                    functional_id=functional_id,
                    title=title,
                    type=row.get('Type', '').strip() or None,
                    module=row.get('Module', '').strip() or None,
                    epic=row.get('Epic', '').strip() or None,
                    feature=row.get('Feature', '').strip() or None,
                    stories=row.get('Stories', '').strip() or None,
                    segment=row.get('Segment ', '').strip() or None,  # Note: есть пробел в CSV!
                    description=row.get('Description', '').strip() or None,
                    tags=row.get('Tags and Aliases', '').strip() or None,
                    roles=row.get('Roles', '').strip() or None,
                    is_focus=parse_boolean(row.get('isFocus', 'FALSE')),
                    is_crit=parse_boolean(row.get('isCrit', 'FALSE')),
                    # TODO: Добавить парсинг ответственных через User модель
                    # responsible_qa_id=...,
                    # responsible_dev_id=...,
                    automation_status=row.get('Automation Status', '').strip() or None,
                    maturity=row.get('Maturity', '').strip() or None,
                    container=row.get('Container', '').strip() or None,
                    database=row.get('Database', '').strip() or None,
                    subsystems_involved=row.get('Subsystems involved', '').strip() or None,
                    external_services=row.get('External Services', '').strip() or None,
                )
                
                session.add(item)
                session.commit()  # Коммитим по одному чтобы избежать откатов при дубликатах
                imported_count += 1
                
                if imported_count % 10 == 0:
                    print(f"  ✅ Импортировано: {imported_count}")
        print(f"\n🎉 Импорт завершён!")
        print(f"  ✅ Импортировано: {imported_count}")
        print(f"  ⏭️  Пропущено: {skipped_count}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Ошибка импорта: {e}")
        raise
    finally:
        session.close()


def main():
    """Основная функция импорта"""
    print("🚀 Импорт данных из CSV → SQLite\n")
    
    csv_path = project_root / "data" / "import" / "voluptas_data.csv"
    
    if not csv_path.exists():
        print(f"❌ CSV файл не найден: {csv_path}")
        sys.exit(1)
    
    # Убеждаемся что БД инициализирована
    print("📊 Проверка БД...")
    init_db()
    
    # Импортируем данные
    import_csv_data(csv_path)
    
    print("\n✨ Готово! Теперь можно запустить UI.")


if __name__ == "__main__":
    main()
