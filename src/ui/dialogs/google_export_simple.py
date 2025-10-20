"""
Simple Google Sheets Export

Просто вставить URL таблицы и экспортировать
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
import re
import webbrowser
import logging

logger = logging.getLogger(__name__)


class ExportThread(QThread):
    """Фоновый экспорт"""
    finished = pyqtSignal(dict, str)
    progress = pyqtSignal(str)
    
    def __init__(self, exporter, spreadsheet_id):
        super().__init__()
        self.exporter = exporter
        self.spreadsheet_id = spreadsheet_id
    
    def run(self):
        try:
            self.progress.emit("📤 Экспорт данных...")
            stats = self.exporter.export_all_tables(self.spreadsheet_id)
            self.finished.emit(stats, "")
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            self.finished.emit({}, str(e))


class GoogleExportSimpleDialog(QDialog):
    """Простой экспорт в Google Sheets"""
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.export_thread = None
        
        self.setWindowTitle('Экспорт в Google Sheets')
        self.setMinimumWidth(600)
        self.setMinimumHeight(300)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel(
            '📤 <b>Экспорт базы данных в Google Sheets</b><br><br>'
            'Вставьте URL вашей таблицы Google Sheets.<br>'
            'Все таблицы БД будут экспортированы в отдельные вкладки.'
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
            '<i>💡 Таблица должна быть расшарена на email из service_account.json<br>'
            'Настройте credentials в: Настройки → Google API</i>'
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
        
        self.export_btn = QPushButton('📤 Экспортировать')
        self.export_btn.setMinimumHeight(35)
        self.export_btn.clicked.connect(self.start_export)
        buttons_layout.addWidget(self.export_btn)
        
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
    
    def start_export(self):
        """Начать экспорт"""
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
                'Не найден файл с Google credentials!\n\n'
                'Заполните JSON в Настройки → Google API.\n'
                'Ожидаемое имя: credentials/google_credentials.json'
            )
            return
        
        # Подтверждение
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            'Экспортировать все данные БД в Google Sheets?\n\n'
            '⚠️ Существующие данные в таблице будут перезаписаны!',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Экспорт
        try:
            from src.services.GoogleSheetsExporter import GoogleSheetsExporter
            exporter = GoogleSheetsExporter(str(creds_path), self.session)
            
            self.export_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_label.setText('🚀 Экспорт начат...')
            
            self.export_thread = ExportThread(exporter, spreadsheet_id)
            self.export_thread.progress.connect(self.on_progress)
            self.export_thread.finished.connect(self.on_export_finished)
            self.export_thread.start()
            
        except Exception as e:
            logger.error(f"Ошибка запуска экспорта: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось запустить экспорт:\n{e}')
            self.export_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_progress(self, message):
        """Прогресс"""
        self.progress_label.setText(message)
    
    def on_export_finished(self, stats, error):
        """Завершение экспорта"""
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if error:
            self.progress_label.setText(f'❌ Ошибка: {error}')
            QMessageBox.critical(self, 'Ошибка', f'Не удалось экспортировать:\n\n{error}')
        else:
            msg_parts = ['✅ Экспорт завершён!\n']
            for key, value in stats.items():
                if key != 'errors':
                    msg_parts.append(f'• {key}: {value}')
            
            msg = '\n'.join(msg_parts)
            self.progress_label.setText('✅ Экспорт завершён!')
            
            result = QMessageBox.information(
                self,
                'Экспорт завершён',
                msg + '\n\nОткрыть таблицу в браузере?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                url = f'https://docs.google.com/spreadsheets/d/{self.extract_spreadsheet_id(self.spreadsheet_url_edit.text())}/edit'
                webbrowser.open(url)
            
            self.accept()
