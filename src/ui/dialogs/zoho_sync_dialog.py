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
            if self.sync_type == "milestone":
                self.progress.emit(
                    f"📋 Синхронизация по milestone: {self.params['milestone_name']}"
                )
                stats = self.sync_service.sync_tasks_by_milestone(
                    self.params["milestone_name"]
                )

            elif self.sync_type == "tasklist":
                self.progress.emit(
                    f"📋 Синхронизация по tasklist: {self.params['tasklist_name']}"
                )
                stats = self.sync_service.sync_tasks_by_tasklist(
                    self.params["tasklist_name"]
                )

            elif self.sync_type == "filter":
                self.progress.emit("📋 Синхронизация по фильтрам")
                stats = self.sync_service.sync_tasks_by_filter(**self.params)

            else:
                stats = {"error": "Неизвестный тип синхронизации"}

            if "error" in stats:
                self.finished.emit({}, stats["error"])
            else:
                self.finished.emit(stats, "")

        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
            self.finished.emit({}, str(e))


class ZohoSyncDialog(QDialog):
    """Диалог синхронизации Zoho Projects (Tasks, Users, Defects)"""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.sync_thread = None

        self.setWindowTitle("Синхронизация Zoho Projects")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Вкладки
        tabs = QTabWidget()

        # Вкладка 1: Tasks
        tasks_tab = self.create_tasks_tab()
        tabs.addTab(tasks_tab, "📋 Tasks")

        # Вкладка 2: Users
        users_tab = self.create_users_tab()
        tabs.addTab(users_tab, "👥 Users")

        # Вкладка 3: Defects
        defects_tab = self.create_defects_tab()
        tabs.addTab(defects_tab, "🐛 Defects")

        layout.addWidget(tabs)

        # Прогресс
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: blue;")
        layout.addWidget(self.progress_label)

        # Кнопки
        layout.addStretch()
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.sync_button = QPushButton("🔄 Синхронизировать")
        self.sync_button.clicked.connect(self.start_sync)
        button_layout.addWidget(self.sync_button)

        self.cancel_button = QPushButton("❌ Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # По умолчанию Tasks
        tabs.setCurrentIndex(0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Неопределённый прогресс
        layout.addWidget(self.progress_bar)

        # === Кнопки ===
        buttons = QDialogButtonBox()
        self.sync_btn = buttons.addButton(
            "🚀 Синхронизировать", QDialogButtonBox.ButtonRole.AcceptRole
        )
        cancel_btn = buttons.addButton("Отмена", QDialogButtonBox.ButtonRole.RejectRole)

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

        if sync_type == "По Milestone (спринт)":
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

        elif sync_type == "По Tasklist":
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

        elif sync_type == "По фильтрам (даты, ответственные)":
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

    def create_users_tab(self):
        """Вкладка синхронизации пользователей"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            "👥 <b>Синхронизация пользователей из Zoho Projects</b><br><br>"
            "Загрузите список пользователей и создайте их в локальной БД."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        self.user_search_edit = QLineEdit()
        self.user_search_edit.setPlaceholderText("Введите имя или email...")
        search_layout.addWidget(self.user_search_edit)
        layout.addLayout(search_layout)

        # Список пользователей
        self.users_list = QListWidget()
        layout.addWidget(self.users_list)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.load_users_btn = QPushButton("📥 Загрузить пользователей")
        self.load_users_btn.clicked.connect(self.load_zoho_users)
        btn_layout.addWidget(self.load_users_btn)

        self.import_users_btn = QPushButton("✅ Импортировать выбранные")
        self.import_users_btn.clicked.connect(self.import_selected_users)
        btn_layout.addWidget(self.import_users_btn)

        layout.addLayout(btn_layout)

        return tab

    def create_defects_tab(self):
        """Вкладка синхронизации дефектов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            "🐛 <b>Синхронизация дефектов (багов) из Zoho Projects</b><br><br>"
            "Загрузите список дефектов и создайте их как FunctionalItem с type='Defect'."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Фильтр по статусу
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Статус:"))
        self.defect_status_combo = QComboBox()
        self.defect_status_combo.addItems(["All", "Open", "Closed", "In Progress"])
        status_layout.addWidget(self.defect_status_combo)
        layout.addLayout(status_layout)

        # Список дефектов
        self.defects_list = QListWidget()
        layout.addWidget(self.defects_list)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.load_defects_btn = QPushButton("📥 Загрузить дефекты")
        self.load_defects_btn.clicked.connect(self.load_zoho_defects)
        btn_layout.addWidget(self.load_defects_btn)

        self.import_defects_btn = QPushButton("✅ Импортировать выбранные")
        self.import_defects_btn.clicked.connect(self.import_selected_defects)
        btn_layout.addWidget(self.import_defects_btn)

        layout.addLayout(btn_layout)

        return tab

    def load_zoho_users(self):
        """Загрузка пользователей из Zoho"""
        from src.integrations.zoho.Zoho_api_client import ZohoAPI

        try:
            zoho = ZohoAPI()
            search_term = self.user_search_edit.text().strip()
            users = zoho.get_users(search_term if search_term else None)

            self.users_list.clear()
            for user in users:
                name = user.get("name", "Unknown")
                email = user.get("email", "")
                role = user.get("role", "")
                item_text = f"{name} ({email}) - {role}"
                self.users_list.addItem(item_text)

            self.progress_label.setText(f"✅ Загружено {len(users)} пользователей")
        except Exception as e:
            self.progress_label.setText(f"❌ Ошибка: {e}")

    def import_selected_users(self):
        """Импорт выбранных пользователей в БД"""
        from src.models import User

        selected_items = self.users_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Внимание", "Выберите пользователей для импорта")
            return

        imported_count = 0
        for item in selected_items:
            item_text = item.text()
            name = item_text.split(" (")[0]

            # Проверяем есть ли уже
            existing = self.session.query(User).filter_by(name=name).first()
            if existing:
                continue

            # Создаём нового
            new_user = User(name=name, is_active=1)
            self.session.add(new_user)
            imported_count += 1

        self.session.commit()
        self.progress_label.setText(f"✅ Импортировано {imported_count} пользователей")

    def load_zoho_defects(self):
        """Загрузка дефектов из Zoho"""
        from src.integrations.zoho.Zoho_api_client import ZohoAPI

        try:
            zoho = ZohoAPI()
            status = self.defect_status_combo.currentText()
            if status == "All":
                status = None
            defects = zoho.get_defects(status)

            self.defects_list.clear()
            for defect in defects:
                title = defect.get("title", "Unknown")
                defect_id = defect.get("defect_id", "")
                status = defect.get("status", "")
                item_text = f"#{defect_id}: {title} [{status}]"
                self.defects_list.addItem(item_text)

            self.progress_label.setText(f"✅ Загружено {len(defects)} дефектов")
        except Exception as e:
            self.progress_label.setText(f"❌ Ошибка: {e}")

    def import_selected_defects(self):
        """Импорт выбранных дефектов в БД"""
        from src.models import FunctionalItem

        selected_items = self.defects_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Внимание", "Выберите дефекты для импорта")
            return

        imported_count = 0
        for item in selected_items:
            item_text = item.text()
            # Парсим: #123: Title [Status]
            parts = item_text.split(": ", 1)
            defect_id = parts[0].replace("#", "") if len(parts) > 0 else ""
            rest = parts[1].split(" [") if len(parts) > 1 else ["", ""]
            title = rest[0] if len(rest) > 0 else item_text

            # Проверяем есть ли уже
            funcid = f"DEFECT:{defect_id}"
            existing = self.session.query(FunctionalItem).filter_by(functional_id=funcid).first()
            if existing:
                continue

            # Создаём новый
            new_defect = FunctionalItem(
                functional_id=funcid,
                title=title,
                type="Defect",
                description=f"Импортировано из Zoho (Defect #{defect_id})",
                is_crit=0,
                is_focus=0,
            )
            self.session.add(new_defect)
            imported_count += 1

        self.session.commit()
        self.progress_label.setText(f"✅ Импортировано {imported_count} дефектов")

    def start_sync(self):
        """Начать синхронизацию"""
        sync_type_map = {
            "По Milestone (спринт)": "milestone",
            "По Tasklist": "tasklist",
            "По фильтрам (даты, ответственные)": "filter",
        }

        sync_type = sync_type_map[self.sync_type_combo.currentText()]

        # Собираем параметры
        params = {}

        if sync_type == "milestone":
            milestone_name = self.milestone_edit.text().strip()
            if not milestone_name:
                QMessageBox.warning(self, "Ошибка", "Укажите название Milestone")
                return
            params["milestone_name"] = milestone_name

        elif sync_type == "tasklist":
            tasklist_name = self.tasklist_edit.text().strip()
            if not tasklist_name:
                QMessageBox.warning(self, "Ошибка", "Укажите название Tasklist")
                return
            params["tasklist_name"] = tasklist_name

        elif sync_type == "filter":
            params["created_after"] = self.date_start_edit.text().strip() or None
            params["created_before"] = self.date_end_edit.text().strip() or None
            params["owner_id"] = self.owner_id_edit.text().strip() or None

            if not any(
                [params["created_after"], params["created_before"], params["owner_id"]]
            ):
                QMessageBox.warning(self, "Ошибка", "Укажите хотя бы один фильтр")
                return

        # Создаём сервис
        try:
            from src.services.ZohoSyncService import ZohoSyncService

            sync_service = ZohoSyncService(self.session)

            # Проверяем подключение к Zoho
            if not sync_service.init_zoho_client():
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Не удалось подключиться к Zoho API.\n\n"
                    "Проверьте настройки в credentials/zoho.env",
                )
                return

            # Запускаем синхронизацию в фоновом потоке
            self.sync_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_label.setText("🚀 Синхронизация начата...")

            self.sync_thread = SyncThread(sync_service, sync_type, params)
            self.sync_thread.progress.connect(self.on_progress)
            self.sync_thread.finished.connect(self.on_sync_finished)
            self.sync_thread.start()

        except Exception as e:
            logger.error(f"Ошибка запуска синхронизации: {e}")
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось запустить синхронизацию:\n{e}"
            )
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
            self.progress_label.setText(f"❌ Ошибка: {error}")
            QMessageBox.critical(
                self, "Ошибка синхронизации", f"Не удалось синхронизировать:\n\n{error}"
            )
        else:
            # Формируем сообщение об успехе
            msg = f"""✅ Синхронизация завершена!

• Новых задач: {stats.get('new', 0)}
• Обновлено задач: {stats.get('updated', 0)}
• Ошибок: {stats.get('errors', 0)}

Задачи сохранены в локальной БД VoluptAS."""

            self.progress_label.setText("✅ Синхронизация завершена!")
            QMessageBox.information(self, "Синхронизация завершена", msg)
            self.accept()
