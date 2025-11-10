"""
Модель FunctionalItem - функциональный элемент продукта

Основная модель системы. Содержит все данные о фиче/эпике/модуле/странице и т.д.
Основана на реальной структуре из VoluptaS VRS.xlsx
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.base import Base
from typing import Optional, List, Dict


# ПРИМЕЧАНИЕ: Таблица functional_item_relations теперь определена в models/relation.py
# как полноценная модель с типами связей


class FunctionalItem(Base):
    """
    Функциональный элемент (фича-строка)
    
    Представляет любой функциональный элемент системы:
    Module, Epic, Feature, Page, Service, Element, Story
    """
    
    __tablename__ = "functional_items"
    
    # === ПЕРВИЧНЫЙ КЛЮЧ ===
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # === Func ID (главный тег) ===
    func_id = Column(String(500), nullable=False, unique=True, index=True)

    # === ОСНОВНЫЕ ПОЛЯ ===
    title = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="New")

    # === ИЕРАРХИЯ ===
    parent_id = Column(Integer, ForeignKey('functional_items.id'), nullable=True)
    children = relationship("FunctionalItem", backref="parent", remote_side=[id])

    module = Column(String(200), nullable=True, index=True)
    epic = Column(String(200), nullable=True, index=True)
    feature = Column(String(200), nullable=True, index=True)

    # === МЕТА-ДАННЫЕ ===
    segment = Column(String(100), nullable=True)
    alias_tag = Column(String(200), unique=True, nullable=True)
    tags = Column(Text, nullable=True)

    # === ФЛАГИ ===
    is_crit = Column(Boolean, nullable=True)
    is_focus = Column(Boolean, nullable=True)

    # === ОТВЕТСТВЕННЫЕ ===
    responsible_qa_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    responsible_dev_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    accountable_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    consulted_ids = Column(Text, nullable=True)
    informed_ids = Column(Text, nullable=True)

    # === ПОКРЫТИЕ ===
    test_cases_linked = Column(Text, nullable=True)
    automation_status = Column(String(50), nullable=True)
    documentation_links = Column(Text, nullable=True)
    maturity = Column(String(50), nullable=True)

    # === ТЕХНИЧЕСКИЕ ДЕТАЛИ ===
    container = Column(String(200), nullable=True)
    database = Column(String(200), nullable=True)
    subsystems_involved = Column(Text, nullable=True)
    external_services = Column(Text, nullable=True)

    # === МЕТА ===
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    created_by = Column(String(200), nullable=True)
    updated_by = Column(String(200), nullable=True)

    # === ОТНОШЕНИЯ ===
    responsible_qa = relationship("User", foreign_keys=[responsible_qa_id])
    responsible_dev = relationship("User", foreign_keys=[responsible_dev_id])
    accountable = relationship("User", foreign_keys=[accountable_id])

    # === МЕТОДЫ ===
    
    def __repr__(self):
        """Строковое представление для отладки"""
        return f"<FunctionalItem(id={self.id}, func_id='{self.func_id}', title='{self.title}')>"

    def __str__(self):
        """Для отображения в UI"""
        return f"{self.func_id}: {self.title}"

    def to_dict(self) -> Dict:
        """
        Преобразовать в словарь для экспорта/API
        
        Returns:
            dict: Словарь с данными элемента
        """
        return {
            "id": self.id,
            "func_id": self.func_id,
            "alias_tag": self.alias_tag,
            "title": self.title,
            "type": self.type,
            "description": self.description,
            
            # Иерархия
            "module": self.module,
            "epic": self.epic,
            "feature": self.feature,
            "stories": self.stories,
            
            # Сегмент и теги
            "segment": self.segment,
            "tags": self.tags,
            "aliases": self.aliases,
            
            # Приоритеты
            "is_crit": bool(self.is_crit),
            "is_focus": bool(self.is_focus),
            
            # Ответственные
            "responsible_qa": self.responsible_qa.name if self.responsible_qa else None,
            "responsible_dev": self.responsible_dev.name if self.responsible_dev else None,
            "accountable": self.accountable.name if self.accountable else None,
            "consulted_ids": self.consulted_ids,
            "informed_ids": self.informed_ids,
            
            # Покрытие
            "test_cases_linked": self.test_cases_linked,
            "automation_status": self.automation_status,
            "documentation_links": self.documentation_links,
            
            # Статус
            "maturity": self.maturity,
            "status": self.status,
            
            # Технические детали
            "container": self.container,
            "database": self.database,
            "subsystems_involved": self.subsystems_involved,
            "external_services": self.external_services,
            
            # Мета
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_covered_by_tests(self) -> bool:
        """Проверка покрытия тест-кейсами"""
        return bool(self.test_cases_linked and len(self.test_cases_linked.strip()) > 0)
    
    @property
    def is_automated(self) -> bool:
        """Проверка автоматизации"""
        return self.automation_status in ["Automated", "Partially Automated"]
    
    @property
    def is_documented(self) -> bool:
        """Проверка наличия документации"""
        return bool(self.documentation_links and len(self.documentation_links.strip()) > 0)
    
    @property
    def coverage_status(self) -> str:
        """
        Статус покрытия (для цветовых индикаторов)
        
        Returns:
            str: "full", "partial", "none"
        """
        has_tests = self.is_covered_by_tests
        has_auto = self.is_automated
        has_docs = self.is_documented
        
        if has_tests and has_auto and has_docs:
            return "full"
        elif has_tests or has_auto or has_docs:
            return "partial"
        else:
            return "none"
