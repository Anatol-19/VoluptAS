"""
Report Generator Dialog

Диалог для генерации отчётов из шаблонов с подстановкой данных
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ReportGeneratorDialog(QDialog):
    """Диалог генерации отчёта"""
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.generated_content = None
        
        self.setWindowTitle('Генератор отчётов')
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)
        
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel(
            '📊 <b>Генератор отчётов из шаблонов</b><br>'
            'Выберите шаблон, укажите параметры и сгенерируйте отчёт с данными из БД.'
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # === Секция 1: Выбор шаблона ===
        template_group = QGroupBox('Шаблон отчёта')
        template_layout = QFormLayout(template_group)
        
        self.template_combo = QComboBox()
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        template_layout.addRow('* Шаблон:', self.template_combo)
        
        self.template_desc_label = QLabel()
        self.template_desc_label.setStyleSheet('color: gray; font-style: italic;')
        self.template_desc_label.setWordWrap(True)
        template_layout.addRow('', self.template_desc_label)
        
        layout.addWidget(template_group)
        
        # === Секция 2: Параметры генерации ===
        params_group = QGroupBox('Параметры генерации')
        params_layout = QFormLayout(params_group)
        
        # Milestone (для Zoho задач)
        self.milestone_edit = QLineEdit()
        self.milestone_edit.setPlaceholderText('Например: Sprint 24, v2.5')
        params_layout.addRow('Milestone (Zoho):', self.milestone_edit)
        
        # Типы элементов
        self.types_list = QListWidget()
        self.types_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.types_list.setMaximumHeight(100)
        for t in ['Module', 'Epic', 'Feature', 'Story', 'Page', 'Element', 'Service']:
            self.types_list.addItem(t)
        params_layout.addRow('Типы элементов:', self.types_list)
        
        # Только критичные/фокусные
        filters_layout = QHBoxLayout()
        self.crit_check = QCheckBox('Только критичные')
        self.focus_check = QCheckBox('Только фокусные')
        filters_layout.addWidget(self.crit_check)
        filters_layout.addWidget(self.focus_check)
        filters_layout.addStretch()
        params_layout.addRow('Фильтры:', filters_layout)
        
        # QA ответственный
        self.qa_combo = QComboBox()
        self.qa_combo.addItem('Все QA', None)
        self.load_qa_users()
        params_layout.addRow('Ответственный QA:', self.qa_combo)
        
        layout.addWidget(params_group)
        
        # === Секция 3: Результат (Preview) ===
        result_label = QLabel('<b>Сгенерированный отчёт:</b>')
        layout.addWidget(result_label)
        
        self.result_text = QTextEdit()
        self.result_text.setFont(QFont('Consolas', 9))
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText('Нажмите "Сгенерировать" для создания отчёта...')
        layout.addWidget(self.result_text)
        
        # === Кнопки действий ===
        buttons_layout = QHBoxLayout()
        
        generate_btn = QPushButton('🚀 Сгенерировать')
        generate_btn.clicked.connect(self.generate_report)
        buttons_layout.addWidget(generate_btn)
        
        save_btn = QPushButton('💾 Сохранить в файл')
        save_btn.clicked.connect(self.save_to_file)
        buttons_layout.addWidget(save_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_templates(self):
        """Загрузка списка шаблонов"""
        from src.models.report_template import ReportTemplate
        
        templates = self.session.query(ReportTemplate).filter_by(is_active=True).all()
        
        self.template_combo.clear()
        for template in templates:
            self.template_combo.addItem(template.name, template.id)
        
        if not templates:
            QMessageBox.information(
                self, 
                'Информация', 
                'Нет активных шаблонов.\n\nСоздайте шаблон в меню "Инструменты → Шаблоны отчётов"'
            )
    
    def load_qa_users(self):
        """Загрузка списка QA"""
        from src.models import User
        
        qa_users = self.session.query(User).filter(
            User.is_active == True,
            User.role.like('%QA%')
        ).all()
        
        for user in qa_users:
            self.qa_combo.addItem(user.name, user.id)
    
    def on_template_changed(self, index):
        """Обработка смены шаблона"""
        if index < 0:
            return
        
        from src.models.report_template import ReportTemplate
        
        template_id = self.template_combo.currentData()
        if template_id:
            template = self.session.query(ReportTemplate).get(template_id)
            if template:
                desc = template.description or 'Нет описания'
                self.template_desc_label.setText(f'📝 {desc}')
    
    def get_filters(self):
        """Получение фильтров из UI"""
        filters = {}
        
        # Milestone
        milestone = self.milestone_edit.text().strip()
        if milestone:
            filters['milestone_name'] = milestone
        
        # Типы
        selected_types = [item.text() for item in self.types_list.selectedItems()]
        if selected_types:
            filters['type'] = selected_types
        
        # Критичные/Фокусные
        if self.crit_check.isChecked():
            filters['is_crit'] = True
        if self.focus_check.isChecked():
            filters['is_focus'] = True
        
        # QA
        qa_id = self.qa_combo.currentData()
        if qa_id:
            filters['responsible_qa_id'] = qa_id
        
        return filters
    
    def generate_report(self):
        """Генерация отчёта"""
        template_id = self.template_combo.currentData()
        if not template_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите шаблон')
            return
        
        try:
            from src.services.ReportGenerator import ReportGenerator
            
            # Создаём генератор
            generator = ReportGenerator(self.session)
            
            # Получаем фильтры
            filters = self.get_filters()
            
            # Генерируем отчёт
            self.result_text.setPlainText('⏳ Генерация отчёта...')
            QApplication.processEvents()
            
            self.generated_content = generator.generate_report(template_id, filters=filters)
            
            # Отображаем результат
            self.result_text.setPlainText(self.generated_content)
            
            QMessageBox.information(
                self, 
                'Успех', 
                f'✅ Отчёт сгенерирован!\n\nСимволов: {len(self.generated_content)}'
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчёта: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сгенерировать отчёт:\n\n{e}')
    
    def save_to_file(self):
        """Сохранение отчёта в файл"""
        if not self.generated_content:
            QMessageBox.warning(self, 'Ошибка', 'Сначала сгенерируйте отчёт')
            return
        
        # Предлагаем имя файла
        template_name = self.template_combo.currentText()
        date_str = datetime.now().strftime('%Y-%m-%d')
        default_filename = f"{template_name}_{date_str}.md"
        
        from datetime import datetime
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Сохранить отчёт',
            default_filename,
            'Markdown Files (*.md);;Text Files (*.txt);;All Files (*)'
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.generated_content)
                
                QMessageBox.information(self, 'Успех', f'✅ Отчёт сохранён:\n{file_path}')
                
            except Exception as e:
                logger.error(f"Ошибка сохранения файла: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
