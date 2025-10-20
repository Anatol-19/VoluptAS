"""
Simple Google Sheets Import

Просто вставить URL таблицы и импортировать
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
import re
import webbrowser
import logging

logger = logging.getLogger(__name__)


class ImportThread(QThread):
    """Фоновый импорт"""
    finished = pyqtSignal(dict, str)
    progress = pyqtSignal(str)
    
    def __init__(self, importer, spreadsheet_id):
        super().__init__()
        self.importer = importer
        self.spreadsheet_id = spreadsheet_id
    
    def run(self):
        try:
            self.progress.emit("📥 Импорт данных...")
            stats = self.importer.import_all_tables(self.spreadsheet_id)
            self.finished.emit(stats, "")
        except Exception as e:
            logger.error(f"Ошибка импорта: {e}")
            self.finished.emit({}, str(e))


class GoogleImportSimpleDialog(QDialog):
    """Простой импорт из Google Sheets"""
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.import_thread = None
        
        self.setWindowTitle('Импорт из Google Sheets')
        self.setMinimumWidth(600)
        self.setMinimumHeight(300)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel(
            '📥 <b>Импорт данных из Google Sheets в БД</b><br><br>'
            'Вставьте URL вашей таблицы Google Sheets.<br>'
            'Все данные из листов будут импортированы в БД.'
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # URL таблицы
        url_layout = QFormLayout()
        self.spreadsheet_url_edit = QLineEdit()
        self.spreadsheet_url_edit.setPlaceholderText(
            'https://docs.google.com/spreadsheets/d/ВАШ_ID/edit'
        )
        self.spreadsheet_url_edit.textChanged.connect(self.on_url_changed)
        url_layout.addRow('* URL таблицы:', self.spreadsheet_url_edit)
        
        # Извлечённый ID
        self.spreadsheet_id_label = QLabel('')
        self.spreadsheet_id_label.setWordWrap(True)
        url_layout.addRow('', self.spreadsheet_id_label)
        
        layout.addLayout(url_layout)
        
        # Hint
        hint_label = QLabel(
            '<i>⚠️ Будут импортированы листы: "Сотрудники", "Функционал", "Связи"<br>'
            '💡 Credentials настроены в: Настройки → Google API</i>'
        )
        hint_label.setStyleSheet('color: gray; font-size: 9pt;')
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        # Прогресс
        self.progress_label = QLabel('')
        self.progress_label.setStyleSheet('color: blue;')
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.import_btn = QPushButton('📥 Импортировать')
        self.import_btn.setMinimumHeight(35)
        self.import_btn.clicked.connect(self.start_import)
        buttons_layout.addWidget(self.import_btn)
        
        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def on_url_changed(self, url):
        """Парсинг URL"""
        spreadsheet_id = self.extract_spreadsheet_id(url)
        
        if spreadsheet_id:
            self.spreadsheet_id_label.setText(f'✅ ID: {spreadsheet_id}')
            self.spreadsheet_id_label.setStyleSheet('color: green; font-size: 9pt;')
        else:
            if url.strip():
                self.spreadsheet_id_label.setText('❌ Некорректный URL')
                self.spreadsheet_id_label.setStyleSheet('color: red; font-size: 9pt;')
            else:
                self.spreadsheet_id_label.setText('')
    
    def extract_spreadsheet_id(self, url):
        """Извлечение ID из URL"""
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        if re.match(r'^[a-zA-Z0-9-_]+$', url.strip()):
            return url.strip()
        
        return None
    
    def start_import(self):
        """Начать импорт"""
        spreadsheet_id = self.extract_spreadsheet_id(self.spreadsheet_url_edit.text())
        
        if not spreadsheet_id:
            QMessageBox.warning(self, 'Ошибка', 'Укажите корректный URL таблицы')
            return
        
        # Проверяем credentials (используем единый путь из настроек)
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        creds_primary = project_root / 'credentials' / 'google_credentials.json'
        creds_alt1 = project_root / 'credentials' / 'google_service_account.json'
        creds_alt2 = project_root / 'credentials' / 'service_account.json'
        
        if creds_primary.exists():
            creds_path = creds_primary
        elif creds_alt1.exists():
            creds_path = creds_alt1
        elif creds_alt2.exists():
            creds_path = creds_alt2
        else:
            QMessageBox.critical(
                self,
                'Ошибка',
                'Не найден файл с Google credentials!\\n\\n'
                'Заполните JSON в Настройки → Google API.\\n'
                'Ожидаемое имя: credentials/google_credentials.json'
            )
            return
        
        # Подтверждение
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            'Импортировать данные из Google Sheets в БД?\\n\\n'
            '⚠️ Существующие записи будут обновлены!',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Импорт
        try:
            from src.services.GoogleSheetsImporter import GoogleSheetsImporter
            importer = GoogleSheetsImporter(str(creds_path), self.session)
            
            self.import_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_label.setText('🚀 Импорт начат...')
            
            self.import_thread = ImportThread(importer, spreadsheet_id)
            self.import_thread.progress.connect(self.on_progress)
            self.import_thread.finished.connect(self.on_import_finished)
            self.import_thread.start()
            
        except Exception as e:
            logger.error(f"Ошибка запуска импорта: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось запустить импорт:\\n{e}')
            self.import_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_progress(self, message):
        """Прогресс"""
        self.progress_label.setText(message)
    
    def on_import_finished(self, stats, error):
        """Завершение импорта"""
        self.import_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if error:
            self.progress_label.setText(f'❌ Ошибка: {error}')
            QMessageBox.critical(self, 'Ошибка', f'Не удалось импортировать:\\n\\n{error}')
        else:
            msg_parts = ['✅ Импорт завершён!\\n']
            for key, value in stats.items():
                if key != 'errors':
                    msg_parts.append(f'• {key}: {value}')
            
            msg = '\\n'.join(msg_parts)
            self.progress_label.setText('✅ Импорт завершён!')
            
            QMessageBox.information(
                self,
                'Импорт завершён',
                msg
            )
            
            self.accept()
