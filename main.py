import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Импорт утилит
from src.utils.funcid_generator import generate_funcid, make_unique_funcid, suggest_children

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
        self.parent_widget = parent  # Сохраняем для диалогов
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
        
        # Hint для Segment
        self.segment_hint = QLabel('<i>Применяется только для Feature, Story, Service, Page, Element</i>')
        self.segment_hint.setStyleSheet('color: gray; font-size: 9pt;')
        self.segment_hint.setWordWrap(True)
        basic_layout.addRow('', self.segment_hint)
        
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
        
        # Кнопки создания дочерних элементов (если элемент не новый)
        if not self.is_new and self.item.type:
            child_buttons_widget = QWidget()
            child_buttons_layout = QHBoxLayout(child_buttons_widget)
            child_buttons_layout.addWidget(QLabel('<b>➕ Создать дочерний:</b>'))
            
            # Определяем подходящие типы дочерних
            child_types = {
                'Module': ['Epic'],
                'Epic': ['Feature'],
                'Feature': ['Story', 'Page', 'Element'],
                'Story': ['Element'],
                'Page': ['Element'],
                'Service': [],
                'Element': [],
            }
            
            for child_type in child_types.get(self.item.type, []):
                btn = QPushButton(f'{child_type}')
                btn.setStyleSheet('background: #e0e0e0; padding: 5px 10px;')
                btn.clicked.connect(lambda checked, t=child_type: self.create_child_from_editor(t))
                child_buttons_layout.addWidget(btn)
            
            if not child_types.get(self.item.type, []):
                child_buttons_layout.addWidget(QLabel('(нет дочерних типов)'))
            
            child_buttons_layout.addStretch()
            tabs.addTab(child_buttons_widget, '👶 Дочерние')
        
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
        
        resp_layout.addRow('', QLabel(''))
        
        # Consulted - множественный выбор
        consulted_label = QLabel('Consulted (консультанты):')
        resp_layout.addRow(consulted_label)
        
        self.consulted_list = QListWidget()
        self.consulted_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.consulted_list.setMaximumHeight(100)
        for u in raci_users:
            self.consulted_list.addItem(u.name)
        resp_layout.addRow(self.consulted_list)
        
        consulted_hint = QLabel('<i>Удерживайте Ctrl для множественного выбора</i>')
        consulted_hint.setStyleSheet('color: gray; font-size: 9pt;')
        resp_layout.addRow('', consulted_hint)
        
        # Informed - множественный выбор
        informed_label = QLabel('Informed (информируемые):')
        resp_layout.addRow(informed_label)
        
        self.informed_list = QListWidget()
        self.informed_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.informed_list.setMaximumHeight(100)
        for u in raci_users:
            self.informed_list.addItem(u.name)
        resp_layout.addRow(self.informed_list)
        
        informed_hint = QLabel('<i>Удерживайте Ctrl для множественного выбора</i>')
        informed_hint.setStyleSheet('color: gray; font-size: 9pt;')
        resp_layout.addRow('', informed_hint)
        
        # Загрузка текущих значений Consulted и Informed
        if self.item.consulted_ids:
            import json
            try:
                consulted_user_ids = json.loads(self.item.consulted_ids)
                consulted_names = [u.name for u in raci_users if u.id in consulted_user_ids]
                for i in range(self.consulted_list.count()):
                    item_widget = self.consulted_list.item(i)
                    if item_widget.text() in consulted_names:
                        item_widget.setSelected(True)
            except (json.JSONDecodeError, TypeError):
                pass
        
        if self.item.informed_ids:
            import json
            try:
                informed_user_ids = json.loads(self.item.informed_ids)
                informed_names = [u.name for u in raci_users if u.id in informed_user_ids]
                for i in range(self.informed_list.count()):
                    item_widget = self.informed_list.item(i)
                    if item_widget.text() in informed_names:
                        item_widget.setSelected(True)
            except (json.JSONDecodeError, TypeError):
                pass
        
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
        
        # Вкладка 5: Инфраструктура
        infra_tab = QWidget()
        infra_layout = QFormLayout(infra_tab)
        
        # Container (для Service)
        self.container_edit = QLineEdit(self.item.container or '')
        self.container_edit.setPlaceholderText('Docker container, K8s pod, etc.')
        infra_layout.addRow('Container:', self.container_edit)
        
        # Database (для Service)
        self.database_edit = QLineEdit(self.item.database or '')
        self.database_edit.setPlaceholderText('PostgreSQL, MongoDB, Redis, etc.')
        infra_layout.addRow('Database:', self.database_edit)
        
        # Subsystems involved
        self.subsystems_edit = QTextEdit(self.item.subsystems_involved or '')
        self.subsystems_edit.setMaximumHeight(60)
        self.subsystems_edit.setPlaceholderText('Задействованные подсистемы (через запятую)')
        infra_layout.addRow('Subsystems:', self.subsystems_edit)
        
        # External services
        self.external_services_edit = QTextEdit(self.item.external_services or '')
        self.external_services_edit.setMaximumHeight(60)
        self.external_services_edit.setPlaceholderText('Внешние сервисы (Stripe, AWS S3, etc.)')
        infra_layout.addRow('External Services:', self.external_services_edit)
        
        # Custom fields (JSON)
        self.custom_fields_edit = QTextEdit(self.item.custom_fields or '')
        self.custom_fields_edit.setMaximumHeight(80)
        self.custom_fields_edit.setPlaceholderText('{"key": "value", ...}')
        self.custom_fields_edit.setStyleSheet('font-family: Consolas, monospace;')
        infra_layout.addRow('Custom Fields (JSON):', self.custom_fields_edit)
        
        tabs.addTab(infra_tab, '🏭 Инфра')
        
        # Вкладка 6: Дополнительные поля (скрытые по типу)
        advanced_tab = QWidget()
        advanced_layout = QFormLayout(advanced_tab)
        
        # Здесь будут скрытые по типу поля
        # Module → epic, feature, segment
        # Epic → feature, segment
        # Feature → segment
        # Они будут добавляться динамически в on_type_changed
        
        # Module (скрыто по умолчанию, если не Module)
        self.advanced_module_combo = QComboBox()
        self.advanced_module_combo.setEditable(True)
        self.populate_combo(self.advanced_module_combo, 'module')
        self.advanced_module_label = QLabel('Module:')
        advanced_layout.addRow(self.advanced_module_label, self.advanced_module_combo)
        
        # Epic
        self.advanced_epic_combo = QComboBox()
        self.advanced_epic_combo.setEditable(True)
        self.populate_combo(self.advanced_epic_combo, 'epic')
        self.advanced_epic_label = QLabel('Epic:')
        advanced_layout.addRow(self.advanced_epic_label, self.advanced_epic_combo)
        
        # Feature
        self.advanced_feature_combo = QComboBox()
        self.advanced_feature_combo.setEditable(True)
        self.populate_combo(self.advanced_feature_combo, 'feature')
        self.advanced_feature_label = QLabel('Feature:')
        advanced_layout.addRow(self.advanced_feature_label, self.advanced_feature_combo)
        
        # Segment
        self.advanced_segment_combo = QComboBox()
        self.advanced_segment_combo.addItems(['', 'UI', 'UX/CX', 'API', 'Backend', 'Database', 'Integration', 'Security', 'Performance'])
        if self.item.segment:
            self.advanced_segment_combo.setCurrentText(self.item.segment)
        self.advanced_segment_label = QLabel('Segment:')
        advanced_layout.addRow(self.advanced_segment_label, self.advanced_segment_combo)
        
        # Подсказка
        adv_hint = QLabel('<i>Здесь доступны поля, скрытые для текущего типа сущности</i>')
        adv_hint.setStyleSheet('color: gray; font-size: 9pt;')
        adv_hint.setWordWrap(True)
        advanced_layout.addRow('', adv_hint)
        
        tabs.addTab(advanced_tab, '🔧 Дополнительные')
        self.advanced_tab = advanced_tab
        
        main_layout.addWidget(tabs)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        # Применяем конфигурацию для текущего типа
        self.on_type_changed(self.type_combo.currentText())
    
    def populate_combo(self, combo, field_name, allow_create=True):
        """Заполняет комбобокс значениями из СУЩНОСТЕЙ соответствующего типа"""
        combo.clear()
        combo.addItem('')
        
        # Маппинг поля к типу сущности
        field_to_type = {
            'module': 'Module',
            'epic': 'Epic',
            'feature': 'Feature',
            'story': 'Story',
            'page': 'Page',
        }
        
        entity_type = field_to_type.get(field_name)
        
        if entity_type:
            # Берём Title сущностей соответствующего типа
            query = self.session.query(FunctionalItem.title).filter(
                FunctionalItem.type == entity_type
            ).order_by(FunctionalItem.title)
        else:
            # Старое поведение для остальных полей
            query = self.session.query(getattr(FunctionalItem, field_name)).filter(
                getattr(FunctionalItem, field_name).isnot(None)
            ).distinct().order_by(getattr(FunctionalItem, field_name))

        values = [v[0] for v in query.all()]
        combo.addItems(values)
        
        # Добавляем "[+ Create new]" если разрешено
        if allow_create:
            combo.insertSeparator(values.count() + 1)
            combo.addItem(f'[+ Create new {entity_type or field_name.title()}...]')

        current_value = getattr(self.item, field_name)
        if current_value:
            combo.setCurrentText(current_value)
        
        # Подключаем обработчик выбора
        if allow_create:
            combo.currentTextChanged.connect(lambda text: self.on_combo_selected(text, field_name, entity_type))
    
    def on_combo_selected(self, text, field_name, entity_type):
        """Обработка выбора '[+ Create new...]'"""
        if not text or not text.startswith('[+ Create'):
            return
        
        # Сбрасываем выбор
        combo = getattr(self, f'{field_name}_combo', None)
        if combo:
            combo.setCurrentIndex(0)
        
        # Открываем диалог создания новой сущности
        from src.models import FunctionalItem
        new_entity = FunctionalItem(
            title='',
            type=entity_type,
        )
        
        dialog = DynamicEditDialog(new_entity, self.session, self.parent_widget)
        if dialog.exec():
            try:
                self.session.add(new_entity)
                self.session.commit()
                
                # Обновляем комбобокс и выбираем созданное
                self.populate_combo(combo, field_name)
                combo.setCurrentText(new_entity.title)
                
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self.parent_widget, 'Ошибка', f'Не удалось создать:\n{e}')
    
    def on_type_changed(self, item_type):
        """Показывает/скрывает поля в зависимости от типа"""
        config = get_field_config_for_type(item_type)
        
        # Показываем/скрываем иерархические поля на основной вкладке
        for field in ['module', 'epic', 'feature']:
            if field in self.field_widgets:
                label, widget = self.field_widgets[field]
                visible = field not in config['hide']
                label.setVisible(visible)
                widget.setVisible(visible)
        
        # Segment отдельно - только для типов с has_segment=True
        if 'segment' in self.field_widgets:
            label, widget = self.field_widgets['segment']
            has_segment = config.get('has_segment', False)
            label.setVisible(has_segment)
            widget.setVisible(has_segment)
            
            if hasattr(self, 'segment_hint'):
                self.segment_hint.setVisible(has_segment)
                if has_segment:
                    self.segment_hint.setText('<i>Применяется для Feature, Story, Service, Page, Element</i>')
            
            if not has_segment:
                widget.setCurrentText('')
        
        # Управляем видимостью полей в "Дополнительных полях"
        # Показываем только те, что скрыты на основной вкладке
        has_hidden_fields = False
        
        if hasattr(self, 'advanced_module_label'):
            # Module - показываем в доп. полях, если скрыт на основной
            show_in_advanced = 'module' in config['hide']
            self.advanced_module_label.setVisible(show_in_advanced)
            self.advanced_module_combo.setVisible(show_in_advanced)
            if show_in_advanced:
                has_hidden_fields = True
            
        if hasattr(self, 'advanced_epic_label'):
            show_in_advanced = 'epic' in config['hide']
            self.advanced_epic_label.setVisible(show_in_advanced)
            self.advanced_epic_combo.setVisible(show_in_advanced)
            if show_in_advanced:
                has_hidden_fields = True
            
        if hasattr(self, 'advanced_feature_label'):
            show_in_advanced = 'feature' in config['hide']
            self.advanced_feature_label.setVisible(show_in_advanced)
            self.advanced_feature_combo.setVisible(show_in_advanced)
            if show_in_advanced:
                has_hidden_fields = True
            
        if hasattr(self, 'advanced_segment_label'):
            show_in_advanced = not config.get('has_segment', False)
            self.advanced_segment_label.setVisible(show_in_advanced)
            self.advanced_segment_combo.setVisible(show_in_advanced)
            if show_in_advanced:
                has_hidden_fields = True
        
        # Скрываем/показываем вкладку "Дополнительные поля" в зависимости от наличия скрытых полей
        if hasattr(self, 'advanced_tab'):
            tab_widget = self.advanced_tab.parent()
            if isinstance(tab_widget, QTabWidget):
                index = tab_widget.indexOf(self.advanced_tab)
                tab_widget.setTabVisible(index, has_hidden_fields)
        
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
        """Сохранение с валидацией и авто-генерацией FuncID"""
        # Валидация обязательных полей
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Title обязателен')
            return
        
        # Авто-генерация FuncID для новых элементов
        if self.is_new:
            title = self.title_edit.text().strip()
            item_type = self.type_combo.currentText()
            
            # Получаем иерархию из полей
            module = self.module_combo.currentText().strip() if hasattr(self, 'module_combo') else None
            epic = self.epic_combo.currentText().strip() if hasattr(self, 'epic_combo') else None
            feature = self.feature_combo.currentText().strip() if hasattr(self, 'feature_combo') else None
            
            # Генерируем FuncID
            generated_funcid = generate_funcid(
                item_type=item_type,
                title=title,
                module=module,
                epic=epic,
                feature=feature
            )
            
            # Делаем уникальным
            unique_funcid = make_unique_funcid(generated_funcid, self.session)
            
            # Устанавливаем в поле (только если поле было пустое)
            if not self.functional_id_edit.text().strip():
                self.functional_id_edit.setText(unique_funcid)
        
        # Валидация FuncID
        if not self.functional_id_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Functional ID обязателен')
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
        
        # Иерархия и Segment - берем из основных полей или из дополнительных
        config = get_field_config_for_type(self.item.type)
        
        # Module
        if 'module' not in config['hide']:
            self.item.module = self.module_combo.currentText().strip() or None
        elif hasattr(self, 'advanced_module_combo'):
            # Берем из дополнительных полей
            self.item.module = self.advanced_module_combo.currentText().strip() or None
        else:
            self.item.module = None
        
        # Epic
        if 'epic' not in config['hide']:
            self.item.epic = self.epic_combo.currentText().strip() or None
        elif hasattr(self, 'advanced_epic_combo'):
            self.item.epic = self.advanced_epic_combo.currentText().strip() or None
        else:
            self.item.epic = None
        
        # Feature
        if 'feature' not in config['hide']:
            self.item.feature = self.feature_combo.currentText().strip() or None
        elif hasattr(self, 'advanced_feature_combo'):
            self.item.feature = self.advanced_feature_combo.currentText().strip() or None
        else:
            self.item.feature = None
        
        # Segment
        if config.get('has_segment', False):
            self.item.segment = self.segment_combo.currentText() or None
        elif hasattr(self, 'advanced_segment_combo'):
            self.item.segment = self.advanced_segment_combo.currentText() or None
        else:
            self.item.segment = None
        
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
        
        # Сохранение Consulted и Informed
        import json
        
        # Consulted
        consulted_items = self.consulted_list.selectedItems()
        consulted_names = [item.text() for item in consulted_items]
        consulted_users = [u for u in self.session.query(User).filter(User.name.in_(consulted_names)).all()]
        self.item.consulted_ids = json.dumps([u.id for u in consulted_users]) if consulted_users else None
        
        # Informed
        informed_items = self.informed_list.selectedItems()
        informed_names = [item.text() for item in informed_items]
        informed_users = [u for u in self.session.query(User).filter(User.name.in_(informed_names)).all()]
        self.item.informed_ids = json.dumps([u.id for u in informed_users]) if informed_users else None
        
        # Покрытие
        if config['has_coverage']:
            self.item.test_cases_linked = self.test_cases_edit.toPlainText().strip() or None
            self.item.automation_status = self.automation_combo.currentText() or None
            self.item.documentation_links = self.docs_edit.toPlainText().strip() or None
        
        # Дополнительные поля
        if hasattr(self, 'container_edit'):
            self.item.container = self.container_edit.text().strip() or None
        if hasattr(self, 'database_edit'):
            self.item.database = self.database_edit.text().strip() or None
        if hasattr(self, 'subsystems_edit'):
            self.item.subsystems_involved = self.subsystems_edit.toPlainText().strip() or None
        if hasattr(self, 'external_services_edit'):
            self.item.external_services = self.external_services_edit.toPlainText().strip() or None
        if hasattr(self, 'custom_fields_edit'):
            self.item.custom_fields = self.custom_fields_edit.toPlainText().strip() or None
        
        # Сохраняем в БД
        self.session.add(self.item)
        self.session.commit()
        
        # Сигнал об успешном сохранении (для обновления выпадающих списков)
        self.accept()
        
        # Показывем уведомление
        if self.is_new:
            QMessageBox.information(
                self, 'Успех',
                f'✅ Элемент создан\nFuncID: {self.item.functional_id}'
            )
    
    def create_child_from_editor(self, child_type):
        """Создание дочернего элемента из редактора"""
        # Создаём новый элемент с иерархией от текущего
        new_item = FunctionalItem()
        
        # Устанавливаем иерархию и parent_id
        if self.item.type == 'Module':
            new_item.module = self.item.title
            new_item.parent_id = self.item.id
        elif self.item.type == 'Epic':
            new_item.module = self.item.module
            new_item.epic = self.item.title
            new_item.parent_id = self.item.id
        elif self.item.type == 'Feature':
            new_item.module = self.item.module
            new_item.epic = self.item.epic
            new_item.feature = self.item.title
            new_item.parent_id = self.item.id
        elif self.item.type == 'Story':
            new_item.module = self.item.module
            new_item.epic = self.item.epic
            new_item.feature = self.item.feature
            new_item.story = self.item.title
            new_item.parent_id = self.item.id
        elif self.item.type == 'Page':
            new_item.module = self.item.module
            new_item.epic = self.item.epic
            new_item.feature = self.item.feature
            new_item.page = self.item.title
            new_item.parent_id = self.item.id
        
        # Устанавливаем тип
        new_item.type = child_type
        
        # Авто-сегмент
        segment_map = {
            'Story': 'UX/CX',
            'Page': 'UI',
            'Element': 'UI',
            'Feature': 'Backend',
        }
        new_item.segment = segment_map.get(child_type, '')
        
        # Открываем редактор
        dialog = DynamicEditDialog(new_item, self.session, self.parent_widget)
        if dialog.exec():
            try:
                self.session.add(new_item)
                self.session.commit()
                self.accept()  # Закрываем текущий редактор
                self.parent_widget.load_data()  # Обновляем таблицу
                QMessageBox.information(
                    self.parent_widget, 'Успех',
                    f'✅ Создан {child_type}: {new_item.functional_id}'
                )
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self.parent_widget, 'Ошибка', f'Не удалось создать:\n{e}')


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
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)  # Изменено: редактирование по двойному клику
        self.table.doubleClicked.connect(self.edit_item)
        
        # Inline делегаты (после load_data будет настроено)
        self.inline_delegates = {}
        
        layout.addWidget(self.table)

        self.statusBar().showMessage('Готов')
    
    def load_data(self):
        """Загрузить все сущности"""
        self.current_items = self.session.query(FunctionalItem).order_by(FunctionalItem.type, FunctionalItem.functional_id).all()
        self.populate_filters()
        self.filter_by_type(self.current_filter_type)
        self.setup_inline_editing()  # Настройка inline делегатов
        self.statusBar().showMessage(f'✅ Загружено: {len(self.current_items)} записей')
    
    def setup_inline_editing(self):
        """Настройка inline редактирования для таблицы"""
        from src.ui.delegates.inline_editors import InlineEditDelegate, InlineSegmentDelegate, InlineCheckDelegate, InlineUserDelegate
        
        # Получаем список пользователей для ComboBox
        users = [u.name for u in self.session.query(User).filter_by(is_active=1).order_by(User.name).all()]
        
        # Создаём делегаты
        # Col 1: Title (inline edit)
        self.table.setItemDelegateForColumn(1, InlineEditDelegate(self, on_commit=self.on_inline_edit))
        
        # Col 5: isCrit (checkbox)
        self.table.setItemDelegateForColumn(5, InlineCheckDelegate(self, on_commit=self.on_inline_edit))
        
        # Col 6: isFocus (checkbox)
        self.table.setItemDelegateForColumn(6, InlineCheckDelegate(self, on_commit=self.on_inline_edit))
    
    def on_inline_edit(self, row, col, value):
        """Обработка inline редактирования"""
        from src.models import FunctionalItem
        
        if row >= len(self.current_items):
            return
        
        item = self.current_items[row]
        
        try:
            # Определяем поле по колонке
            if col == 1:  # Title
                item.title = value
            elif col == 5:  # isCrit
                item.is_crit = value
            elif col == 6:  # isFocus
                item.is_focus = value
            
            self.session.commit()
            self.statusBar().showMessage(f'✅ Сохранено: {item.functional_id}')
            
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
    
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
        
        # Инициализация мультипроектности
        from src.models.project_config import ProjectManager
        from src.db.database_manager import get_database_manager
        from src.utils.migration import check_and_migrate
        
        config_dir = project_root / 'data' / 'config'
        
        # Проверка миграции
        migrated, msg = check_and_migrate(project_root, self.show_migration_dialog)
        if migrated:
            QMessageBox.information(self, 'Миграция завершена', msg)
        
        # Инициализация менеджеров
        self.project_manager = ProjectManager(config_dir)
        self.db_manager = get_database_manager()
        
        # Загрузка текущего проекта
        current_project = self.project_manager.get_current_project()
        
        if not current_project:
            # Нет проектов - показываем selector
            self.show_project_selector_startup()
            current_project = self.project_manager.get_current_project()
            
            if not current_project:
                # Пользователь отменил выбор - выход
                QMessageBox.warning(self, 'Выход', 'Не выбран проект. Приложение будет закрыто.')
                sys.exit(0)
        
        # Подключаемся к БД проекта
        if not self.db_manager.connect_to_database(current_project.database_path):
            QMessageBox.critical(self, 'Ошибка', f'Не удалось подключиться к БД проекта:\n{current_project.database_path}')
            sys.exit(1)
        
        # Проверяем наличие таблиц, инициализируем если нужно
        self.ensure_database_initialized()
        
        # Теперь можно создавать session и инициализировать UI
        self.session = self.db_manager.get_session()
        self.current_items = []
        self.current_filter = 'all'  # all, crit, focus
        self.init_ui()
        self.load_data()
        
        # Проверка на пустую базу — показываем Starter Wizard
        if not self.current_items:
            self.show_starter_wizard()
    
    def init_ui(self):
        self.setGeometry(100, 100, 1400, 900)
        self.update_window_title()  # Устанавливаем заголовок с названием проекта
        
        # === НОВОЕ МЕНЮ ===
        menubar = self.menuBar()
        
        # Меню "Проект"
        file_menu = menubar.addMenu('🗂️ Проект')
        
        # Проекты
        switch_project_action = QAction('🗂️ Переключить проект...', self)
        switch_project_action.setShortcut('Ctrl+Shift+P')
        switch_project_action.triggered.connect(self.switch_project)
        file_menu.addAction(switch_project_action)
        
        new_project_action = QAction('➕ Новый проект...', self)
        new_project_action.triggered.connect(self.create_new_project)
        file_menu.addAction(new_project_action)
        
        delete_project_action = QAction('🗑️ Удалить проект...', self)
        delete_project_action.triggered.connect(self.delete_project)
        file_menu.addAction(delete_project_action)

        project_settings_action = QAction('⚙️ Настройки проекта...', self)
        project_settings_action.triggered.connect(self.open_project_settings)
        file_menu.addAction(project_settings_action)
        
        file_menu.addSeparator()
        
        save_action = QAction('💾 Сохранить', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_data)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Экспорт
        export_google_action = QAction('📤 Экспорт В Google Sheets', self)
        export_google_action.triggered.connect(self.export_google_sheets)
        file_menu.addAction(export_google_action)
        
        export_csv_action = QAction('📤 Экспорт В CSV', self)
        export_csv_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_csv_action)
        
        file_menu.addSeparator()
        
        # Импорт
        import_google_action = QAction('📥 Импорт ИЗ Google Sheets', self)
        import_google_action.triggered.connect(self.import_google_sheets)
        file_menu.addAction(import_google_action)
        
        import_csv_action = QAction('📥 Импорт ИЗ CSV', self)
        import_csv_action.triggered.connect(self.import_data)
        file_menu.addAction(import_csv_action)
        
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
        
        add_action = QAction('➞ Добавить', self)
        add_action.setShortcut('Ctrl+N')
        add_action.triggered.connect(self.add_item)
        edit_menu.addAction(add_action)
        
        # Редактировать и Удалить удалены - доступны через контекстное меню и Actions
        # edit_item_action - теперь через двойной клик / правую кнопку / кнопку Actions
        # delete_action - теперь через правую кнопку / кнопку Actions
        
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
        
        # Стартовый помощник (Starter Wizard)
        starter_wizard_action = QAction('🚀 Помощник по наполнению базы', self)
        starter_wizard_action.setShortcut('Ctrl+Shift+S')
        starter_wizard_action.triggered.connect(self.show_starter_wizard)
        tools_menu.addAction(starter_wizard_action)

        tools_menu.addSeparator()

        # Шаблоны отчётов
        report_templates_action = QAction('📋 Шаблоны отчётов', self)
        report_templates_action.triggered.connect(self.open_report_templates)
        tools_menu.addAction(report_templates_action)
        
        # Генератор отчётов
        report_generator_action = QAction('📊 Генератор отчётов', self)
        report_generator_action.setShortcut('Ctrl+R')
        report_generator_action.triggered.connect(self.open_report_generator)
        tools_menu.addAction(report_generator_action)
        
        tools_menu.addSeparator()
        
        # Граф связей
        graph_action = QAction('🔗 Граф связей', self)
        graph_action.setShortcut('Ctrl+G')
        graph_action.triggered.connect(self.open_graph_view)
        tools_menu.addAction(graph_action)
        
        tools_menu.addSeparator()
        
        sync_menu = tools_menu.addMenu('🔄 Синхронизация')
        
        sync_zoho_action = QAction('📋 Zoho Projects', self)
        sync_zoho_action.triggered.connect(self.sync_zoho_projects)
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
        
        # === TOOLBAR ===
        toolbar = QToolBar('Проект')
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Project selector
        toolbar.addWidget(QLabel('🗂️ Проект:'))
        
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(200)
        self.project_combo.currentIndexChanged.connect(self.on_project_combo_changed)
        toolbar.addWidget(self.project_combo)
        
        # Заполняем список проектов
        self.populate_project_combo()
        
        toolbar.addSeparator()
        
        # Quick actions
        refresh_action = QAction('🔄 Обновить', self)
        refresh_action.triggered.connect(self.load_data)
        toolbar.addAction(refresh_action)
        
        add_action = QAction('➡️ Добавить', self)
        add_action.triggered.connect(self.add_item)
        toolbar.addAction(add_action)
        
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
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            'FuncID', 'Alias', 'Title', 'Type', 'Module', 'Epic', 'Feature', 'QA', 'Dev', 'Segment', 'Crit', 'Focus', 'Actions'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Inline-редактирование по double-click для определённых колонок
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)
        self.table.itemChanged.connect(self.on_item_changed)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        # Контекстное меню для таблицы
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Двойной клик на Actions колонке (12) открывает карточку редактирования
        self.table.doubleClicked.connect(self.on_table_double_click)
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
        from src.utils.version import get_version_banner
        banner = get_version_banner(project_root)
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
            
            # Module - показываем ──┐ если item.type == 'Module'
            module_display = '──┐' if item.type == 'Module' else (item.module or '')
            module_item = QTableWidgetItem(module_display)
            module_item.setFlags(module_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 4, module_item)
            
            # Epic - показываем ──┐ если item.type == 'Epic'
            epic_display = '──┐' if item.type == 'Epic' else (item.epic or '')
            epic_item = QTableWidgetItem(epic_display)
            epic_item.setFlags(epic_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 5, epic_item)
            
            # Feature - показываем ──┐ если item.type == 'Feature'
            feature_display = '──┐' if item.type == 'Feature' else (item.feature or '')
            feature_item = QTableWidgetItem(feature_display)
            feature_item.setFlags(feature_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 6, feature_item)
            
            qa_item = QTableWidgetItem(item.responsible_qa.name if item.responsible_qa else '')
            qa_item.setFlags(qa_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 7, qa_item)
            
            dev_item = QTableWidgetItem(item.responsible_dev.name if item.responsible_dev else '')
            dev_item.setFlags(dev_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 8, dev_item)
            
            self.table.setItem(row_idx, 9, QTableWidgetItem(item.segment or ''))  # Редактируемый
            
            # Crit и Focus - чекбоксы
            crit_widget = QWidget()
            crit_layout = QHBoxLayout(crit_widget)
            crit_layout.setContentsMargins(0, 0, 0, 0)
            crit_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            crit_check = QCheckBox()
            crit_check.setChecked(bool(item.is_crit))
            crit_check.stateChanged.connect(lambda state, r=row_idx, c=10: self.on_checkbox_changed(r, c, state))
            crit_layout.addWidget(crit_check)
            self.table.setCellWidget(row_idx, 10, crit_widget)
            
            focus_widget = QWidget()
            focus_layout = QHBoxLayout(focus_widget)
            focus_layout.setContentsMargins(0, 0, 0, 0)
            focus_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            focus_check = QCheckBox()
            focus_check.setChecked(bool(item.is_focus))
            focus_check.stateChanged.connect(lambda state, r=row_idx, c=11: self.on_checkbox_changed(r, c, state))
            focus_layout.addWidget(focus_check)
            self.table.setCellWidget(row_idx, 11, focus_widget)
            
            # Actions - кнопки редактирования и удаления
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton('✏️')
            edit_btn.setFixedSize(30, 25)
            edit_btn.setToolTip('Редактировать')
            edit_btn.setStyleSheet('QPushButton { font-size: 14px; }')
            edit_btn.clicked.connect(lambda checked, r=row_idx: self.edit_item_by_row(r))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton('🗑️')
            delete_btn.setFixedSize(30, 25)
            delete_btn.setToolTip('Удалить')
            delete_btn.setStyleSheet('QPushButton { font-size: 14px; }')
            delete_btn.clicked.connect(lambda checked, r=row_idx: self.delete_item_by_row(r))
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row_idx, 12, actions_widget)
        
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
                    # Crit теперь в колонке 10 (было 9)
                    crit_widget = self.table.cellWidget(row, 10)
                    if crit_widget:
                        crit_check = crit_widget.findChild(QCheckBox)
                        show = crit_check and crit_check.isChecked()
                    else:
                        show = False
                elif self.current_filter == 'focus':
                    # Focus теперь в колонке 11 (было 10)
                    focus_widget = self.table.cellWidget(row, 11)
                    if focus_widget:
                        focus_check = focus_widget.findChild(QCheckBox)
                        show = focus_check and focus_check.isChecked()
                    else:
                        show = False
                
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

        # Редактируемые колонки: Alias(1), Title(2), Segment(8), isCrit(10), isFocus(11)
        if col not in [1, 2, 8, 10, 11]:
            return

        functional_id = self.table.item(row, 0).text()
        db_item = self.session.query(FunctionalItem).filter_by(functional_id=functional_id).first()

        if not db_item:
            return

        # Обработка checkbox (isCrit, isFocus)
        if col in [10, 11]:
            # Для checkbox используем текст "✓" или пустую строку
            new_value = 1 if item.text() == '✓' else 0
            
            try:
                if col == 10:  # isCrit
                    db_item.is_crit = new_value
                elif col == 11:  # isFocus
                    db_item.is_focus = new_value
                
                self.session.commit()
                self.statusBar().showMessage(f'✅ Сохранено: {functional_id}')
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
            return
        
        # Обработка текстовых полей
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
        """Фильтрация таблицы — ВСЕГДА из всех элементов"""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        module_filter = self.module_filter.currentText()
        epic_filter = self.epic_filter.currentText()
        segment_filter = self.segment_filter.currentText()
        qa_filter = self.qa_filter.currentText()
        dev_filter = self.dev_filter.currentText()

        # Фильтруем ВСЕ строки, а не только видимые
        for row in range(self.table.rowCount()):
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
                segment_cell = self.table.item(row, 9)  # Изменено: 8 → 9
                show = show and (segment_cell and segment_cell.text() == segment_filter)

            # Фильтр по QA
            if qa_filter and show:
                qa_cell = self.table.item(row, 7)  # Изменено: 6 → 7
                show = show and (qa_cell and qa_cell.text() == qa_filter)

            # Фильтр по Dev
            if dev_filter and show:
                dev_cell = self.table.item(row, 8)  # Изменено: 7 → 8
                show = show and (dev_cell and dev_cell.text() == dev_filter)

            self.table.setRowHidden(row, not show)
    
    def add_item(self):
        """Добавление нового элемента"""
        new_item = FunctionalItem()
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
        """Редактирование выбранного элемента"""
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
                    self.statusBar().showMessage(f'✅ Обновлён: {item.functional_id}')
                except Exception as e:
                    self.session.rollback()
                    QMessageBox.critical(self, 'Ошибка', f'Не удалось обновить:\n{e}')
    
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
    
    def edit_item_by_row(self, row_idx):
        """Редактирование элемента по номеру строки"""
        if row_idx < 0 or row_idx >= self.table.rowCount():
            return
        
        functional_id = self.table.item(row_idx, 0).text()
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
    
    def delete_item_by_row(self, row_idx):
        """Удаление элемента по номеру строки"""
        if row_idx < 0 or row_idx >= self.table.rowCount():
            return
        
        functional_id = self.table.item(row_idx, 0).text()
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
    
    def show_context_menu(self, position):
        """Показать контекстное меню для таблицы"""
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        menu = QMenu(self)

        # Создание дочернего элемента
        create_child_menu = menu.addMenu('➕ Создать дочерний')
        
        # Определяем тип текущего элемента и предлагаем подходящие дочерние
        type_cell = self.table.item(row, 3)  # Type column
        current_type = type_cell.text() if type_cell else ''
        
        child_types = {
            'Module': ['Epic'],
            'Epic': ['Feature'],
            'Feature': ['Story', 'Page', 'Element'],
            'Story': ['Element'],
            'Page': ['Element'],
            'Service': [],
            'Element': [],
        }
        
        for child_type in child_types.get(current_type, []):
            action = QAction(f'{child_type}', self)
            action.triggered.connect(lambda checked, t=child_type: self.create_child_item(row, t))
            create_child_menu.addAction(action)
        
        if not child_types.get(current_type, []):
            no_action = QAction('Нет дочерних типов', self)
            no_action.setEnabled(False)
            create_child_menu.addAction(no_action)
        
        menu.addSeparator()

        edit_action = QAction('✏️ Редактировать', self)
        edit_action.triggered.connect(lambda: self.edit_item_by_row(row))
        menu.addAction(edit_action)

        duplicate_action = QAction('📋 Дублировать', self)
        duplicate_action.triggered.connect(lambda: self.duplicate_item_by_row(row))
        menu.addAction(duplicate_action)

        menu.addSeparator()

        delete_action = QAction('🗑️ Удалить', self)
        delete_action.triggered.connect(lambda: self.delete_item_by_row(row))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def create_child_item(self, parent_row, child_type):
        """Создание дочернего элемента с авто-FuncID и связями"""
        parent_funcid = self.table.item(parent_row, 0).text()
        parent_item = self.session.query(FunctionalItem).filter_by(functional_id=parent_funcid).first()
        
        if not parent_item:
            return
        
        # Создаём новый элемент
        new_item = FunctionalItem()
        
        # Устанавливаем иерархию и parent_id
        if parent_item.type == 'Module':
            new_item.module = parent_item.title
            new_item.parent_id = parent_item.id
        elif parent_item.type == 'Epic':
            new_item.module = parent_item.module
            new_item.epic = parent_item.title
            new_item.parent_id = parent_item.id
        elif parent_item.type == 'Feature':
            new_item.module = parent_item.module
            new_item.epic = parent_item.epic
            new_item.feature = parent_item.title
            new_item.parent_id = parent_item.id
        elif parent_item.type == 'Story':
            new_item.module = parent_item.module
            new_item.epic = parent_item.epic
            new_item.feature = parent_item.feature
            new_item.story = parent_item.title
            new_item.parent_id = parent_item.id
        elif parent_item.type == 'Page':
            new_item.module = parent_item.module
            new_item.epic = parent_item.epic
            new_item.feature = parent_item.feature
            new_item.page = parent_item.title
            new_item.parent_id = parent_item.id
        
        # Устанавливаем тип
        new_item.type = child_type
        
        # Авто-сегмент в зависимости от типа дочернего
        segment_map = {
            'Story': 'UX/CX',
            'Page': 'UI',
            'Element': 'UI',
            'Feature': 'Backend',
        }
        new_item.segment = segment_map.get(child_type, '')
        
        # Открываем редактор (FuncID сгенерируется при сохранении)
        dialog = DynamicEditDialog(new_item, self.session, self)
        if dialog.exec():
            try:
                self.session.add(new_item)
                self.session.commit()
                self.load_data()
                self.statusBar().showMessage(f'✅ Создан {child_type}: {new_item.functional_id}')
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Не удалось создать:\n{e}')
    
    def on_table_double_click(self, index):
        """Обработка двойного клика — открыть карточку редактирования"""
        # Открываем карточку ТОЛЬКО при клике на Actions колонку (12)
        # Для остальных колонок работает inline редактирование
        if index.column() != 12:  # Не Actions column
            return  # Inline editing обработает

        row = index.row()
        self.edit_item_by_row(row)
    
    def duplicate_item_by_row(self, row_idx):
        """Дублирование элемента по номеру строки"""
        if row_idx < 0 or row_idx >= self.table.rowCount():
            return
        
        functional_id = self.table.item(row_idx, 0).text()
        original_item = self.session.query(FunctionalItem).filter_by(functional_id=functional_id).first()
        
        if original_item:
            # Создаем копию
            new_item = FunctionalItem(
                functional_id=f"{original_item.functional_id}.copy",
                alias_tag=f"{original_item.alias_tag}_copy" if original_item.alias_tag else None,
                title=f"{original_item.title} (copy)",
                type=original_item.type,
                description=original_item.description,
                parent_id=original_item.parent_id,
                module=original_item.module,
                epic=original_item.epic,
                feature=original_item.feature,
                segment=original_item.segment,
                is_crit=original_item.is_crit,
                is_focus=original_item.is_focus,
                responsible_qa_id=original_item.responsible_qa_id,
                responsible_dev_id=original_item.responsible_dev_id,
                accountable_id=original_item.accountable_id
            )
            
            # Открываем диалог редактирования для копии
            dialog = DynamicEditDialog(new_item, self.session, self)
            if dialog.exec():
                try:
                    self.session.add(new_item)
                    self.session.commit()
                    self.load_data()
                    self.statusBar().showMessage(f'✅ Дублировано: {new_item.functional_id}')
                except Exception as e:
                    self.session.rollback()
                    QMessageBox.critical(self, 'Ошибка', f'Не удалось дублировать:\n{e}')
    
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
        dialog = SettingsDialog(self.project_manager, self)
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
    
    def open_report_templates(self):
        """Открыть менеджер шаблонов отчётов"""
        from src.ui.dialogs.report_template_editor import TemplateManagerDialog
        manager = TemplateManagerDialog(self.session, self)
        manager.show()
    
    def open_report_generator(self):
        """Открыть генератор отчётов"""
        from src.ui.dialogs.report_generator_dialog import ReportGeneratorDialog
        dialog = ReportGeneratorDialog(self.session, self)
        dialog.exec()
    
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
    
    def export_google_sheets(self):
        """Экспорт в Google Sheets"""
        from src.ui.dialogs.google_export_simple import GoogleExportSimpleDialog
        dialog = GoogleExportSimpleDialog(self.session, self)
        dialog.exec()
    
    def import_google_sheets(self):
        """Импорт из Google Sheets"""
        from src.ui.dialogs.google_import_simple import GoogleImportSimpleDialog
        dialog = GoogleImportSimpleDialog(self.session, self)
        if dialog.exec():
            # Обновляем таблицу после импорта
            self.load_data()
            self.statusBar().showMessage('✅ Данные импортированы из Google Sheets')
    
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
    
    def sync_zoho_projects(self):
        """Синхронизация задач из Zoho Projects"""
        from src.ui.dialogs.zoho_sync_dialog import ZohoSyncDialog
        
        dialog = ZohoSyncDialog(self.session, self)
        if dialog.exec():
            # После успешной синхронизации можно обновить данные
            self.statusBar().showMessage('✅ Задачи Zoho синхронизированы')
    
    def ensure_database_initialized(self):
        """Проверка и инициализация БД если нужно"""
        from sqlalchemy import inspect
        
        try:
            inspector = inspect(self.db_manager.engine)
            tables = inspector.get_table_names()
            required_tables = ['functional_items', 'users']
            
            if not all(table in tables for table in required_tables):
                logger.info('⚠️  Отсутствуют необходимые таблицы, инициализирую БД...')
                self.db_manager.init_database()
                
                # Создаём дефолтного пользователя
                from src.models.user import User
                session = self.db_manager.get_session()
                try:
                    if session.query(User).count() == 0:
                        default_user = User(
                            name='Default User',
                            role='QA',
                            email='user@example.com',
                            is_active=1
                        )
                        session.add(default_user)
                        session.commit()
                        logger.info('✅ Дефолтный пользователь создан')
                finally:
                    session.close()
                
                logger.info('✅ БД инициализирована')
        except Exception as e:
            logger.error(f'❌ Ошибка проверки БД: {e}')
    
    def show_migration_dialog(self, message: str) -> bool:
        """Диалог подтверждения миграции"""
        reply = QMessageBox.question(
            None, 'Миграция структуры БД',
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def show_project_selector_startup(self):
        """Показать selector проектов при запуске"""
        from src.ui.dialogs.project_dialogs import ProjectSelectorDialog

        dialog = ProjectSelectorDialog(self.project_manager, None)
        if dialog.exec() and dialog.selected_project_id:
            self.project_manager.switch_project(dialog.selected_project_id)
    
    def show_starter_wizard(self):
        """Показать мастер наполнения базы для пустых проектов"""
        from src.ui.dialogs.starter_wizard import StarterWizard
        
        dialog = StarterWizard(self.session, self)
        if dialog.exec() and dialog.selected_template:
            try:
                created_count = dialog.apply_template()
                if created_count > 0:
                    QMessageBox.information(
                        self, '✅ Готово',
                        f'Создано элементов: {created_count}\n\nТеперь вы можете редактировать их в таблице.'
                    )
                    self.load_data()  # Обновляем таблицу
                    self.statusBar().showMessage(f'✅ Создано {created_count} элементов из шаблона')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось применить шаблон:\n{e}')
    
    def switch_project(self):
        """Переключение проекта"""
        from src.ui.dialogs.project_dialogs import ProjectSelectorDialog
        
        dialog = ProjectSelectorDialog(self.project_manager, self)
        if dialog.exec() and dialog.selected_project_id:
            current_project = self.project_manager.get_current_project()
            
            # Если выбран тот же проект - не переключаем
            if current_project and dialog.selected_project_id == current_project.id:
                self.statusBar().showMessage(f'🗂️ Уже в проекте: {current_project.name}')
                return
            
            # Закрываем текущую сессию
            if self.session:
                self.session.close()
            
            # Переключаемся
            self.project_manager.switch_project(dialog.selected_project_id)
            new_project = self.project_manager.get_current_project()
            
            # Переподключаемся к новой БД
            if self.db_manager.connect_to_database(new_project.database_path):
                self.session = self.db_manager.get_session()
                
                # Обновляем UI
                self.load_data()
                self.update_window_title()
                self.statusBar().showMessage(f'✅ Переключено на: {new_project.name}')
            else:
                QMessageBox.critical(
                    self, 'Ошибка',
                    f'Не удалось подключиться к БД проекта:\n{new_project.database_path}'
                )
    
    def create_new_project(self):
        """Создание нового проекта"""
        from src.ui.dialogs.project_dialogs import NewProjectDialog

        dialog = NewProjectDialog(self.project_manager, self)
        if dialog.exec() and dialog.created_project_id:
            # Спрашиваем, переключиться на новый проект?
            reply = QMessageBox.question(
                self, 'Переключиться?',
                f'Проект создан. Переключиться на него?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Закрываем текущую сессию
                if self.session:
                    self.session.close()

                # Переключаемся
                self.project_manager.switch_project(dialog.created_project_id)
                new_project = self.project_manager.get_current_project()

                if self.db_manager.connect_to_database(new_project.database_path):
                    self.ensure_database_initialized()
                    self.session = self.db_manager.get_session()
                    self.load_data()
                    self.update_window_title()
                    self.populate_project_combo()  # Обновляем combobox
                    self.statusBar().showMessage(f'✅ Работаем в проекте: {new_project.name}')
    
    def delete_project(self):
        """Удаление проекта"""
        current_project = self.project_manager.get_current_project()
        if not current_project:
            QMessageBox.warning(self, 'Ошибка', 'Нет активного проекта')
            return
        
        # Предупреждение
        reply = QMessageBox.warning(
            self,
            '⚠️ Удаление проекта',
            f'Вы уверены что хотите удалить проект "{current_project.name}"?\n\n'
            f'🗑️ Будет удалена папка: {Path(current_project.database_path).parent}\n'
            f'🗑️ Все данные будут потеряны!\n\n'
            f'Это действие НЕОБРАТИМО!',
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Нужно переключиться на другой проект перед удалением
        from src.ui.dialogs.project_dialogs import ProjectSelectorDialog
        
        dialog = ProjectSelectorDialog(self.project_manager, self)
        dialog.setWindowTitle('Выберите проект для переключения')
        
        if not dialog.exec() or not dialog.selected_project_id:
            QMessageBox.warning(self, 'Отменено', 'Удаление отменено')
            return
        
        # Переключаемся на другой проект
        self.project_manager.switch_project(dialog.selected_project_id)
        new_project = self.project_manager.get_current_project()
        
        # Закрываем текущую сессию
        if self.session:
            self.session.close()
        
        # Переподключаемся к новой БД
        if self.db_manager.connect_to_database(new_project.database_path):
            self.ensure_database_initialized()
            self.session = self.db_manager.get_session()
            
            # Удаляем старый проект
            try:
                self.project_manager.delete_project(current_project.id)
                self.load_data()
                self.update_window_title()
                self.populate_project_combo()
                self.statusBar().showMessage(f'🗑️ Проект "{current_project.name}" удалён')
                QMessageBox.information(self, 'Успех', f'✅ Проект "{current_project.name}" удалён')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить проект:\n{e}')
    
    def open_project_settings(self):
        """Настройки текущего проекта"""
        from src.ui.dialogs.project_dialogs import ProjectSettingsDialog
        
        current_project = self.project_manager.get_current_project()
        if not current_project:
            QMessageBox.warning(self, 'Ошибка', 'Нет активного проекта')
            return
        
        dialog = ProjectSettingsDialog(self.project_manager, current_project.id, self)
        if dialog.exec():
            # Обновляем WindowTitle и combobox если изменили название
            self.update_window_title()
            self.populate_project_combo()
    
    def populate_project_combo(self):
        """Заполнение combobox списком проектов"""
        if not hasattr(self, 'project_combo'):
            return
        
        # Блокируем сигналы чтобы не вызвать on_project_combo_changed
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        
        projects = self.project_manager.list_projects()
        current_project = self.project_manager.get_current_project()
        
        # Сортируем: сначала активные, потом по last_used
        active_projects = [p for p in projects if p.is_active]
        active_projects.sort(key=lambda p: p.last_used or '0', reverse=True)
        
        for project in active_projects:
            profile_emoji = '🏭' if project.settings_profile == 'production' else '🧪'
            self.project_combo.addItem(f'{profile_emoji} {project.name}', project.id)
        
        # Выбираем текущий проект
        if current_project:
            index = self.project_combo.findData(current_project.id)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)
        
        self.project_combo.blockSignals(False)
    
    def on_project_combo_changed(self, index):
        """Обработка смены проекта в combobox"""
        if index < 0:
            return
        
        project_id = self.project_combo.itemData(index)
        current_project = self.project_manager.get_current_project()
        
        # Если выбран тот же проект - ничего не делаем
        if current_project and project_id == current_project.id:
            return
        
        # Закрываем текущую сессию
        if self.session:
            self.session.close()
        
        # Переключаемся
        self.project_manager.switch_project(project_id)
        new_project = self.project_manager.get_current_project()
        
        # Переподключаемся к новой БД
        if self.db_manager.connect_to_database(new_project.database_path):
            self.ensure_database_initialized()
            self.session = self.db_manager.get_session()
            
            # Обновляем UI
            self.load_data()
            self.update_window_title()
            self.statusBar().showMessage(f'✅ Переключено на: {new_project.name}')
        else:
            QMessageBox.critical(
                self, 'Ошибка',
                f'Не удалось подключиться к БД проекта:\n{new_project.database_path}'
            )
            # Возвращаем предыдущий выбор
            self.populate_project_combo()
    
    def update_window_title(self):
        """Обновление заголовка окна с названием проекта"""
        banner = get_version_banner(project_root)
        current_project = self.project_manager.get_current_project()
        
        if current_project:
            profile_emoji = '🏭' if current_project.settings_profile == 'production' else '🧪'
            self.setWindowTitle(
                f'VoluptAS {banner} - {profile_emoji} {current_project.name}'
            )
        else:
            self.setWindowTitle(f'VoluptAS {banner} - Functional Coverage Management')
    
    def closeEvent(self, event):
        if self.session:
            self.session.close()
        if self.db_manager:
            self.db_manager.close()
        event.accept()


if __name__ == '__main__':
    # При мультипроектности инициализация БД происходит в MainWindow
    # или при создании нового проекта
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
