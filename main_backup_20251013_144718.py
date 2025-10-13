import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from src.db import SessionLocal
from src.models import FunctionalItem

class EditDialog(QDialog):
    def __init__(self, item, session, parent=None):
        super().__init__(parent)
        self.item = item
        self.session = session
        self.setWindowTitle(f'Редактирование: {item.functional_id}')
        self.setMinimumWidth(600)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout(self)
        self.functional_id_edit = QLineEdit(self.item.functional_id)
        self.functional_id_edit.setReadOnly(True)
        self.title_edit = QLineEdit(self.item.title or '')
        self.type_combo = QComboBox()
        self.type_combo.addItems(['', 'Module', 'Epic', 'Feature', 'Page', 'Service', 'Element', 'Story'])
        if self.item.type:
            self.type_combo.setCurrentText(self.item.type)
        
        # Динамические выпадающие списки с возможностью редактирования
        self.module_combo = QComboBox()
        self.module_combo.setEditable(True)
        self.module_combo.addItem('')
        modules = self.session.query(FunctionalItem.module).filter(FunctionalItem.module.isnot(None)).distinct().order_by(FunctionalItem.module).all()
        self.module_combo.addItems([m[0] for m in modules])
        if self.item.module:
            self.module_combo.setCurrentText(self.item.module)
        
        self.epic_combo = QComboBox()
        self.epic_combo.setEditable(True)
        self.epic_combo.addItem('')
        epics = self.session.query(FunctionalItem.epic).filter(FunctionalItem.epic.isnot(None)).distinct().order_by(FunctionalItem.epic).all()
        self.epic_combo.addItems([e[0] for e in epics])
        if self.item.epic:
            self.epic_combo.setCurrentText(self.item.epic)
        
        self.feature_combo = QComboBox()
        self.feature_combo.setEditable(True)
        self.feature_combo.addItem('')
        features = self.session.query(FunctionalItem.feature).filter(FunctionalItem.feature.isnot(None)).distinct().order_by(FunctionalItem.feature).all()
        self.feature_combo.addItems([f[0] for f in features])
        if self.item.feature:
            self.feature_combo.setCurrentText(self.item.feature)
        self.segment_combo = QComboBox()
        self.segment_combo.addItems(['', 'UI', 'UX/CX', 'API', 'Backend', 'Database', 'Integration', 'Security', 'Performance'])
        if self.item.segment:
            self.segment_combo.setCurrentText(self.item.segment)
        self.description_edit = QTextEdit(self.item.description or '')
        self.description_edit.setMaximumHeight(100)
        self.is_crit_check = QCheckBox()
        self.is_crit_check.setChecked(bool(self.item.is_crit))
        self.is_focus_check = QCheckBox()
        self.is_focus_check.setChecked(bool(self.item.is_focus))
        layout.addRow('Functional ID:', self.functional_id_edit)
        layout.addRow('Title:', self.title_edit)
        layout.addRow('Type:', self.type_combo)
        layout.addRow('Module:', self.module_combo)
        layout.addRow('Epic:', self.epic_combo)
        layout.addRow('Feature:', self.feature_combo)
        layout.addRow('Segment:', self.segment_combo)
        layout.addRow('Description:', self.description_edit)
        layout.addRow('Is Critical:', self.is_crit_check)
        layout.addRow('Is Focus:', self.is_focus_check)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def save(self):
        self.item.title = self.title_edit.text()
        self.item.type = self.type_combo.currentText() or None
        self.item.module = self.module_combo.currentText() or None
        self.item.epic = self.epic_combo.currentText() or None
        self.item.feature = self.feature_combo.currentText() or None
        self.item.segment = self.segment_combo.currentText() or None
        self.item.description = self.description_edit.toPlainText() or None
        self.item.is_crit = 1 if self.is_crit_check.isChecked() else 0
        self.item.is_focus = 1 if self.is_focus_check.isChecked() else 0
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.session = SessionLocal()
        self.current_items = []
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        self.setWindowTitle('VoluptAS - Functional Coverage Management')
        self.setGeometry(100, 100, 1400, 900)
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')
        exit_action = QAction('Выход', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        edit_menu = menubar.addMenu('Правка')
        add_action = QAction('➕ Добавить', self)
        add_action.triggered.connect(self.add_item)
        edit_menu.addAction(add_action)
        toolbar = QToolBar('Главная')
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        refresh_action = QAction('🔄 Обновить', self)
        refresh_action.triggered.connect(self.load_data)
        toolbar.addAction(refresh_action)
        add_action_tb = QAction('➕ Добавить', self)
        add_action_tb.triggered.connect(self.add_item)
        toolbar.addAction(add_action_tb)
        edit_action = QAction('✏️ Редактировать', self)
        edit_action.triggered.connect(self.edit_item)
        toolbar.addAction(edit_action)
        delete_action = QAction('🗑️ Удалить', self)
        delete_action.triggered.connect(self.delete_item)
        toolbar.addAction(delete_action)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('🔍 Поиск:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Functional ID, Title, Module, Epic...')
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(['Functional ID', 'Title', 'Type', 'Module', 'Epic', 'Segment', 'Crit', 'Focus'])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_item)
        layout.addWidget(self.table)
        self.statusBar().showMessage('Готов')
    
    def load_data(self):
        self.current_items = self.session.query(FunctionalItem).order_by(FunctionalItem.functional_id).all()
        self.populate_table(self.current_items)
        self.statusBar().showMessage(f'✅ Загружено: {len(self.current_items)} записей')
    
    def populate_table(self, items):
        self.table.setRowCount(len(items))
        for row_idx, item in enumerate(items):
            self.table.setItem(row_idx, 0, QTableWidgetItem(item.functional_id))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item.title or ''))
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.type or ''))
            self.table.setItem(row_idx, 3, QTableWidgetItem(item.module or ''))
            self.table.setItem(row_idx, 4, QTableWidgetItem(item.epic or ''))
            self.table.setItem(row_idx, 5, QTableWidgetItem(item.segment or ''))
            self.table.setItem(row_idx, 6, QTableWidgetItem('✓' if item.is_crit else ''))
            self.table.setItem(row_idx, 7, QTableWidgetItem('✓' if item.is_focus else ''))
        self.table.resizeColumnsToContents()
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = any(self.table.item(row, col) and search_text in self.table.item(row, col).text().lower() for col in range(self.table.columnCount()))
            self.table.setRowHidden(row, not match)
    
    def add_item(self):
        new_item = FunctionalItem(functional_id='new.item', title='Новый элемент', type='Feature')
        dialog = EditDialog(new_item, self.session, self)
        if dialog.exec():
            try:
                self.session.add(new_item)
                self.session.commit()
                self.load_data()
                self.statusBar().showMessage(f'✅ Добавлено: {new_item.functional_id}')
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить:\n{e}')
    
    def edit_item(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, 'Внимание', 'Выберите элемент')
            return
        item = self.current_items[selected]
        dialog = EditDialog(item, self.session, self)
        if dialog.exec():
            try:
                self.session.commit()
                self.load_data()
                self.statusBar().showMessage(f'✅ Сохранено: {item.functional_id}')
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
    
    def delete_item(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, 'Внимание', 'Выберите элемент')
            return
        item = self.current_items[selected]
        reply = QMessageBox.question(self, 'Подтверждение', f'Удалить:\n{item.functional_id}?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(item)
                self.session.commit()
                self.load_data()
                self.statusBar().showMessage(f'✅ Удалено: {item.functional_id}')
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить:\n{e}')
    
    def closeEvent(self, event):
        self.session.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
