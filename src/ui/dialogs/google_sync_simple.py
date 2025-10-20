"""
Google Sheets Sync - Simple Interface

Упрощённая синхронизация БД с Google Sheets через браузер:
- Открытие Google Drive в браузере
- Вставка URL таблицы
- Экспорт/Импорт всех данных БД
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
import webbrowser
import re
import logging

logger = logging.getLogger(__name__)


class SyncThread(QThread):
    """Фоновый поток для синхронизации"""
    finished = pyqtSignal(dict, str)  # stats, error_message
    progress = pyqtSignal(str)  # status message
    
    def __init__(self, exporter, spreadsheet_id, sync_type):
        super().__init__()
        self.exporter = exporter
        self.spreadsheet_id = spreadsheet_id
        self.sync_type = sync_type
    
    def run(self):
        try:
            if self.sync_type == 'export':
                self.progress.emit("📤 Экспорт данных в Google Sheets...")
                stats = self.exporter.export_all_tables(self.spreadsheet_id)
                self.finished.emit(stats, "")
                
            elif self.sync_type == 'import':
                self.progress.emit("📥 Импорт данных из Google Sheets...")
                # TODO: Реализовать импорт
                stats = {'imported': 0}
                self.finished.emit(stats, "Импорт будет реализован в следующей версии")
                
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
            self.finished.emit({}, str(e))


class GoogleSheetsSyncDialog(QDialog):
    """Диалог синхронизации с Google Sheets"""
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.sync_thread = None
        
        self.setWindowTitle('Синхронизация с Google Sheets')
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel(
            '☁️ <b>Синхронизация БД с Google Sheets</b><br><br>'
            'Используйте одну таблицу для переноса данных между компьютерами:<br>'
            '• <b>Экспорт</b> — сохранить все данные БД в Google Sheets<br>'
            '• <b>Импорт</b> — загрузить данные из Google Sheets в БД'
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # === Секция 1: Настройки ===
        settings_group = QGroupBox('Настройки Google')
        settings_layout = QFormLayout(settings_group)
        
        # Путь к credentials
        creds_layout = QHBoxLayout()
        self.credentials_path_edit = QLineEdit()
        self.credentials_path_edit.setPlaceholderText('Путь к service_account.json')
        creds_layout.addWidget(self.credentials_path_edit)
        
        browse_btn = QPushButton('📂 Выбрать')
        browse_btn.clicked.connect(self.select_credentials)
        creds_layout.addWidget(browse_btn)
        
        settings_layout.addRow('Credentials JSON:', creds_layout)
        
        hint_label = QLabel(
            '<i>💡 Сохраните service_account.json отдельно для безопасности.<br>'
            'Передавайте только при необходимости.</i>'
        )
        hint_label.setStyleSheet('color: gray; font-size: 9pt;')
        hint_label.setWordWrap(True)
        settings_layout.addRow('', hint_label)
        
        layout.addWidget(settings_group)
        
        # === Секция 2: Подключение к таблице ===
        connect_group = QGroupBox('Подключение к Google Sheets')
        connect_layout = QVBoxLayout(connect_group)
        
        # Кнопка открытия Google Drive
        open_drive_btn = QPushButton('🌐 Открыть Google Drive в браузере')
        open_drive_btn.setMinimumHeight(40)
        open_drive_btn.clicked.connect(self.open_google_drive)
        connect_layout.addWidget(open_drive_btn)
        
        # Разделитель
        separator_label = QLabel('<center>— или —</center>')
        separator_label.setStyleSheet('color: gray;')
        connect_layout.addWidget(separator_label)
        
        # Вставка URL таблицы
        url_layout = QFormLayout()
        self.spreadsheet_url_edit = QLineEdit()
        self.spreadsheet_url_edit.setPlaceholderText(
            'https://docs.google.com/spreadsheets/d/ВАША_ТАБЛИЦА/edit'
        )
        self.spreadsheet_url_edit.textChanged.connect(self.on_url_changed)
        url_layout.addRow('URL таблицы:', self.spreadsheet_url_edit)
        
        # Извлечённый ID
        self.spreadsheet_id_label = QLabel('')
        self.spreadsheet_id_label.setStyleSheet('color: green; font-size: 9pt;')
        self.spreadsheet_id_label.setWordWrap(True)
        url_layout.addRow('', self.spreadsheet_id_label)
        
        connect_layout.addLayout(url_layout)
        
        layout.addWidget(connect_group)
        
        # === Прогресс ===
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet('color: blue;')
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Неопределённый прогресс
        layout.addWidget(self.progress_bar)
        
        # === Кнопки действий ===
        buttons_layout = QHBoxLayout()
        
        self.export_btn = QPushButton('📤 Экспортировать в Google Sheets')
        self.export_btn.setMinimumHeight(35)
        self.export_btn.clicked.connect(lambda: self.start_sync('export'))
        buttons_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton('📥 Импортировать из Google Sheets')
        self.import_btn.setMinimumHeight(35)
        self.import_btn.clicked.connect(lambda: self.start_sync('import'))
        buttons_layout.addWidget(self.import_btn)
        
        layout.addLayout(buttons_layout)
        
        # Кнопка закрытия
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def load_settings(self):
        """Загрузка сохранённых настроек"""
        # TODO: Загрузить из конфига
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        default_creds = project_root / 'credentials' / 'service_account.json'
        
        if default_creds.exists():
            self.credentials_path_edit.setText(str(default_creds))
    
    def select_credentials(self):
        """Выбор файла credentials"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Выберите service_account.json',
            '',
            'JSON Files (*.json);;All Files (*)'
        )
        if file_path:
            self.credentials_path_edit.setText(file_path)
            self.save_settings()
    
    def save_settings(self):
        """Сохранение настроек"""
        # TODO: Сохранить в конфиг
        pass
    
    def open_google_drive(self):
        """Открытие Google Drive в браузере"""
        url = "https://drive.google.com/drive/my-drive"
        try:
            webbrowser.open(url)
            QMessageBox.information(
                self,
                'Google Drive открыт',
                '✅ Google Drive открыт в браузере.\n\n'
                '1. Найдите или создайте Google Sheets таблицу\n'
                '2. Скопируйте URL таблицы из адресной строки\n'
                '3. Вставьте URL в поле ниже'
            )
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть браузер:\n{e}')
    
    def on_url_changed(self, url):
        """Обработка изменения URL"""
        spreadsheet_id = self.extract_spreadsheet_id(url)
        
        if spreadsheet_id:
            self.spreadsheet_id_label.setText(f'✅ Spreadsheet ID: {spreadsheet_id}')
            self.spreadsheet_id_label.setStyleSheet('color: green; font-size: 9pt;')
        else:
            if url.strip():
                self.spreadsheet_id_label.setText('❌ Некорректный URL таблицы')
                self.spreadsheet_id_label.setStyleSheet('color: red; font-size: 9pt;')
            else:
                self.spreadsheet_id_label.setText('')
    
    def extract_spreadsheet_id(self, url):
        """Извлечение Spreadsheet ID из URL"""
        # Паттерны URL Google Sheets
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Если это просто ID
        if re.match(r'^[a-zA-Z0-9-_]+$', url.strip()):
            return url.strip()
        
        return None
    
    def start_sync(self, sync_type):
        """Начать синхронизацию"""
        # Валидация
        credentials_path = self.credentials_path_edit.text().strip()
        spreadsheet_url = self.spreadsheet_url_edit.text().strip()
        
        if not credentials_path or not Path(credentials_path).exists():
            QMessageBox.warning(
                self,
                'Ошибка',
                'Укажите корректный путь к service_account.json'
            )
            return
        
        spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_url)
        if not spreadsheet_id:
            QMessageBox.warning(
                self,
                'Ошибка',
                'Укажите корректный URL или ID таблицы Google Sheets'
            )
            return
        
        # Подтверждение
        if sync_type == 'export':
            msg = (
                'Экспортировать все данные БД в Google Sheets?\n\n'
                '⚠️ Существующие данные в таблице будут перезаписаны!'
            )
        else:
            msg = (
                'Импортировать данные из Google Sheets в БД?\n\n'
                '⚠️ Существующие данные в БД будут перезаписаны!'
            )
        
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Создаём экспортер
        try:
            from src.services.GoogleSheetsExporter import GoogleSheetsExporter
            exporter = GoogleSheetsExporter(credentials_path, self.session)
            
            # Запускаем синхронизацию в фоновом потоке
            self.export_btn.setEnabled(False)
            self.import_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            
            action_name = 'Экспорт' if sync_type == 'export' else 'Импорт'
            self.progress_label.setText(f'🚀 {action_name} начат...')
            
            self.sync_thread = SyncThread(exporter, spreadsheet_id, sync_type)
            self.sync_thread.progress.connect(self.on_progress)
            self.sync_thread.finished.connect(self.on_sync_finished)
            self.sync_thread.start()
            
        except Exception as e:
            logger.error(f"Ошибка запуска синхронизации: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось запустить синхронизацию:\n{e}')
            self.export_btn.setEnabled(True)
            self.import_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_progress(self, message):
        """Обновление прогресса"""
        self.progress_label.setText(message)
        logger.info(message)
    
    def on_sync_finished(self, stats, error):
        """Обработка завершения синхронизации"""
        self.export_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if error:
            self.progress_label.setText(f'❌ Ошибка: {error}')
            QMessageBox.critical(self, 'Ошибка синхронизации', f'Не удалось синхронизировать:\n\n{error}')
        else:
            # Формируем сообщение об успехе
            msg_parts = ['✅ Синхронизация завершена!\n']
            for key, value in stats.items():
                if key != 'errors':
                    msg_parts.append(f'• {key}: {value}')
            
            msg = '\n'.join(msg_parts)
            self.progress_label.setText('✅ Синхронизация завершена!')
            
            # Диалог с кнопкой "Открыть таблицу"
            result = QMessageBox.information(
                self,
                'Синхронизация завершена',
                msg + '\n\nОткрыть таблицу в браузере?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                spreadsheet_id = self.extract_spreadsheet_id(self.spreadsheet_url_edit.text())
                url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit'
                webbrowser.open(url)
