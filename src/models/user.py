"""
Модель User - справочник сотрудников

Содержит информацию о пользователях системы (QA, Dev, и другие роли)
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from src.db.base import Base


class User(Base):
    """
    Модель пользователя (сотрудника)

    Используется для:
    - Назначения ответственных (Responsible QA/Dev)
    - RACI ролей (Accountable, Consulted, Informed)
    - Справочника сотрудников

    Редактируется только через отдельный менеджер (не "на лету")
    """

    __tablename__ = "users"

    # Первичный ключ
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Основные поля
    name = Column(String(200), nullable=False, unique=True, index=True)
    position = Column(String(200), nullable=True)  # Должность
    email = Column(String(200), nullable=True, unique=True)

    # Интеграции
    zoho_id = Column(String(100), nullable=True)  # ID в Zoho
    github_username = Column(String(100), nullable=True)

    # Метаданные
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Дополнительные поля
    is_active = Column(Integer, default=1)  # 1 = активен, 0 = неактивен
    notes = Column(String(500), nullable=True)  # Заметки

    def __repr__(self):
        """Строковое представление"""
        return f"<User(id={self.id}, name='{self.name}', position='{self.position}')>"

    def __str__(self):
        """Для отображения в UI"""
        return self.name

    def to_dict(self):
        """
        Преобразовать в словарь

        Returns:
            dict: Словарь с данными пользователя
        """
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "email": self.email,
            "zoho_id": self.zoho_id,
            "github_username": self.github_username,
            "is_active": bool(self.is_active),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
