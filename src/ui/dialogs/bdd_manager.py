"""
BDD Feature Manager

Диалог для управления BDD Feature файлами
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton,
    QLabel, QListWidget, QMessageBox,
    QTextEdit
)
from src.config import Config
from src.bdd.feature_generator import FeatureGenerator


class BDDManagerDialog(QDialog):
    """Диалог управления BDD Feature файлами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BDD Feature Manager")
        self.setMinimumSize(600, 400)
        self.config = Config()
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Список функциональных элементов
        self.list_widget = QListWidget()
        layout.addWidget(QLabel("Функциональные элементы:"))
        layout.addWidget(self.list_widget)

        # Предпросмотр Feature файла
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(QLabel("Предпросмотр Feature файла:"))
        layout.addWidget(self.preview)

        # Кнопки
        btn_generate = QPushButton("Сгенерировать Feature файлы")
        btn_generate.clicked.connect(self.generate_features)
        layout.addWidget(btn_generate)

        # Загрузка данных
        self.refresh_items()

    def refresh_items(self):
        """Обновление списка элементов"""
        # TODO: Загрузить элементы из БД
        self.list_widget.clear()
        self.list_widget.addItems([
            "Login Feature",
            "User Profile",
            "Product Catalog"
        ])

    def generate_features(self):
        """Генерация Feature файлов"""
        # TODO: Реализовать генерацию
        QMessageBox.information(
            self,
            "Генерация Feature файлов",
            "Генерация Feature файлов будет реализована в следующей версии"
        )
