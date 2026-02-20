"""
Infrastructure Maturity View

Вид для анализа зрелости инфраструктуры
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QComboBox
from PyQt6.QtCore import pyqtSignal


class InfraMaturityView(QWidget):
    """
    Вид для анализа зрелости инфраструктуры

    Signals:
        item_selected (str): Сигнал выбора элемента
    """

    item_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Фильтр по уровням
        self.level_filter = QComboBox()
        self.level_filter.addItems([
            "Все уровни",
            "L1 - Basic",
            "L2 - Controlled",
            "L3 - Efficient",
            "L4 - Optimized"
        ])
        layout.addWidget(self.level_filter)

        # Таблица зрелости
        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # TODO: Добавить модель данных
        # TODO: Добавить графики и метрики

        # Обработчики событий
        self.level_filter.currentTextChanged.connect(self.refresh)

        # Обновление данных
        self.refresh()

    def refresh(self):
        """Обновление данных"""
        # TODO: Загрузить данные о зрелости инфраструктуры
        selected_level = self.level_filter.currentText()
