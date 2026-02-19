"""
Zoho OAuth Wizard - мастер получения токенов через OAuth flow

Пошаговый процесс:
1. Ввод Client ID и Client Secret
2. Генерация authorization URL
3. Получение authorization code из браузера
4. Автоматическое получение refresh_token и access_token
5. Сохранение в credentials/zoho.env
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
import requests
import os
from pathlib import Path


class OAuthTokenThread(QThread):
    """Поток для получения токенов в фоне"""

    finished = pyqtSignal(dict, str)  # tokens_data, error_message

    def __init__(self, client_id, client_secret, auth_code, redirect_uri):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_code = auth_code
        self.redirect_uri = redirect_uri

    def run(self):
        try:
            url = "https://accounts.zoho.com/oauth/v2/token"
            params = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": self.auth_code,
                "redirect_uri": self.redirect_uri,
            }

            response = requests.post(url, data=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.finished.emit(data, "")
            else:
                error = f"HTTP {response.status_code}: {response.text}"
                self.finished.emit({}, error)
        except Exception as e:
            self.finished.emit({}, str(e))


class ZohoOAuthWizard(QDialog):
    """Мастер OAuth авторизации Zoho"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zoho OAuth Wizard")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self.tokens_data = {}
        self.thread = None

        # Дефолтные значения
        self.redirect_uri = "https://www.zoho.com/projects/"

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel("🔐 Zoho OAuth Authorization")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(
            "Этот мастер поможет получить токены доступа к Zoho Projects API.\n"
            "Следуйте инструкциям на каждом шаге."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(10)

        # Стек виджетов для шагов
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Шаг 1: Client ID & Secret
        self.stack.addWidget(self.create_step1())

        # Шаг 2: Authorization URL
        self.stack.addWidget(self.create_step2())

        # Шаг 3: Authorization Code
        self.stack.addWidget(self.create_step3())

        # Шаг 4: Получение токенов
        self.stack.addWidget(self.create_step4())

        # Шаг 5: Успех
        self.stack.addWidget(self.create_step5())

        # Кнопки навигации
        button_layout = QHBoxLayout()

        self.back_btn = QPushButton("◀ Назад")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        button_layout.addWidget(self.back_btn)

        button_layout.addStretch()

        self.next_btn = QPushButton("Далее ▶")
        self.next_btn.clicked.connect(self.go_next)
        button_layout.addWidget(self.next_btn)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Прогресс
        self.progress = QLabel("Шаг 1 из 5")
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress)

    def create_step1(self):
        """Шаг 1: Ввод Client ID и Secret"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<h3>📋 Шаг 1: Client ID и Client Secret</h3>"))

        info = QLabel(
            "<b>Где взять Client ID и Secret?</b><br><br>"
            '1. Откройте <a href="https://api-console.zoho.com/">Zoho API Console</a><br>'
            "2. Создайте новое приложение (Server-based Applications)<br>"
            "3. Скопируйте Client ID и Client Secret<br><br>"
            "<b>Redirect URI:</b> https://www.zoho.com/projects/"
        )
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()

        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("1000.XXXXXXXXXXXXXXXXXXXXXXXX")
        form.addRow("* Client ID:", self.client_id_input)

        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_input.setPlaceholderText("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        form.addRow("* Client Secret:", self.client_secret_input)

        self.redirect_uri_input = QLineEdit(self.redirect_uri)
        form.addRow("Redirect URI:", self.redirect_uri_input)

        layout.addLayout(form)
        layout.addStretch()

        return widget

    def create_step2(self):
        """Шаг 2: Authorization URL"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<h3>🔗 Шаг 2: Authorization URL</h3>"))

        info = QLabel(
            "<b>Что нужно сделать?</b><br><br>"
            '1. Нажмите кнопку "Открыть в браузере"<br>'
            "2. Авторизуйтесь в Zoho (если ещё не авторизованы)<br>"
            "3. Разрешите доступ к Zoho Projects<br>"
            '4. Скопируйте "code" из URL после редиректа<br><br>'
            "<b>Пример URL после редиректа:</b><br>"
            "<code>https://www.zoho.com/projects/?code=<b>1000.xxxxx</b>&...</code>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.auth_url_text = QTextEdit()
        self.auth_url_text.setReadOnly(True)
        self.auth_url_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Authorization URL:"))
        layout.addWidget(self.auth_url_text)

        open_btn = QPushButton("🌐 Открыть в браузере")
        open_btn.clicked.connect(self.open_auth_url)
        layout.addWidget(open_btn)

        layout.addStretch()

        return widget

    def create_step3(self):
        """Шаг 3: Ввод Authorization Code"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<h3>🔑 Шаг 3: Authorization Code</h3>"))

        info = QLabel(
            "<b>Вставьте код авторизации:</b><br><br>"
            "После редиректа в браузере скопируйте значение параметра <b>code</b> из URL.<br><br>"
            "<b>Пример:</b><br>"
            "https://www.zoho.com/projects/?<b>code=1000.xxxxx</b>&...<br><br>"
            'Вставьте только сам код (без "code="):'
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.auth_code_input = QLineEdit()
        self.auth_code_input.setPlaceholderText("1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        layout.addWidget(QLabel("* Authorization Code:"))
        layout.addWidget(self.auth_code_input)

        layout.addStretch()

        return widget

    def create_step4(self):
        """Шаг 4: Получение токенов"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<h3>⏳ Шаг 4: Получение токенов</h3>"))

        self.step4_info = QLabel('Нажмите "Далее" для получения токенов...')
        self.step4_info.setWordWrap(True)
        layout.addWidget(self.step4_info)

        self.step4_progress = QProgressBar()
        self.step4_progress.setRange(0, 0)  # Indeterminate
        self.step4_progress.setVisible(False)
        layout.addWidget(self.step4_progress)

        self.step4_log = QTextEdit()
        self.step4_log.setReadOnly(True)
        self.step4_log.setMaximumHeight(200)
        layout.addWidget(self.step4_log)

        layout.addStretch()

        return widget

    def create_step5(self):
        """Шаг 5: Успех"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<h3>✅ Успех!</h3>"))

        self.step5_info = QLabel()
        self.step5_info.setWordWrap(True)
        layout.addWidget(self.step5_info)

        self.step5_details = QTextEdit()
        self.step5_details.setReadOnly(True)
        self.step5_details.setMaximumHeight(200)
        layout.addWidget(self.step5_details)

        layout.addStretch()

        finish_btn = QPushButton("✅ Завершить")
        finish_btn.clicked.connect(self.accept)
        layout.addWidget(finish_btn)

        return widget

    def go_next(self):
        """Переход на следующий шаг"""
        current = self.stack.currentIndex()

        if current == 0:  # Шаг 1 -> 2
            if not self.validate_step1():
                return
            self.prepare_step2()
            self.stack.setCurrentIndex(1)
            self.back_btn.setEnabled(True)

        elif current == 1:  # Шаг 2 -> 3
            self.stack.setCurrentIndex(2)

        elif current == 2:  # Шаг 3 -> 4
            if not self.validate_step3():
                return
            self.stack.setCurrentIndex(3)
            self.next_btn.setEnabled(False)
            self.request_tokens()

        elif current == 3:  # Шаг 4 -> 5 (auto)
            pass

        elif current == 4:  # Finish
            self.accept()

        self.update_progress()

    def go_back(self):
        """Возврат на предыдущий шаг"""
        current = self.stack.currentIndex()
        if current > 0:
            self.stack.setCurrentIndex(current - 1)
            if current == 1:
                self.back_btn.setEnabled(False)
        self.update_progress()

    def update_progress(self):
        """Обновить прогресс-бар"""
        step = self.stack.currentIndex() + 1
        self.progress.setText(f"Шаг {step} из 5")

    def validate_step1(self):
        """Валидация шага 1"""
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()

        if not client_id or not client_secret:
            QMessageBox.warning(self, "Ошибка", "Заполните Client ID и Client Secret")
            return False

        return True

    def prepare_step2(self):
        """Подготовка шага 2"""
        client_id = self.client_id_input.text().strip()
        redirect_uri = self.redirect_uri_input.text().strip()

        # Генерация authorization URL
        # Полный набор скопов для Zoho Projects + Bug Tracker + WorkDrive
        scopes = [
            "ZohoProjects.portals.ALL",
            "ZohoProjects.projects.ALL",
            "ZohoProjects.activities.ALL",
            "ZohoProjects.feeds.ALL",
            "ZohoProjects.status.ALL",
            "ZohoProjects.milestones.ALL",
            "ZohoProjects.tasklists.ALL",
            "ZohoProjects.tasks.ALL",
            "ZohoProjects.timesheets.ALL",
            "ZohoProjects.bugs.ALL",
            "ZohoProjects.events.ALL",
            "ZohoProjects.forums.ALL",
            "ZohoProjects.clients.ALL",
            "ZohoProjects.users.ALL",
            "ZohoProjects.documents.ALL",
            "ZohoProjects.search.ALL",
            "ZohoProjects.tags.ALL",
            "ZohoProjects.calendar.ALL",
            "ZohoProjects.integrations.ALL",
            "ZohoProjects.projectgroups.ALL",
            "ZohoProjects.entity_properties.ALL",
            "ZohoBugTracker.bugs.ALL",
            "ZohoBugTracker.milestones.ALL",
            "ZohoBugTracker.tasklists.ALL",
            "ZohoBugTracker.projects.ALL",
            "ZohoBugTracker.users.ALL",
            "ZohoBugTracker.status.ALL",
            "ZohoPC.files.ALL",
            "WorkDrive.workspace.ALL",
            "WorkDrive.files.ALL",
            "WorkDrive.team.ALL",
        ]

        auth_url = (
            f"https://accounts.zoho.com/oauth/v2/auth?"
            f"scope={','.join(scopes)}&"
            f"client_id={client_id}&"
            f"response_type=code&"
            f"redirect_uri={redirect_uri}&"
            f"access_type=offline"
        )

        self.auth_url = auth_url
        self.auth_url_text.setPlainText(auth_url)

    def open_auth_url(self):
        """Открыть authorization URL в браузере"""
        QDesktopServices.openUrl(QUrl(self.auth_url))

    def validate_step3(self):
        """Валидация шага 3"""
        auth_code = self.auth_code_input.text().strip()

        if not auth_code:
            QMessageBox.warning(self, "Ошибка", "Введите authorization code")
            return False

        return True

    def request_tokens(self):
        """Запрос токенов"""
        self.step4_info.setText("⏳ Получение токенов...")
        self.step4_progress.setVisible(True)
        self.step4_log.append("🔄 Отправка запроса к Zoho OAuth...")

        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        auth_code = self.auth_code_input.text().strip()
        redirect_uri = self.redirect_uri_input.text().strip()

        self.thread = OAuthTokenThread(
            client_id, client_secret, auth_code, redirect_uri
        )
        self.thread.finished.connect(self.on_tokens_received)
        self.thread.start()

    def on_tokens_received(self, data, error):
        """Обработка полученных токенов"""
        self.step4_progress.setVisible(False)

        if error:
            self.step4_info.setText(f"❌ Ошибка: {error}")
            self.step4_log.append(f"\n❌ ОШИБКА:\n{error}")
            self.next_btn.setEnabled(True)
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось получить токены:\n{error}"
            )
            return

        if not data.get("access_token"):
            error_msg = f"Неожиданный ответ от сервера: {data}"
            self.step4_info.setText(f"❌ Ошибка")
            self.step4_log.append(f"\n❌ {error_msg}")
            self.next_btn.setEnabled(True)
            QMessageBox.critical(self, "Ошибка", error_msg)
            return

        self.tokens_data = data

        # Сохранение токенов
        try:
            self.save_tokens(data)
            self.step4_log.append("\n✅ Токены успешно получены!")
            self.step4_log.append(f'✅ Access Token: {data["access_token"][:20]}...')
            self.step4_log.append(
                f'✅ Refresh Token: {data.get("refresh_token", "N/A")[:20]}...'
            )
            self.step4_log.append(f"✅ Токены сохранены в credentials/zoho.env")

            # Переход на шаг 5
            self.prepare_step5()
            self.stack.setCurrentIndex(4)
            self.next_btn.setText("Завершить")
            self.next_btn.setEnabled(True)
            self.update_progress()

        except Exception as e:
            self.step4_log.append(f"\n❌ Ошибка сохранения: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить токены:\n{e}")
            self.next_btn.setEnabled(True)

    def save_tokens(self, data):
        """Сохранение токенов в credentials/zoho.env"""
        project_root = Path(__file__).parent.parent.parent.parent
        env_path = project_root / "credentials" / "zoho.env"

        # Читаем существующий файл
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Обновляем токены
        with open(env_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith("ZOHO_ACCESS_TOKEN="):
                    f.write(f'ZOHO_ACCESS_TOKEN={data["access_token"]}\n')
                elif line.startswith("ZOHO_REFRESH_TOKEN="):
                    refresh_token = data.get("refresh_token", "")
                    f.write(f"ZOHO_REFRESH_TOKEN={refresh_token}\n")
                elif line.startswith("ZOHO_CLIENT_ID="):
                    f.write(f"ZOHO_CLIENT_ID={self.client_id_input.text().strip()}\n")
                elif line.startswith("ZOHO_CLIENT_SECRET="):
                    f.write(
                        f"ZOHO_CLIENT_SECRET={self.client_secret_input.text().strip()}\n"
                    )
                else:
                    f.write(line)

    def prepare_step5(self):
        """Подготовка шага 5"""
        info = (
            "<b>✅ Авторизация успешно завершена!</b><br><br>"
            "Токены доступа к Zoho Projects API получены и сохранены.<br><br>"
            "Теперь вы можете:<br>"
            "• Импортировать пользователей из Zoho<br>"
            "• Синхронизировать задачи и баги<br>"
            "• Использовать все возможности интеграции<br><br>"
            "<b>Токены автоматически обновляются при необходимости.</b>"
        )
        self.step5_info.setText(info)

        details = f"""
Сохранено в: credentials/zoho.env

Access Token: {self.tokens_data.get('access_token', 'N/A')[:30]}...
Refresh Token: {self.tokens_data.get('refresh_token', 'N/A')[:30]}...
Expires in: {self.tokens_data.get('expires_in', 'N/A')} seconds

Client ID: {self.client_id_input.text().strip()}
"""
        self.step5_details.setPlainText(details)
