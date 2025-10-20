"""
Google Sheets Export Dialog

Диалог для экспорта данных VoluptAS в Google Sheets
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ExportThread(QThread):
    """Фоновый поток для экспорта"""
    finished = pyqtSignal(dict, str)  # stats, error_message
    progress = pyqtSignal(str)  # status message
    
    def __init__(self, exporter, spreadsheet_id, export_type, filters=None):
        super().__init__()
        self.exporter = exporter
        self.spreadsheet_id = spreadsheet_id
        self.export_type = export_type
        self.filters = filters or {}
    
    def run(self):
        try:
            if self.export_type == 'all_tables':
                self.progress.emit("📊 Экспорт всех таблиц...")
                stats = self.exporter.export_all_tables(self.spreadsheet_id, self.filters)
                self.finished.emit(stats, "")
                
            elif self.export_type == 'coverage_matrix':
                self.progress.emit("📋 Экспорт матрицы покрытия...")
                count = self.exporter.export_coverage_matrix(self.spreadsheet_id)
                self.finished.emit({'coverage': count}, "")
                
            elif self.export_type == 'raci_matrix':
                self.progress.emit("👥 Экспорт RACI матрицы...")
                count = self.exporter.export_raci_matrix(self.spreadsheet_id)
                self.finished.emit({'raci': count}, "")
                
            elif self.export_type == 'test_plan':
                self.progress.emit("📝 Экспорт тест-плана...")
                count = self.exporter.export_test_plan(
                    self.spreadsheet_id, 
                    "Test Plan", 
                    self.filters
                )
                self.finished.emit({'test_plan': count}, "")
                
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            self.finished.emit({}, str(e))


class GoogleExportDialog(QDialog):
    """Диалог экспорта в Google Sheets"""
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.export_thread = None
        
        self.setWindowTitle('Экспорт в Google Sheets')
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel(
            '📤 <b>Экспорт данных VoluptAS в Google Sheets</b><br><br>'
            'Выберите тип экспорта и параметры.'
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # === Секция 1: Google Sheets настройки ===
        gs_group = QGroupBox('Google Sheets')
        gs_layout = QFormLayout(gs_group)
        
        # Service Account JSON
        self.credentials_path_edit = QLineEdit()
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        default_creds = project_root / 'credentials' / 'service_account.json'
        self.credentials_path_edit.setText(str(default_creds))
        
        creds_btn = QPushButton('📂 Выбрать')
        creds_btn.clicked.connect(self.select_credentials)
        creds_layout = QHBoxLayout()
        creds_layout.addWidget(self.credentials_path_edit)
        creds_layout.addWidget(creds_btn)
        gs_layout.addRow('Service Account:', creds_layout)
        
        # Spreadsheet ID
        self.spreadsheet_id_edit = QLineEdit()
        self.spreadsheet_id_edit.setPlaceholderText('1Abc...XYZ (ID из URL таблицы)')
        gs_layout.addRow('* Spreadsheet ID:', self.spreadsheet_id_edit)
        
        hint = QLabel('<i>ID можно скопировать из URL: docs.google.com/spreadsheets/d/<b>ID</b>/edit</i>')
        hint.setWordWrap(True)
        hint.setStyleSheet('color: gray; font-size: 9pt;')
        gs_layout.addRow('', hint)
        
        layout.addWidget(gs_group)
        
        # === Секция 2: Тип экспорта ===
        export_group = QGroupBox('Тип экспорта')
        export_layout = QVBoxLayout(export_group)
        
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems([
            'Все таблицы БД',
            'Матрица покрытия',
            'RACI матрица',
            'Тест-план (с фильтрами)'
        ])
        self.export_type_combo.currentTextChanged.connect(self.on_export_type_changed)
        export_layout.addWidget(self.export_type_combo)
        
        layout.addWidget(export_group)
        
        # === Секция 3: Фильтры ===
        self.filters_group = QGroupBox('Фильтры (опционально)')
        filters_layout = QFormLayout(self.filters_group)
        
        # Типы элементов
        self.types_list = QListWidget()
        self.types_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.types_list.setMaximumHeight(120)
        for t in ['Module', 'Epic', 'Feature', 'Story', 'Page', 'Element', 'Service']:
            self.types_list.addItem(t)
        filters_layout.addRow('Типы элементов:', self.types_list)
        
        # Только критичные
        self.crit_check = QCheckBox('Только критичный функционал (isCrit)')
        filters_layout.addRow('', self.crit_check)
        
        # Только фокусные
        self.focus_check = QCheckBox('Только фокусный функционал (isFocus)')
        filters_layout.addRow('', self.focus_check)
        
        # Ответственные QA
        self.qa_list = QListWidget()
        self.qa_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.qa_list.setMaximumHeight(100)
        self.load_qa_users()
        filters_layout.addRow('Ответственные QA:', self.qa_list)
        
        layout.addWidget(self.filters_group)
        
        # === Прогресс ===
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet('color: blue;')
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Неопределённый прогресс
        layout.addWidget(self.progress_bar)
        
        # === Кнопки ===
        buttons = QDialogButtonBox()
        self.export_btn = buttons.addButton('🚀 Экспортировать', QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_btn = buttons.addButton('Отмена', QDialogButtonBox.ButtonRole.RejectRole)
        
        self.export_btn.clicked.connect(self.start_export)
        cancel_btn.clicked.connect(self.reject)
        
        layout.addWidget(buttons)
        
        # Начальное состояние
        self.on_export_type_changed(self.export_type_combo.currentText())
    
    def select_credentials(self):
        """Выбор service_account.json"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Выберите service_account.json',
            '',
            'JSON Files (*.json);;All Files (*)'
        )
        if file_path:
            self.credentials_path_edit.setText(file_path)
    
    def load_qa_users(self):
        """Загрузка списка QA из БД"""
        from src.models import User
        
        try:
            qa_users = self.session.query(User).filter(
                User.is_active == True,
                User.role.like('%QA%')
            ).all()
            
            for user in qa_users:
                item = QListWidgetItem(user.name)
                item.setData(Qt.ItemDataRole.UserRole, user.id)
                self.qa_list.addItem(item)
                
        except Exception as e:
            logger.warning(f"Не удалось загрузить QA: {e}")
    
    def on_export_type_changed(self, export_type):
        """Показать/скрыть фильтры в зависимости от типа экспорта"""
        # Фильтры актуальны для "Все таблицы" и "Тест-план"
        show_filters = export_type in ['Все таблицы БД', 'Тест-план (с фильтрами)']
        self.filters_group.setVisible(show_filters)
    
    def get_filters(self):
        """Собрать фильтры из UI"""
        filters = {}
        
        # Типы
        selected_types = [item.text() for item in self.types_list.selectedItems()]
        if selected_types:
            filters['type'] = selected_types
        
        # isCrit / isFocus
        if self.crit_check.isChecked():
            filters['is_crit'] = True
        if self.focus_check.isChecked():
            filters['is_focus'] = True
        
        # QA
        selected_qa = [item.data(Qt.ItemDataRole.UserRole) for item in self.qa_list.selectedItems()]
        if selected_qa:
            filters['responsible_qa_id'] = selected_qa
        
        return filters
    
    def start_export(self):
        """Начать экспорт"""
        # Валидация
        credentials_path = self.credentials_path_edit.text().strip()
        spreadsheet_id = self.spreadsheet_id_edit.text().strip()
        
        if not credentials_path or not Path(credentials_path).exists():
            QMessageBox.warning(
                self, 
                'Ошибка', 
                'Укажите корректный путь к service_account.json'
            )
            return
        
        if not spreadsheet_id:
            QMessageBox.warning(self, 'Ошибка', 'Укажите Spreadsheet ID')
            return
        
        # Определяем тип экспорта
        export_type_map = {
            'Все таблицы БД': 'all_tables',
            'Матрица покрытия': 'coverage_matrix',
            'RACI матрица': 'raci_matrix',
            'Тест-план (с фильтрами)': 'test_plan'
        }
        export_type = export_type_map[self.export_type_combo.currentText()]
        
        # Собираем фильтры
        filters = self.get_filters()
        
        # Создаём экспортер
        try:
            from src.services.GoogleSheetsExporter import GoogleSheetsExporter
            exporter = GoogleSheetsExporter(credentials_path, self.session)
            
            # Запускаем экспорт в фоновом потоке
            self.export_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_label.setText('🚀 Экспорт начат...')
            
            self.export_thread = ExportThread(exporter, spreadsheet_id, export_type, filters)
            self.export_thread.progress.connect(self.on_progress)
            self.export_thread.finished.connect(self.on_export_finished)
            self.export_thread.start()
            
        except Exception as e:
            logger.error(f"Ошибка запуска экспорта: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось запустить экспорт:\n{e}')
            self.export_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_progress(self, message):
        """Обновление прогресса"""
        self.progress_label.setText(message)
        logger.info(message)
    
    def on_export_finished(self, stats, error):
        """Обработка завершения экспорта"""
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if error:
            self.progress_label.setText(f'❌ Ошибка: {error}')
            QMessageBox.critical(self, 'Ошибка экспорта', f'Не удалось экспортировать:\n\n{error}')
        else:
            # Формируем сообщение об успехе
            msg_parts = ['✅ Экспорт завершён успешно!\n']
            for key, value in stats.items():
                if key != 'errors':
                    msg_parts.append(f'• {key}: {value}')
            
            msg = '\n'.join(msg_parts)
            self.progress_label.setText('✅ Экспорт завершён!')
            
            # Диалог с кнопкой "Открыть в браузере"
            result = QMessageBox.information(
                self,
                'Экспорт завершён',
                msg + '\n\nОткрыть таблицу в браузере?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                import webbrowser
                spreadsheet_id = self.spreadsheet_id_edit.text().strip()
                url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit'
                webbrowser.open(url)
            
            self.accept()
