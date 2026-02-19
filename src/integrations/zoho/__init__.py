"""
Zoho Projects API Integration - MATURE CODE

Полноценный клиент для работы с Zoho Projects API:
- Задачи (tasks)
- Баги (bugs)
- Мейлстоуны (milestones)
- Пользователи (users)
- Статусы (statuses)

⚠️ MATURE CODE - проверенный код из продакшена
Используется в боевых скриптах генерации тест-планов
"""

from .Zoho_api_client import ZohoAPI
from .User import User, UserManager
from .TaskStatus import TaskStatus, TaskStatusManager
from .DefectStatus import DefectStatus, DefectStatusManager
from .portal_data import (
    user_manager,
    task_status_manager,
    defect_status_manager,
    create_user_manager,
    create_task_status_manager,
    create_defect_status_manager,
)

__all__ = [
    "ZohoAPI",
    "User",
    "UserManager",
    "TaskStatus",
    "TaskStatusManager",
    "DefectStatus",
    "DefectStatusManager",
    "user_manager",
    "task_status_manager",
    "defect_status_manager",
    "create_user_manager",
    "create_task_status_manager",
    "create_defect_status_manager",
]
