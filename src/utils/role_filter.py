"""
Фильтрация пользователей по ролям для назначений

Определяет какие роли могут быть назначены на конкретные позиции.
"""


class RoleFilter:
    """Фильтрация пользователей по ролям и должностям"""

    # QA роли - только для Responsible QA
    QA_ROLES = ["QA Engineer", "QA Team Lead", "QA Tech Lead"]

    # Dev роли - для Responsible Dev
    DEV_ROLES = [
        "Frontend Developer",
        "Frontend Lead",
        "Backend Tech Developer",
        "Backend Tech Lead",
        "DevOps Engineer",
        "Project Manager",
        "Product Owner",
    ]

    # Все роли - для Accountable, Consulted, Informed
    ALL_ROLES = (
        QA_ROLES
        + DEV_ROLES
        + ["Business Analyst", "Designer", "Content Manager", "Other"]
    )

    @classmethod
    def filter_users_for_qa(cls, users):
        """
        Фильтрует пользователей для назначения Responsible QA
        Только QA роли

        Args:
            users: список объектов User

        Returns:
            список отфильтрованных пользователей
        """
        return [u for u in users if cls._has_qa_role(u)]

    @classmethod
    def filter_users_for_dev(cls, users):
        """
        Фильтрует пользователей для назначения Responsible Dev
        Dev, PM, DevOps роли

        Args:
            users: список объектов User

        Returns:
            список отфильтрованных пользователей
        """
        return [u for u in users if cls._has_dev_role(u)]

    @classmethod
    def filter_users_for_raci(cls, users):
        """
        Фильтрует пользователей для RACI (Accountable, Consulted, Informed)
        Все активные сотрудники

        Args:
            users: список объектов User

        Returns:
            список всех активных пользователей
        """
        return users  # Все активные пользователи

    @classmethod
    def _has_qa_role(cls, user):
        """Проверяет, имеет ли пользователь QA роль"""
        if not user.position:
            return False
        return any(qa_role.lower() in user.position.lower() for qa_role in cls.QA_ROLES)

    @classmethod
    def _has_dev_role(cls, user):
        """Проверяет, имеет ли пользователь Dev/PM/DevOps роль"""
        if not user.position:
            return False
        return any(
            dev_role.lower() in user.position.lower() for dev_role in cls.DEV_ROLES
        )

    @classmethod
    def get_role_category(cls, position):
        """
        Определяет категорию роли по должности

        Args:
            position: строка с должностью

        Returns:
            'QA', 'DEV', 'OTHER' или None
        """
        if not position:
            return None

        position_lower = position.lower()

        if any(qa_role.lower() in position_lower for qa_role in cls.QA_ROLES):
            return "QA"

        if any(dev_role.lower() in position_lower for dev_role in cls.DEV_ROLES):
            return "DEV"

        return "OTHER"

    @classmethod
    def get_available_positions_for_assignment(cls, assignment_type):
        """
        Получить список доступных должностей для типа назначения

        Args:
            assignment_type: 'QA', 'DEV', 'RACI'

        Returns:
            список должностей
        """
        if assignment_type == "QA":
            return cls.QA_ROLES
        elif assignment_type == "DEV":
            return cls.DEV_ROLES
        elif assignment_type == "RACI":
            return cls.ALL_ROLES
        else:
            return []
