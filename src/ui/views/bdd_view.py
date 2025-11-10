"""
BDD View

Вид для работы с BDD Feature файлами
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QListWidget
from PyQt6.QtCore import pyqtSignal


class BDDView(QWidget):
    """
    Вид для работы с BDD Feature файлами

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

        # Список Feature файлов
        self.list_widget = QListWidget()
        layout.addWidget(QLabel("Feature файлы:"))
        layout.addWidget(self.list_widget)

        # Предпросмотр содержимого
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(QLabel("Содержимое:"))
        layout.addWidget(self.preview)

        # Обработчики событий
        self.list_widget.currentItemChanged.connect(self._on_item_changed)

        # Загрузка данных
        self.refresh()

    def _on_item_changed(self, current, previous):
        """Обработка выбора элемента"""
        if current:
            # TODO: Загрузить содержимое Feature файла
            self.preview.setText(f"# TODO: Загрузить содержимое {current.text()}")
            self.item_selected.emit(current.text())

    def refresh(self):
        """Обновление данных"""
        # TODO: Загрузить список Feature файлов
        self.list_widget.clear()
        self.list_widget.addItems([
            "login.feature",
            "user_profile.feature",
            "product_catalog.feature"
        ])
