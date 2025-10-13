import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from src.db import SessionLocal
from src.models import FunctionalItem, User
from src.utils.role_filter import RoleFilter


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def get_field_config_for_type(item_type):
    """Возвращает конфигурацию полей для типа сущности"""
    base_fields = ['functional_id', 'title', 'description', 'segment', 'is_crit', 'is_focus', 
                   'responsible_qa', 'responsible_dev', 'accountable']
    
    configs = {
        'Module': {
            'show': ['functional_id', 'title', 'description', 'is_crit', 'is_focus', 
                     'responsible_qa', 'responsible_dev', 'accountable', 'documentation_links'],
            'hide': ['module', 'epic', 'feature', 'segment'],
            'has_coverage': False
        },
        'Epic': {
            'show': base_fields + ['module', 'documentation_links'],
            'hide': ['epic', 'feature'],
            'has_coverage': False
        },
        'Feature': {
            'show': base_fields + ['module', 'epic', 'test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': ['feature'],
            'has_coverage': True
        },
        'Story': {
            'show': base_fields + ['module', 'epic', 'feature', 'test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': [],
            'has_coverage': True
        },
        'Page': {
            'show': base_fields + ['module', 'epic', 'test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': ['feature'],
            'has_coverage': True
        },
        'Element': {
            'show': base_fields + ['test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': ['module', 'epic', 'feature'],
            'has_coverage': True
        },
        'Service': {
            'show': base_fields + ['module', 'container', 'database', 'test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': ['epic', 'feature'],
            'has_coverage': True
        }
    }
    return configs.get(item_type, configs['Feature'])


# === ДИНАМИЧЕСКИЙ ДИАЛОГ РЕДАКТИРОВАНИЯ ===

class DynamicEditDialog(QDialog):
    """Динамический диалог с полями в зависимости от типа сущности"""
    
    def __init__(self, item, session, parent=None):
        super().__init__(parent)
        self.item = item
        self.session = session
        self.is_new = not hasattr(item, 'id') or item.id is None
        self.setWindowTitle(f'Редактирование: {item.functional_id}' if not self.is_new else 'Новая сущность')
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        # Виджеты для полей
        self.field_widgets = {}
        
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Вкладки
        tabs = QTabWidget()
        
        # Вкладка 1: Основные поля
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        
        # Functional ID
        self.functional_id_edit = QLineEdit(self.item.functional_id or '')
        self.functional_id_edit.setReadOnly(not self.is_new)
        basic_layout.addRow('* Functional ID:', self.functional_id_edit)
        
        # Title
        self.title_edit = QLineEdit(self.item.title or '')
        basic_layout.addRow('* Title:', self.title_edit)
        
        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Module', 'Epic', 'Feature', 'Page', 'Service', 'Element', 'Story'])
        if self.item.type:
            self.type_combo.setCurrentText(self.item.type)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        basic_layout.addRow('* Type:', self.type_combo)
        
        # Description
        self.description_edit = QTextEdit(self.item.description or '')
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow('Description:', self.description_edit)
        
        # Segment
        self.segment_combo = QComboBox()
        self.segment_combo.addItems(['', 'UI', 'UX/CX', 'API', 'Backend', 'Database', 'Integration', 'Security', 'Performance'])
        if self.item.segment:
            self.segment_combo.setCurrentText(self.item.segment)
        basic_layout.addRow('Segment:', self.segment_combo)
        self.field_widgets['segment'] = (basic_layout.labelForField(self.segment_combo), self.segment_combo)
        
        # Module
        self.module_combo = QComboBox()
        self.module_combo.setEditable(True)
        self.populate_combo(self.module_combo, 'module')
        basic_layout.addRow('Module:', self.module_combo)
        self.field_widgets['module'] = (basic_layout.labelForField(self.module_combo), self.module_combo)
        
        # Epic
        self.epic_combo = QComboBox()
        self.epic_combo.setEditable(True)
        self.populate_combo(self.epic_combo, 'epic')
        basic_layout.addRow('Epic:', self.epic_combo)
        self.field_widgets['epic'] = (basic_layout.labelForField(self.epic_combo), self.epic_combo)
        
        # Feature
        self.feature_combo = QComboBox()
        self.feature_combo.setEditable(True)
        self.populate_combo(self.feature_combo, 'feature')
        basic_layout.addRow('Feature:', self.feature_combo)
        self.field_widgets['feature'] = (basic_layout.labelForField(self.feature_combo), self.feature_combo)
        
        # Checkboxes
        self.is_crit_check = QCheckBox()
        self.is_crit_check.setChecked(bool(self.item.is_crit))
        basic_layout.addRow('Is Critical:', self.is_crit_check)
        
        self.is_focus_check = QCheckBox()
        self.is_focus_check.setChecked(bool(self.item.is_focus))
        basic_layout.addRow('Is Focus:', self.is_focus_check)
        
        tabs.addTab(basic_tab, '📋 Основные')
        
        # Вкладка 2: Ответственные
        responsible_tab = QWidget()
        resp_layout = QFormLayout(responsible_tab)
        
        # Загружаем активных пользователей
        all_users = self.session.query(User).filter_by(is_active=1).order_by(User.name).all()
        
        # Фильтруем по ролям
        qa_users = RoleFilter.filter_users_for_qa(all_users)
        dev_users = RoleFilter.filter_users_for_dev(all_users)
        raci_users = RoleFilter.filter_users_for_raci(all_users)
        
        # Responsible QA - только QA роли
        self.qa_combo = QComboBox()
        qa_names = [''] + [u.name for u in qa_users]
        self.qa_combo.addItems(qa_names)
        if self.item.responsible_qa:
            self.qa_combo.setCurrentText(self.item.responsible_qa.name)
        resp_layout.addRow('Responsible QA:', self.qa_combo)
        
        # Подсказка для QA
        qa_hint = QLabel('(только QA роли)')
        qa_hint.setStyleSheet('color: gray; font-size: 9pt; font-style: italic;')
        resp_layout.addRow('', qa_hint)
        
        # Responsible Dev - Dev, PM, DevOps роли
        self.dev_combo = QComboBox()
        dev_names = [''] + [u.name for u in dev_users]
        self.dev_combo.addItems(dev_names)
        if self.item.responsible_dev:
            self.dev_combo.setCurrentText(self.item.responsible_dev.name)
        resp_layout.addRow('Responsible Dev:', self.dev_combo)
        
        # Подсказка для Dev
        dev_hint = QLabel('(Dev, PM, DevOps роли)')
        dev_hint.setStyleSheet('color: gray; font-size: 9pt; font-style: italic;')
        resp_layout.addRow('', dev_hint)
        
        # Accountable - все роли
        self.accountable_combo = QComboBox()
        raci_names = [''] + [u.name for u in raci_users]
        self.accountable_combo.addItems(raci_names)
        if self.item.accountable:
            self.accountable_combo.setCurrentText(self.item.accountable.name)
        resp_layout.addRow('Accountable:', self.accountable_combo)
        
        # Информация
        info_label = QLabel('Consulted и Informed будут добавлены в следующих версиях')
        info_label.setStyleSheet('color: gray; font-style: italic;')
        resp_layout.addRow(info_label)
        
        tabs.addTab(responsible_tab, '👥 Ответственные')
        
        # Вкладка 3: Покрытие тестами
        coverage_tab = QWidget()
        cov_layout = QFormLayout(coverage_tab)
        
        self.test_cases_edit = QTextEdit(self.item.test_cases_linked or '')
        self.test_cases_edit.setMaximumHeight(80)
        self.test_cases_edit.setPlaceholderText('TC-001, TC-002, TC-003...')
        cov_layout.addRow('Test Cases:', self.test_cases_edit)
        
        self.automation_combo = QComboBox()
        self.automation_combo.addItems(['', 'Not Started', 'In Progress', 'Automated', 'Partially Automated', 'Not Applicable'])
        if self.item.automation_status:
            self.automation_combo.setCurrentText(self.item.automation_status)
        cov_layout.addRow('Automation Status:', self.automation_combo)
        
        self.docs_edit = QTextEdit(self.item.documentation_links or '')
        self.docs_edit.setMaximumHeight(80)
        self.docs_edit.setPlaceholderText('https://confluence..., https://docs...')
        cov_layout.addRow('Documentation Links:', self.docs_edit)
        
        tabs.addTab(coverage_tab, '✅ Покрытие')
        self.coverage_tab = coverage_tab
        
        main_layout.addWidget(tabs)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        # Применяем конфигурацию для текущего типа
        self.on_type_changed(self.type_combo.currentText())
    
    def populate_combo(self, combo, field_name):
        """Заполняет комбобокс уникальными значениями из БД"""
        combo.addItem('')
        query = self.session.query(getattr(FunctionalItem, field_name)).filter(
            getattr(FunctionalItem, field_name).isnot(None)
        ).distinct().order_by(getattr(FunctionalItem, field_name))
        
        values = [v[0] for v in query.all()]
        combo.addItems(values)
        
        current_value = getattr(self.item, field_name)
        if current_value:
            combo.setCurrentText(current_value)
    
    def on_type_changed(self, item_type):
        """Показывает/скрывает поля в зависимости от типа"""
        config = get_field_config_for_type(item_type)
        
        # Показываем/скрываем иерархические поля и segment
        for field in ['module', 'epic', 'feature', 'segment']:
            if field in self.field_widgets:
                label, widget = self.field_widgets[field]
                visible = field not in config['hide']
                label.setVisible(visible)
                widget.setVisible(visible)
        
        # Показываем/скрываем вкладку покрытия
        if hasattr(self, 'coverage_tab'):
            tab_widget = self.coverage_tab.parent()
            if isinstance(tab_widget, QTabWidget):
                index = tab_widget.indexOf(self.coverage_tab)
                tab_widget.setTabVisible(index, config['has_coverage'])
    
    def save(self):
        """Сохранение с валидацией"""
        # Валидация обязательных полей
        if not self.functional_id_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Functional ID обязателен')
            return
        
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Title обязателен')
            return
        
        qa_name = self.qa_combo.currentText().strip()
        dev_name = self.dev_combo.currentText().strip()
        
        # QA и Dev теперь необязательны
        # if not qa_name or not dev_name:
        #     QMessageBox.warning(self, 'Ошибка', 'Responsible QA и Responsible Dev обязательны')
        #     return
        
        # Сохраняем данные
        self.item.functional_id = self.functional_id_edit.text().strip()
        self.item.title = self.title_edit.text().strip()
        self.item.type = self.type_combo.currentText()
        self.item.description = self.description_edit.toPlainText().strip() or None
        self.item.segment = self.segment_combo.currentText() or None
        
        # Иерархия
        config = get_field_config_for_type(self.item.type)
        if 'module' not in config['hide']:
            self.item.module = self.module_combo.currentText().strip() or None
        else:
            self.item.module = None
            
        if 'epic' not in config['hide']:
            self.item.epic = self.epic_combo.currentText().strip() or None
        else:
            self.item.epic = None
            
        if 'feature' not in config['hide']:
            self.item.feature = self.feature_combo.currentText().strip() or None
        else:
            self.item.feature = None
        
        self.item.is_crit = 1 if self.is_crit_check.isChecked() else 0
        self.item.is_focus = 1 if self.is_focus_check.isChecked() else 0
        
        # Ответственные
        qa_user = self.session.query(User).filter_by(name=qa_name).first()
        dev_user = self.session.query(User).filter_by(name=dev_name).first()
        accountable_name = self.accountable_combo.currentText().strip()
        accountable_user = self.session.query(User).filter_by(name=accountable_name).first() if accountable_name else None
        
        self.item.responsible_qa_id = qa_user.id if qa_user else None
        self.item.responsible_dev_id = dev_user.id if dev_user else None
        self.item.accountable_id = accountable_user.id if accountable_user else None
        
        # Покрытие
        if config['has_coverage']:
            self.item.test_cases_linked = self.test_cases_edit.toPlainText().strip() or None
            self.item.automation_status = self.automation_combo.currentText() or None
            self.item.documentation_links = self.docs_edit.toPlainText().strip() or None
        
        self.accept()


# === РЕДАКТОР СУЩНОСТЕЙ ПО ТИПАМ ===

class EntityEditorWindow(QMainWindow):
    """Редактор сущностей с фильтрацией по типам"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = SessionLocal()
        self.current_items = []
        self.current_filter_type = 'All'
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        self.setWindowTitle('Редактор сущностей по типам')
        self.setGeometry(150, 150, 1200, 700)
        
        # Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')
        close_action = QAction('Закрыть', self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # Тулбар
        toolbar = QToolBar('Типы')
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Кнопки фильтров по типам
        types = ['All', 'Module', 'Epic', 'Feature', 'Story', 'Page', 'Element', 'Service']
        for t in types:
            action = QAction(f'📦 {t}' if t == 'All' else t, self)
            action.triggered.connect(lambda checked, type_name=t: self.filter_by_type(type_name))
            toolbar.addAction(action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction('🔄 Обновить', self)
        refresh_action.triggered.connect(self.load_data)
        toolbar.addAction(refresh_action)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Фильтры
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel('🔍 Поиск:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Functional ID, Title...')
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(QLabel('Module:'))
        self.module_filter = QComboBox()
        self.module_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.module_filter)
        
        filter_layout.addWidget(QLabel('Epic:'))
        self.epic_filter = QComboBox()
        self.epic_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.epic_filter)
        
        layout.addLayout(filter_layout)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['Functional ID', 'Title', 'Type', 'Module', 'Epic', 'Crit', 'Focus'])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_item)
        layout.addWidget(self.table)
        
        self.statusBar().showMessage('Готов')
    
    def load_data(self):
        """Загрузить все сущности"""
        self.current_items = self.session.query(FunctionalItem).order_by(FunctionalItem.type, FunctionalItem.functional_id).all()
        self.populate_filters()
        self.filter_by_type(self.current_filter_type)
        self.statusBar().showMessage(f'✅ Загружено: {len(self.current_items)} записей')
    
    def populate_filters(self):
        """Заполнить фильтры уникальными значениями"""
        modules = [''] + sorted(set(item.module for item in self.current_items if item.module))
        epics = [''] + sorted(set(item.epic for item in self.current_items if item.epic))
        
        self.module_filter.clear()
        self.module_filter.addItems(modules)
        
        self.epic_filter.clear()
        self.epic_filter.addItems(epics)
    
    def filter_by_type(self, type_name):
        """Фильтрация по типу"""
        self.current_filter_type = type_name
        if type_name == 'All':
            filtered = self.current_items
        else:
            filtered = [item for item in self.current_items if item.type == type_name]
        
        self.populate_table(filtered)
        self.statusBar().showMessage(f'📊 {type_name}: {len(filtered)} записей')
    
    def populate_table(self, items):
        """Заполнить таблицу"""
        self.table.setRowCount(len(items))
        for row_idx, item in enumerate(items):
            self.table.setItem(row_idx, 0, QTableWidgetItem(item.functional_id))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item.title or ''))
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.type or ''))
            self.table.setItem(row_idx, 3, QTableWidgetItem(item.module or ''))
            self.table.setItem(row_idx, 4, QTableWidgetItem(item.epic or ''))
            self.table.setItem(row_idx, 5, QTableWidgetItem('✓' if item.is_crit else ''))
            self.table.setItem(row_idx, 6, QTableWidgetItem('✓' if item.is_focus else ''))
        self.table.resizeColumnsToContents()
    
    def apply_filters(self):
        """Применить все фильтры"""
        search_text = self.search_input.text().lower()
        module_filter = self.module_filter.currentText()
        epic_filter = self.epic_filter.currentText()
        
        for row in range(self.table.rowCount()):
            show = True
            
            # Текстовый поиск
            if search_text:
                match = any(
                    self.table.item(row, col) and search_text in self.table.item(row, col).text().lower()
                    for col in [0, 1]
                )
                show = show and match
            
            # Фильтр по модулю
            if module_filter and show:
                module_cell = self.table.item(row, 3)
                show = show and (module_cell and module_cell.text() == module_filter)
            
            # Фильтр по эпику
            if epic_filter and show:
                epic_cell = self.table.item(row, 4)
                show = show and (epic_cell and epic_cell.text() == epic_filter)
            
            self.table.setRowHidden(row, not show)
    
    def edit_item(self):
        """Редактировать выбранную сущность"""
        selected = self.table.currentRow()
        if selected < 0:
            return
        
        functional_id = self.table.item(selected, 0).text()
        item = self.session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
        
        if item:
            dialog = DynamicEditDialog(item, self.session, self)
            if dialog.exec():
                try:
                    self.session.commit()
                    self.load_data()
                    self.statusBar().showMessage(f'✅ Сохранено: {item.functional_id}')
                except Exception as e:
                    self.session.rollback()
                    QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
    
    def closeEvent(self, event):
        self.session.close()
        event.accept()


# === ГЛАВНОЕ ОКНО ===

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.session = SessionLocal()
        self.current_items = []
        self.current_filter = 'all'  # all, crit, focus
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        self.setWindowTitle('VoluptAS - Functional Coverage Management')
        self.setGeometry(100, 100, 1400, 900)
        
        # Меню
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('Файл')
        exit_action = QAction('Выход', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu('Правка')
        add_action = QAction('➕ Добавить', self)
        add_action.triggered.connect(self.add_item)
        edit_menu.addAction(add_action)
        
        tools_menu = menubar.addMenu('Инструменты')
        entity_editor_action = QAction('📦 Редактор сущностей', self)
        entity_editor_action.triggered.connect(self.open_entity_editor)
        tools_menu.addAction(entity_editor_action)
        
        user_manager_action = QAction('👥 Управление пользователями', self)
        user_manager_action.triggered.connect(self.open_user_manager)
        tools_menu.addAction(user_manager_action)
        
        # Меню Граф
        graph_menu = menubar.addMenu('🕸️ Граф')
        open_graph_action = QAction('🌐 Открыть граф', self)
        open_graph_action.triggered.connect(self.open_graph_view)
        graph_menu.addAction(open_graph_action)
        
        # Меню Настройки
        settings_menu = menubar.addMenu('Настройки')
        zoho_settings_action = QAction('⚙️ Zoho API', self)
        zoho_settings_action.triggered.connect(self.open_zoho_settings)
        settings_menu.addAction(zoho_settings_action)
        
        # Тулбар
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
        
        toolbar.addSeparator()
        
        # Быстрые фильтры
        all_action = QAction('📋 Все', self)
        all_action.triggered.connect(lambda: self.quick_filter('all'))
        toolbar.addAction(all_action)
        
        crit_action = QAction('🔴 Критичное', self)
        crit_action.triggered.connect(lambda: self.quick_filter('crit'))
        toolbar.addAction(crit_action)
        
        focus_action = QAction('🎯 Фокусное', self)
        focus_action.triggered.connect(lambda: self.quick_filter('focus'))
        toolbar.addAction(focus_action)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Поиск и фильтры
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('🔍 Поиск:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Functional ID, Title, Module, Epic...')
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        
        search_layout.addWidget(QLabel('QA:'))
        self.qa_filter = QComboBox()
        self.qa_filter.currentTextChanged.connect(self.filter_table)
        search_layout.addWidget(self.qa_filter)
        
        search_layout.addWidget(QLabel('Dev:'))
        self.dev_filter = QComboBox()
        self.dev_filter.currentTextChanged.connect(self.filter_table)
        search_layout.addWidget(self.dev_filter)
        
        layout.addLayout(search_layout)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            'Functional ID', 'Title', 'Type', 'Module', 'Epic', 'QA', 'Dev', 'Segment', 'Crit', 'Focus'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_item)
        layout.addWidget(self.table)
        
        self.statusBar().showMessage('Готов')
    
    def load_data(self):
        self.current_items = self.session.query(FunctionalItem).order_by(FunctionalItem.functional_id).all()
        
        # Обновляем фильтры ответственных
        qa_users = sorted(set(item.responsible_qa.name for item in self.current_items if item.responsible_qa))
        dev_users = sorted(set(item.responsible_dev.name for item in self.current_items if item.responsible_dev))
        
        self.qa_filter.clear()
        self.qa_filter.addItems([''] + qa_users)
        
        self.dev_filter.clear()
        self.dev_filter.addItems([''] + dev_users)
        
        self.populate_table(self.current_items)
        self.apply_quick_filter()
        self.statusBar().showMessage(f'✅ Загружено: {len(self.current_items)} записей')
    
    def populate_table(self, items):
        self.table.setRowCount(len(items))
        for row_idx, item in enumerate(items):
            self.table.setItem(row_idx, 0, QTableWidgetItem(item.functional_id))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item.title or ''))
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.type or ''))
            self.table.setItem(row_idx, 3, QTableWidgetItem(item.module or ''))
            self.table.setItem(row_idx, 4, QTableWidgetItem(item.epic or ''))
            self.table.setItem(row_idx, 5, QTableWidgetItem(item.responsible_qa.name if item.responsible_qa else ''))
            self.table.setItem(row_idx, 6, QTableWidgetItem(item.responsible_dev.name if item.responsible_dev else ''))
            self.table.setItem(row_idx, 7, QTableWidgetItem(item.segment or ''))
            self.table.setItem(row_idx, 8, QTableWidgetItem('✓' if item.is_crit else ''))
            self.table.setItem(row_idx, 9, QTableWidgetItem('✓' if item.is_focus else ''))
        self.table.resizeColumnsToContents()
    
    def quick_filter(self, filter_type):
        """Быстрая фильтрация (все/критичное/фокусное)"""
        self.current_filter = filter_type
        self.apply_quick_filter()
    
    def apply_quick_filter(self):
        """Применить быстрый фильтр"""
        for row in range(self.table.rowCount()):
            show = True
            if self.current_filter == 'crit':
                crit_item = self.table.item(row, 8)
                show = crit_item and crit_item.text() == '✓'
            elif self.current_filter == 'focus':
                focus_item = self.table.item(row, 9)
                show = focus_item and focus_item.text() == '✓'
            
            if not show:
                self.table.setRowHidden(row, True)
        
        self.filter_table()  # Применяем остальные фильтры
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        qa_filter = self.qa_filter.currentText()
        dev_filter = self.dev_filter.currentText()
        
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            
            show = True
            
            # Текстовый поиск
            if search_text:
                match = any(
                    self.table.item(row, col) and search_text in self.table.item(row, col).text().lower()
                    for col in range(self.table.columnCount())
                )
                show = show and match
            
            # Фильтр по QA
            if qa_filter and show:
                qa_cell = self.table.item(row, 5)
                show = show and (qa_cell and qa_cell.text() == qa_filter)
            
            # Фильтр по Dev
            if dev_filter and show:
                dev_cell = self.table.item(row, 6)
                show = show and (dev_cell and dev_cell.text() == dev_filter)
            
            self.table.setRowHidden(row, not show)
    
    def add_item(self):
        new_item = FunctionalItem(functional_id='new.item', title='Новый элемент', type='Feature')
        dialog = DynamicEditDialog(new_item, self.session, self)
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
        
        functional_id = self.table.item(selected, 0).text()
        item = self.session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
        
        if item:
            dialog = DynamicEditDialog(item, self.session, self)
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
        
        functional_id = self.table.item(selected, 0).text()
        item = self.session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
        
        if item:
            reply = QMessageBox.question(
                self, 'Подтверждение',
                f'Удалить:\n{item.functional_id}?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.session.delete(item)
                    self.session.commit()
                    self.load_data()
                    self.statusBar().showMessage(f'✅ Удалено: {item.functional_id}')
                except Exception as e:
                    self.session.rollback()
                    QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить:\n{e}')
    
    def open_entity_editor(self):
        """Открыть редактор сущностей"""
        editor = EntityEditorWindow(self)
        editor.show()
    
    def open_user_manager(self):
        """Открыть управление пользователями"""
        from src.ui.dialogs.user_manager import UserManagerWindow
        manager = UserManagerWindow(self)
        manager.show()
    
    def open_zoho_settings(self):
        """Открыть единые настройки интеграций"""
        from src.ui.dialogs.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def open_graph_view(self):
        """Открыть граф связей"""
        from src.ui.graph_view import GraphViewWindow
        graph_window = GraphViewWindow(self)
        graph_window.show()
    
    def closeEvent(self, event):
        self.session.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
