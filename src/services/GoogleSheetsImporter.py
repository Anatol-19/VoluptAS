"""
Google Sheets Importer Service

Импорт данных из Google Sheets в БД VoluptAS:
- Импорт functional_items
- Импорт users
- Импорт relations
- Обработка существующих записей (update vs insert)
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from src.models import FunctionalItem, User, Relation
from src.integrations.google import GoogleSheetsClient
import logging

logger = logging.getLogger(__name__)


class GoogleSheetsImporter:
    """Импорт данных из Google Sheets в БД"""
    
    def __init__(self, credentials_path: str, session: Session):
        """
        Args:
            credentials_path: Путь к service_account.json
            session: SQLAlchemy session
        """
        self.credentials_path = credentials_path
        self.session = session
    
    def import_all_tables(self, spreadsheet_id: str) -> Dict[str, int]:
        """
        Импорт всех таблиц из Google Sheets
        
        Args:
            spreadsheet_id: ID Google Spreadsheet
        
        Returns:
            dict: Статистика импорта
        """
        logger.info(f"🚀 Начало импорта из spreadsheet {spreadsheet_id}")
        
        stats = {
            'functional_items': 0,
            'users': 0,
            'relations': 0,
            'errors': []
        }
        
        try:
            # 1. Импорт пользователей (сначала, т.к. на них ссылки)
            stats['users'] = self._import_users(spreadsheet_id, "Сотрудники")
            
            # 2. Импорт функциональных элементов
            stats['functional_items'] = self._import_functional_items(
                spreadsheet_id, 
                "Функционал"
            )
            
            # 3. Импорт связей
            stats['relations'] = self._import_relations(spreadsheet_id, "Связи")
            
            logger.info(f"✅ Импорт завершён: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка импорта: {e}")
            stats['errors'].append(str(e))
            raise
    
    def _import_users(self, spreadsheet_id: str, sheet_name: str) -> int:
        """Импорт пользователей"""
        logger.info(f"👥 Импорт users из листа '{sheet_name}'")
        
        client = GoogleSheetsClient(
            credentials_path=self.credentials_path,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=sheet_name,
            clear_on_open=False  # НЕ очищать при импорте!
        )
        
        # Читаем все данные
        all_data = client.sheet.get_all_records()
        logger.info(f"   Найдено строк: {len(all_data)}")
        
        imported_count = 0
        updated_count = 0
        
        for row in all_data:
            try:
                # Ищем существующего пользователя
                user = self.session.query(User).filter(
                    User.name == row.get('Name', '')
                ).first()
                
                if user:
                    # Обновляем
                    user.position = row.get('Position', '') or None
                    user.email = row.get('Email', '') or None
                    user.zoho_id = row.get('Zoho ID', '') or None
                    user.github_username = row.get('GitHub', '') or None
                    user.is_active = 1 if row.get('Active') == 'Да' else 0
                    updated_count += 1
                else:
                    # Создаём нового
                    user = User(
                        name=row.get('Name', ''),
                        position=row.get('Position', '') or None,
                        email=row.get('Email', '') or None,
                        zoho_id=row.get('Zoho ID', '') or None,
                        github_username=row.get('GitHub', '') or None,
                        is_active=1 if row.get('Active') == 'Да' else 0
                    )
                    self.session.add(user)
                    imported_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка импорта пользователя {row.get('Name')}: {e}")
        
        self.session.commit()
        logger.info(f"✅ Импортировано: {imported_count}, Обновлено: {updated_count}")
        
        return imported_count + updated_count
    
    def _import_functional_items(self, spreadsheet_id: str, sheet_name: str) -> int:
        """Импорт функциональных элементов"""
        logger.info(f"📊 Импорт functional_items из листа '{sheet_name}'")
        
        client = GoogleSheetsClient(
            credentials_path=self.credentials_path,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=sheet_name,
            clear_on_open=False  # НЕ очищать при импорте!
        )
        
        all_data = client.sheet.get_all_records()
        logger.info(f"   Найдено строк: {len(all_data)}")
        
        imported_count = 0
        updated_count = 0
        
        for row in all_data:
            try:
                func_id = row.get('FuncID', '').strip()
                if not func_id:
                    continue
                
                # Ищем существующий элемент
                item = self.session.query(FunctionalItem).filter(
                    FunctionalItem.func_id == func_id
                ).first()
                
                # Находим пользователей по имени
                qa_user = self.session.query(User).filter(
                    User.name == row.get('QA', '')
                ).first() if row.get('QA') else None
                
                dev_user = self.session.query(User).filter(
                    User.name == row.get('Dev', '')
                ).first() if row.get('Dev') else None
                
                accountable_user = self.session.query(User).filter(
                    User.name == row.get('Accountable', '')
                ).first() if row.get('Accountable') else None
                
                data = {
                    'func_id': func_id,
                    'alias_tag': row.get('Alias', '') or None,
                    'title': row.get('Title', '') or None,
                    'type': row.get('Type', '') or None,
                    'segment': row.get('Segment', '') or None,
                    'module': row.get('Module', '') or None,
                    'epic': row.get('Epic', '') or None,
                    'feature': row.get('Feature', '') or None,
                    'is_crit': row.get('isCrit') == 'Да',
                    'is_focus': row.get('isFocus') == 'Да',
                    'responsible_qa_id': qa_user.id if qa_user else None,
                    'responsible_dev_id': dev_user.id if dev_user else None,
                    'accountable_id': accountable_user.id if accountable_user else None,
                    'test_cases_linked': row.get('Test Cases', '') or None,
                    'automation_status': row.get('Automation', '') or None,
                    'documentation_links': row.get('Documentation', '') or None,
                    'status': row.get('Status', '') or None,
                    'maturity': row.get('Maturity', '') or None,
                }
                
                if item:
                    # Обновляем существующий
                    for key, value in data.items():
                        setattr(item, key, value)
                    updated_count += 1
                else:
                    # Создаём новый
                    item = FunctionalItem(**data)
                    self.session.add(item)
                    imported_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка импорта элемента {row.get('FuncID')}: {e}")
        
        self.session.commit()
        logger.info(f"✅ Импортировано: {imported_count}, Обновлено: {updated_count}")
        
        return imported_count + updated_count
    
    def _import_relations(self, spreadsheet_id: str, sheet_name: str) -> int:
        """Импорт связей"""
        logger.info(f"🔗 Импорт relations из листа '{sheet_name}'")
        
        try:
            client = GoogleSheetsClient(
                credentials_path=self.credentials_path,
                spreadsheet_id=spreadsheet_id,
                worksheet_name=sheet_name,
                clear_on_open=False  # НЕ очищать при импорте!
            )
        except Exception as e:
            logger.warning(f"Лист '{sheet_name}' не найден, пропускаем: {e}")
            return 0
        
        all_data = client.sheet.get_all_records()
        logger.info(f"   Найдено строк: {len(all_data)}")
        
        imported_count = 0
        
        for row in all_data:
            try:
                source_id = row.get('Source ID')
                target_id = row.get('Target ID')
                
                if not source_id or not target_id:
                    continue
                
                # Ищем существующую связь
                rel = self.session.query(Relation).filter(
                    Relation.source_id == source_id,
                    Relation.target_id == target_id,
                    Relation.type == row.get('Type', 'hierarchy')
                ).first()
                
                if not rel:
                    # Создаём новую связь
                    rel = Relation(
                        source_id=int(source_id),
                        target_id=int(target_id),
                        type=row.get('Type', 'hierarchy'),
                        weight=float(row.get('Weight', 1.0)),
                        directed=row.get('Directed') == 'Да',
                        active=row.get('Active', 'Да') == 'Да'
                    )
                    
                    # Устанавливаем notes в metadata
                    notes = row.get('Notes', '')
                    if notes:
                        rel.set_metadata({'notes': notes})
                    
                    self.session.add(rel)
                    imported_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка импорта связи {row.get('Source ID')}->{row.get('Target ID')}: {e}")
        
        self.session.commit()
        logger.info(f"✅ Импортировано связей: {imported_count}")
        
        return imported_count
