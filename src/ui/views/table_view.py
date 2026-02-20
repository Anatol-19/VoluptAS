"""
Table View

Основной табличный вид для отображения функциональных элементов
"""

from PyQt6.QtWidgets import QTableView, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from src.db import SessionLocal
from src.models.functional_item import FunctionalItem


class TableView(QTableView):
    """
    Табличное представление функциональных элементов

    Signals:
        item_selected (str): Сигнал выбора элемента (func_id)
    """

    item_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = SessionLocal()
        self.model = QStandardItemModel()
        self.init_ui()
        self.refresh()

    def init_ui(self):
        """Инициализация интерфейса"""
        # Настройка заголовков
        self.setModel(self.model)
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.horizontalHeader().setStretchLastSection(True)

        # Настройка выделения
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        # Отключаем редактирование в таблице
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        # Подключаем сигнал выбора
        self.clicked.connect(self._on_item_clicked)

    def refresh(self):
        """Обновление данных"""
        self.model.clear()

        # Заголовки
        headers = [
            "ID",
            "Func ID",
            "Название",
            "Тип",
            "Статус",
            "QA",
            "Dev",
            "Module",
            "Epic",
            "Feature",
        ]
        self.model.setHorizontalHeaderLabels(headers)

        # Загрузка данных
        items = self.session.query(FunctionalItem).all()

        for item in items:
            row = [
                QStandardItem(str(item.id)),
                QStandardItem(item.func_id or ""),
                QStandardItem(item.title),
                QStandardItem(item.type),
                QStandardItem(item.status),
                QStandardItem(item.responsible_qa.name if item.responsible_qa else ""),
                QStandardItem(
                    item.responsible_dev.name if item.responsible_dev else ""
                ),
                QStandardItem(item.module or ""),
                QStandardItem(item.epic or ""),
                QStandardItem(item.feature or ""),
            ]
            self.model.appendRow(row)

    def _on_item_clicked(self, index):
        """Обработка клика по элементу"""
        # Получаем id из первой колонки
        item_id = self.model.data(self.model.index(index.row(), 0))
        self.item_selected.emit(item_id)

    def closeEvent(self, event):
        """Обработка закрытия"""
        self.session.close()
        event.accept()
