"""
User Manager - Управление справочником сотрудников

Окно для CRUD операций с пользователями и синхронизации с Zoho
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction
from src.db import SessionLocal
from src.models import User
from src.integrations.zoho.Zoho_api_client import ZohoAPI
from src.utils.smart_merge import MergeStrategy


class ZohoSyncThread(QThread):
    """Поток для синхронизации с Zoho в фоне"""

    finished = pyqtSignal(list, str)  # users, error_message

    def run(self):
        try:
            print("[DEBUG] Запуск Zoho Sync Thread...")
            client = ZohoAPI()
            print("[DEBUG] ZohoAPI инициализирован")
            users_data = client.get_users()
            print(
                f"[DEBUG] Получено пользователей: {len(users_data) if users_data else 0}"
            )
            if not users_data:
                self.finished.emit(
                    [],
                    "Не удалось получить данные пользователей из Zoho. Проверьте настройки OAuth scope.",
                )
            else:
                self.finished.emit(users_data, "")
        except Exception as e:
            print(f"[ERROR] Zoho Sync Thread: {e}")
            import traceback

            traceback.print_exc()
            self.finished.emit([], str(e))


class UserEditDialog(QDialog):
    """Диалог создания/редактирования пользователя"""

    # Предустановленные должности
    POSITIONS = [
        "",
        "QA Engineer",
        "QA Team Lead",
        "QA Tech Lead",
        "Frontend Developer",
        "Frontend Lead",
        "Backend Tech Developer",
        "Backend Tech Lead",
        "DevOps Engineer",
        "Project Manager",
        "Product Owner",
        "Business Analyst",
        "Designer",
        "Content Manager",
        "Other",
    ]

    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.user = user if user else User()
        self.is_new = user is None
        self.setWindowTitle(
            "Новый сотрудник" if self.is_new else f"Редактирование: {user.name}"
        )
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        # Поля
        self.name_edit = QLineEdit(self.user.name or "")

        # Должность - выпадающий список с возможностью редактирования
        self.position_combo = QComboBox()
        self.position_combo.setEditable(True)
        self.position_combo.addItems(self.POSITIONS)
        if self.user.position:
            self.position_combo.setCurrentText(self.user.position)
        self.email_edit = QLineEdit(self.user.email or "")
        self.zoho_id_edit = QLineEdit(self.user.zoho_id or "")
        self.github_edit = QLineEdit(self.user.github_username or "")
        self.is_active_check = QCheckBox()
        self.is_active_check.setChecked(
            bool(self.user.is_active if hasattr(self.user, "is_active") else 1)
        )
        self.notes_edit = QTextEdit(self.user.notes or "")
        self.notes_edit.setMaximumHeight(80)

        layout.addRow("* Имя:", self.name_edit)
        layout.addRow("Должность:", self.position_combo)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Zoho ID:", self.zoho_id_edit)
        layout.addRow("GitHub:", self.github_edit)
        layout.addRow("Активен:", self.is_active_check)
        layout.addRow("Заметки:", self.notes_edit)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Имя обязательно для заполнения")
            return

        self.user.name = name
        self.user.position = self.position_combo.currentText().strip() or None
        self.user.email = self.email_edit.text().strip() or None
        self.user.zoho_id = self.zoho_id_edit.text().strip() or None
        self.user.github_username = self.github_edit.text().strip() or None
        self.user.is_active = 1 if self.is_active_check.isChecked() else 0
        self.user.notes = self.notes_edit.toPlainText().strip() or None

        self.accept()


class UserManagerWindow(QMainWindow):
    """Главное окно управления пользователями"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = SessionLocal()
        self.current_users = []
        self.sync_thread = None
        self.init_ui()
        self.load_users()

    def init_ui(self):
        self.setWindowTitle("Управление сотрудниками")
        self.setGeometry(200, 200, 1000, 600)

        # Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        close_action = QAction("Закрыть", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # Тулбар
        toolbar = QToolBar("Главная")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.load_users)
        toolbar.addAction(refresh_action)

        add_action = QAction("➕ Добавить", self)
        add_action.triggered.connect(self.add_user)
        toolbar.addAction(add_action)

        edit_action = QAction("✏️ Редактировать", self)
        edit_action.triggered.connect(self.edit_user)
        toolbar.addAction(edit_action)

        delete_action = QAction("🗑️ Удалить", self)
        delete_action.triggered.connect(self.delete_user)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        export_action = QAction("📥 Экспорт из Zoho", self)
        export_action.triggered.connect(self.export_from_zoho)
        toolbar.addAction(export_action)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Имя, должность, email...")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Имя", "Должность", "Email", "Zoho ID", "GitHub", "Активен"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_user)
        self.table.hideColumn(0)  # Скрыть ID
        layout.addWidget(self.table)

        # Статус-бар
        self.statusBar().showMessage("Готов")

    def load_users(self):
        """Загрузить пользователей из БД"""
        self.current_users = self.session.query(User).order_by(User.name).all()
        self.populate_table(self.current_users)
        self.statusBar().showMessage(
            f"✅ Загружено: {len(self.current_users)} сотрудников"
        )

    def populate_table(self, users):
        """Заполнить таблицу данными"""
        self.table.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(user.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(user.name or ""))
            self.table.setItem(row_idx, 2, QTableWidgetItem(user.position or ""))
            self.table.setItem(row_idx, 3, QTableWidgetItem(user.email or ""))
            self.table.setItem(row_idx, 4, QTableWidgetItem(user.zoho_id or ""))
            self.table.setItem(row_idx, 5, QTableWidgetItem(user.github_username or ""))
            self.table.setItem(
                row_idx, 6, QTableWidgetItem("✓" if user.is_active else "")
            )
        self.table.resizeColumnsToContents()

    def filter_table(self):
        """Фильтрация таблицы по поиску"""
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col)
                and search_text in self.table.item(row, col).text().lower()
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    def add_user(self):
        """Добавить нового пользователя"""
        dialog = UserEditDialog(parent=self)
        if dialog.exec():
            try:
                self.session.add(dialog.user)
                self.session.commit()
                self.load_users()
                self.statusBar().showMessage(f"✅ Добавлен: {dialog.user.name}")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить:\n{e}")

    def edit_user(self):
        """Редактировать выбранного пользователя"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Внимание", "Выберите сотрудника")
            return

        user = self.current_users[selected]
        dialog = UserEditDialog(user, self)
        if dialog.exec():
            try:
                self.session.commit()
                self.load_users()
                self.statusBar().showMessage(f"✅ Сохранено: {user.name}")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def delete_user(self):
        """Удалить выбранного пользователя"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Внимание", "Выберите сотрудника")
            return

        user = self.current_users[selected]
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить:\n{user.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(user)
                self.session.commit()
                self.load_users()
                self.statusBar().showMessage(f"✅ Удалён: {user.name}")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить:\n{e}")

    def export_from_zoho(self):
        """Экспорт пользователей из Zoho"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Экспортировать пользователей из Zoho?\n\n"
            "Уже существующие пользователи будут обновлены.\n"
            "Это может занять некоторое время.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.statusBar().showMessage("📥 Экспорт из Zoho...")
        self.sync_thread = ZohoSyncThread()
        self.sync_thread.finished.connect(self.on_sync_finished)
        self.sync_thread.start()

    def on_sync_finished(self, users_data, error):
        """Обработка результата экспорта"""
        if error:
            error_msg = f"Не удалось экспортировать из Zoho:\n{error}"
            if "OAuth scope" in error or "Invalid" in error:
                error_msg += "\n\n⚠️ Возможно, нужно перезапустить OAuth Wizard с правильными scope.\nПерейдите в Настройки → Zoho → OAuth Wizard"
            QMessageBox.critical(self, "Ошибка экспорта", error_msg)
            self.statusBar().showMessage("❌ Ошибка экспорта")
            return

        # Импортируем пользователей
        added_count = 0
        updated_count = 0

        for user_data in users_data:
            try:
                # Ищем по zoho_id
                existing = (
                    self.session.query(User)
                    .filter_by(zoho_id=user_data.get("id"))
                    .first()
                )

                if existing:
                    # Умное слияние
                    merge_fields = MergeStrategy.merge_user(existing, user_data)
                    for field, value in merge_fields.items():
                        setattr(existing, field, value)
                    updated_count += 1
                else:
                    # Создаём нового
                    new_user = User(
                        name=user_data.get("name", f'User {user_data.get("id")}'),
                        email=user_data.get("email"),
                        position=user_data.get("position"),
                        zoho_id=user_data.get("id"),
                        is_active=1,
                    )
                    self.session.add(new_user)
                    added_count += 1

                self.session.commit()
            except Exception as e:
                self.session.rollback()
                print(f"Ошибка при импорте пользователя {user_data}: {e}")

        self.load_users()
        message = (
            f"✅ Экспорт завершён: добавлено {added_count}, обновлено {updated_count}"
        )
        self.statusBar().showMessage(message)
        QMessageBox.information(self, "Экспорт завершён", message)

    def closeEvent(self, event):
        """Закрытие окна"""
        if self.sync_thread and self.sync_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Экспорт ещё выполняется. Всё равно закрыть?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.sync_thread.terminate()

        self.session.close()
        event.accept()
