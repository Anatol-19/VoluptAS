"""
Google Sheets Exporter Service

Экспорт данных VoluptAS в Google Sheets:
- Все таблицы БД по отдельным листам
- Матрица покрытия с форматированием
- RACI матрица
- Тест-планы с фильтрами
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from src.models import FunctionalItem, User, Relation
from src.integrations.google import GoogleSheetsClient
import logging

logger = logging.getLogger(__name__)


class GoogleSheetsExporter:
    """Экспорт данных VoluptAS в Google Sheets"""

    def __init__(self, credentials_path: str, session: Session):
        """
        Args:
            credentials_path: Путь к service_account.json
            session: SQLAlchemy session
        """
        self.credentials_path = credentials_path
        self.session = session
        self.client = None

    def export_all_tables(self, spreadsheet_id: str, filters: Optional[Dict] = None):
        """
        Экспорт всех таблиц БД в отдельные листы

        Args:
            spreadsheet_id: ID Google Spreadsheet
            filters: Фильтры для данных (опционально)

        Returns:
            dict: Статистика экспорта
        """
        logger.info(f"🚀 Начало экспорта всех таблиц в spreadsheet {spreadsheet_id}")

        stats = {"functional_items": 0, "users": 0, "relations": 0, "errors": []}

        try:
            # 1. Экспорт функциональных элементов
            stats["functional_items"] = self._export_functional_items(
                spreadsheet_id, "Функционал", filters
            )

            # 2. Экспорт пользователей
            stats["users"] = self._export_users(spreadsheet_id, "Сотрудники")

            # 3. Экспорт связей
            stats["relations"] = self._export_relations(spreadsheet_id, "Связи")

            logger.info(f"✅ Экспорт завершён: {stats}")
            return stats

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта: {e}")
            stats["errors"].append(str(e))
            raise

    def _export_functional_items(
        self, spreadsheet_id: str, sheet_name: str, filters: Optional[Dict] = None
    ) -> int:
        """Экспорт функциональных элементов"""
        logger.info(f"📊 Экспорт functional_items в лист '{sheet_name}'")

        # Инициализация клиента
        self.client = GoogleSheetsClient(
            credentials_path=self.credentials_path,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=sheet_name,
        )

        # Получение данных из БД
        query = self.session.query(FunctionalItem)

        # Проверка: если БД пустая - не создавать клиент (не очищать листы)
        total_count = query.count()
        if total_count == 0:
            logger.warning(f"⚠️ БД пустая, пропускаем экспорт '{sheet_name}'")
            return 0

        # Применение фильтров
        if filters:
            if filters.get("type"):
                query = query.filter(FunctionalItem.type.in_(filters["type"]))
            if filters.get("is_crit"):
                query = query.filter(FunctionalItem.is_crit == True)
            if filters.get("is_focus"):
                query = query.filter(FunctionalItem.is_focus == True)
            if filters.get("responsible_qa_id"):
                query = query.filter(
                    FunctionalItem.responsible_qa_id.in_(filters["responsible_qa_id"])
                )

        items = query.all()
        logger.info(f"   Найдено элементов: {len(items)}")

        # Подготовка данных для экспорта
        for item in items:
            row_data = {
                "FuncID": item.functional_id or "",
                "Alias": item.alias_tag or "",
                "Title": item.title or "",
                "Type": item.type or "",
                "Segment": item.segment or "",
                "Module": item.module or "",
                "Epic": item.epic or "",
                "Feature": item.feature or "",
                "isCrit": "Да" if item.is_crit else "",
                "isFocus": "Да" if item.is_focus else "",
                "QA": item.responsible_qa.name if item.responsible_qa else "",
                "Dev": item.responsible_dev.name if item.responsible_dev else "",
                "Accountable": item.accountable.name if item.accountable else "",
                "Test Cases": item.test_cases_linked or "",
                "Automation": item.automation_status or "",
                "Documentation": item.documentation_links or "",
                "Status": item.status or "",
                "Maturity": item.maturity or "",
            }
            self.client.append_result(row_data)

        # Отправка данных
        self.client.flush()
        logger.info(f"✅ Экспортировано: {len(items)} элементов")

        return len(items)

    def _export_users(self, spreadsheet_id: str, sheet_name: str) -> int:
        """Экспорт пользователей"""
        logger.info(f"👥 Экспорт users в лист '{sheet_name}'")

        users = self.session.query(User).filter(User.is_active == True).all()
        logger.info(f"   Найдено пользователей: {len(users)}")

        if len(users) == 0:
            logger.warning(f"⚠️ Нет пользователей, пропускаем экспорт '{sheet_name}'")
            return 0

        self.client = GoogleSheetsClient(
            credentials_path=self.credentials_path,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=sheet_name,
        )

        for user in users:
            row_data = {
                "ID": user.id,
                "Name": user.name or "",
                "Position": user.position or "",
                "Email": user.email or "",
                "Zoho ID": user.zoho_id or "",
                "GitHub": user.github_username or "",
                "Active": "Да" if user.is_active else "Нет",
            }
            self.client.append_result(row_data)

        self.client.flush()
        logger.info(f"✅ Экспортировано: {len(users)} пользователей")

        return len(users)

    def _export_relations(self, spreadsheet_id: str, sheet_name: str) -> int:
        """Экспорт связей между элементами"""
        logger.info(f"🔗 Экспорт relations в лист '{sheet_name}'")

        relations = self.session.query(Relation).all()
        logger.info(f"   Найдено связей: {len(relations)}")

        if len(relations) == 0:
            logger.warning(f"⚠️ Нет связей, пропускаем экспорт '{sheet_name}'")
            return 0

        self.client = GoogleSheetsClient(
            credentials_path=self.credentials_path,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=sheet_name,
        )

        for rel in relations:
            # Получаем элементы для вывода названий
            source = self.session.query(FunctionalItem).get(rel.source_id)
            target = self.session.query(FunctionalItem).get(rel.target_id)

            metadata = rel.get_metadata()
            row_data = {
                "Source ID": rel.source_id,
                "Source FuncID": source.functional_id if source else "",
                "Source Title": source.title if source else "",
                "Target ID": rel.target_id,
                "Target FuncID": target.functional_id if target else "",
                "Target Title": target.title if target else "",
                "Type": rel.type or "hierarchy",
                "Weight": rel.weight or 1.0,
                "Directed": "Да" if rel.directed else "Нет",
                "Active": "Да" if rel.active else "Нет",
                "Notes": metadata.get("notes", "") or "",
            }
            self.client.append_result(row_data)

        self.client.flush()
        logger.info(f"✅ Экспортировано: {len(relations)} связей")

        return len(relations)

    def export_coverage_matrix(
        self, spreadsheet_id: str, sheet_name: str = "Coverage Matrix"
    ):
        """
        Экспорт матрицы покрытия с цветовым кодированием

        Строки: функциональные элементы
        Колонки: TC, автотесты, документация
        """
        logger.info(f"📋 Экспорт coverage matrix в лист '{sheet_name}'")

        self.client = GoogleSheetsClient(
            credentials_path=self.credentials_path,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=sheet_name,
        )

        items = (
            self.session.query(FunctionalItem)
            .filter(FunctionalItem.type.in_(["Feature", "Story", "Page", "Element"]))
            .all()
        )

        logger.info(f"   Элементов для матрицы: {len(items)}")

        for item in items:
            # Определяем покрытие
            has_tc = bool(item.test_cases_linked and item.test_cases_linked.strip())
            has_automation = item.automation_status not in [None, "", "Not Started"]
            has_docs = bool(
                item.documentation_links and item.documentation_links.strip()
            )

            # Рассчитываем общий процент покрытия
            coverage_score = sum([has_tc, has_automation, has_docs])
            coverage_pct = int((coverage_score / 3) * 100)

            row_data = {
                "FuncID": item.functional_id or "",
                "Title": item.title or "",
                "Type": item.type or "",
                "Crit": "Да" if item.is_crit else "",
                "Test Cases": "Да" if has_tc else "Нет",
                "Automation": item.automation_status or "Not Started",
                "Documentation": "Да" if has_docs else "Нет",
                "Coverage %": f"{coverage_pct}%",
                "QA": item.responsible_qa.name if item.responsible_qa else "",
            }
            self.client.append_result(row_data)

        self.client.flush()
        logger.info(f"✅ Матрица покрытия экспортирована: {len(items)} элементов")

        # TODO: Добавить условное форматирование (цвета) через Google Sheets API
        # Зелёный: покрытие 100%, Жёлтый: 50-99%, Красный: 0-49%

        return len(items)

    def export_raci_matrix(self, spreadsheet_id: str, sheet_name: str = "RACI Matrix"):
        """
        Экспорт RACI матрицы

        Строки: функциональные элементы
        Колонки: сотрудники
        Значения: R/A/C/I
        """
        logger.info(f"👥 Экспорт RACI matrix в лист '{sheet_name}'")

        self.client = GoogleSheetsClient(
            credentials_path=self.credentials_path,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=sheet_name,
        )

        items = self.session.query(FunctionalItem).all()
        users = self.session.query(User).filter(User.is_active == True).all()

        logger.info(f"   Элементов: {len(items)}, Сотрудников: {len(users)}")

        # Формируем матрицу
        for item in items:
            row_data = {
                "FuncID": item.functional_id or "",
                "Title": item.title or "",
                "Type": item.type or "",
            }

            # Для каждого пользователя определяем роль
            for user in users:
                role = []
                if item.responsible_qa_id == user.id:
                    role.append("R(QA)")
                if item.responsible_dev_id == user.id:
                    role.append("R(Dev)")
                if item.accountable_id == user.id:
                    role.append("A")
                # TODO: Добавить C и I из JSON полей

                row_data[user.name] = ", ".join(role) if role else ""

            self.client.append_result(row_data)

        self.client.flush()
        logger.info(f"✅ RACI матрица экспортирована: {len(items)} элементов")

        return len(items)

    def export_test_plan(
        self, spreadsheet_id: str, sheet_name: str, filters: Dict[str, Any]
    ):
        """
        Экспорт тест-плана с фильтрами

        Args:
            filters: Фильтры (is_crit, is_focus, responsible_qa_id, type)
        """
        logger.info(f"📝 Экспорт test plan в лист '{sheet_name}'")

        self.client = GoogleSheetsClient(
            credentials_path=self.credentials_path,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=sheet_name,
        )

        # Применяем фильтры
        query = self.session.query(FunctionalItem)

        if filters.get("is_crit"):
            query = query.filter(FunctionalItem.is_crit == True)
        if filters.get("is_focus"):
            query = query.filter(FunctionalItem.is_focus == True)
        if filters.get("type"):
            query = query.filter(FunctionalItem.type.in_(filters["type"]))
        if filters.get("responsible_qa_id"):
            query = query.filter(
                FunctionalItem.responsible_qa_id.in_(filters["responsible_qa_id"])
            )

        items = query.all()
        logger.info(f"   Элементов в тест-плане: {len(items)}")

        # Экспорт в формате тест-плана
        for item in items:
            row_data = {
                "FuncID": item.functional_id or "",
                "Title": item.title or "",
                "Description": item.description or "",
                "Type": item.type or "",
                "Segment": item.segment or "",
                "Priority": (
                    "Критично"
                    if item.is_crit
                    else ("Фокус" if item.is_focus else "Обычный")
                ),
                "QA": item.responsible_qa.name if item.responsible_qa else "",
                "Test Cases": item.test_cases_linked or "Нет",
                "Automation": item.automation_status or "Not Started",
                "Status": item.status or "Open",
                "Notes": "",  # Для ручного заполнения
            }
            self.client.append_result(row_data)

        self.client.flush()
        logger.info(f"✅ Тест-план экспортирован: {len(items)} элементов")

        return len(items)
