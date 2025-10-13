"""
Zoho Settings Dialog - Управление настройками API и токенами
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
import os
from pathlib import Path


class ZohoSettingsDialog(QDialog):
    """Диалог настроек Zoho API"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Настройки Zoho API')
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # Путь к credentials
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.env_path = self.project_root / 'credentials' / 'zoho.env'
        
        self.init_ui()
        self.load_credentials()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Инфо
        info_label = QLabel(
            '⚙️ <b>Настройки интеграции с Zoho Projects</b><br><br>'
            'Здесь можно обновить токены доступа и другие параметры API.<br>'
            '<font color="red">⚠️ Будьте осторожны при изменении этих данных!</font>'
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Форма
        form = QFormLayout()
        
        # Client ID
        self.client_id_edit = QLineEdit()
        self.client_id_edit.setPlaceholderText('1000.XXXXXXXXXX...')
        form.addRow('Client ID:', self.client_id_edit)
        
        # Client Secret
        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_edit.setPlaceholderText('Секретный ключ...')
        show_secret_btn = QPushButton('👁️')
        show_secret_btn.setMaximumWidth(40)
        show_secret_btn.clicked.connect(lambda: self.toggle_password(self.client_secret_edit))
        secret_layout = QHBoxLayout()
        secret_layout.addWidget(self.client_secret_edit)
        secret_layout.addWidget(show_secret_btn)
        form.addRow('Client Secret:', secret_layout)
        
        # Access Token
        self.access_token_edit = QLineEdit()
        self.access_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.access_token_edit.setPlaceholderText('1000.XXXXXXXXXX...')
        show_access_btn = QPushButton('👁️')
        show_access_btn.setMaximumWidth(40)
        show_access_btn.clicked.connect(lambda: self.toggle_password(self.access_token_edit))
        access_layout = QHBoxLayout()
        access_layout.addWidget(self.access_token_edit)
        access_layout.addWidget(show_access_btn)
        form.addRow('Access Token:', access_layout)
        
        # Refresh Token
        self.refresh_token_edit = QLineEdit()
        self.refresh_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.refresh_token_edit.setPlaceholderText('1000.XXXXXXXXXX...')
        show_refresh_btn = QPushButton('👁️')
        show_refresh_btn.setMaximumWidth(40)
        show_refresh_btn.clicked.connect(lambda: self.toggle_password(self.refresh_token_edit))
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(self.refresh_token_edit)
        refresh_layout.addWidget(show_refresh_btn)
        form.addRow('Refresh Token:', refresh_layout)
        
        # Authorization Code
        self.auth_code_edit = QLineEdit()
        self.auth_code_edit.setPlaceholderText('1000.XXXXXXXXXX... (опционально)')
        form.addRow('Authorization Code:', self.auth_code_edit)
        
        # Portal Name
        self.portal_edit = QLineEdit()
        self.portal_edit.setPlaceholderText('vrbgroup')
        form.addRow('Portal Name:', self.portal_edit)
        
        # Project ID
        self.project_id_edit = QLineEdit()
        self.project_id_edit.setPlaceholderText('1209515000001238053')
        form.addRow('Project ID:', self.project_id_edit)
        
        # Region
        self.region_combo = QComboBox()
        self.region_combo.addItems(['com', 'eu', 'in', 'cn'])
        form.addRow('Region:', self.region_combo)
        
        layout.addLayout(form)
        
        # Инструкция
        instruction = QLabel(
            '<br><b>📋 Как получить новые токены:</b><br>'
            '1. Перейдите в <a href="https://api-console.zoho.com/">Zoho API Console</a><br>'
            '2. Сгенерируйте новый Access Token<br>'
            '3. Скопируйте и вставьте новые токены в поля выше<br>'
            '4. Нажмите "Сохранить"'
        )
        instruction.setWordWrap(True)
        instruction.setOpenExternalLinks(True)
        layout.addWidget(instruction)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.accepted.connect(self.save_credentials)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).setText('Сбросить')
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.load_credentials)
        layout.addWidget(buttons)
    
    def toggle_password(self, line_edit):
        """Показать/скрыть пароль"""
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def load_credentials(self):
        """Загрузить credentials из файла"""
        if not self.env_path.exists():
            QMessageBox.warning(self, 'Ошибка', f'Файл credentials не найден:\n{self.env_path}')
            return
        
        try:
            with open(self.env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            creds = {}
            for line in lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    creds[key.strip()] = value.strip()
            
            self.client_id_edit.setText(creds.get('ZOHO_CLIENT_ID', ''))
            self.client_secret_edit.setText(creds.get('ZOHO_CLIENT_SECRET', ''))
            self.access_token_edit.setText(creds.get('ZOHO_ACCESS_TOKEN', ''))
            self.refresh_token_edit.setText(creds.get('ZOHO_REFRESH_TOKEN', ''))
            self.auth_code_edit.setText(creds.get('ZOHO_AUTHORIZATION_CODE', ''))
            self.portal_edit.setText(creds.get('ZOHO_PORTAL_NAME', ''))
            self.project_id_edit.setText(creds.get('ZOHO_PROJECT_ID', ''))
            
            region = creds.get('ZOHO_REGION', 'com')
            index = self.region_combo.findText(region)
            if index >= 0:
                self.region_combo.setCurrentIndex(index)
            
            self.statusBar().showMessage('✅ Credentials загружены')
        
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить credentials:\n{e}')
    
    def save_credentials(self):
        """Сохранить credentials в файл"""
        # Валидация
        if not self.client_id_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Client ID обязателен')
            return
        
        if not self.portal_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Portal Name обязателен')
            return
        
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Сохранить изменения в credentials?\n\n'
            '⚠️ Убедитесь, что данные корректны!',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            content = f"""ZOHO_CLIENT_ID={self.client_id_edit.text().strip()}
ZOHO_CLIENT_SECRET={self.client_secret_edit.text().strip()}
ZOHO_AUTHORIZATION_CODE={self.auth_code_edit.text().strip()}
ZOHO_REGION={self.region_combo.currentText()}
ZOHO_ACCESS_TOKEN={self.access_token_edit.text().strip()}
ZOHO_REFRESH_TOKEN={self.refresh_token_edit.text().strip()}
ZOHO_PORTAL_NAME={self.portal_edit.text().strip()}
ZOHO_PROJECT_ID={self.project_id_edit.text().strip()}
"""
            
            # Backup старого файла
            if self.env_path.exists():
                backup_path = self.env_path.with_suffix('.env.backup')
                import shutil
                shutil.copy2(self.env_path, backup_path)
            
            with open(self.env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            QMessageBox.information(self, 'Успех', '✅ Credentials сохранены!\n\nПерезапустите приложение для применения.')
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить credentials:\n{e}')
    
    def statusBar(self):
        """Заглушка для совместимости"""
        class FakeStatusBar:
            def showMessage(self, msg): pass
        return FakeStatusBar()
