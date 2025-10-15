"""
Модель Relation - типизированная связь между функциональными элементами
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.database import Base
import json


class Relation(Base):
    """
    Типизированная связь между функциональными элементами
    
    Типы связей:
    - hierarchy: Parent-child иерархия (Module → Epic → Feature)
    - functional: N:M функциональные связи (Feature ↔ Feature)
    - page_element: POM-иерархия (Page → Element)
    - service_dependency: Зависимость от сервиса (Feature → Service)
    - test_coverage: Связь с тест-кейсами (Feature → TestCase)
    - bug_link: Связь с багами/задачами (Feature → ZohoBug)
    - doc_link: Ссылка на документацию (Feature → Doc)
    - custom: Пользовательская связь
    """
    
    __tablename__ = "functional_item_relations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Источник и цель связи
    source_id = Column(Integer, ForeignKey('functional_items.id', ondelete='CASCADE'), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey('functional_items.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Тип связи
    type = Column(String(50), nullable=False, default='functional', index=True)
    # Enum: hierarchy, functional, page_element, service_dependency, 
    #       test_coverage, bug_link, doc_link, custom
    
    # Направленная или нет
    directed = Column(Boolean, default=True)
    
    # Вес/важность связи
    weight = Column(Float, default=1.0)
    
    # Метаданные (JSON)
    meta_data = Column(Text, nullable=True)
    # {"origin": "manual|zoho|csv|qase|import", 
    #  "created_by": "user_id", 
    #  "notes": "Description",
    #  "provenance": {...}}
    
    # Активность связи
    active = Column(Boolean, default=True, index=True)
    
    # Даты создания/обновления
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    source = relationship("FunctionalItem", foreign_keys=[source_id], backref="outgoing_relations")
    target = relationship("FunctionalItem", foreign_keys=[target_id], backref="incoming_relations")
    
    def __repr__(self):
        return f"<Relation(id={self.id}, {self.source_id} -[{self.type}]-> {self.target_id})>"
    
    def get_metadata(self):
        """Парсинг JSON metadata"""
        if self.meta_data:
            try:
                return json.loads(self.meta_data)
            except:
                return {}
        return {}
    
    def set_metadata(self, data: dict):
        """Установка JSON metadata"""
        self.meta_data = json.dumps(data, ensure_ascii=False)
    
    def to_dict(self):
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "directed": self.directed,
            "weight": self.weight,
            "metadata": self.get_metadata(),
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Константы для типов связей
RELATION_TYPES = {
    'hierarchy': {
        'name': 'Hierarchy',
        'color': '#555555',
        'style': 'solid',
        'width': 3,
        'description': 'Parent-child иерархия'
    },
    'functional': {
        'name': 'Functional',
        'color': '#FF8C00',
        'style': 'solid',
        'width': 1.5,
        'description': 'Функциональные N:M связи'
    },
    'page_element': {
        'name': 'Page → Element',
        'color': '#87CEEB',
        'style': 'dashed',
        'width': 1,
        'description': 'POM-иерархия'
    },
    'service_dependency': {
        'name': 'Service Dependency',
        'color': '#9370DB',
        'style': 'dotted',
        'width': 2,
        'description': 'Зависимость от сервиса'
    },
    'test_coverage': {
        'name': 'Test Coverage',
        'color': '#32CD32',
        'style': 'dashed',
        'width': 1.5,
        'description': 'Связь с тест-кейсами'
    },
    'bug_link': {
        'name': 'Bug Link',
        'color': '#DC143C',
        'style': 'dashdot',
        'width': 1.5,
        'description': 'Связь с багами'
    },
    'doc_link': {
        'name': 'Documentation',
        'color': '#4169E1',
        'style': 'solid',
        'width': 1,
        'description': 'Ссылка на документацию'
    },
    'custom': {
        'name': 'Custom',
        'color': '#808080',
        'style': 'solid',
        'width': 1,
        'description': 'Пользовательская связь'
    }
}
