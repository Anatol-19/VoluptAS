"""
Модель Dictionary - справочники системы

Универсальная таблица для хранения всех справочников:
- Types (типы элементов)
- Segments (сегменты)
- Automation Statuses
- Maturity Levels
- Positions (должности)
"""

from sqlalchemy import Column, Integer, String, Boolean
from src.db.base import Base


class Dictionary(Base):
    """
    Справочник (универсальная таблица для всех словарей)

    Хранит все справочные данные системы.
    Вместо хардкода в Python коде - все в БД.
    """

    __tablename__ = "dictionaries"

    id = Column(Integer, primary_key=True, autoincrement=True)

    dict_type = Column(String(50), nullable=False, index=True)
    # Enum: 'type', 'segment', 'automation_status', 'maturity', 'position'

    value = Column(String(200), nullable=False)
    # Значение справочника (например: "Module", "Epic", "UI", "QA Engineer")

    display_order = Column(Integer, default=0)
    # Порядок отображения в UI (для сортировки)

    is_active = Column(Boolean, default=True, index=True)
    # Активен ли элемент справочника (для скрытия без удаления)

    description = Column(String(500), nullable=True)
    # Описание/комментарий (опционально)

    def __repr__(self):
        return f"<Dictionary(type='{self.dict_type}', value='{self.value}')>"

    def __str__(self):
        return self.value

    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            "id": self.id,
            "dict_type": self.dict_type,
            "value": self.value,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "description": self.description,
        }
