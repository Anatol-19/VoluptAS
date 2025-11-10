"""
Relations Editor Dialog

Диалог управления связями между сущностями
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox
)


class RelationsEditorDialog(QDialog):
    """Диалог управления связями"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление связями")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Кнопки
        buttons = QHBoxLayout()

        add_btn = QPushButton("Добавить связь")
        add_btn.clicked.connect(self.add_relation)
        buttons.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_relation)
        buttons.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_relation)
        buttons.addWidget(delete_btn)

        buttons.addStretch()

        layout.addLayout(buttons)

        # Таблица связей
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Источник", "Тип связи", "Цель", "Описание"
        ])
        layout.addWidget(self.table)

    def add_relation(self):
        """Добавление новой связи"""
        QMessageBox.information(self, "Info", "Функция в разработке")

    def edit_relation(self):
        """Редактирование выбранной связи"""
        QMessageBox.information(self, "Info", "Функция в разработке")

    def delete_relation(self):
        """Удаление выбранной связи"""
        QMessageBox.information(self, "Info", "Функция в разработке")
