"""
Report Template Editor

Простой редактор markdown шаблонов отчётов с preview
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class TemplateEditorDialog(QDialog):
    """Редактор шаблона отчёта"""
    
    def __init__(self, session, template=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.template = template
        self.is_new = template is None
        
        self.setWindowTitle('Редактор шаблона отчёта' if self.is_new else f'Редактирование: {template.name}')
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        
        self.init_ui()
        
        if self.template:
            self.load_template()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # === Секция 1: Метаданные ===
        meta_group = QGroupBox('Метаданные шаблона')
        meta_layout = QFormLayout(meta_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('Например: Test Plan Sprint')
        meta_layout.addRow('* Название:', self.name_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText('Краткое описание шаблона')
        meta_layout.addRow('Описание:', self.description_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(['test_plan', 'bug_report', 'sprint_report', 'custom'])
        meta_layout.addRow('* Тип шаблона:', self.type_combo)
        
        layout.addWidget(meta_group)
        
        # === Секция 2: Контент (Split: Editor | Preview) ===
        content_label = QLabel('<b>Контент шаблона (Markdown)</b>')
        layout.addWidget(content_label)
        
        # Hint с placeholder'ами
        hint_label = QLabel(
            '<i>💡 Доступные placeholder\'ы: {{milestone_name}}, {{task_count}}, {{date}}, {{qa_name}}</i>'
        )
        hint_label.setStyleSheet('color: gray; font-size: 9pt;')
        layout.addWidget(hint_label)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель: Markdown Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_label = QLabel('📝 Markdown Editor:')
        editor_layout.addWidget(editor_label)
        
        self.content_edit = QTextEdit()
        self.content_edit.setFont(QFont('Consolas', 10))
        self.content_edit.setPlaceholderText('# Введите markdown текст шаблона...\n\n## Раздел 1\n...')
        self.content_edit.textChanged.connect(self.update_preview)
        editor_layout.addWidget(self.content_edit)
        
        splitter.addWidget(editor_widget)
        
        # Правая панель: Preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel('👁️ Preview:')
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet('background-color: #f5f5f5;')
        preview_layout.addWidget(self.preview_text)
        
        splitter.addWidget(preview_widget)
        
        # Пропорции 60/40
        splitter.setStretchFactor(0, 60)
        splitter.setStretchFactor(1, 40)
        
        layout.addWidget(splitter)
        
        # === Кнопки действий ===
        buttons_layout = QHBoxLayout()
        
        # Левые кнопки (шаблоны)
        template_btn = QPushButton('📋 Вставить пример')
        template_btn.clicked.connect(self.insert_example)
        buttons_layout.addWidget(template_btn)
        
        buttons_layout.addStretch()
        
        # Правые кнопки (сохранить/отмена)
        save_btn = QPushButton('💾 Сохранить')
        save_btn.clicked.connect(self.save_template)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_template(self):
        """Загрузка существующего шаблона"""
        self.name_edit.setText(self.template.name)
        self.description_edit.setText(self.template.description or '')
        self.type_combo.setCurrentText(self.template.template_type)
        self.content_edit.setPlainText(self.template.content)
    
    def update_preview(self):
        """Обновление preview (простой вариант без markdown рендеринга)"""
        content = self.content_edit.toPlainText()
        # Простое отображение без markdown парсинга
        self.preview_text.setPlainText(content)
    
    def insert_example(self):
        """Вставка примера шаблона"""
        example = """# Тест-план спринта {{milestone_name}}

> Дата: {{date}}
> QA Lead: {{qa_name}}

## 1. Функциональность в релизе

{{feature_list}}

## 2. Задачи спринта

| ID | Задача | Приоритет | QA | Status |
|----|--------|-----------|-----|--------|
{{task_table}}

## 3. Виды тестирования

- [ ] Smoke тестирование
- [ ] Функциональное тестирование
- [ ] Регрессионное тестирование
- [ ] Performance тестирование

## 4. Обнаруженные дефекты

{{bug_list}}

## 5. Метрики

