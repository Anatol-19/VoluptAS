"""
Unified Settings Dialog - Единый центр настроек

Включает настройки для:
- Zoho Projects API
- Google API
- Qase.io API
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import json
import os
import shutil
from pathlib import Path
from .zoho_oauth_wizard import ZohoOAuthWizard
from src.config import Config


class TokenRefreshThread(QThread):
    """Фоновый поток для обновления Access Token через Refresh Token"""
    finished = pyqtSignal(str, str)  # new_access_token, error_message
    
    def __init__(self, client_id, client_secret, refresh_token):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
    
    def run(self):
        try:
            import requests
            url = "https://accounts.zoho.com/oauth/v2/token"
            params = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }
            response = requests.post(url, data=params)
            response.raise_for_status()
            result = response.json()
            new_access_token = result.get("access_token", "")
            if not new_access_token:
                self.finished.emit("", "Не удалось получить access_token из ответа")
            else:
                self.finished.emit(new_access_token, "")
        except Exception as e:
            self.finished.emit("", str(e))


class ProjectsFetchThread(QThread):
    """Фоновый поток для получения списка проектов"""
    finished = pyqtSignal(list, str)  # projects, error_message
    
    def __init__(self, access_token, portal_name, region):
        super().__init__()
        self.access_token = access_token
        self.portal_name = portal_name
        self.region = region
    
    def run(self):
        try:
            import requests
            domains = {
                "com": "projectsapi.zoho.com",
                "eu": "projectsapi.zoho.eu",
                "in": "projectsapi.zoho.in",
                "cn": "projectsapi.zoho.com.cn"
            }
            domain = domains.get(self.region, domains["com"])
            url = f"https://{domain}/restapi/portal/{self.portal_name}/projects/"
            headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            projects = response.json().get("projects", [])
            self.finished.emit(projects, "")
        except Exception as e:
            self.finished.emit([], str(e))


class SettingsDialog(QDialog):
    """Единый диалог настроек для всех интеграций"""
    
    def __init__(self, project_manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Настройки интеграций')
        self.setMinimumWidth(750)
        self.setMinimumHeight(600)
        
        self.project_root = Config.BASE_DIR
        
        # Пути к файлам настроек - из профиля проекта
        if project_manager:
            current_project = project_manager.get_current_project()
            if current_project:
                profile = project_manager.get_profile(current_project.settings_profile)
                if profile:
                    self.zoho_env_path = profile.zoho_env_path or Config.get_credentials_path('zoho.env')
                    self.google_json_path = profile.google_json_path or Config.get_credentials_path('google_credentials.json')
                    self.qase_env_path = profile.qase_env_path or Config.get_credentials_path('qase.env')
                else:
                    # Профиль не найден - используем дефолтные пути
                    self._set_default_paths()
            else:
                self._set_default_paths()
        else:
            # Старое поведение для обратной совместимости
            self._set_default_paths()
        
        # Fallback на альтернативные имена для Google
        if not self.google_json_path.exists():
            for alt_name in ['google_service_account.json', 'service_account.json']:
                fallback = self.google_json_path.parent / alt_name
                if fallback.exists():
                    self.google_json_path = fallback
                    break
        
        # Потоки
        self.token_thread = None
        self.projects_thread = None
        
        self.init_ui()
        self.load_all_settings()
    
    def _set_default_paths(self):
        """Установить дефолтные пути к credentials"""
        self.zoho_env_path = Config.get_credentials_path('zoho.env')
        self.google_json_path = Config.get_credentials_path('google_credentials.json')
        self.qase_env_path = Config.get_credentials_path('qase.env')
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs
        tabs = QTabWidget()
        
        # === TAB 1: ZOHO ===
        zoho_tab = self.create_zoho_tab()
        tabs.addTab(zoho_tab, '🔵 Zoho Projects')
        
        # === TAB 2: GOOGLE ===
        google_tab = self.create_google_tab()
        tabs.addTab(google_tab, '🔴 Google API')
        
        # === TAB 3: QASE ===
        qase_tab = self.create_qase_tab()
        tabs.addTab(qase_tab, '📊 Qase.io')
        
        layout.addWidget(tabs)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_all_settings)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText('💾 Сохранить всё')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('❌ Отмена')
        layout.addWidget(buttons)
        
        # Status
        self.status_label = QLabel('Готов')
        self.status_label.setStyleSheet('color: gray; padding: 5px;')
        layout.addWidget(self.status_label)
    
    def create_zoho_tab(self):
        """Создать вкладку Zoho"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info
        info = QLabel(
            '<b>⚙️ Настройки Zoho Projects API</b><br><br>'
            'Для работы с Zoho Projects нужны Client ID, Client Secret и Refresh Token.<br>'
            'Refresh Token получается один раз, Access Token обновляется автоматически.'
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Form
        form = QFormLayout()
        
        # Client ID
        self.zoho_client_id_edit = QLineEdit()
        self.zoho_client_id_edit.setPlaceholderText('1000.XXXXXXXXXX...')
        form.addRow('* Client ID:', self.zoho_client_id_edit)
        
        # Client Secret
        self.zoho_client_secret_edit = QLineEdit()
        self.zoho_client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        secret_layout = QHBoxLayout()
        secret_layout.addWidget(self.zoho_client_secret_edit)
        show_secret_btn = QPushButton('👁️')
        show_secret_btn.setMaximumWidth(40)
        show_secret_btn.clicked.connect(lambda: self.toggle_password(self.zoho_client_secret_edit))
        secret_layout.addWidget(show_secret_btn)
        form.addRow('* Client Secret:', secret_layout)
        
        # Refresh Token
        self.zoho_refresh_token_edit = QLineEdit()
        self.zoho_refresh_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(self.zoho_refresh_token_edit)
        show_refresh_btn = QPushButton('👁️')
        show_refresh_btn.setMaximumWidth(40)
        show_refresh_btn.clicked.connect(lambda: self.toggle_password(self.zoho_refresh_token_edit))
        refresh_layout.addWidget(show_refresh_btn)
        form.addRow('Refresh Token:', refresh_layout)
        
        # Access Token (readonly, автообновляется)
        self.zoho_access_token_edit = QLineEdit()
        self.zoho_access_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.zoho_access_token_edit.setReadOnly(True)
        access_layout = QHBoxLayout()
        access_layout.addWidget(self.zoho_access_token_edit)
        self.refresh_token_btn = QPushButton('🔄 Обновить')
        self.refresh_token_btn.clicked.connect(self.refresh_access_token)
        access_layout.addWidget(self.refresh_token_btn)
        form.addRow('Access Token:', access_layout)
        
        # Portal Name
        self.zoho_portal_edit = QLineEdit()
        self.zoho_portal_edit.setPlaceholderText('vrbgroup')
        form.addRow('* Portal Name:', self.zoho_portal_edit)
        
        # Region
        self.zoho_region_combo = QComboBox()
        self.zoho_region_combo.addItems(['com', 'eu', 'in', 'cn'])
        form.addRow('Region:', self.zoho_region_combo)
        
        layout.addLayout(form)
        
        # Project selection
        project_group = QGroupBox('📁 Выбор проекта')
        project_layout = QVBoxLayout(project_group)
        
        self.load_projects_btn = QPushButton('📥 Загрузить проекты из Zoho')
        self.load_projects_btn.clicked.connect(self.fetch_projects)
        project_layout.addWidget(self.load_projects_btn)
        
        self.projects_list = QListWidget()
        self.projects_list.itemClicked.connect(self.on_project_selected)
        project_layout.addWidget(self.projects_list)
        
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel('Или введите вручную:'))
        self.zoho_project_id_edit = QLineEdit()
        self.zoho_project_id_edit.setPlaceholderText('1209515000001238053')
        manual_layout.addWidget(self.zoho_project_id_edit)
        project_layout.addLayout(manual_layout)
        
        layout.addWidget(project_group)
        
        # OAuth Wizard button
        oauth_group = QGroupBox('🔐 Автоматическое получение токенов')
        oauth_layout = QVBoxLayout(oauth_group)
        
        oauth_info = QLabel(
            'Если у вас ещё нет токенов, используйте мастер OAuth.<br>'
            'Он поможет получить все необходимые токены за 5 простых шагов.'
        )
        oauth_info.setWordWrap(True)
        oauth_layout.addWidget(oauth_info)
        
        self.oauth_wizard_btn = QPushButton('🧙 Запустить OAuth Wizard')
        self.oauth_wizard_btn.clicked.connect(self.launch_oauth_wizard)
        oauth_layout.addWidget(self.oauth_wizard_btn)
        
        layout.addWidget(oauth_group)
        
        # Instructions
        instruction = QLabel(
            '<br><b>📋 Ручное получение токенов:</b><br>'
            '1. Перейдите в <a href="https://api-console.zoho.com/">Zoho API Console</a><br>'
            '2. Создайте Self Client<br>'
            '3. Получите Authorization Code и обменяйте на Refresh Token<br>'
            '4. Refresh Token действует долго, Access Token обновляется автоматически'
        )
        instruction.setWordWrap(True)
        instruction.setOpenExternalLinks(True)
        layout.addWidget(instruction)
        
        layout.addStretch()
        return tab
    
    def create_google_tab(self):
        """Создать вкладку Google"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info
        info = QLabel(
            '<b>🔴 Настройки Google API</b><br><br>'
            'Для работы с Google Sheets, Drive и другими сервисами нужен Service Account JSON.<br>'
            'Скачайте JSON файл из Google Cloud Console и вставьте содержимое ниже.'
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # JSON Editor
        json_label = QLabel('Service Account JSON:')
        layout.addWidget(json_label)
        
        self.google_json_edit = QTextEdit()
        self.google_json_edit.setPlaceholderText(
            '{\n'
            '  "type": "service_account",\n'
            '  "project_id": "your-project",\n'
            '  "private_key_id": "...",\n'
            '  "private_key": "...",\n'
            '  "client_email": "...",\n'
            '  ...\n'
            '}'
        )
        self.google_json_edit.setMinimumHeight(300)
        layout.addWidget(self.google_json_edit)
        
        # Validate button
        validate_btn = QPushButton('✅ Проверить JSON')
        validate_btn.clicked.connect(self.validate_google_json)
        layout.addWidget(validate_btn)
        
        # Instructions
        instruction = QLabel(
            '<br><b>📋 Как получить Service Account JSON:</b><br>'
            '1. Перейдите в <a href="https://console.cloud.google.com/">Google Cloud Console</a><br>'
            '2. Создайте проект (если нет)<br>'
            '3. Включите нужные API (Sheets, Drive, etc.)<br>'
            '4. Создайте Service Account<br>'
            '5. Скачайте JSON ключ<br>'
            '6. Вставьте содержимое JSON в поле выше'
        )
        instruction.setWordWrap(True)
        instruction.setOpenExternalLinks(True)
        layout.addWidget(instruction)
        
        layout.addStretch()
        return tab
    
    def create_qase_tab(self):
        """Создать вкладку Qase.io"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info
        info = QLabel(
            '<b>📊 Настройки Qase.io API</b><br><br>'
            'Для работы с Qase.io нужен API Token.<br>'
            'Получите его в настройках вашего аккаунта Qase.io.'
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Form
        form = QFormLayout()
        
        # API Token
        self.qase_token_edit = QLineEdit()
        self.qase_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        token_layout = QHBoxLayout()
        token_layout.addWidget(self.qase_token_edit)
        show_token_btn = QPushButton('👁️')
        show_token_btn.setMaximumWidth(40)
        show_token_btn.clicked.connect(lambda: self.toggle_password(self.qase_token_edit))
        token_layout.addWidget(show_token_btn)
        form.addRow('* API Token:', token_layout)
        
        # Project Code
        self.qase_project_edit = QLineEdit()
        self.qase_project_edit.setPlaceholderText('ITS')
        form.addRow('* Project Code:', self.qase_project_edit)
        
        # Base URL (обычно не меняется)
        self.qase_url_edit = QLineEdit()
        self.qase_url_edit.setText('https://api.qase.io/v1')
        form.addRow('Base URL:', self.qase_url_edit)
        
        layout.addLayout(form)
        
        # Test connection
        test_btn = QPushButton('🔌 Проверить подключение')
        test_btn.clicked.connect(self.test_qase_connection)
        layout.addWidget(test_btn)
        
        # Instructions
        instruction = QLabel(
            '<br><b>📋 Как получить API Token:</b><br>'
            '1. Войдите в <a href="https://app.qase.io/">Qase.io</a><br>'
            '2. Перейдите в Settings → API Tokens<br>'
            '3. Создайте новый токен<br>'
            '4. Скопируйте и вставьте в поле выше<br><br>'
            '<b>Project Code:</b> Найдите в URL вашего проекта<br>'
            'Например: https://app.qase.io/project/<b>ITS</b>'
        )
        instruction.setWordWrap(True)
        instruction.setOpenExternalLinks(True)
        layout.addWidget(instruction)
        
        layout.addStretch()
        return tab
    
    def toggle_password(self, line_edit):
        """Показать/скрыть пароль"""
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def load_all_settings(self):
        """Загрузить все настройки"""
        self.load_zoho_settings()
        self.load_google_settings()
        self.load_qase_settings()
    
    def load_zoho_settings(self):
        """Загрузить настройки Zoho"""
        if not self.zoho_env_path.exists():
            self.status_label.setText('⚠️ Файл zoho.env не найден')
            self.status_label.setStyleSheet('color: orange; padding: 5px;')
            return
        
        try:
            with open(self.zoho_env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            creds = {}
            for line in lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    creds[key.strip()] = value.strip()
            
            self.zoho_client_id_edit.setText(creds.get('ZOHO_CLIENT_ID', ''))
            self.zoho_client_secret_edit.setText(creds.get('ZOHO_CLIENT_SECRET', ''))
            self.zoho_access_token_edit.setText(creds.get('ZOHO_ACCESS_TOKEN', ''))
            self.zoho_refresh_token_edit.setText(creds.get('ZOHO_REFRESH_TOKEN', ''))
            self.zoho_portal_edit.setText(creds.get('ZOHO_PORTAL_NAME', ''))
            self.zoho_project_id_edit.setText(creds.get('ZOHO_PROJECT_ID', ''))
            
            region = creds.get('ZOHO_REGION', 'com')
            index = self.zoho_region_combo.findText(region)
            if index >= 0:
                self.zoho_region_combo.setCurrentIndex(index)
        
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить настройки Zoho:\n{e}')
    
    def load_google_settings(self):
        """Загрузить настройки Google"""
        if not self.google_json_path.exists():
            return
        
        try:
            with open(self.google_json_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.google_json_edit.setPlainText(content)
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить Google JSON:\n{e}')
    
    def load_qase_settings(self):
        """Загрузить настройки Qase"""
        if not self.qase_env_path.exists():
            return
        
        try:
            with open(self.qase_env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            creds = {}
            for line in lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    creds[key.strip()] = value.strip()
            
            self.qase_token_edit.setText(creds.get('QASE_API_TOKEN', ''))
            self.qase_project_edit.setText(creds.get('QASE_PROJECT_CODE', ''))
            self.qase_url_edit.setText(creds.get('QASE_BASE_URL', 'https://api.qase.io/v1'))
        
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить настройки Qase:\n{e}')
    
    def refresh_access_token(self):
        """Обновить Access Token через Refresh Token"""
        client_id = self.zoho_client_id_edit.text().strip()
        client_secret = self.zoho_client_secret_edit.text().strip()
        refresh_token = self.zoho_refresh_token_edit.text().strip()
        
        if not all([client_id, client_secret, refresh_token]):
            QMessageBox.warning(self, 'Ошибка', 'Заполните Client ID, Client Secret и Refresh Token!')
            return
        
        self.refresh_token_btn.setEnabled(False)
        self.status_label.setText('🔄 Обновление Access Token...')
        self.status_label.setStyleSheet('color: blue; padding: 5px;')
        
        self.token_thread = TokenRefreshThread(client_id, client_secret, refresh_token)
        self.token_thread.finished.connect(self.on_token_refreshed)
        self.token_thread.start()
    
    def on_token_refreshed(self, new_access_token, error):
        """Обработка обновлённого токена"""
        self.refresh_token_btn.setEnabled(True)
        
        if error:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось обновить токен:\n{error}')
            self.status_label.setText(f'❌ Ошибка: {error}')
            self.status_label.setStyleSheet('color: red; padding: 5px;')
            return
        
        self.zoho_access_token_edit.setText(new_access_token)
        QMessageBox.information(self, 'Успех', '✅ Access Token успешно обновлён!')
        self.status_label.setText('✅ Access Token обновлён')
    
    def launch_oauth_wizard(self):
        """Запуск OAuth Wizard для Zoho"""
        wizard = ZohoOAuthWizard(self)
        
        # Предзаполнить существующими значениями
        client_id = self.zoho_client_id_edit.text().strip()
        client_secret = self.zoho_client_secret_edit.text().strip()
        
        if client_id:
            wizard.client_id_input.setText(client_id)
        if client_secret:
            wizard.client_secret_input.setText(client_secret)
        
        if wizard.exec():
            # После успешного завершения - перезагрузить настройки
            self.load_zoho_settings()
            QMessageBox.information(
                self, 
                'Успех', 
                '✅ Токены Zoho успешно получены!\n\n'
                'Теперь вы можете использовать интеграцию с Zoho Projects.'
            )
            self.status_label.setText('✅ Zoho OAuth завершён')
            self.status_label.setStyleSheet('color: green; padding: 5px;')
        self.status_label.setStyleSheet('color: green; padding: 5px;')
    
    def fetch_projects(self):
        """Загрузить проекты из Zoho"""
        access_token = self.zoho_access_token_edit.text().strip()
        portal_name = self.zoho_portal_edit.text().strip()
        region = self.zoho_region_combo.currentText()
        
        if not access_token or not portal_name:
            QMessageBox.warning(self, 'Ошибка', 'Сначала обновите Access Token и укажите Portal Name!')
            return
        
        self.load_projects_btn.setEnabled(False)
        self.status_label.setText('🔄 Загрузка проектов...')
        self.status_label.setStyleSheet('color: blue; padding: 5px;')
        
        self.projects_thread = ProjectsFetchThread(access_token, portal_name, region)
        self.projects_thread.finished.connect(self.on_projects_received)
        self.projects_thread.start()
    
    def on_projects_received(self, projects, error):
        """Обработка списка проектов"""
        self.load_projects_btn.setEnabled(True)
        
        if error:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить проекты:\n{error}')
            self.status_label.setText(f'❌ Ошибка: {error}')
            self.status_label.setStyleSheet('color: red; padding: 5px;')
            return
        
        self.projects_list.clear()
        for project in projects:
            item = QListWidgetItem(f"{project.get('name', 'Unnamed')} (ID: {project.get('id', 'N/A')})")
            item.setData(Qt.ItemDataRole.UserRole, project.get('id'))
            self.projects_list.addItem(item)
        
        self.status_label.setText(f'✅ Загружено проектов: {len(projects)}')
        self.status_label.setStyleSheet('color: green; padding: 5px;')
    
    def on_project_selected(self, item):
        """Выбор проекта из списка"""
        project_id = item.data(Qt.ItemDataRole.UserRole)
        if project_id:
            self.zoho_project_id_edit.setText(str(project_id))
    
    def validate_google_json(self):
        """Проверить валидность Google JSON"""
        try:
            content = self.google_json_edit.toPlainText().strip()
            if not content:
                QMessageBox.warning(self, 'Ошибка', 'JSON пустой!')
                return
            
            data = json.loads(content)
            
            # Проверяем обязательные поля
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing = [f for f in required_fields if f not in data]
            
            if missing:
                QMessageBox.warning(
                    self, 'Ошибка', 
                    f'JSON неполный! Отсутствуют поля:\n{", ".join(missing)}'
                )
                return
            
            QMessageBox.information(
                self, 'Успех', 
                f'✅ JSON валидный!\n\nProject: {data.get("project_id")}\nEmail: {data.get("client_email")}'
            )
        
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, 'Ошибка', f'Невалидный JSON:\n{e}')
    
    def test_qase_connection(self):
        """Проверить подключение к Qase.io"""
        token = self.qase_token_edit.text().strip()
        project_code = self.qase_project_edit.text().strip()
        base_url = self.qase_url_edit.text().strip()
        
        if not token or not project_code:
            QMessageBox.warning(self, 'Ошибка', 'Заполните API Token и Project Code!')
            return
        
        try:
            import requests
            url = f"{base_url}/project/{project_code}"
            headers = {"Token": token}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            project_data = response.json().get('result', {})
            QMessageBox.information(
                self, 'Успех', 
                f'✅ Подключение успешно!\n\n'
                f'Project: {project_data.get("title", "N/A")}\n'
                f'Code: {project_data.get("code", "N/A")}'
            )
        
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось подключиться:\n{e}')
    
    def save_all_settings(self):
        """Сохранить все настройки"""
        try:
            # Создаём папку credentials если нет
            Config.get_credentials_path().mkdir(parents=True, exist_ok=True)
            
            # Zoho
            self.save_zoho_settings()
            
            # Google
            self.save_google_settings()
            
            # Qase
            self.save_qase_settings()
            
            QMessageBox.information(
                self, 'Успех', 
                '✅ Все настройки сохранены!\n\nПерезапустите приложение для применения изменений.'
            )
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить настройки:\n{e}')
    
    def save_zoho_settings(self):
        """Сохранить настройки Zoho"""
        # Backup
        if self.zoho_env_path.exists():
            backup_path = self.zoho_env_path.parent / 'zoho.env.backup'
            shutil.copy2(self.zoho_env_path, backup_path)
        
        content = f"""ZOHO_CLIENT_ID={self.zoho_client_id_edit.text().strip()}
ZOHO_CLIENT_SECRET={self.zoho_client_secret_edit.text().strip()}
ZOHO_REFRESH_TOKEN={self.zoho_refresh_token_edit.text().strip()}
ZOHO_ACCESS_TOKEN={self.zoho_access_token_edit.text().strip()}
ZOHO_PORTAL_NAME={self.zoho_portal_edit.text().strip()}
ZOHO_PROJECT_ID={self.zoho_project_id_edit.text().strip()}
ZOHO_REGION={self.zoho_region_combo.currentText()}
"""
        
        with open(self.zoho_env_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def save_google_settings(self):
        """Сохранить настройки Google"""
        content = self.google_json_edit.toPlainText().strip()
        if content:
            # Проверяем валидность
            json.loads(content)  # Бросит исключение если невалидный
            
            # Backup
            if self.google_json_path.exists():
                backup_path = self.google_json_path.parent / 'google_credentials.json.backup'
                shutil.copy2(self.google_json_path, backup_path)
            
            with open(self.google_json_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def save_qase_settings(self):
        """Сохранить настройки Qase"""
        # Backup
        if self.qase_env_path.exists():
            backup_path = self.qase_env_path.parent / 'qase.env.backup'
            shutil.copy2(self.qase_env_path, backup_path)
        
        content = f"""QASE_API_TOKEN={self.qase_token_edit.text().strip()}
QASE_PROJECT_CODE={self.qase_project_edit.text().strip()}
QASE_BASE_URL={self.qase_url_edit.text().strip()}
"""
        
        with open(self.qase_env_path, 'w', encoding='utf-8') as f:
            f.write(content)
