"""
Starter Wizard — Помощник по наполнению пустой базы

Предлагает шаблоны декомпозиции для быстрого старта.
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from src.utils.funcid_generator import generate_funcid
import logging

logger = logging.getLogger(__name__)


class StarterWizard(QDialog):
    """Мастер создания первых элементов"""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.selected_template = None

        self.setWindowTitle("🚀 Помощник по наполнению базы")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel("📋 Добро пожаловать в VoluptAS!")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Описание
        desc = QLabel(
            "Похоже, база данных пуста. Выберите шаблон для быстрого старта:\n"
            "или начните с чистого листа."
        )
        desc.setStyleSheet("font-size: 11pt; margin: 10px;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Шаблоны
        template_group = QGroupBox("📁 Шаблоны декомпозиции")
        template_layout = QVBoxLayout(template_group)

        # Шаблон 1: QA Management
        self.qa_template_btn = QRadioButton(
            "🧪 QA Management — Управление тестированием"
        )
        self.qa_template_btn.setStyleSheet("font-size: 11pt; padding: 10px;")
        self.qa_template_btn.toggled.connect(
            lambda checked: self.on_template_selected("qa")
        )
        template_layout.addWidget(self.qa_template_btn)

        qa_desc = QLabel(
            "  Module: QA Core\n"
            "  → Epic: Test Planning, Test Execution, Automation\n"
            "  → → Feature: Test Cases, Bug Tracking, Reports"
        )
        qa_desc.setStyleSheet("color: gray; font-size: 10pt; margin-left: 30px;")
        qa_desc.setWordWrap(True)
        template_layout.addWidget(qa_desc)

        # Шаблон 2: Product Development
        self.product_template_btn = QRadioButton(
            "📦 Product Development — Разработка продукта"
        )
        self.product_template_btn.setStyleSheet("font-size: 11pt; padding: 10px;")
        self.product_template_btn.toggled.connect(
            lambda checked: self.on_template_selected("product")
        )
        template_layout.addWidget(self.product_template_btn)

        product_desc = QLabel(
            "  Module: Product\n"
            "  → Epic: Features, Bugs, Technical Debt\n"
            "  → → Feature: CRUD, Validation, Integration"
        )
        product_desc.setStyleSheet("color: gray; font-size: 10pt; margin-left: 30px;")
        product_desc.setWordWrap(True)
        template_layout.addWidget(product_desc)

        # Шаблон 3: VoluptAS Documentation (фрактал)
        self.voluptas_template_btn = QRadioButton(
            "📘 VoluptAS Documentation — Фрактальная документация"
        )
        self.voluptas_template_btn.setStyleSheet("font-size: 11pt; padding: 10px;")
        self.voluptas_template_btn.setChecked(True)
        self.voluptas_template_btn.toggled.connect(
            lambda checked: self.on_template_selected("voluptas")
        )
        template_layout.addWidget(self.voluptas_template_btn)

        voluptas_desc = QLabel(
            "  Module: VOLUPTAS CORE\n"
            "  → Epic: Управление функционалом, Матрица покрытия, RACI\n"
            "  → → Feature: CRUD элементов, Декомпозиция, Граф связей\n"
            "  → → → Story: Создание Module/Epic/Feature"
        )
        voluptas_desc.setStyleSheet("color: gray; font-size: 10pt; margin-left: 30px;")
        voluptas_desc.setWordWrap(True)
        template_layout.addWidget(voluptas_desc)

        layout.addWidget(template_group)

        # Шаблон 4: Чистый лист
        self.empty_template_btn = QRadioButton("📄 Начать с чистого листа")
        self.empty_template_btn.setStyleSheet("font-size: 11pt; padding: 10px;")
        self.empty_template_btn.toggled.connect(
            lambda checked: self.on_template_selected("empty")
        )
        template_layout.addWidget(self.empty_template_btn)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_template_selected(self, template_name):
        self.selected_template = template_name

    def get_template_data(self):
        """Возвращает данные выбранного шаблона"""
        templates = {
            "qa": {
                "modules": [
                    {
                        "title": "QA Core",
                        "description": "Основной модуль управления тестированием",
                        "epics": [
                            {
                                "title": "Test Planning",
                                "description": "Планирование тестирования",
                                "features": [
                                    {"title": "Test Cases", "segment": "UI"},
                                    {"title": "Test Plans", "segment": "UI"},
                                ],
                            },
                            {
                                "title": "Test Execution",
                                "description": "Выполнение тестов",
                                "features": [
                                    {"title": "Manual Testing", "segment": "UI"},
                                    {"title": "Bug Tracking", "segment": "UI"},
                                ],
                            },
                            {
                                "title": "Automation",
                                "description": "Автоматизация тестирования",
                                "features": [
                                    {"title": "Test Scripts", "segment": "Backend"},
                                    {
                                        "title": "CI/CD Integration",
                                        "segment": "Integration",
                                    },
                                ],
                            },
                        ],
                    }
                ]
            },
            "product": {
                "modules": [
                    {
                        "title": "Product",
                        "description": "Разработка продукта",
                        "epics": [
                            {
                                "title": "Features",
                                "description": "Новый функционал",
                                "features": [
                                    {"title": "CRUD Operations", "segment": "Backend"},
                                    {"title": "Validation", "segment": "Backend"},
                                ],
                            },
                            {
                                "title": "Bugs",
                                "description": "Исправление ошибок",
                                "features": [
                                    {"title": "Bug Tracking", "segment": "UI"},
                                    {"title": "Hot Fixes", "segment": "Backend"},
                                ],
                            },
                        ],
                    }
                ]
            },
            "voluptas": {
                "modules": [
                    {
                        "title": "VOLUPTAS CORE",
                        "description": "Ядро системы VoluptAS — управление функционалом и покрытием QA",
                        "epics": [
                            {
                                "title": "Управление функционалом",
                                "description": "Эпик — крупная функциональная область. Пример: CRUD, Декомпозиция, Матрица",
                                "features": [
                                    {"title": "CRUD элементов", "segment": "UI"},
                                    {"title": "Декомпозиция", "segment": "UX/CX"},
                                ],
                            },
                            {
                                "title": "Матрица покрытия",
                                "description": "Отслеживание покрытия тест-кейсами, автотестами и документацией",
                                "features": [
                                    {"title": "Тест-кейсы", "segment": "UI"},
                                    {"title": "Автотесты", "segment": "Backend"},
                                    {"title": "Документация", "segment": "UI"},
                                ],
                            },
                            {
                                "title": "RACI матрица",
                                "description": "Управление ответственностью (Responsible, Accountable, Consulted, Informed)",
                                "features": [
                                    {
                                        "title": "Назначение ответственных",
                                        "segment": "UI",
                                    },
                                ],
                            },
                            {
                                "title": "Граф связей",
                                "description": "Интерактивная визуализация иерархии",
                                "features": [
                                    {"title": "Визуализация", "segment": "UI"},
                                    {"title": "Фильтрация", "segment": "UI"},
                                ],
                            },
                        ],
                    }
                ]
            },
            "empty": None,
        }

        return templates.get(self.selected_template)

    def apply_template(self):
        """Применение шаблона — создание элементов"""
        template_data = self.get_template_data()

        if not template_data:
            return 0

        created_count = 0

        for module_data in template_data["modules"]:
            # Создаём Module
            from src.models import FunctionalItem

            module = FunctionalItem(
                functional_id=generate_funcid("Module", module_data["title"]),
                title=module_data["title"],
                type="Module",
                description=module_data.get("description"),
                is_crit=0,
                is_focus=1,
            )
            self.session.add(module)
            self.session.flush()  # Получаем ID
            created_count += 1

            for epic_data in module_data.get("epics", []):
                # Создаём Epic
                epic = FunctionalItem(
                    functional_id=generate_funcid(
                        "Epic", epic_data["title"], module=module.title
                    ),
                    title=epic_data["title"],
                    type="Epic",
                    module=module.title,
                    description=epic_data.get("description"),
                    is_crit=0,
                    is_focus=0,
                )
                self.session.add(epic)
                self.session.flush()
                created_count += 1

                for feature_data in epic_data.get("features", []):
                    # Создаём Feature
                    feature = FunctionalItem(
                        functional_id=generate_funcid(
                            "Feature",
                            feature_data["title"],
                            module=module.title,
                            epic=epic.title,
                        ),
                        title=feature_data["title"],
                        type="Feature",
                        module=module.title,
                        epic=epic.title,
                        segment=feature_data.get("segment"),
                        is_crit=1,
                        is_focus=0,
                    )
                    self.session.add(feature)
                    created_count += 1

        self.session.commit()
        return created_count
