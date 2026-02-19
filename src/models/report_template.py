"""
Модель для хранения шаблонов отчётов

Поддерживает markdown шаблоны с placeholder'ами для динамической генерации
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from src.db.base import Base
from datetime import datetime, timezone


class ReportTemplate(Base):
    """Шаблон отчёта в формате Markdown"""

    __tablename__ = "report_templates"

    # Первичный ключ
    id = Column(Integer, primary_key=True)

    # Основные поля
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Markdown контент шаблона
    content = Column(Text, nullable=False)

    # Тип шаблона (test_plan, bug_report, sprint_report)
    template_type = Column(String(100), nullable=False, default="test_plan")

    # Метаданные
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<ReportTemplate(name='{self.name}', type='{self.template_type}')>"

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "template_type": self.template_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
