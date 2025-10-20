import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Настройка логирования с ротацией
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'voluptas.log'

# Ротация: максимум 10 MB на файл, 5 backup файлов
file_handler = RotatingFileHandler(
    log_file, 
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)-8s] %(name)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)-8s] %(message)s',
    datefmt='%H:%M:%S'
))

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)
logger.info("="*60)
logger.info(f"VoluptAS starting... Working directory: {project_root}")
logger.info(f"Log file: {log_file}")

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from src.db import SessionLocal
from src.models import FunctionalItem, User
from src.utils.role_filter import RoleFilter
from src.utils.version import get_version_banner


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
            'has_coverage': False,
            'has_segment': False
        },
        'Epic': {
            'show': base_fields + ['module', 'documentation_links'],
            'hide': ['epic', 'feature', 'segment'],
            'has_coverage': False,
            'has_segment': False
        },
        'Feature': {
            'show': base_fields + ['module', 'epic', 'test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': ['feature'],
            'has_coverage': True,
            'has_segment': True
        },
        'Story': {
            'show': base_fields + ['module', 'epic', 'feature', 'test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': [],
            'has_coverage': True,
            'has_segment': True
        },
        'Page': {
            'show': base_fields + ['module', 'epic', 'test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': ['feature'],
            'has_coverage': True,
            'has_segment': True
        },
        'Element': {
            'show': base_fields + ['test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': ['module', 'epic', 'feature'],
            'has_coverage': True,
            'has_segment': True
        },
        'Service': {
            'show': base_fields + ['module', 'container', 'database', 'test_cases_linked', 'automation_status', 'documentation_links'],
            'hide': ['epic', 'feature'],
            'has_coverage': True,
            'has_segment': True
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
        
        # Functional ID (FuncID)
        self.functional_id_edit = QLineEdit(self.item.functional_id or '')
        self.functional_id_edit.setReadOnly(not self.is_new)
        basic_layout.addRow('* FuncID:', self.functional_id_edit)
        
        # Alias Tag (короткий уникальный алиас)
        self.alias_tag_edit = QLineEdit(self.item.alias_tag or '')
        self.alias_tag_edit.setPlaceholderText('Короткое название (напр.: cookies, Login_Page)')
        alias_hint = QLabel('<i>Уникальный алиас для удобного поиска. Если пустой — используется последняя часть FuncID</i>')
        alias_hint.setStyleSheet('color: gray; font-size: 9pt;')
        alias_hint.setWordWrap(True)
        basic_layout.addRow('Alias Tag:', self.alias_tag_edit)
        basic_layout.addRow('', alias_hint)
        
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
        
        # Вкладка 4: BDD Feature
        bdd_tab = QWidget()
        bdd_layout = QVBoxLayout(bdd_tab)
        
        # Кнопки управления
        bdd_buttons = QHBoxLayout()
        generate_btn = QPushButton('🛠️ Сгенерировать Feature')
        generate_btn.clicked.connect(self.generate_bdd_feature)
        bdd_buttons.addWidget(generate_btn)
        
        export_btn = QPushButton('💾 Экспорт .feature')
        export_btn.clicked.connect(self.export_bdd_feature)
        bdd_buttons.addWidget(export_btn)
        
        bdd_buttons.addStretch()
        bdd_layout.addLayout(bdd_buttons)
        
        # Текстовое поле для Gherkin
        self.bdd_edit = QTextEdit()
        self.bdd_edit.setPlaceholderText('Нажмите "Сгенерировать Feature" для автогенерации или введите вручную...')
        self.bdd_edit.setStyleSheet('font-family: Consolas, monospace; font-size: 10pt;')
        bdd_layout.addWidget(self.bdd_edit)
        
        # Подсказка
        hint_label = QLabel('💡 Gherkin syntax: Feature, Scenario, Given, When, Then, And')
        hint_label.setStyleSheet('color: gray; font-size: 9pt; font-style: italic;')
        bdd_layout.addWidget(hint_label)
        
        tabs.addTab(bdd_tab, '🧑‍💻 BDD')
        self.bdd_tab = bdd_tab
        
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
        
        # Показываем/скрываем иерархические поля
        for field in ['module', 'epic', 'feature']:
            if field in self.field_widgets:
                label, widget = self.field_widgets[field]
                visible = field not in config['hide']
                label.setVisible(visible)
                widget.setVisible(visible)
        
        # Segment отдельно - только для типов с has_segment=True
        if 'segment' in self.field_widgets:
            label, widget = self.field_widgets['segment']
            visible = config.get('has_segment', False)
            label.setVisible(visible)
            widget.setVisible(visible)
            if not visible:
                widget.setCurrentText('')  # Очищаем если скрыто
        
        # Показываем/скрываем вкладку покрытия
        if hasattr(self, 'coverage_tab'):
            tab_widget = self.coverage_tab.parent()
            if isinstance(tab_widget, QTabWidget):
                index = tab_widget.indexOf(self.coverage_tab)
                tab_widget.setTabVisible(index, config['has_coverage'])
    
    def generate_bdd_feature(self):
        """Генерация BDD Feature для текущего элемента"""
        from src.bdd.feature_generator import FeatureGenerator
        
        # Генерируем feature для текущего item
        feature_content = FeatureGenerator.generate_feature(self.item)
        self.bdd_edit.setPlainText(feature_content)
        
        QMessageBox.information(self, 'Успех', '✅ Feature файл сгенерирован!\n\nВы можете отредактировать его вручную.')
    
    def export_bdd_feature(self):
        """Экспорт feature файла"""
        content = self.bdd_edit.toPlainText().strip()
        
        if not content:
            QMessageBox.warning(self, 'Предупреждение', 'Feature файл пуст.\nСначала сгенерируйте его.')
            return
        
        # Выбор пути для сохранения
        filename = f"{self.item.functional_id.replace('.', '_')}.feature"
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить feature файл', filename, 'Feature Files (*.feature)'
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, 'Успех', f'✅ Feature файл сохранён:\n{filepath}')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
    
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
        self.item.alias_tag = self.alias_tag_edit.text().strip() or None
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
        banner = get_version_banner(project_root)
        self.setWindowTitle(f'VoluptAS {banner} - Functional Coverage Management')
        self.setGeometry(100, 100, 1400, 900)
        
        # === НОВОЕ МЕНЮ ===
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu('📁 Файл')
        
        save_action = QAction('💾 Сохранить', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_data)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('📤 Экспорт', self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        import_action = QAction('📥 Импорт', self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('🚺 Выход', self)
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Правка"
        edit_menu = menubar.addMenu('✏️ Правка')
        
        refresh_action = QAction('🔄 Обновить', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.load_data)
        edit_menu.addAction(refresh_action)
        
        edit_menu.addSeparator()
        
        add_action = QAction('➕ Добавить', self)
        add_action.setShortcut('Ctrl+N')
        add_action.triggered.connect(self.add_item)
        edit_menu.addAction(add_action)
        
        edit_item_action = QAction('✏️ Редактировать', self)
        edit_item_action.setShortcut('Ctrl+E')
        edit_item_action.triggered.connect(self.edit_item)
        edit_menu.addAction(edit_item_action)
        
        delete_action = QAction('🗑️ Удалить', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.delete_item)
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        save_edit_action = QAction('💾 Сохранить', self)
        save_edit_action.setShortcut('Ctrl+S')
        save_edit_action.triggered.connect(self.save_data)
        edit_menu.addAction(save_edit_action)
        
        # Меню "Инструменты"
        tools_menu = menubar.addMenu('🔧 Инструменты')
        
        # BDD Feature генерация
        bdd_manager_action = QAction('🧑‍💻 BDD Feature Manager', self)
        bdd_manager_action.triggered.connect(self.open_bdd_manager)
        tools_menu.addAction(bdd_manager_action)
        
        generate_bdd_action = QAction('🛠️ Генерация BDD Features', self)
        generate_bdd_action.setShortcut('Ctrl+B')
        generate_bdd_action.triggered.connect(self.generate_bdd_features)
        tools_menu.addAction(generate_bdd_action)
        
        tools_menu.addSeparator()
        
        # Граф связей
        graph_action = QAction('🔗 Граф связей', self)
        graph_action.setShortcut('Ctrl+G')
        graph_action.triggered.connect(self.open_graph_view)
        tools_menu.addAction(graph_action)
        
        tools_menu.addSeparator()
        
        sync_menu = tools_menu.addMenu('🔄 Синхронизация')
        
        sync_zoho_action = QAction('Zoho', self)
        sync_zoho_action.triggered.connect(self.sync_zoho)
        sync_menu.addAction(sync_zoho_action)
        
        sync_google_action = QAction('Google', self)
        sync_menu.addAction(sync_google_action)
        
        sync_qase_action = QAction('Qase', self)
        sync_menu.addAction(sync_qase_action)
        
        # Меню "Настройки"
        settings_menu = menubar.addMenu('⚙️ Настройки')
        
        settings_action = QAction('⚙️ Настройки', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.open_zoho_settings)
        settings_menu.addAction(settings_action)
        
        entity_editor_action = QAction('📦 Редактор сущностей', self)
        entity_editor_action.triggered.connect(self.open_entity_editor)
        settings_menu.addAction(entity_editor_action)
        
        user_manager_action = QAction('👥 Пользователи', self)
        user_manager_action.triggered.connect(self.open_user_manager)
        settings_menu.addAction(user_manager_action)
        
        dict_manager_action = QAction('📚 Справочники', self)
        dict_manager_action.triggered.connect(self.open_dict_manager)
        settings_menu.addAction(dict_manager_action)
        
        # Меню "Помощь"
        help_menu = menubar.addMenu('❓ Помощь')
        
        docs_action = QAction('📖 Документация', self)
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        
        about_action = QAction('ℹ️ О программе', self)
        help_menu.addAction(about_action)
        
        # Тулбар удалён (всё в меню)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # === НОВАЯ АРХИТЕКТУРА: ТАБЫ ===
        from src.ui.widgets.main_tabs_widget import MainTabsWidget
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Таб 1: Таблица (существующий функционал)
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        
        # Поиск и фильтры - первая строка
        search_layout1 = QHBoxLayout()
        search_layout1.addWidget(QLabel('🔍 Поиск:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Functional ID, Alias, Title, Module, Epic...')
        self.search_input.textChanged.connect(self.filter_table)
        search_layout1.addWidget(self.search_input, stretch=2)
        
        search_layout1.addWidget(QLabel('Type:'))
        self.type_filter = QComboBox()
        self.type_filter.currentTextChanged.connect(self.filter_table)
        search_layout1.addWidget(self.type_filter)
        
        search_layout1.addWidget(QLabel('Module:'))
        self.module_filter = QComboBox()
        self.module_filter.currentTextChanged.connect(self.filter_table)
        search_layout1.addWidget(self.module_filter)
        
        search_layout1.addWidget(QLabel('Epic:'))
        self.epic_filter = QComboBox()
        self.epic_filter.currentTextChanged.connect(self.filter_table)
        search_layout1.addWidget(self.epic_filter)
        
        table_layout.addLayout(search_layout1)
        
        # Фильтры - вторая строка
        search_layout2 = QHBoxLayout()
        
        search_layout2.addWidget(QLabel('Segment:'))
        self.segment_filter = QComboBox()
        self.segment_filter.currentTextChanged.connect(self.filter_table)
        search_layout2.addWidget(self.segment_filter)
        
        search_layout2.addWidget(QLabel('QA:'))
        self.qa_filter = QComboBox()
        self.qa_filter.currentTextChanged.connect(self.filter_table)
        search_layout2.addWidget(self.qa_filter)
        
        search_layout2.addWidget(QLabel('Dev:'))
        self.dev_filter = QComboBox()
        self.dev_filter.currentTextChanged.connect(self.filter_table)
        search_layout2.addWidget(self.dev_filter)
        
        # Кнопка сброса фильтров
        clear_filters_btn = QPushButton('❌ Сбросить фильтры')
        clear_filters_btn.clicked.connect(self.clear_filters)
        search_layout2.addWidget(clear_filters_btn)
        
        search_layout2.addSeparator() if hasattr(search_layout2, 'addSeparator') else None
        
        # Быстрые фильтры (перенесены из toolbar)
        all_btn = QPushButton('📋 Все')
        all_btn.clicked.connect(lambda: self.quick_filter('all'))
        search_layout2.addWidget(all_btn)
        
        crit_btn = QPushButton('🔴 Критичное')
        crit_btn.clicked.connect(lambda: self.quick_filter('crit'))
        search_layout2.addWidget(crit_btn)
        
        focus_btn = QPushButton('🎯 Фокусное')
        focus_btn.clicked.connect(lambda: self.quick_filter('focus'))
        search_layout2.addWidget(focus_btn)
        
        search_layout2.addStretch()
        
        table_layout.addLayout(search_layout2)
        
        # Горизонтальный layout: таблица + мини-граф
        content_layout = QHBoxLayout()
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            'FuncID', 'Alias', 'Title', 'Type', 'Module', 'Epic', 'QA', 'Dev', 'Segment', 'Crit', 'Focus'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Разрешаем inline-редактирование по double-click
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.table.itemChanged.connect(self.on_item_changed)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        content_layout.addWidget(self.table, stretch=7)
        
        # Мини-граф справа
        from src.ui.mini_graph_widget import MiniGraphWidget
        self.mini_graph = MiniGraphWidget(self)
        self.mini_graph.setMinimumWidth(350)
        self.mini_graph.setMaximumWidth(450)
        content_layout.addWidget(self.mini_graph, stretch=3)
        
        table_layout.addLayout(content_layout)
        
        # Добавляем таб с таблицей
        self.tabs.addTab(table_tab, '📊 Таблица')
        
        # Таб 2: Полный граф
        from src.ui.widgets.full_graph_tab import FullGraphTabWidget
        self.graph_tab = FullGraphTabWidget(self)
        self.tabs.addTab(self.graph_tab, '🌐 Граф')
        
        # Таб 3: BDD
        from src.ui.widgets.bdd_tab import BddTabWidget
        self.bdd_tab = BddTabWidget(self)
        self.tabs.addTab(self.bdd_tab, '🧑‍💻 BDD')
        
        # Таб 4: Матрица трассировок
        from src.ui.widgets.coverage_matrix_tab import CoverageMatrixTabWidget
        self.coverage_tab = CoverageMatrixTabWidget(self)
        self.tabs.addTab(self.coverage_tab, '📋 Трассировки')
        
        # Таб 5: INFRA
        from src.ui.widgets.infra_maturity_tab import InfraMaturityTabWidget
        self.infra_tab = InfraMaturityTabWidget(self)
        self.tabs.addTab(self.infra_tab, '🏗️ INFRA')
        
        # Добавляем табы в главный layout
        layout.addWidget(self.tabs)
        
        # Hotkeys для переключения табов
        from PyQt6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence('Ctrl+1'), self).activated.connect(lambda: self.tabs.setCurrentIndex(0))
        QShortcut(QKeySequence('Ctrl+2'), self).activated.connect(lambda: self.tabs.setCurrentIndex(1))
        QShortcut(QKeySequence('Ctrl+3'), self).activated.connect(lambda: self.tabs.setCurrentIndex(2))
        QShortcut(QKeySequence('Ctrl+4'), self).activated.connect(lambda: self.tabs.setCurrentIndex(3))
        QShortcut(QKeySequence('Ctrl+5'), self).activated.connect(lambda: self.tabs.setCurrentIndex(4))
        
        # Обработка смены таба
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.statusBar().showMessage('Готов')
        # Печатаем баннер и путь запуска в консоль для быстрой диагностики
        print(f"[VoluptAS] {banner} | root={project_root}")
    
    def load_data(self):
        self.current_items = self.session.query(FunctionalItem).order_by(FunctionalItem.functional_id).all()
        
        # Обновляем все фильтры
        types = sorted(set(item.type for item in self.current_items if item.type))
        modules = sorted(set(item.module for item in self.current_items if item.module))
        epics = sorted(set(item.epic for item in self.current_items if item.epic))
        segments = sorted(set(item.segment for item in self.current_items if item.segment))
        qa_users = sorted(set(item.responsible_qa.name for item in self.current_items if item.responsible_qa))
        dev_users = sorted(set(item.responsible_dev.name for item in self.current_items if item.responsible_dev))
        
        self.type_filter.clear()
        self.type_filter.addItems([''] + types)
        
        self.module_filter.clear()
        self.module_filter.addItems([''] + modules)
        
        self.epic_filter.clear()
        self.epic_filter.addItems([''] + epics)
        
        self.segment_filter.clear()
        self.segment_filter.addItems([''] + segments)
        
        self.qa_filter.clear()
        self.qa_filter.addItems([''] + qa_users)
        
        self.dev_filter.clear()
        self.dev_filter.addItems([''] + dev_users)
        
        self.populate_table(self.current_items)
        self.apply_quick_filter()
        self.statusBar().showMessage(f'✅ Загружено: {len(self.current_items)} записей')
    
    def populate_table(self, items):
        # Отключаем itemChanged на время заполнения
        self.table.itemChanged.disconnect(self.on_item_changed)
        
        self.table.setRowCount(len(items))
        for row_idx, item in enumerate(items):
            # Если alias_tag пустой, используем последнюю часть functional_id
            alias_display = item.alias_tag if item.alias_tag else item.functional_id.split('.')[-1]
            
            # Нередактируемые колонки
            funcid_item = QTableWidgetItem(item.functional_id)
            funcid_item.setFlags(funcid_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 0, funcid_item)
            
            self.table.setItem(row_idx, 1, QTableWidgetItem(alias_display))  # Редактируемый
            self.table.setItem(row_idx, 2, QTableWidgetItem(item.title or ''))  # Редактируемый
            
            type_item = QTableWidgetItem(item.type or '')
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 3, type_item)
            
            module_item = QTableWidgetItem(item.module or '')
            module_item.setFlags(module_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 4, module_item)
            
            epic_item = QTableWidgetItem(item.epic or '')
            epic_item.setFlags(epic_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 5, epic_item)
            
            qa_item = QTableWidgetItem(item.responsible_qa.name if item.responsible_qa else '')
            qa_item.setFlags(qa_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 6, qa_item)
            
            dev_item = QTableWidgetItem(item.responsible_dev.name if item.responsible_dev else '')
            dev_item.setFlags(dev_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 7, dev_item)
            
            self.table.setItem(row_idx, 8, QTableWidgetItem(item.segment or ''))  # Редактируемый
            
            # Crit и Focus - чекбоксы
            crit_widget = QWidget()
            crit_layout = QHBoxLayout(crit_widget)
            crit_layout.setContentsMargins(0, 0, 0, 0)
            crit_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            crit_check = QCheckBox()
            crit_check.setChecked(bool(item.is_crit))
            crit_check.stateChanged.connect(lambda state, r=row_idx, c=9: self.on_checkbox_changed(r, c, state))
            crit_layout.addWidget(crit_check)
            self.table.setCellWidget(row_idx, 9, crit_widget)
            
            focus_widget = QWidget()
            focus_layout = QHBoxLayout(focus_widget)
            focus_layout.setContentsMargins(0, 0, 0, 0)
            focus_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            focus_check = QCheckBox()
            focus_check.setChecked(bool(item.is_focus))
            focus_check.stateChanged.connect(lambda state, r=row_idx, c=10: self.on_checkbox_changed(r, c, state))
            focus_layout.addWidget(focus_check)
            self.table.setCellWidget(row_idx, 10, focus_widget)
        
        self.table.resizeColumnsToContents()
        
        # Включаем itemChanged обратно
        self.table.itemChanged.connect(self.on_item_changed)
    
    def quick_filter(self, filter_type):
        """Быстрая фильтрация (все/критичное/фокусное)"""
        self.current_filter = filter_type
        self.apply_quick_filter()
    
    def apply_quick_filter(self):
        """Применить быстрый фильтр"""
        # Сначала показываем все строки
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)
        
        # Потом применяем фильтр
        if self.current_filter != 'all':
            for row in range(self.table.rowCount()):
                show = True
                if self.current_filter == 'crit':
                    crit_item = self.table.item(row, 9)  # Изменено: 8 → 9
                    show = crit_item and crit_item.text() == '✓'
                elif self.current_filter == 'focus':
                    focus_item = self.table.item(row, 10)  # Изменено: 9 → 10
                    show = focus_item and focus_item.text() == '✓'
                
                self.table.setRowHidden(row, not show)
        
        self.filter_table()  # Применяем остальные фильтры
    
    def clear_filters(self):
        """Сбросить все фильтры"""
        self.search_input.clear()
        self.type_filter.setCurrentIndex(0)
        self.module_filter.setCurrentIndex(0)
        self.epic_filter.setCurrentIndex(0)
        self.segment_filter.setCurrentIndex(0)
        self.qa_filter.setCurrentIndex(0)
        self.dev_filter.setCurrentIndex(0)
        self.current_filter = 'all'
        self.apply_quick_filter()
    
    def on_checkbox_changed(self, row, col, state):
        """Обработка изменения чекбокса"""
        functional_id = self.table.item(row, 0).text()
        db_item = self.session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
        
        if not db_item:
            return
        
        try:
            if col == 9:  # Crit
                db_item.is_crit = 1 if state == Qt.CheckState.Checked.value else 0
            elif col == 10:  # Focus
                db_item.is_focus = 1 if state == Qt.CheckState.Checked.value else 0
            
            self.session.commit()
            self.statusBar().showMessage(f'✅ Сохранено: {functional_id}')
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
    
    def on_item_changed(self, item):
        """Обработка изменения ячейки в таблице"""
        row = item.row()
        col = item.column()
        
        # Редактируемые колонки: Alias(1), Title(2), Segment(8)
        if col not in [1, 2, 8]:
            return
        
        functional_id = self.table.item(row, 0).text()
        db_item = self.session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
        
        if not db_item:
            return
        
        new_value = item.text().strip()
        
        try:
            if col == 1:  # Alias
                db_item.alias_tag = new_value if new_value else None
            elif col == 2:  # Title
                if not new_value:
                    QMessageBox.warning(self, 'Ошибка', 'Title не может быть пустым')
                    item.setText(db_item.title)
                    return
                db_item.title = new_value
            elif col == 8:  # Segment
                db_item.segment = new_value if new_value else None
            
            self.session.commit()
            self.statusBar().showMessage(f'✅ Сохранено: {functional_id}')
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
    
    def on_selection_changed(self):
        """Обработка выбора строки в таблице"""
        selected = self.table.currentRow()
        if selected >= 0:
            functional_id = self.table.item(selected, 0).text()
            item = self.session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
            if item:
                self.mini_graph.update_graph(item.id)
        else:
            self.mini_graph.clear_graph()
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        module_filter = self.module_filter.currentText()
        epic_filter = self.epic_filter.currentText()
        segment_filter = self.segment_filter.currentText()
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
            
            # Фильтр по Type
            if type_filter and show:
                type_cell = self.table.item(row, 3)
                show = show and (type_cell and type_cell.text() == type_filter)
            
            # Фильтр по Module
            if module_filter and show:
                module_cell = self.table.item(row, 4)
                show = show and (module_cell and module_cell.text() == module_filter)
            
            # Фильтр по Epic
            if epic_filter and show:
                epic_cell = self.table.item(row, 5)
                show = show and (epic_cell and epic_cell.text() == epic_filter)
            
            # Фильтр по Segment
            if segment_filter and show:
                segment_cell = self.table.item(row, 8)
                show = show and (segment_cell and segment_cell.text() == segment_filter)
            
            # Фильтр по QA
            if qa_filter and show:
                qa_cell = self.table.item(row, 6)
                show = show and (qa_cell and qa_cell.text() == qa_filter)
            
            # Фильтр по Dev
            if dev_filter and show:
                dev_cell = self.table.item(row, 7)
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
        from src.ui.graph_view_new import GraphViewWindow
        graph_window = GraphViewWindow(self)
        graph_window.show()
    
    def open_dict_manager(self):
        """Открыть управление справочниками"""
        from src.ui.dialogs.dictionary_manager import DictionaryManagerWindow
        manager = DictionaryManagerWindow(self)
        manager.show()
    
    def open_bdd_manager(self):
        """Открыть BDD Feature Manager"""
        from src.ui.dialogs.bdd_manager import BDDFeatureManager
        manager = BDDFeatureManager(self)
        manager.show()
    
    def generate_bdd_features(self):
        """Генерация BDD Feature файлов"""
        from src.bdd.feature_generator import FeatureGenerator
        from pathlib import Path
        
        # Выбор директории
        output_dir = QFileDialog.getExistingDirectory(
            self, 'Выберите директорию для сохранения feature файлов', ''
        )
        
        if not output_dir:
            return
        
        # Генерируем для всех элементов или только для Feature/Story?
        reply = QMessageBox.question(
            self, 'Генерация Feature файлов',
            'Генерировать для всех элементов?\n\n'
            'Yes - все элементы\n'
            'No - только Feature и Story',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Cancel:
            return
        
        # Фильтруем элементы
        if reply == QMessageBox.StandardButton.Yes:
            items = self.session.query(FunctionalItem).all()
        else:
            items = self.session.query(FunctionalItem).filter(
                FunctionalItem.type.in_(['Feature', 'Story'])
            ).all()
        
        if not items:
            QMessageBox.information(self, 'Информация', 'Нет элементов для генерации')
            return
        
        # Генерируем
        try:
            saved_files = FeatureGenerator.batch_generate(items, Path(output_dir))
            QMessageBox.information(
                self, 'Успех',
                f'✅ Сгенерировано {len(saved_files)} feature файлов\n\n'
                f'Директория: {output_dir}'
            )
            self.statusBar().showMessage(f'✅ Сгенерировано {len(saved_files)} feature файлов')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сгенерировать:\n{e}')
    
    def on_tab_changed(self, index: int):
        """Обработка смены таба"""
        tab_names = ['Таблица', 'Граф', 'BDD', 'Трассировки', 'INFRA']
        if 0 <= index < len(tab_names):
            self.statusBar().showMessage(f'Активная вкладка: {tab_names[index]}')
    
    def save_data(self):
        """Сохранить данные"""
        try:
            self.session.commit()
            self.statusBar().showMessage('✅ Данные сохранены')
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
    
    def export_data(self):
        """Экспорт данных (CSV или Excel)"""
        reply = QMessageBox.question(
            self, 'Экспорт',
            'Выберите формат экспорта:\n\n'
            'Yes - CSV\n'
            'No - Excel',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Cancel:
            return
        
        if reply == QMessageBox.StandardButton.Yes:
            self.export_csv()
        else:
            self.export_excel()
    
    def import_data(self):
        """Импорт данных (CSV)"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Выберите CSV файл', '', 'CSV Files (*.csv);;All Files (*)'
        )
        
        if not file_path:
            return
        
        try:
            from scripts.import_csv_full import import_from_csv
            count = import_from_csv(file_path, self.session)
            QMessageBox.information(
                self, 'Успех',
                f'✅ Импортировано: {count} элементов'
            )
            self.load_data()
            self.statusBar().showMessage(f'✅ Импортировано: {count} элементов')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось импортировать:\n{e}')
    
    def export_csv(self):
        """Экспорт в CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить CSV', 'functional_items.csv', 'CSV Files (*.csv)'
        )
        
        if not file_path:
            return
        
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'FuncID', 'Alias', 'Title', 'Type', 'Module', 'Epic', 'QA', 'Dev', 'Segment', 'Crit', 'Focus'
                ])
                
                for item in self.current_items:
                    writer.writerow([
                        item.functional_id,
                        item.alias_tag or '',
                        item.title or '',
                        item.type or '',
                        item.module or '',
                        item.epic or '',
                        item.responsible_qa.name if item.responsible_qa else '',
                        item.responsible_dev.name if item.responsible_dev else '',
                        item.segment or '',
                        '1' if item.is_crit else '0',
                        '1' if item.is_focus else '0'
                    ])
            
            QMessageBox.information(self, 'Успех', f'✅ Экспортировано: {len(self.current_items)} элементов')
            self.statusBar().showMessage(f'✅ Экспорт в CSV: {file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось экспортировать:\n{e}')
    
    def export_excel(self):
        """Экспорт в Excel"""
        QMessageBox.information(self, 'Excel Export', 'Экспорт в Excel будет реализован позже')
    
    def sync_zoho(self):
        """Синхронизация с Zoho"""
        QMessageBox.information(self, 'Zoho Sync', 'Синхронизация с Zoho будет реализована позже')
    
    def closeEvent(self, event):
        self.session.close()
        event.accept()


if __name__ == '__main__':
    # Инициализировать БД при первом запуске
    from src.db.database import init_db, DATABASE_PATH, engine
    from sqlalchemy import inspect
    
    db_needs_init = False
    
    # Проверяем существование файла БД
    if not DATABASE_PATH.exists() or DATABASE_PATH.stat().st_size == 0:
        logger.warning(f'⚠️  БД не найдена или пуста: {DATABASE_PATH}')
        db_needs_init = True
    else:
        # Проверяем наличие таблиц
        try:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            required_tables = ['functional_items', 'users', 'functional_item_relations', 'dictionaries']
            missing_tables = [t for t in required_tables if t not in tables]
            if missing_tables:
                logger.warning(f'⚠️  Отсутствуют таблицы: {missing_tables}')
                db_needs_init = True
        except Exception as e:
            logger.error(f'❌ Ошибка проверки БД: {e}')
            db_needs_init = True
    
    if db_needs_init:
        logger.info('⚙️  Инициализирую БД...')
        init_db()
        logger.info('✅ БД инициализирована')
    else:
        logger.info(f'✅ БД готова: {DATABASE_PATH}')
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
