"""
Таб: BDD Features

Split-view: список элементов + предпросмотр Gherkin
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QListWidget,
    QTextEdit,
)
from PyQt6.QtCore import Qt


class BddTabWidget(QWidget):
    """Таб для управления BDD-сценариями"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Панель фильтров
        filters = QHBoxLayout()
        filters.addWidget(QLabel("🔍 Поиск:"))
        filters.addWidget(QLineEdit())
        filters.addWidget(QLabel("Type:"))
        filters.addWidget(QComboBox())
        filters.addWidget(QLabel("Segment:"))
        filters.addWidget(QComboBox())
        filters.addStretch()
        filters.addWidget(QPushButton("🛠️ Генерировать всё"))

        layout.addLayout(filters)

        # Splitter для списка и предпросмотра
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Список элементов (30%)
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.addWidget(QLabel("<b>📋 СПИСОК ЭЛЕМЕНТОВ</b>"))
        list_layout.addWidget(QListWidget())
        splitter.addWidget(list_widget)

        # Предпросмотр Gherkin (70%)
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.addWidget(QLabel("<b>📝 ПРЕДПРОСМОТР GHERKIN</b>"))

        preview_text = QTextEdit()
        preview_text.setPlainText(
            "# Feature: User Authentication\n\n"
            "## Scenario: Valid login\n"
            '  Given user at "/login"\n'
            "  When enter valid credentials\n"
            "  Then user redirected to dashboard\n\n"
            "## Scenario: Invalid login\n"
            '  Given user at "/login"\n'
            "  When enter invalid credentials\n"
            "  Then show error message\n"
        )
        preview_layout.addWidget(preview_text)

        actions = QHBoxLayout()
        actions.addWidget(QPushButton("✏️ Редактировать"))
        actions.addWidget(QPushButton("🛠️ Генерировать"))
        actions.addStretch()
        preview_layout.addLayout(actions)

        splitter.addWidget(preview_widget)

        # Пропорции 30/70
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        layout.addWidget(splitter, 1)

        # Нижняя панель действий
        bottom_actions = QHBoxLayout()
        bottom_actions.addWidget(QPushButton("💾 Экспорт в .feature файлы"))
        bottom_actions.addWidget(QPushButton("📤 Batch-генерация по фильтру"))
        bottom_actions.addStretch()

        layout.addLayout(bottom_actions)

    def refresh(self):
        """Обновление данных"""
        pass
