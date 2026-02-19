"""
Dictionary Manager - Управление справочниками

Редактирование справочников системы: типы элементов, сегменты, статусы и т.д.
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from src.db import SessionLocal
from src.models import Dictionary


class DictionaryEditDialog(QDialog):
    """Диалог создания/редактирования элемента справочника"""

    DICT_TYPES = {
        "type": "Тип элемента",
        "segment": "Сегмент",
        "automation_status": "Статус автоматизации",
        "maturity": "Уровень зрелости",
        "position": "Должность",
    }

    def __init__(self, dict_item=None, dict_type=None, parent=None):
        super().__init__(parent)
        self.dict_item = dict_item if dict_item else Dictionary()
        self.is_new = dict_item is None

        if self.is_new and dict_type:
            self.dict_item.dict_type = dict_type

        title = "Новый элемент" if self.is_new else f"Редактирование: {dict_item.value}"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        # Тип справочника
        self.type_combo = QComboBox()
        for key, label in self.DICT_TYPES.items():
            self.type_combo.addItem(label, key)

        if self.dict_item.dict_type:
            index = self.type_combo.findData(self.dict_item.dict_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

        self.type_combo.setEnabled(self.is_new)  # Тип нельзя менять после создания

        # Значение
        self.value_edit = QLineEdit(self.dict_item.value or "")

        # Порядок отображения
        self.order_spin = QSpinBox()
        self.order_spin.setRange(0, 999)
        self.order_spin.setValue(self.dict_item.display_order or 0)

        # Активность
        self.active_check = QCheckBox()
        self.active_check.setChecked(
            bool(
                self.dict_item.is_active
                if hasattr(self.dict_item, "is_active")
                else True
            )
        )

        # Описание
        self.desc_edit = QTextEdit(self.dict_item.description or "")
        self.desc_edit.setMaximumHeight(80)

        layout.addRow("* Тип справочника:", self.type_combo)
        layout.addRow("* Значение:", self.value_edit)
        layout.addRow("Порядок:", self.order_spin)
        layout.addRow("Активен:", self.active_check)
        layout.addRow("Описание:", self.desc_edit)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def save(self):
        value = self.value_edit.text().strip()
        if not value:
            QMessageBox.warning(self, "Ошибка", "Значение обязательно для заполнения")
            return

        self.dict_item.dict_type = self.type_combo.currentData()
        self.dict_item.value = value
        self.dict_item.display_order = self.order_spin.value()
        self.dict_item.is_active = self.active_check.isChecked()
        self.dict_item.description = self.desc_edit.toPlainText().strip() or None

        self.accept()


class DictionaryManagerWindow(QMainWindow):
    """Главное окно управления справочниками"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = SessionLocal()
        self.current_items = []
        self.current_dict_type = "type"  # По умолчанию показываем типы
        self.init_ui()
        self.load_dictionaries()

    def init_ui(self):
        self.setWindowTitle("Управление справочниками")
        self.setGeometry(200, 200, 1000, 600)

        # Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        close_action = QAction("Закрыть", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # Тулбар
        toolbar = QToolBar("Главная")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.load_dictionaries)
        toolbar.addAction(refresh_action)

        add_action = QAction("➕ Добавить", self)
        add_action.triggered.connect(self.add_item)
        toolbar.addAction(add_action)

        edit_action = QAction("✏️ Редактировать", self)
        edit_action.triggered.connect(self.edit_item)
        toolbar.addAction(edit_action)

        delete_action = QAction("🗑️ Удалить", self)
        delete_action.triggered.connect(self.delete_item)
        toolbar.addAction(delete_action)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Выбор типа справочника
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("📚 Справочник:"))

        self.type_combo = QComboBox()
        self.type_combo.addItem("Типы элементов", "type")
        self.type_combo.addItem("Сегменты", "segment")
        self.type_combo.addItem("Статусы автоматизации", "automation_status")
        self.type_combo.addItem("Уровни зрелости", "maturity")
        self.type_combo.addItem("Должности", "position")
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()

        layout.addLayout(type_layout)

        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Значение, описание...")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Тип", "Значение", "Порядок", "Активен", "Описание"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_item)
        self.table.hideColumn(0)  # Скрыть ID
        self.table.hideColumn(1)  # Скрыть Тип (мы фильтруем по нему)
        layout.addWidget(self.table)

        # Статус-бар
        self.statusBar().showMessage("Готов")

    def on_type_changed(self):
        """Обработчик изменения типа справочника"""
        self.current_dict_type = self.type_combo.currentData()
        self.load_dictionaries()

    def load_dictionaries(self):
        """Загрузить элементы справочника из БД"""
        self.current_items = (
            self.session.query(Dictionary)
            .filter(Dictionary.dict_type == self.current_dict_type)
            .order_by(Dictionary.display_order, Dictionary.value)
            .all()
        )

        self.populate_table(self.current_items)
        self.statusBar().showMessage(
            f"✅ Загружено: {len(self.current_items)} элементов"
        )

    def populate_table(self, items):
        """Заполнить таблицу данными"""
        self.table.setRowCount(len(items))
        for row_idx, item in enumerate(items):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(item.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item.dict_type or ""))
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.value or ""))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(item.display_order)))
            self.table.setItem(
                row_idx, 4, QTableWidgetItem("✓" if item.is_active else "✗")
            )
            self.table.setItem(row_idx, 5, QTableWidgetItem(item.description or ""))

    def filter_table(self):
        """Фильтровать таблицу по поисковому запросу"""
        query = self.search_input.text().lower()
        if not query:
            self.populate_table(self.current_items)
            return

        filtered = [
            item
            for item in self.current_items
            if query in (item.value or "").lower()
            or query in (item.description or "").lower()
        ]
        self.populate_table(filtered)
        self.statusBar().showMessage(
            f"🔍 Найдено: {len(filtered)} из {len(self.current_items)}"
        )

    def add_item(self):
        """Добавить новый элемент"""
        dialog = DictionaryEditDialog(dict_type=self.current_dict_type, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.session.add(dialog.dict_item)
                self.session.commit()
                self.load_dictionaries()
                self.statusBar().showMessage(f"✅ Добавлено: {dialog.dict_item.value}")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(
                    self, "Ошибка", f"Не удалось добавить элемент:\n{e}"
                )

    def edit_item(self):
        """Редактировать выбранный элемент"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self, "Предупреждение", "Выберите элемент для редактирования"
            )
            return

        row = selected_rows[0].row()
        item_id = int(self.table.item(row, 0).text())
        item = self.session.query(Dictionary).get(item_id)

        if not item:
            QMessageBox.warning(self, "Ошибка", "Элемент не найден")
            return

        dialog = DictionaryEditDialog(item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.session.commit()
                self.load_dictionaries()
                self.statusBar().showMessage(f"✅ Обновлено: {item.value}")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def delete_item(self):
        """Удалить выбранный элемент"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите элемент для удаления")
            return

        row = selected_rows[0].row()
        item_id = int(self.table.item(row, 0).text())
        item = self.session.query(Dictionary).get(item_id)

        if not item:
            QMessageBox.warning(self, "Ошибка", "Элемент не найден")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f'Вы уверены, что хотите удалить "{item.value}"?\n\n'
            f"⚠️ Это может повлиять на существующие данные!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(item)
                self.session.commit()
                self.load_dictionaries()
                self.statusBar().showMessage(f"✅ Удалено: {item.value}")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить:\n{e}")

    def closeEvent(self, event):
        """При закрытии окна"""
        self.session.close()
        event.accept()
