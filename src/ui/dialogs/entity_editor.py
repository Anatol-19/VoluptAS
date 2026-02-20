"""
Entity Editor Dialog

Диалог управления функциональными элементами
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QMenu,
    QLineEdit,
    QComboBox,
)
from PyQt6.QtCore import Qt
from src.db import SessionLocal
from src.models.functional_item import FunctionalItem


class EntityEditorDialog(QDialog):
    """Диалог редактирования сущностей"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление сущностями")
        self.setMinimumSize(800, 600)
        self.session = SessionLocal()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Дерево сущностей
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Название", "Тип", "Статус"])
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.tree)

        # Кнопки
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self.add_item)
        btn_layout.addWidget(btn_add)

        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self.edit_item)
        btn_layout.addWidget(btn_edit)

        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self.delete_item)
        btn_layout.addWidget(btn_delete)

        layout.addLayout(btn_layout)

    def load_data(self):
        """Загрузка данных из БД"""
        self.tree.clear()
        items = self.session.query(FunctionalItem).all()

        # Создаем словарь для быстрого поиска родителей
        items_dict = {
            item.id: QTreeWidgetItem([str(item.id), item.name, item.type, item.status])
            for item in items
        }

        # Строим дерево
        for item in items:
            tree_item = items_dict[item.id]
            if item.parent_id and item.parent_id in items_dict:
                items_dict[item.parent_id].addChild(tree_item)
            else:
                self.tree.addTopLevelItem(tree_item)

    def filter_items(self):
        """Фильтрация элементов по поиску"""
        search_text = self.search_input.text().lower()

        def filter_item(item):
            show = any(
                search_text in item.text(col).lower()
                for col in range(item.columnCount())
            )

            # Проверяем дочерние элементы
            for i in range(item.childCount()):
                if filter_item(item.child(i)):
                    show = True

            item.setHidden(not show)
            return show

        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))

    def show_context_menu(self, position):
        """Показать контекстное меню"""
        menu = QMenu()

        add_action = menu.addAction("Добавить")
        add_action.triggered.connect(self.add_item)

        if self.tree.currentItem():
            edit_action = menu.addAction("Редактировать")
            edit_action.triggered.connect(self.edit_item)

            delete_action = menu.addAction("Удалить")
            delete_action.triggered.connect(self.delete_item)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def add_item(self):
        """Добавление элемента"""
        dialog = EntityDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                item = FunctionalItem(
                    name=dialog.name_input.text(),
                    type=dialog.type_combo.currentText(),
                    status=dialog.status_combo.currentText(),
                )

                current = self.tree.currentItem()
                if current:
                    item.parent_id = int(current.text(0))

                self.session.add(item)
                self.session.commit()
                self.load_data()

            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка", f"Не удалось добавить элемент: {str(e)}"
                )

    def edit_item(self):
        """Редактирование элемента"""
        current = self.tree.currentItem()
        if not current:
            return

        dialog = EntityDialog(parent=self)
        dialog.name_input.setText(current.text(1))
        dialog.type_combo.setCurrentText(current.text(2))
        dialog.status_combo.setCurrentText(current.text(3))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                item_id = int(current.text(0))
                item = self.session.query(FunctionalItem).get(item_id)
                if item:
                    item.name = dialog.name_input.text()
                    item.type = dialog.type_combo.currentText()
                    item.status = dialog.status_combo.currentText()
                    self.session.commit()
                    self.load_data()

            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка", f"Не удалось обновить элемент: {str(e)}"
                )

    def delete_item(self):
        """Удаление элемента"""
        current = self.tree.currentItem()
        if not current:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этот элемент?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                item_id = int(current.text(0))
                item = self.session.query(FunctionalItem).get(item_id)
                if item:
                    self.session.delete(item)
                    self.session.commit()
                    self.load_data()

            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка", f"Не удалось удалить элемент: {str(e)}"
                )

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.session.close()
        event.accept()


class EntityDialog(QDialog):
    """Диалог добавления/редактирования элемента"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Элемент")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Название
        layout.addWidget(QLabel("Название:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # Тип
        layout.addWidget(QLabel("Тип:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(
            ["Module", "Epic", "Feature", "Story", "Page", "Element", "Service"]
        )
        layout.addWidget(self.type_combo)

        # Статус
        layout.addWidget(QLabel("Статус:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["New", "In Progress", "Done", "Blocked"])
        layout.addWidget(self.status_combo)

        # Кнопки
        btn_layout = QHBoxLayout()

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)

        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)
