"""
Mini Graph Widget

Виджет с миниатюрой графа связей
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal


class MiniGraphWidget(QWidget):
    """
    Виджет с миниатюрой графа связей

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

        # Заголовок
        title = QLabel("Граф связей")
        layout.addWidget(title)

        # Область миниатюры
        # TODO: Добавить визуализацию графа
        self.graph_container = QWidget()
        layout.addWidget(self.graph_container)

    def refresh(self):
        """Обновление данных"""
        # TODO: Реализовать обновление миниатюры