- Всего задач: {{task_count}}
- Найдено багов: {{bug_count}}
- Покрытие: {{coverage}}%
"""
        self.content_edit.setPlainText(example)
    
    def save_template(self):
        """Сохранение шаблона"""
        # Валидация
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, 'Ошибка', 'Укажите название шаблона')
            return
        
        content = self.content_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, 'Ошибка', 'Контент шаблона не может быть пустым')
            return
        
        try:
            from src.models.report_template import ReportTemplate
            
            if self.is_new:
                # Создание нового шаблона
                self.template = ReportTemplate(
                    name=name,
                    description=self.description_edit.text().strip() or None,
                    content=content,
                    template_type=self.type_combo.currentText()
                )
                self.session.add(self.template)
            else:
                # Обновление существующего
                self.template.name = name
                self.template.description = self.description_edit.text().strip() or None
                self.template.content = content
                self.template.template_type = self.type_combo.currentText()
            
            self.session.commit()
            QMessageBox.information(self, 'Успех', f'✅ Шаблон "{name}" сохранён')
            self.accept()
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Ошибка сохранения шаблона: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить шаблон:\n{e}')


class TemplateManagerDialog(QDialog):
    """Менеджер шаблонов отчётов"""
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        
        self.setWindowTitle('Менеджер шаблонов отчётов')
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel(
            '📋 <b>Управление шаблонами отчётов</b><br>'
            'Создавайте и редактируйте markdown шаблоны для генерации тест-планов и отчётов.'
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Таблица шаблонов
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Название', 'Тип', 'Описание', 'Активен', 'Обновлён'])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_template)
        layout.addWidget(self.table)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton('➕ Создать')
        add_btn.clicked.connect(self.add_template)
        buttons_layout.addWidget(add_btn)
        
        edit_btn = QPushButton('✏️ Редактировать')
        edit_btn.clicked.connect(self.edit_template)
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton('🗑️ Удалить')
        delete_btn.clicked.connect(self.delete_template)
        buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_templates(self):
        """Загрузка списка шаблонов"""
        from src.models.report_template import ReportTemplate
        
        templates = self.session.query(ReportTemplate).order_by(ReportTemplate.created_at.desc()).all()
        
        self.table.setRowCount(len(templates))
        for row, template in enumerate(templates):
            self.table.setItem(row, 0, QTableWidgetItem(template.name))
            self.table.setItem(row, 1, QTableWidgetItem(template.template_type))
            self.table.setItem(row, 2, QTableWidgetItem(template.description or ''))
            self.table.setItem(row, 3, QTableWidgetItem('✓' if template.is_active else ''))
            
            updated = template.updated_at.strftime('%Y-%m-%d %H:%M') if template.updated_at else ''
            self.table.setItem(row, 4, QTableWidgetItem(updated))
        
        self.table.resizeColumnsToContents()
    
    def add_template(self):
        """Создание нового шаблона"""
        dialog = TemplateEditorDialog(self.session, parent=self)
        if dialog.exec():
            self.load_templates()
    
    def edit_template(self):
        """Редактирование выбранного шаблона"""
        from src.models.report_template import ReportTemplate
        
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, 'Внимание', 'Выберите шаблон для редактирования')
            return
        
        template_name = self.table.item(selected, 0).text()
        template = self.session.query(ReportTemplate).filter_by(name=template_name).first()
        
        if template:
            dialog = TemplateEditorDialog(self.session, template, parent=self)
            if dialog.exec():
                self.load_templates()
    
    def delete_template(self):
        """Удаление шаблона"""
        from src.models.report_template import ReportTemplate
        
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, 'Внимание', 'Выберите шаблон для удаления')
            return
        
        template_name = self.table.item(selected, 0).text()
        
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            f'Удалить шаблон "{template_name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                template = self.session.query(ReportTemplate).filter_by(name=template_name).first()
                if template:
                    self.session.delete(template)
                    self.session.commit()
                    self.load_templates()
                    QMessageBox.information(self, 'Успех', f'✅ Шаблон "{template_name}" удалён')
            except Exception as e:
                self.session.rollback()
                logger.error(f"Ошибка удаления шаблона: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить:\n{e}')
