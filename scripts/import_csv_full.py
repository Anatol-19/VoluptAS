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

def import_from_csv(csv_path, session=None):
    """
    Импорт из любого CSV файла
    
    Args:
        csv_path: Путь к CSV файлу
        session: Сессия SQLAlchemy (если None, создаётся новая)
    
    Returns:
        int: Количество импортированных элементов
    """
    close_session = False
    if session is None:
        from src.db import SessionLocal
        session = SessionLocal()  # Вызываем функцию для получения сессии
        close_session = True
    
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
                
                # Поддержка разных форматов CSV
                functional_id = (row.get('Functional ID', '') or row.get('FuncID', '')).strip()
                title = row.get('Title', '').strip()
                
                # Поддержка вариантов написания Responsible
                responsible_qa = (
                    row.get('Responsible (QA)', '') or 
                    row.get('ResponsibleQA', '') or 
                    row.get('QA', '')
                ).strip()
                
                responsible_dev = (
                    row.get('Responsible (Dev)', '') or 
                    row.get('ResponsibleDev', '') or 
                    row.get('Dev', '')
                ).strip()
                
                accountable = (
                    row.get('Accountable', '') or 
                    row.get('Resp (Accountable)', '')
                ).strip()

                # Пропускаем пустые строки
                if not functional_id or not title:
                    stats['skipped_empty'] += 1
                    print(f'  ⚠️  Пропущено (пустое): строка {stats["total"]} - нет FuncID или Title')
                    continue
                
                # Проверяем дубликаты
                existing = session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
                if existing:
                    stats['skipped_duplicate'] += 1
                    continue
                
                try:
                    # Определяем Type из Title если не указан
                    item_type = row.get('Type', '').strip()
                    if not item_type:
                        # Авто-определение из Title
                        title_upper = title.upper()
                        if '[MODULE]' in title_upper:
                            item_type = 'Module'
                        elif '[EPIC]' in title_upper:
                            item_type = 'Epic'
                        elif '[FEATURE]' in title_upper:
                            item_type = 'Feature'
                        elif '[STORY]' in title_upper:
                            item_type = 'Story'
                        elif '[PAGE]' in title_upper:
                            item_type = 'Page'
                        elif '[ELEMENT]' in title_upper or '[ELEMENT]' in title_upper:
                            item_type = 'Element'
                        elif 'SERVICE:' in title_upper:
                            item_type = 'Service'
                        else:
                            print(f'  ⚠️  Пропущено (нет Type): строка {stats["total"]} - {functional_id}')
                            stats['skipped_empty'] += 1
                            continue
                    
                    # Создаём элемент со ВСЕМИ полями
                    item = FunctionalItem(
                        functional_id=functional_id,
                        alias_tag=row.get('Alias', '').strip() or row.get('Alias Tag', '').strip() or None,
                        title=title,
                        type=item_type,
                        module=row.get('Module', '').strip() or None,
                        epic=row.get('Epic', '').strip() or None,
                        feature=row.get('Feature', '').strip() or None,
                        stories=row.get('Stories', '').strip() or None,
                        segment=row.get('Segment', '').strip() or row.get('Segment ', '').strip() or None,
                        description=row.get('Description', '').strip() or None,
                        tags=row.get('Tags and Aliases', '').strip() or row.get('Tags', '').strip() or None,
                        roles=row.get('Roles', '').strip() or None,
                        is_focus=1 if (row.get('isFocus', '') or row.get('Focus', '')).strip() in ['TRUE', '1', 'Yes', 'Да'] else 0,
                        is_crit=1 if (row.get('isCrit', '') or row.get('Crit', '')).strip() in ['TRUE', '1', 'Yes', 'Да'] else 0,
                        # Покрытие
                        test_cases_linked=row.get('Test Cases', '').strip() or row.get('Test Cases Linked', '').strip() or None,
                        automation_status=row.get('Automation Status', '').strip() or None,
                        documentation_links=row.get('Documentation', '').strip() or row.get('Documentation Links', '').strip() or None,
                        # INFRA
                        maturity=row.get('Maturity', '').strip() or None,
                        container=row.get('Container', '').strip() or None,
                        database=row.get('Database', '').strip() or None,
                        subsystems_involved=row.get('Subsystems involved', '').strip() or row.get('Subsystems Involved', '').strip() or None,
                        external_services=row.get('External Services', '').strip() or None,
                    )
                    
                    # Ответственные (используем новые переменные с поддержкой вариантов)
                    if responsible_qa:
                        qa_user = get_or_create_user(responsible_qa)
                        if qa_user:
                            item.responsible_qa_id = qa_user.id
                            print(f'    👤 QA: {responsible_qa}')

                    if responsible_dev:
                        dev_user = get_or_create_user(responsible_dev)
                        if dev_user:
                            item.responsible_dev_id = dev_user.id
                            print(f'    👤 Dev: {responsible_dev}')

                    if accountable:
                        accountable_user = get_or_create_user(accountable)
                        if accountable_user:
                            item.accountable_id = accountable_user.id
                            print(f'    👤 Accountable: {accountable}')
                    
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
        
        return stats['imported']
        
    except Exception as e:
        print(f'❌ Критическая ошибка: {e}')
        session.rollback()
        return 0
    finally:
        if close_session:
            session.close()


def import_csv():
    """Импорт из стандартного места (data/import/voluptas_data.csv)"""
    csv_path = project_root / 'data' / 'import' / 'voluptas_data.csv'
    print(f'📂 Читаем: {csv_path}')
    import_from_csv(str(csv_path))


if __name__ == '__main__':
    import_csv()
