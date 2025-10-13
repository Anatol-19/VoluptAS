"""
Полный импортёр данных из CSV
Обрабатывает все поля и создаёт пользователей
"""
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import csv
from src.db import SessionLocal
from src.models import FunctionalItem, User

def import_csv():
    session = SessionLocal()
    csv_path = project_root / 'data' / 'import' / 'voluptas_data.csv'
    
    print(f'📂 Читаем: {csv_path}')
    
    # Статистика
    stats = {
        'total': 0,
        'imported': 0,
        'skipped_empty': 0,
        'skipped_duplicate': 0,
        'users_created': 0,
        'errors': 0
    }
    
    # Кэш пользователей
    users_cache = {}
    
    def get_or_create_user(name):
        """Получить или создать пользователя"""
        if not name or name.strip() == '':
            return None
        
        name = name.strip()
        
        if name in users_cache:
            return users_cache[name]
        
        # Ищем в БД
        user = session.query(User).filter_by(name=name).first()
        if user:
            users_cache[name] = user
            return user
        
        # Создаём нового
        user = User(name=name, is_active=1)
        session.add(user)
        session.flush()  # Получаем ID
        users_cache[name] = user
        stats['users_created'] += 1
        print(f'  ➕ Создан пользователь: {name}')
        return user
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                stats['total'] += 1
                
                functional_id = row.get('Functional ID', '').strip()
                title = row.get('Title', '').strip()
                
                # Пропускаем пустые строки
                if not functional_id or not title:
                    stats['skipped_empty'] += 1
                    continue
                
                # Проверяем дубликаты
                existing = session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
                if existing:
                    stats['skipped_duplicate'] += 1
                    continue
                
                try:
                    # Создаём элемент
                    item = FunctionalItem(
                        functional_id=functional_id,
                        title=title,
                        type=row.get('Type', '').strip() or None,
                        module=row.get('Module', '').strip() or None,
                        epic=row.get('Epic', '').strip() or None,
                        feature=row.get('Feature', '').strip() or None,
                        stories=row.get('Stories', '').strip() or None,
                        segment=row.get('Segment ', '').strip() or None,  # Обратите внимание на пробел!
                        description=row.get('Description', '').strip() or None,
                        tags=row.get('Tags and Aliases', '').strip() or None,
                        roles=row.get('Roles', '').strip() or None,
                        is_focus=1 if row.get('isFocus', '').strip().upper() == 'TRUE' else 0,
                        is_crit=1 if row.get('isCrit', '').strip().upper() == 'TRUE' else 0,
                        automation_status=row.get('Automation Status', '').strip() or None,
                        maturity=row.get('Maturity', '').strip() or None,
                        container=row.get('Container', '').strip() or None,
                        database=row.get('Database', '').strip() or None,
                        subsystems_involved=row.get('Subsystems involved', '').strip() or None,
                        external_services=row.get('External Services', '').strip() or None,
                    )
                    
                    # Ответственные
                    qa_name = row.get('Responsible (QA)', '').strip()
                    dev_name = row.get('Responsible (Dev)', '').strip()
                    accountable_name = row.get('Accountable', '').strip()
                    
                    if qa_name:
                        qa_user = get_or_create_user(qa_name)
                        if qa_user:
                            item.responsible_qa_id = qa_user.id
                    
                    if dev_name:
                        dev_user = get_or_create_user(dev_name)
                        if dev_user:
                            item.responsible_dev_id = dev_user.id
                    
                    if accountable_name:
                        accountable_user = get_or_create_user(accountable_name)
                        if accountable_user:
                            item.accountable_id = accountable_user.id
                    
                    session.add(item)
                    session.commit()
                    stats['imported'] += 1
                    
                    if stats['imported'] % 10 == 0:
                        print(f'  ✓ Импортировано: {stats["imported"]}')
                
                except Exception as e:
                    session.rollback()
                    stats['errors'] += 1
                    print(f'  ❌ Ошибка при импорте {functional_id}: {e}')
                    continue
        
        # Финальная статистика
        print('\n' + '='*60)
        print('📊 ИТОГИ ИМПОРТА:')
        print(f'  📁 Всего строк в CSV: {stats["total"]}')
        print(f'  ✅ Импортировано: {stats["imported"]}')
        print(f'  👥 Создано пользователей: {stats["users_created"]}')
        print(f'  ⏭️  Пропущено (пустые): {stats["skipped_empty"]}')
        print(f'  ⏭️  Пропущено (дубли): {stats["skipped_duplicate"]}')
        print(f'  ❌ Ошибок: {stats["errors"]}')
        print('='*60)
        
    except Exception as e:
        print(f'❌ Критическая ошибка: {e}')
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    import_csv()
