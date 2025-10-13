"""
Enhanced Zoho Settings Dialog - Расширенное управление настройками API

Возможности:
- Получение первой пары токенов через Authorization Code
- Автоматическое обновление Access Token
- Выбор проекта из списка доступных проектов
- Поддержка нескольких проектов с переключением
- Корректное сохранение настроек
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os
import shutil
from pathlib import Path


class TokenFetchThread(QThread):
    """Фоновый поток для получения токенов"""
    finished = pyqtSignal(dict, str)  # result, error_message
    
    def __init__(self, client_id, client_secret, auth_code, redirect_uri):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_code = auth_code
        self.redirect_uri = redirect_uri
    
    def run(self):
        try:
            import requests
            url = "https://accounts.zoho.com/oauth/v2/token"
            params = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": self.auth_code,
                "redirect_uri": self.redirect_uri
            }
            response = requests.post(url, data=params)
            response.raise_for_status()
            self.finished.emit(response.json(), "")
        except Exception as e:
            self.finished.emit({}, str(e))


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


class ZohoSettingsDialog(QDialog):
    """Расширенный диалог настроек Zoho API"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Настройки Zoho API')
        self.setMinimumWidth(700)
        self.setMinimumHeight(700)
        
        # Путь к credentials
        self.project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.env_path = self.project_root / 'credentials' / 'zoho.env'
        
        # Потоки для фоновых операций
        self.token_thread = None
        self.projects_thread = None
        
        self.init_ui()
        self.load_credentials()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # === TABS ===
        tabs = QTabWidget()
        
        # Tab 1: Credentials
        creds_tab = QWidget()
        creds_layout = QVBoxLayout(creds_tab)
        
        # Инфо
        info_label = QLabel(
            '⚙️ <b>Настройки интеграции с Zoho Projects</b><br><br>'
            'Настройте учётные данные для доступа к Zoho Projects API.<br>'
            '<font color="red">⚠️ Будьте осторожны при изменении этих данных!</font>'
        )
        info_label.setWordWrap(True)
        creds_layout.addWidget(info_label)
        
        # Форма credentials
        form = QFormLayout()
        
        # Client ID
        self.client_id_edit = QLineEdit()
        self.client_id_edit.setPlaceholderText('1000.XXXXXXXXXX...')
        form.addRow('* Client ID:', self.client_id_edit)
        
        # Client Secret
        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_edit.setPlaceholderText('Секретный ключ...')
        secret_layout = QHBoxLayout()
        secret_layout.addWidget(self.client_secret_edit)
        show_secret_btn = QPushButton('👁️ Показать')
        show_secret_btn.clicked.connect(lambda: self.toggle_password(self.client_secret_edit, show_secret_btn))
        secret_layout.addWidget(show_secret_btn)
        form.addRow('* Client Secret:', secret_layout)
        
        # Redirect URI
        self.redirect_uri_edit = QLineEdit()
        self.redirect_uri_edit.setPlaceholderText('https://your-redirect-uri.com')
        form.addRow('Redirect URI:', self.redirect_uri_edit)
        
        # Portal Name
        self.portal_edit = QLineEdit()
        self.portal_edit.setPlaceholderText('vrbgroup')
        form.addRow('* Portal Name:', self.portal_edit)
        
        # Region
        self.region_combo = QComboBox()
        self.region_combo.addItems(['com', 'eu', 'in', 'cn'])
        form.addRow('Region:', self.region_combo)
        
        creds_layout.addLayout(form)
        
        # Инструкция
        instruction = QLabel(
            '<br><b>📋 Как получить Client ID и Client Secret:</b><br>'
            '1. Перейдите в <a href="https://api-console.zoho.com/">Zoho API Console</a><br>'
            '2. Создайте Self Client или Server-based Application<br>'
            '3. Скопируйте Client ID и Client Secret'
        )
        instruction.setWordWrap(True)
        instruction.setOpenExternalLinks(True)
        creds_layout.addWidget(instruction)
        
        tabs.addTab(creds_tab, '🔐 Credentials')
        
        # Tab 2: Tokens
        tokens_tab = QWidget()
        tokens_layout = QVBoxLayout(tokens_tab)
        
        # Инфо о токенах
        tokens_info = QLabel(
            '<b>Управление токенами доступа</b><br><br>'
            'Если у вас ещё нет токенов, получите их через Authorization Code.<br>'
            'Если токены уже есть, можете просто проверить или обновить их.'
        )
        tokens_info.setWordWrap(True)
        tokens_layout.addWidget(tokens_info)
        
        # === STEP 1: Получение Authorization Code ===
        step1_group = QGroupBox('Шаг 1: Получение Authorization Code')
        step1_layout = QVBoxLayout(step1_group)
        
        step1_info = QLabel(
            '1. Перейдите по ссылке для получения Authorization Code:<br>'
            '<a href="https://accounts.zoho.com/oauth/v2/auth?response_type=code&client_id=YOUR_CLIENT_ID&scope=ZohoProjects.portals.ALL,ZohoProjects.projects.ALL&redirect_uri=YOUR_REDIRECT_URI&access_type=offline">Получить Authorization Code</a><br><br>'
            '2. Авторизуйтесь и скопируйте код из URL<br>'
            '3. Вставьте код ниже:'
        )
        step1_info.setWordWrap(True)
        step1_info.setOpenExternalLinks(True)
        step1_layout.addWidget(step1_info)
        
        self.auth_code_edit = QLineEdit()
        self.auth_code_edit.setPlaceholderText('1000.XXXXXXXXXX...')
        step1_layout.addWidget(self.auth_code_edit)
        
        self.get_tokens_btn = QPushButton('🔑 Получить Access и Refresh Token')
        self.get_tokens_btn.clicked.connect(self.fetch_tokens)
        step1_layout.addWidget(self.get_tokens_btn)
        
        tokens_layout.addWidget(step1_group)
        
        # === STEP 2: Токены ===
        step2_group = QGroupBox('Шаг 2: Токены доступа')
        step2_layout = QFormLayout(step2_group)
        
        # Access Token
        self.access_token_edit = QLineEdit()
        self.access_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.access_token_edit.setPlaceholderText('1000.XXXXXXXXXX...')
        access_layout = QHBoxLayout()
        access_layout.addWidget(self.access_token_edit)
        show_access_btn = QPushButton('👁️ Показать')
        show_access_btn.clicked.connect(lambda: self.toggle_password(self.access_token_edit, show_access_btn))
        access_layout.addWidget(show_access_btn)
        step2_layout.addRow('Access Token:', access_layout)
        
        # Refresh Token
        self.refresh_token_edit = QLineEdit()
        self.refresh_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.refresh_token_edit.setPlaceholderText('1000.XXXXXXXXXX...')
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(self.refresh_token_edit)
        show_refresh_btn = QPushButton('👁️ Показать')
        show_refresh_btn.clicked.connect(lambda: self.toggle_password(self.refresh_token_edit, show_refresh_btn))
        refresh_layout.addWidget(show_refresh_btn)
        step2_layout.addRow('Refresh Token:', refresh_layout)
        
        tokens_layout.addWidget(step2_group)
        tokens_layout.addStretch()
        
        tabs.addTab(tokens_tab, '🔑 Tokens')
        
        # Tab 3: Projects
        projects_tab = QWidget()
        projects_layout = QVBoxLayout(projects_tab)
        
        projects_info = QLabel(
            '<b>Выбор проекта</b><br><br>'
            'Нажмите "Загрузить проекты", чтобы получить список доступных проектов из Zoho.<br>'
            'Выберите нужный проект из списка или введите ID вручную.'
        )
        projects_info.setWordWrap(True)
        projects_layout.addWidget(projects_info)
        
        # Кнопка загрузки проектов
        self.load_projects_btn = QPushButton('📥 Загрузить проекты из Zoho')
        self.load_projects_btn.clicked.connect(self.fetch_projects)
        projects_layout.addWidget(self.load_projects_btn)
        
        # Список проектов
        self.projects_list = QListWidget()
        self.projects_list.itemClicked.connect(self.on_project_selected)
        projects_layout.addWidget(self.projects_list)
        
        # Ручной ввод Project ID
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel('Или введите вручную:'))
        self.project_id_edit = QLineEdit()
        self.project_id_edit.setPlaceholderText('1209515000001238053')
        manual_layout.addWidget(self.project_id_edit)
        projects_layout.addLayout(manual_layout)
        
        tabs.addTab(projects_tab, '📁 Projects')
        
        layout.addWidget(tabs)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.accepted.connect(self.save_credentials)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).setText('🔄 Сбросить')
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.load_credentials)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText('💾 Сохранить')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('❌ Отмена')
        layout.addWidget(buttons)
        
        # Status bar
        self.status_label = QLabel('Готов')
        self.status_label.setStyleSheet('color: gray; padding: 5px;')
        layout.addWidget(self.status_label)
    
    def toggle_password(self, line_edit, button):
        """Показать/скрыть пароль"""
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            button.setText('🙈 Скрыть')
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            button.setText('👁️ Показать')
    
    def load_credentials(self):
        """Загрузить credentials из файла"""
        if not self.env_path.exists():
            self.status_label.setText(f'⚠️ Файл не найден: {self.env_path}')
            self.status_label.setStyleSheet('color: orange; padding: 5px;')
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
            self.redirect_uri_edit.setText(creds.get('ZOHO_REDIRECT_URI', ''))
            self.portal_edit.setText(creds.get('ZOHO_PORTAL_NAME', ''))
            self.project_id_edit.setText(creds.get('ZOHO_PROJECT_ID', ''))
            
            region = creds.get('ZOHO_REGION', 'com')
            index = self.region_combo.findText(region)
            if index >= 0:
                self.region_combo.setCurrentIndex(index)
            
            self.status_label.setText('✅ Настройки загружены')
            self.status_label.setStyleSheet('color: green; padding: 5px;')
        
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить настройки:\\n{e}')
            self.status_label.setText(f'❌ Ошибка загрузки: {e}')
            self.status_label.setStyleSheet('color: red; padding: 5px;')
    
    def fetch_tokens(self):
        """Получить Access и Refresh Token через Authorization Code"""
        client_id = self.client_id_edit.text().strip()
        client_secret = self.client_secret_edit.text().strip()
        auth_code = self.auth_code_edit.text().strip()
        redirect_uri = self.redirect_uri_edit.text().strip()
        
        if not all([client_id, client_secret, auth_code]):
            QMessageBox.warning(self, 'Ошибка', 'Заполните Client ID, Client Secret и Authorization Code!')
            return
        
        self.get_tokens_btn.setEnabled(False)
        self.status_label.setText('🔄 Получение токенов...')
        self.status_label.setStyleSheet('color: blue; padding: 5px;')
        
        self.token_thread = TokenFetchThread(client_id, client_secret, auth_code, redirect_uri)
        self.token_thread.finished.connect(self.on_tokens_received)
        self.token_thread.start()
    
    def on_tokens_received(self, result, error):
        """Обработка полученных токенов"""
        self.get_tokens_btn.setEnabled(True)
        
        if error:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось получить токены:\\n{error}')
            self.status_label.setText(f'❌ Ошибка: {error}')
            self.status_label.setStyleSheet('color: red; padding: 5px;')
            return
        
        access_token = result.get('access_token', '')
        refresh_token = result.get('refresh_token', '')
        
        if not access_token or not refresh_token:
            QMessageBox.warning(self, 'Ошибка', f'Неполный ответ от сервера:\\n{result}')
            return
        
        self.access_token_edit.setText(access_token)
        self.refresh_token_edit.setText(refresh_token)
        
        QMessageBox.information(
            self, 'Успех', 
            '✅ Токены успешно получены!\\n\\n'
            'Access Token и Refresh Token заполнены.\\n'
            'Теперь сохраните настройки.'
        )
        self.status_label.setText('✅ Токены получены')
        self.status_label.setStyleSheet('color: green; padding: 5px;')
    
    def fetch_projects(self):
        """Получить список проектов из Zoho"""
        access_token = self.access_token_edit.text().strip()
        portal_name = self.portal_edit.text().strip()
        region = self.region_combo.currentText()
        
        if not access_token or not portal_name:
            QMessageBox.warning(self, 'Ошибка', 'Заполните Access Token и Portal Name!')
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
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить проекты:\\n{error}')
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
        
        if not projects:
            QMessageBox.information(self, 'Информация', 'Проектов не найдено или нет доступа.')
    
    def on_project_selected(self, item):
        """Выбор проекта из списка"""
        project_id = item.data(Qt.ItemDataRole.UserRole)
        if project_id:
            self.project_id_edit.setText(project_id)
            self.status_label.setText(f'✅ Выбран проект: {project_id}')
            self.status_label.setStyleSheet('color: green; padding: 5px;')
    
    def save_credentials(self):
        """Сохранить credentials в файл"""
        # Валидация
        if not self.client_id_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Client ID обязателен!')
            return
        
        if not self.portal_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Portal Name обязателен!')
            return
        
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Сохранить изменения?\\n\\n'
            '⚠️ Убедитесь, что данные корректны!',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Создаём директорию если не существует
            self.env_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Формируем содержимое
            content = f"""ZOHO_CLIENT_ID={self.client_id_edit.text().strip()}
ZOHO_CLIENT_SECRET={self.client_secret_edit.text().strip()}
ZOHO_AUTHORIZATION_CODE={self.auth_code_edit.text().strip()}
ZOHO_REDIRECT_URI={self.redirect_uri_edit.text().strip()}
ZOHO_REGION={self.region_combo.currentText()}
ZOHO_ACCESS_TOKEN={self.access_token_edit.text().strip()}
ZOHO_REFRESH_TOKEN={self.refresh_token_edit.text().strip()}
ZOHO_PORTAL_NAME={self.portal_edit.text().strip()}
ZOHO_PROJECT_ID={self.project_id_edit.text().strip()}
"""
            
            # Backup старого файла
            if self.env_path.exists():
                backup_path = self.env_path.parent / 'zoho.env.backup'
                shutil.copy2(self.env_path, backup_path)
                backup_msg = f'\\n\\n📦 Резервная копия: {backup_path}'
            else:
                backup_msg = ''
            
            # Сохраняем
            with open(self.env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            QMessageBox.information(
                self, 'Успех', 
                f'✅ Настройки сохранены!{backup_msg}\\n\\n'
                'Перезапустите приложение для применения изменений.'
            )
            self.status_label.setText('✅ Настройки сохранены')
            self.status_label.setStyleSheet('color: green; padding: 5px;')
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить настройки:\\n{e}')
            self.status_label.setText(f'❌ Ошибка сохранения: {e}')
            self.status_label.setStyleSheet('color: red; padding: 5px;')
