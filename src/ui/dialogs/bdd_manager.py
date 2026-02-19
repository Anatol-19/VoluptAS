"""
BDD Feature Manager - каталог для управления всеми feature файлами
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from pathlib import Path

from src.db import SessionLocal
from src.models import FunctionalItem
from src.bdd.feature_generator import FeatureGenerator


class BDDFeatureManager(QMainWindow):
    """Менеджер BDD Feature файлов"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = SessionLocal()
        self.current_items = []
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setWindowTitle("BDD Feature Manager")
        self.setGeometry(150, 150, 1200, 700)

        # Меню
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Файл")

        export_all_action = QAction("💾 Экспорт всех", self)
        export_all_action.triggered.connect(self.export_all)
        file_menu.addAction(export_all_action)

        file_menu.addSeparator()

        close_action = QAction("Закрыть", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # Toolbar
        toolbar = QToolBar("Действия")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.load_data)
        toolbar.addAction(refresh_action)

        generate_action = QAction("🛠️ Генерация", self)
        generate_action.triggered.connect(self.generate_selected)
        toolbar.addAction(generate_action)

        export_selected_action = QAction("💾 Экспорт выбранных", self)
        export_selected_action.triggered.connect(self.export_selected)
        toolbar.addAction(export_selected_action)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Фильтры
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Functional ID, Title...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)

        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.type_filter)

        filter_layout.addWidget(QLabel("Segment:"))
        self.segment_filter = QComboBox()
        self.segment_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.segment_filter)

        # Чекбоксы
        self.crit_check = QCheckBox("Только Critical")
        self.crit_check.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.crit_check)

        self.focus_check = QCheckBox("Только Focus")
        self.focus_check.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.focus_check)

        filter_layout.addStretch()

        main_layout.addLayout(filter_layout)

        # Splitter: таблица + предпросмотр
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Functional ID", "Title", "Type", "Segment", "Crit", "Focus"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        splitter.addWidget(self.table)

        # Предпросмотр
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)

        preview_layout.addWidget(QLabel("Предпросмотр Feature:"))

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 9pt;"
        )
        preview_layout.addWidget(self.preview_text)

        # Кнопки для предпросмотра
        preview_buttons = QHBoxLayout()

        generate_preview_btn = QPushButton("🛠️ Генерировать")
        generate_preview_btn.clicked.connect(self.generate_preview)
        preview_buttons.addWidget(generate_preview_btn)

        export_preview_btn = QPushButton("💾 Экспорт")
        export_preview_btn.clicked.connect(self.export_preview)
        preview_buttons.addWidget(export_preview_btn)

        preview_buttons.addStretch()
        preview_layout.addLayout(preview_buttons)

        splitter.addWidget(preview_widget)
        splitter.setSizes([600, 600])

        main_layout.addWidget(splitter)

        self.statusBar().showMessage("Готов")

    def load_data(self):
        """Загрузить все элементы"""
        self.current_items = (
            self.session.query(FunctionalItem)
            .order_by(FunctionalItem.functional_id)
            .all()
        )

        # Обновляем фильтры
        types = sorted(set(item.type for item in self.current_items if item.type))
        segments = sorted(
            set(item.segment for item in self.current_items if item.segment)
        )

        self.type_filter.clear()
        self.type_filter.addItems([""] + types)

        self.segment_filter.clear()
        self.segment_filter.addItems([""] + segments)

        self.populate_table(self.current_items)
        self.statusBar().showMessage(
            f"✅ Загружено: {len(self.current_items)} элементов"
        )

    def populate_table(self, items):
        """Заполнить таблицу"""
        self.table.setRowCount(len(items))

        for row_idx, item in enumerate(items):
            self.table.setItem(row_idx, 0, QTableWidgetItem(item.functional_id))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item.title or ""))
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.type or ""))
            self.table.setItem(row_idx, 3, QTableWidgetItem(item.segment or ""))
            self.table.setItem(
                row_idx, 4, QTableWidgetItem("✓" if item.is_crit else "")
            )
            self.table.setItem(
                row_idx, 5, QTableWidgetItem("✓" if item.is_focus else "")
            )

        self.table.resizeColumnsToContents()

    def apply_filters(self):
        """Применить фильтры"""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        segment_filter = self.segment_filter.currentText()
        only_crit = self.crit_check.isChecked()
        only_focus = self.focus_check.isChecked()

        for row in range(self.table.rowCount()):
            show = True

            # Текстовый поиск
            if search_text:
                match = any(
                    self.table.item(row, col)
                    and search_text in self.table.item(row, col).text().lower()
                    for col in range(self.table.columnCount())
                )
                show = show and match

            # Type фильтр
            if type_filter and show:
                type_cell = self.table.item(row, 2)
                show = show and (type_cell and type_cell.text() == type_filter)

            # Segment фильтр
            if segment_filter and show:
                segment_cell = self.table.item(row, 3)
                show = show and (segment_cell and segment_cell.text() == segment_filter)

            # Crit фильтр
            if only_crit and show:
                crit_cell = self.table.item(row, 4)
                show = show and (crit_cell and crit_cell.text() == "✓")

            # Focus фильтр
            if only_focus and show:
                focus_cell = self.table.item(row, 5)
                show = show and (focus_cell and focus_cell.text() == "✓")

            self.table.setRowHidden(row, not show)

    def on_selection_changed(self):
        """Обработка выбора строки"""
        selected = self.table.currentRow()
        if selected >= 0:
            functional_id = self.table.item(selected, 0).text()
            item = (
                self.session.query(FunctionalItem)
                .filter_by(functional_id=functional_id)
                .first()
            )
            if item:
                self.generate_preview()
        else:
            self.preview_text.clear()

    def generate_preview(self):
        """Генерация предпросмотра для выбранного элемента"""
        selected = self.table.currentRow()
        if selected < 0:
            return

        functional_id = self.table.item(selected, 0).text()
        item = (
            self.session.query(FunctionalItem)
            .filter_by(functional_id=functional_id)
            .first()
        )

        if item:
            feature_content = FeatureGenerator.generate_feature(item)
            self.preview_text.setPlainText(feature_content)

    def export_preview(self):
        """Экспорт feature из предпросмотра"""
        content = self.preview_text.toPlainText().strip()

        if not content:
            QMessageBox.warning(
                self, "Предупреждение", "Предпросмотр пуст.\nСгенерируйте feature."
            )
            return

        selected = self.table.currentRow()
        if selected < 0:
            return

        functional_id = self.table.item(selected, 0).text()
        filename = f"{functional_id.replace('.', '_')}.feature"

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить feature файл", filename, "Feature Files (*.feature)"
        )

        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                QMessageBox.information(
                    self, "Успех", f"✅ Feature сохранён:\n{filepath}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def generate_selected(self):
        """Генерация feature для выбранных элементов"""
        selected_rows = set(item.row() for item in self.table.selectedItems())

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите элементы в таблице")
            return

        output_dir = QFileDialog.getExistingDirectory(
            self, "Выберите директорию для сохранения", ""
        )

        if not output_dir:
            return

        items_to_generate = []
        for row in selected_rows:
            functional_id = self.table.item(row, 0).text()
            item = (
                self.session.query(FunctionalItem)
                .filter_by(functional_id=functional_id)
                .first()
            )
            if item:
                items_to_generate.append(item)

        try:
            saved_files = FeatureGenerator.batch_generate(
                items_to_generate, Path(output_dir)
            )
            QMessageBox.information(
                self,
                "Успех",
                f"✅ Сгенерировано {len(saved_files)} feature файлов\n\nДиректория: {output_dir}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать:\n{e}")

    def export_selected(self):
        """Алиас для generate_selected"""
        self.generate_selected()

    def export_all(self):
        """Экспорт всех элементов"""
        reply = QMessageBox.question(
            self,
            "Экспорт всех",
            f"Сгенерировать feature файлы для всех {len(self.current_items)} элементов?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            return

        output_dir = QFileDialog.getExistingDirectory(
            self, "Выберите директорию для сохранения", ""
        )

        if not output_dir:
            return

        try:
            saved_files = FeatureGenerator.batch_generate(
                self.current_items, Path(output_dir)
            )
            QMessageBox.information(
                self,
                "Успех",
                f"✅ Сгенерировано {len(saved_files)} feature файлов\n\nДиректория: {output_dir}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать:\n{e}")

    def closeEvent(self, event):
        self.session.close()
        event.accept()
