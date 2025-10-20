"""
Zoho Sync Dialog

Диалог для синхронизации задач из Zoho Projects в VoluptAS
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SyncThread(QThread):
    """Фоновый поток для синхронизации"""
    finished = pyqtSignal(dict, str)  # stats, error_message
    progress = pyqtSignal(str)  # status message
    
    def __init__(self, sync_service, sync_type, params):
        super().__init__()
        self.sync_service = sync_service
        self.sync_type = sync_type
        self.params = params
    
    def run(self):
        try:
            if self.sync_type == 'milestone':
                self.progress.emit(f"📋 Синхронизация по milestone: {self.params['milestone_name']}")
                stats = self.sync_service.sync_tasks_by_milestone(self.params['milestone_name'])
                
            elif self.sync_type == 'tasklist':
                self.progress.emit(f"📋 Синхронизация по tasklist: {self.params['tasklist_name']}")
                stats = self.sync_service.sync_tasks_by_tasklist(self.params['tasklist_name'])
                
            elif self.sync_type == 'filter':
                self.progress.emit("📋 Синхронизация по фильтрам")
                stats = self.sync_service.sync_tasks_by_filter(**self.params)
            
            else:
                stats = {'error': 'Неизвестный тип синхронизации'}
            
            if 'error' in stats:
                self.finished.emit({}, stats['error'])
            else:
                self.finished.emit(stats, "")
                
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
            self.finished.emit({}, str(e))


class ZohoSyncDialog(QDialog):
    """Диалог синхронизации задач Zoho Projects"""
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.sync_thread = None
        
        self.setWindowTitle('Синхронизация Zoho Projects')
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel(
            '🔄 <b>Синхронизация задач из Zoho Projects</b><br><br>'
            'Загрузите задачи из Zoho и сохраните их в локальной БД VoluptAS.'
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # === Секция 1: Тип синхронизации ===
        sync_type_group = QGroupBox('Тип синхронизации')
        sync_type_layout = QVBoxLayout(sync_type_group)
        
        self.sync_type_combo = QComboBox()
        self.sync_type_combo.addItems([
            'По Milestone (спринт)',
            'По Tasklist',
            'По фильтрам (даты, ответственные)'
        ])
        self.sync_type_combo.currentTextChanged.connect(self.on_sync_type_changed)
        sync_type_layout.addWidget(self.sync_type_combo)
        
        layout.addWidget(sync_type_group)
        
        # === Секция 2: Параметры (динамические) ===
        self.params_group = QGroupBox('Параметры')
        self.params_layout = QFormLayout(self.params_group)
        
        # Milestone
        self.milestone_edit = QLineEdit()
        self.milestone_edit.setPlaceholderText('Например: Sprint 24, v2.5')
        self.params_layout.addRow('* Название Milestone:', self.milestone_edit)
        
        # Tasklist
        self.tasklist_edit = QLineEdit()
        self.tasklist_edit.setPlaceholderText('Например: QA Testing, Development')
        self.params_layout.addRow('* Название Tasklist:', self.tasklist_edit)
        
        # Фильтры по датам
        self.date_start_edit = QLineEdit()
        self.date_start_edit.setPlaceholderText('YYYY-MM-DD')
        self.params_layout.addRow('Дата начала:', self.date_start_edit)
        
        self.date_end_edit = QLineEdit()
        self.date_end_edit.setPlaceholderText('YYYY-MM-DD')
        self.params_layout.addRow('Дата окончания:', self.date_end_edit)
        
        # Owner ID (опционально)
        self.owner_id_edit = QLineEdit()
        self.owner_id_edit.setPlaceholderText('ID ответственного в Zoho')
        self.params_layout.addRow('Owner ID:', self.owner_id_edit)
        
        layout.addWidget(self.params_group)
        
        # Скрываем ненужные поля по умолчанию
        self.on_sync_type_changed(self.sync_type_combo.currentText())
        
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
        self.sync_btn = buttons.addButton('🚀 Синхронизировать', QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_btn = buttons.addButton('Отмена', QDialogButtonBox.ButtonRole.RejectRole)
        
        self.sync_btn.clicked.connect(self.start_sync)
        cancel_btn.clicked.connect(self.reject)
        
        layout.addWidget(buttons)
    
    def on_sync_type_changed(self, sync_type):
        """Показать/скрыть поля в зависимости от типа синхронизации"""
        # Получаем все виджеты из FormLayout
        milestone_label = self.params_layout.labelForField(self.milestone_edit)
        tasklist_label = self.params_layout.labelForField(self.tasklist_edit)
        date_start_label = self.params_layout.labelForField(self.date_start_edit)
        date_end_label = self.params_layout.labelForField(self.date_end_edit)
        owner_label = self.params_layout.labelForField(self.owner_id_edit)
        
        if sync_type == 'По Milestone (спринт)':
            # Показать только milestone
            milestone_label.setVisible(True)
            self.milestone_edit.setVisible(True)
            
            tasklist_label.setVisible(False)
            self.tasklist_edit.setVisible(False)
            
            date_start_label.setVisible(False)
            self.date_start_edit.setVisible(False)
            
            date_end_label.setVisible(False)
            self.date_end_edit.setVisible(False)
            
            owner_label.setVisible(False)
            self.owner_id_edit.setVisible(False)
            
        elif sync_type == 'По Tasklist':
            # Показать только tasklist
            milestone_label.setVisible(False)
            self.milestone_edit.setVisible(False)
            
            tasklist_label.setVisible(True)
            self.tasklist_edit.setVisible(True)
            
            date_start_label.setVisible(False)
            self.date_start_edit.setVisible(False)
            
            date_end_label.setVisible(False)
            self.date_end_edit.setVisible(False)
            
            owner_label.setVisible(False)
            self.owner_id_edit.setVisible(False)
            
        elif sync_type == 'По фильтрам (даты, ответственные)':
            # Показать фильтры
            milestone_label.setVisible(False)
            self.milestone_edit.setVisible(False)
            
            tasklist_label.setVisible(False)
            self.tasklist_edit.setVisible(False)
            
            date_start_label.setVisible(True)
            self.date_start_edit.setVisible(True)
            
            date_end_label.setVisible(True)
            self.date_end_edit.setVisible(True)
            
            owner_label.setVisible(True)
            self.owner_id_edit.setVisible(True)
    
    def start_sync(self):
        """Начать синхронизацию"""
        sync_type_map = {
            'По Milestone (спринт)': 'milestone',
            'По Tasklist': 'tasklist',
            'По фильтрам (даты, ответственные)': 'filter'
        }
        
        sync_type = sync_type_map[self.sync_type_combo.currentText()]
        
        # Собираем параметры
        params = {}
        
        if sync_type == 'milestone':
            milestone_name = self.milestone_edit.text().strip()
            if not milestone_name:
                QMessageBox.warning(self, 'Ошибка', 'Укажите название Milestone')
                return
            params['milestone_name'] = milestone_name
            
        elif sync_type == 'tasklist':
            tasklist_name = self.tasklist_edit.text().strip()
            if not tasklist_name:
                QMessageBox.warning(self, 'Ошибка', 'Укажите название Tasklist')
                return
            params['tasklist_name'] = tasklist_name
            
        elif sync_type == 'filter':
            params['created_after'] = self.date_start_edit.text().strip() or None
            params['created_before'] = self.date_end_edit.text().strip() or None
            params['owner_id'] = self.owner_id_edit.text().strip() or None
            
            if not any([params['created_after'], params['created_before'], params['owner_id']]):
                QMessageBox.warning(self, 'Ошибка', 'Укажите хотя бы один фильтр')
                return
        
        # Создаём сервис
        try:
            from src.services.ZohoSyncService import ZohoSyncService
            sync_service = ZohoSyncService(self.session)
            
            # Проверяем подключение к Zoho
            if not sync_service.init_zoho_client():
                QMessageBox.critical(
                    self, 
                    'Ошибка', 
                    'Не удалось подключиться к Zoho API.\n\n'
                    'Проверьте настройки в credentials/zoho.env'
                )
                return
            
            # Запускаем синхронизацию в фоновом потоке
            self.sync_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_label.setText('🚀 Синхронизация начата...')
            
            self.sync_thread = SyncThread(sync_service, sync_type, params)
            self.sync_thread.progress.connect(self.on_progress)
            self.sync_thread.finished.connect(self.on_sync_finished)
            self.sync_thread.start()
            
        except Exception as e:
            logger.error(f"Ошибка запуска синхронизации: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось запустить синхронизацию:\n{e}')
            self.sync_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_progress(self, message):
        """Обновление прогресса"""
        self.progress_label.setText(message)
        logger.info(message)
    
    def on_sync_finished(self, stats, error):
        """Обработка завершения синхронизации"""
        self.sync_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if error:
            self.progress_label.setText(f'❌ Ошибка: {error}')
            QMessageBox.critical(self, 'Ошибка синхронизации', f'Не удалось синхронизировать:\n\n{error}')
        else:
            # Формируем сообщение об успехе
            msg = f"""✅ Синхронизация завершена!

• Новых задач: {stats.get('new', 0)}
• Обновлено задач: {stats.get('updated', 0)}
• Ошибок: {stats.get('errors', 0)}

Задачи сохранены в локальной БД VoluptAS."""
            
            self.progress_label.setText('✅ Синхронизация завершена!')
            QMessageBox.information(self, 'Синхронизация завершена', msg)
            self.accept()
