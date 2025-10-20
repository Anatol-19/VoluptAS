"""
Zoho Sync Service

Сервис для синхронизации задач из Zoho Projects в VoluptAS:
- Загрузка задач из Zoho Projects (по milestone, tasklist, фильтрам)
- Сохранение в локальную БД (zoho_tasks)
- Сопоставление с functional_items
- Обновление ответственных QA
"""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.integrations.zoho.Zoho_api_client import ZohoAPI
from src.models import ZohoTask, FunctionalItem, User
import logging

logger = logging.getLogger(__name__)


class ZohoSyncService:
    """Сервис синхронизации задач Zoho с VoluptAS"""
    
    def __init__(self, session: Session):
        """
        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.zoho_client = None
    
    def init_zoho_client(self) -> bool:
        """
        Инициализация Zoho API клиента
        
        Returns:
            bool: Успешность инициализации
        """
        try:
            self.zoho_client = ZohoAPI()
            logger.info("✅ Zoho API клиент инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Zoho API: {e}")
            return False
    
    def sync_tasks_by_milestone(self, milestone_name: str) -> Dict[str, int]:
        """
        Синхронизация задач из Zoho по названию milestone
        
        Args:
            milestone_name: Название milestone в Zoho
            
        Returns:
            dict: Статистика синхронизации
        """
        if not self.zoho_client:
            if not self.init_zoho_client():
                return {'error': 'Не удалось инициализировать Zoho API'}
        
        logger.info(f"📋 Синхронизация задач из milestone: {milestone_name}")
        
        # Получаем ID milestone
        milestone_id = self.zoho_client.get_milestone_id_by_name(milestone_name)
        if not milestone_id:
            logger.warning(f"⚠️ Milestone '{milestone_name}' не найден")
            return {'error': f'Milestone "{milestone_name}" не найден'}
        
        # Получаем задачи
        tasks_data = self.zoho_client.get_tasks_by_milestone(milestone_id)
        logger.info(f"   Получено задач: {len(tasks_data)}")
        
        return self._process_tasks(tasks_data, milestone_id, milestone_name)
    
    def sync_tasks_by_tasklist(self, tasklist_name: str) -> Dict[str, int]:
        """
        Синхронизация задач из Zoho по названию tasklist
        
        Args:
            tasklist_name: Название tasklist в Zoho
            
        Returns:
            dict: Статистика синхронизации
        """
        if not self.zoho_client:
            if not self.init_zoho_client():
                return {'error': 'Не удалось инициализировать Zoho API'}
        
        logger.info(f"📋 Синхронизация задач из tasklist: {tasklist_name}")
        
        # Получаем ID tasklist
        tasklist_id = self.zoho_client.get_tasklist_id_by_name(tasklist_name)
        if not tasklist_id:
            logger.warning(f"⚠️ Tasklist '{tasklist_name}' не найден")
            return {'error': f'Tasklist "{tasklist_name}" не найден'}
        
        # Получаем задачи
        tasks_data = self.zoho_client.get_tasks_by_tasklist(tasklist_id)
        logger.info(f"   Получено задач: {len(tasks_data)}")
        
        return self._process_tasks(tasks_data, tasklist_id=tasklist_id, tasklist_name=tasklist_name)
    
    def sync_tasks_by_filter(
        self, 
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        owner_id: Optional[str] = None,
        milestone_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Синхронизация задач по фильтрам
        
        Args:
            created_after: Дата начала (YYYY-MM-DD)
            created_before: Дата окончания (YYYY-MM-DD)
            owner_id: ID ответственного
            milestone_id: ID milestone
            
        Returns:
            dict: Статистика синхронизации
        """
        if not self.zoho_client:
            if not self.init_zoho_client():
                return {'error': 'Не удалось инициализировать Zoho API'}
        
        logger.info(f"📋 Синхронизация задач по фильтрам")
        
        # Получаем задачи
        tasks_data = self.zoho_client.get_entities_by_filter(
            entity_type='tasks',
            created_after=created_after,
            created_before=created_before,
            owner_id=owner_id,
            milestone_id=milestone_id
        )
        logger.info(f"   Получено задач: {len(tasks_data)}")
        
        return self._process_tasks(tasks_data)
    
    def _process_tasks(
        self, 
        tasks_data: List[Dict], 
        milestone_id: Optional[str] = None,
        milestone_name: Optional[str] = None,
        tasklist_id: Optional[str] = None,
        tasklist_name: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Обработка и сохранение задач в БД
        
        Args:
            tasks_data: Данные задач из Zoho API
            milestone_id: ID milestone (опционально)
            milestone_name: Название milestone (опционально)
            tasklist_id: ID tasklist (опционально)
            tasklist_name: Название tasklist (опционально)
            
        Returns:
            dict: Статистика (new, updated, skipped)
        """
        stats = {'new': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        
        for task in tasks_data:
            try:
                zoho_task_id = str(task.get('id'))
                
                # Проверяем, существует ли задача
                existing_task = self.session.query(ZohoTask).filter_by(
                    zoho_task_id=zoho_task_id
                ).first()
                
                if existing_task:
                    # Обновляем существующую
                    self._update_task(existing_task, task, milestone_name, tasklist_name)
                    stats['updated'] += 1
                else:
                    # Создаём новую
                    self._create_task(task, milestone_id, milestone_name, tasklist_id, tasklist_name)
                    stats['new'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Ошибка обработки задачи {task.get('id')}: {e}")
                stats['errors'] += 1
        
        # Сохраняем изменения
        try:
            self.session.commit()
            logger.info(f"✅ Синхронизация завершена: {stats}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Ошибка сохранения в БД: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _create_task(
        self, 
        task_data: Dict, 
        milestone_id: Optional[str] = None,
        milestone_name: Optional[str] = None,
        tasklist_id: Optional[str] = None,
        tasklist_name: Optional[str] = None
    ):
        """Создание новой задачи в БД"""
        zoho_task = ZohoTask(
            zoho_task_id=str(task_data.get('id')),
            zoho_project_id=str(task_data.get('project_id', '')),
            name=task_data.get('name', ''),
            description=task_data.get('description', ''),
            status=task_data.get('status', {}).get('name', ''),
            priority=task_data.get('priority', ''),
            created_time=self._parse_zoho_date(task_data.get('created_time')),
            start_date=self._parse_zoho_date(task_data.get('start_date')),
            end_date=self._parse_zoho_date(task_data.get('end_date')),
            owner_id=str(task_data.get('details', {}).get('owners', [{}])[0].get('id', '')),
            owner_name=task_data.get('details', {}).get('owners', [{}])[0].get('name', ''),
            milestone_id=milestone_id or str(task_data.get('milestone', {}).get('id', '')),
            milestone_name=milestone_name or task_data.get('milestone', {}).get('name', ''),
            tasklist_id=tasklist_id or str(task_data.get('tasklist', {}).get('id', '')),
            tasklist_name=tasklist_name or task_data.get('tasklist', {}).get('name', ''),
            tags=task_data.get('tags', []),
            custom_fields=task_data.get('custom_fields', {}),
        )
        self.session.add(zoho_task)
        logger.debug(f"   + Создана задача: {zoho_task.name}")
    
    def _update_task(
        self, 
        zoho_task: ZohoTask, 
        task_data: Dict,
        milestone_name: Optional[str] = None,
        tasklist_name: Optional[str] = None
    ):
        """Обновление существующей задачи"""
        zoho_task.name = task_data.get('name', zoho_task.name)
        zoho_task.description = task_data.get('description', zoho_task.description)
        zoho_task.status = task_data.get('status', {}).get('name', zoho_task.status)
        zoho_task.priority = task_data.get('priority', zoho_task.priority)
        zoho_task.start_date = self._parse_zoho_date(task_data.get('start_date')) or zoho_task.start_date
        zoho_task.end_date = self._parse_zoho_date(task_data.get('end_date')) or zoho_task.end_date
        zoho_task.owner_name = task_data.get('details', {}).get('owners', [{}])[0].get('name', zoho_task.owner_name)
        
        if milestone_name:
            zoho_task.milestone_name = milestone_name
        if tasklist_name:
            zoho_task.tasklist_name = tasklist_name
        
        zoho_task.synced_at = datetime.utcnow()
        logger.debug(f"   ↻ Обновлена задача: {zoho_task.name}")
    
    @staticmethod
    def _parse_zoho_date(date_str: Optional[str]) -> Optional[datetime]:
        """Парсинг даты из Zoho (формат: MM-DD-YYYY или ISO)"""
        if not date_str:
            return None
        
        # Попытка парсинга различных форматов
        formats = ['%m-%d-%Y', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"⚠️ Не удалось распарсить дату: {date_str}")
        return None
    
    def get_zoho_tasks(self, filters: Optional[Dict] = None) -> List[ZohoTask]:
        """
        Получение задач Zoho из локальной БД
        
        Args:
            filters: Фильтры (is_synced, milestone_name, status)
            
        Returns:
            List[ZohoTask]: Список задач
        """
        query = self.session.query(ZohoTask)
        
        if filters:
            if 'is_synced' in filters:
                query = query.filter(ZohoTask.is_synced == filters['is_synced'])
            if 'milestone_name' in filters:
                query = query.filter(ZohoTask.milestone_name == filters['milestone_name'])
            if 'status' in filters:
                query = query.filter(ZohoTask.status == filters['status'])
        
        return query.order_by(ZohoTask.created_time.desc()).all()
