"""
Coverage Matrix View

Матрица трассировки для анализа покрытия
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView
from PyQt6.QtCore import pyqtSignal


class CoverageMatrixView(QWidget):
    """
    Матрица трассировки для анализа покрытия

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

        # Таблица покрытия
        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        layout.addWidget(self.table)

        # TODO: Добавить модель данных
        # TODO: Добавить фильтры и группировку

        # Обновление данных
        self.refresh()

    def refresh(self):
        """Обновление данных"""
        # TODO: Загрузить данные о покрытии
