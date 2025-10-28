"""
Модель для хранения задач из Zoho Projects

Сохраняет задачи из Zoho для синхронизации с VoluptAS functional_items
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.db.base import Base
from datetime import datetime


class ZohoTask(Base):
    """Задача из Zoho Projects"""
    __tablename__ = 'zoho_tasks'
    
    # Первичный ключ
    id = Column(Integer, primary_key=True)
    
    # Zoho данные
    zoho_task_id = Column(String(50), unique=True, nullable=False, index=True)
    zoho_project_id = Column(String(50), nullable=False, index=True)
    
    # Основные поля
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)
    
    # Даты
    created_time = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
    # Ответственные (Zoho ID)
    owner_id = Column(String(50), nullable=True)
    owner_name = Column(String(255), nullable=True)
    
    # Связи
    milestone_id = Column(String(50), nullable=True, index=True)
    milestone_name = Column(String(500), nullable=True)
    tasklist_id = Column(String(50), nullable=True, index=True)
    tasklist_name = Column(String(500), nullable=True)
    
    # Дополнительные данные
    tags = Column(JSON, nullable=True)  # Список тегов
    custom_fields = Column(JSON, nullable=True)  # Кастомные поля из Zoho
    
    # Связь с VoluptAS
    functional_item_id = Column(Integer, ForeignKey('functional_items.id'), nullable=True, index=True)
    functional_item = relationship("FunctionalItem", backref="zoho_tasks")
    
    # Метаданные синхронизации
    synced_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_synced = Column(Boolean, default=False)  # Синхронизирована ли с functional_items
    
    def __repr__(self):
        return f"<ZohoTask(zoho_id={self.zoho_task_id}, name='{self.name}', status='{self.status}')>"
    
    def to_dict(self):
        """Преобразование в словарь для экспорта"""
        return {
            'id': self.id,
            'zoho_task_id': self.zoho_task_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'owner_name': self.owner_name,
            'milestone_name': self.milestone_name,
            'tasklist_name': self.tasklist_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_synced': self.is_synced,
            'functional_item_id': self.functional_item_id,
        }
