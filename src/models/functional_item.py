"""
Модель FunctionalItem - функциональный элемент продукта

Основная модель системы. Содержит все данные о фиче/эпике/модуле/странице и т.д.
Основана на реальной структуре из VoluptaS VRS.xlsx
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.database import Base
from typing import Optional, List, Dict


# ПРИМЕЧАНИЕ: Таблица functional_item_relations теперь определена в models/relation.py
# как полноценная модель с типами связей


class FunctionalItem(Base):
    """
    Функциональный элемент (фича-строка)
    
    Представляет любой функциональный элемент системы:
    Module, Epic, Feature, Page, Service, Element, Story
    
    Содержит все поля из ТЗ + реальной таблицы VoluptaS VRS.xlsx
    """
    
    __tablename__ = "functional_items"
    
    # === ПЕРВИЧНЫЙ КЛЮЧ ===
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # === FUNCTIONAL ID (главный тег) ===
    functional_id = Column(String(500), nullable=False, unique=True, index=True)
    # Примеры: "front", "front.splash_page", "front.splash_page.cookies"
    # Автогенерируется по структуре module.epic.feature
    
    # === ALIAS TAG (короткий уникальный алиас) ===
    alias_tag = Column(String(200), unique=True, nullable=True, index=True)
    # Примеры: "cookies", "Value_Popup", "Login_Page"
    # Короткое название для удобного поиска
    # Если пустой — используется последняя часть functional_id
    
    # === ОСНОВНЫЕ ПОЛЯ ===
    title = Column(String(500), nullable=False)
    # Примеры: "[Module]: FRONT", "[Epic]: Slash Page", "[Feature]: Age cookies"
    
    type = Column(String(50), nullable=False, index=True)
    # Enum: Module, Epic, Feature, Page, Service, Element, Story
    
    description = Column(Text, nullable=True)
    # Подробное описание функционала
    
    # === ИЕРАРХИЯ ===
    # Иерархическая связь (parent-child)
    parent_id = Column(Integer, ForeignKey('functional_items.id'), nullable=True, index=True)
    
    # Старые поля для обратной совместимости
    module = Column(String(200), nullable=True, index=True)
    epic = Column(String(200), nullable=True, index=True)
    feature = Column(String(200), nullable=True, index=True)
    stories = Column(Text, nullable=True)  # JSON array или CSV строка
    
    # === СЕГМЕНТАЦИЯ ===
    segment = Column(String(100), nullable=True, index=True)
    # Enum: UI, UX/CX, API, Backend, Database, Integration, Security, Performance
    
    # === ТЕГИ И АЛИАСЫ ===
    tags = Column(Text, nullable=True)  # JSON array
    # Автоматические теги из структуры
    
    aliases = Column(Text, nullable=True)  # JSON array
    # Ручные алиасы для поиска и интеграций
    
    # === ПРИОРИТЕЗАЦИЯ ===
    is_crit = Column(Integer, default=0, index=True)  # 1 = критичный, 0 = нет
    is_focus = Column(Integer, default=0, index=True)  # 1 = фокусный, 0 = нет
    
    # === ОТВЕТСТВЕННЫЕ (RACI) ===
    # Foreign Keys к User
    responsible_qa_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    responsible_dev_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    accountable_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Множественные роли (JSON array of user IDs)
    consulted_ids = Column(Text, nullable=True)  # JSON array
    informed_ids = Column(Text, nullable=True)  # JSON array
    
    # Relationships для ответственных
    responsible_qa = relationship("User", foreign_keys=[responsible_qa_id])
    responsible_dev = relationship("User", foreign_keys=[responsible_dev_id])
    accountable = relationship("User", foreign_keys=[accountable_id])
    
    # Иерархические relationships
    parent = relationship("FunctionalItem", remote_side=[id], backref="children")
    
    # ПРИМЕЧАНИЕ: Связи теперь управляются через модель Relation
    # related_items доступны через outgoing_relations и incoming_relations
    
    # === ПОКРЫТИЕ ТЕСТАМИ ===
    test_cases_linked = Column(Text, nullable=True)  # JSON array или CSV
    # Список связанных тест-кейсов
    
    automation_status = Column(String(50), nullable=True, index=True)
    # Enum: Not Started, In Progress, Automated, Partially Automated, Not Applicable
    
    # === ДОКУМЕНТАЦИЯ ===
    documentation_links = Column(Text, nullable=True)  # JSON array
    # Ссылки на документацию, спеки, дизайны и т.д.
    
    # === ЗРЕЛОСТЬ И СТАТУС ===
    maturity = Column(String(50), nullable=True, index=True)
    # Enum: Draft, In Review, Approved, Deprecated
    
    status = Column(String(50), default="Approved", index=True)
    # Статус элемента (по умолчанию Approved)
    
    # === ТЕХНИЧЕСКИЕ ДЕТАЛИ ===
    container = Column(String(200), nullable=True)
    # Контейнер/сервис, где реализован функционал
    
    database = Column(String(200), nullable=True)
    # База данных, используемая функционалом
    
    subsystems_involved = Column(Text, nullable=True)  # JSON array
    # Список задействованных подсистем
    
    external_services = Column(Text, nullable=True)  # JSON array
    # Список внешних сервисов
    
    # === ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ ===
    roles = Column(Text, nullable=True)
    # Роли пользователей, для которых доступен функционал
    
    custom_fields = Column(Text, nullable=True)  # JSON object
    # Кастомные поля (для будущего расширения)
    
    # === МЕТАДАННЫЕ ===
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(200), nullable=True)
    updated_by = Column(String(200), nullable=True)
    
    # === МЕТОДЫ ===
    
    def __repr__(self):
        """Строковое представление для отладки"""
        return f"<FunctionalItem(id={self.id}, functional_id='{self.functional_id}', title='{self.title}')>"
    
    def __str__(self):
        """Для отображения в UI"""
        return f"{self.functional_id}: {self.title}"
    
    def to_dict(self) -> Dict:
        """
        Преобразовать в словарь для экспорта/API
        
        Returns:
            dict: Словарь с данными элемента
        """
        return {
            "id": self.id,
            "functional_id": self.functional_id,
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
