"""
Qase Sync Dialog - Диалог синхронизации с Qase.io

Для импорта/экспорта тест-кейсов из/в Qase.io
"""

import logging
from typing import List, Dict
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QComboBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from src.integrations.qase import QaseClient
from src.config import Config
from dotenv import dotenv_values
import os

logger = logging.getLogger(__name__)


class QaseImportThread(QThread):
    """Фоновый поток для импорта кейсов из Qase"""

    progress = pyqtSignal(int)  # 0-100
    finished = pyqtSignal(list, str)  # cases, error_message

    def __init__(self, client: QaseClient, suite_id: int = None):
        super().__init__()
        self.client = client
        self.suite_id = suite_id

    def run(self):
        try:
            logger.info(f"Начало импорта кейсов (suite_id: {self.suite_id})")
            self.progress.emit(10)

            cases = self.client.get_cases(suite_id=self.suite_id)

            self.progress.emit(100)
            logger.info(f"Импортировано {len(cases)} кейсов")
            self.finished.emit(cases, "")

        except Exception as e:
            logger.error(f"Ошибка импорта: {e}")
            self.finished.emit([], str(e))


class QaseSyncDialog(QDialog):
    """Диалог синхронизации с Qase.io"""

    def __init__(self, session=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🧪 Qase.io Синхронизация")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)

        self.session = session
        self.client = None
        self.import_thread = None

        self._load_credentials()
        self.init_ui()

    def _load_credentials(self):
        """Загрузить credentials Qase из qase.env"""
        try:
            qase_env = Config.get_credentials_path("qase.env")
            if qase_env.exists():
                env = dotenv_values(qase_env)
                token = env.get("QASE_API_TOKEN")
                project_code = env.get("QASE_PROJECT_CODE")

                if token and project_code:
                    try:
                        self.client = QaseClient(
                            api_token=token, project_code=project_code
                        )
                        logger.info("✅ QaseClient инициализирован из credentials")
                    except Exception as e:
                        logger.warning(f"Ошибка инициализации QaseClient: {e}")
                        self.client = None
                else:
                    logger.warning(
                        "Отсутствуют QASE_API_TOKEN или QASE_PROJECT_CODE в qase.env"
                    )
                    self.client = None
            else:
                logger.warning("Файл qase.env не найден")
                self.client = None
        except Exception as e:
            logger.error(f"Ошибка при загрузке credentials: {e}")
            self.client = None

    def init_ui(self):
        """Инициализировать UI"""
        layout = QVBoxLayout(self)

        # Статус подключения
        status_layout = QHBoxLayout()
        status_label = QLabel("Статус подключения:")
        if self.client:
            status_text = QLabel("✅ Подключено к Qase.io")
            status_text.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_text = QLabel("❌ Не подключено (проверьте credentials в Settings)")
            status_text.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Tabs
        tabs = QTabWidget()

        # === TAB 1: IMPORT ===
        import_tab = self._create_import_tab()
        tabs.addTab(import_tab, "📥 Импорт из Qase")

        # === TAB 2: EXPORT ===
        export_tab = self._create_export_tab()
        tabs.addTab(export_tab, "📤 Экспорт в Qase")

        # === TAB 3: MAPPING ===
        mapping_tab = self._create_mapping_tab()
        tabs.addTab(mapping_tab, "🔗 Маппинг FuncID ↔ Qase ID")

        layout.addWidget(tabs)

        # Кнопки
        button_layout = QHBoxLayout()
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def _create_import_tab(self) -> QWidget:
        """Создать вкладку импорта"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Инфо
        info = QLabel(
            "<b>📥 Импорт тест-кейсов из Qase.io</b><br><br>"
            "Выберите тест-сюиту и импортируйте кейсы в VoluptAS."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Выбор сюиты
        suite_layout = QHBoxLayout()
        suite_layout.addWidget(QLabel("Тест-сюита:"))
        self.import_suite_combo = QComboBox()
        self.import_suite_combo.setEnabled(bool(self.client))
        suite_layout.addWidget(self.import_suite_combo)

        load_suites_btn = QPushButton("🔄 Загрузить сюиты")
        load_suites_btn.clicked.connect(self._load_suites)
        load_suites_btn.setEnabled(bool(self.client))
        suite_layout.addWidget(load_suites_btn)
        layout.addLayout(suite_layout)

        # Список кейсов
        layout.addWidget(QLabel("<b>Кейсы для импорта:</b>"))
        self.import_cases_table = QTableWidget()
        self.import_cases_table.setColumnCount(4)
        self.import_cases_table.setHorizontalHeaderLabels(
            ["ID", "Название", "Suite", "Description"]
        )
        self.import_cases_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.import_cases_table)

        # Прогресс
        self.import_progress = QProgressBar()
        self.import_progress.setVisible(False)
        layout.addWidget(self.import_progress)

        # Кнопка импорта
        import_btn = QPushButton("📥 Импортировать выбранные кейсы")
        import_btn.clicked.connect(self._import_cases)
        import_btn.setEnabled(bool(self.client))
        layout.addWidget(import_btn)

        return tab

    def _create_export_tab(self) -> QWidget:
        """Создать вкладку экспорта"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Инфо
        info = QLabel(
            "<b>📤 Экспорт функционала в Qase.io</b><br><br>"
            "Экспортируйте функциональные элементы как тест-кейсы в Qase."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Placeholder текст
        placeholder = QLabel("🚧 Экспорт будет реализован в v0.4.1")
        placeholder.setStyleSheet("color: gray; padding: 20px;")
        layout.addWidget(placeholder)

        layout.addStretch()
        return tab

    def _create_mapping_tab(self) -> QWidget:
        """Создать вкладку маппинга"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Инфо
        info = QLabel(
            "<b>🔗 Маппинг FuncID ↔ Qase Case ID</b><br><br>"
            "Связывает функциональные элементы с тест-кейсами."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Placeholder текст
        placeholder = QLabel("🚧 Маппинг будет реализован в v0.4.1")
        placeholder.setStyleSheet("color: gray; padding: 20px;")
        layout.addWidget(placeholder)

        layout.addStretch()
        return tab

    def _load_suites(self):
        """Загрузить список тест-сюит"""
        if not self.client:
            QMessageBox.warning(self, "Ошибка", "Не подключено к Qase")
            return

        try:
            suites = self.client.get_suites()

            self.import_suite_combo.clear()
            for suite in suites:
                suite_id = suite.get("id")
                title = suite.get("title", "Unknown")
                self.import_suite_combo.addItem(f"{title} (ID: {suite_id})", suite_id)

            if not suites:
                QMessageBox.information(self, "Информация", "Сюит не найдено")
            else:
                logger.info(f"Загружено {len(suites)} сюит")

        except Exception as e:
            logger.error(f"Ошибка загрузки сюит: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сюиты:\n{e}")

    def _import_cases(self):
        """Импортировать кейсы из выбранной сюиты"""
        if not self.client:
            QMessageBox.warning(self, "Ошибка", "Не подключено к Qase")
            return

        if self.import_suite_combo.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите сюиты")
            return

        suite_id = self.import_suite_combo.currentData()

        logger.info(f"Начало импорта кейсов из сюиты {suite_id}")

        self.import_progress.setVisible(True)
        self.import_progress.setValue(0)

        self.import_thread = QaseImportThread(self.client, suite_id)
        self.import_thread.progress.connect(self.import_progress.setValue)
        self.import_thread.finished.connect(self._on_import_finished)
        self.import_thread.start()

    def _on_import_finished(self, cases: List[Dict], error: str):
        """Обработка завершения импорта"""
        self.import_progress.setVisible(False)

        if error:
            logger.error(f"Ошибка импорта: {error}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать:\n{error}")
            return

        # Показать таблицу импортированных кейсов
        self.import_cases_table.setRowCount(0)

        for i, case in enumerate(cases):
            row = i
            self.import_cases_table.insertRow(row)

            # ID
            id_item = QTableWidgetItem(str(case.get("id", "")))
            self.import_cases_table.setItem(row, 0, id_item)

            # Название
            title = case.get("title", "")
            title_item = QTableWidgetItem(title)
            self.import_cases_table.setItem(row, 1, title_item)

            # Suite
            suite_id = case.get("suite_id", "")
            suite_item = QTableWidgetItem(str(suite_id))
            self.import_cases_table.setItem(row, 2, suite_item)

            # Description
            desc = case.get("description", "")[:100]
            desc_item = QTableWidgetItem(desc)
            self.import_cases_table.setItem(row, 3, desc_item)

        logger.info(f"✅ Импортировано {len(cases)} кейсов")
        QMessageBox.information(
            self, "✅ Успех", f"Импортировано {len(cases)} кейсов из Qase.io"
        )
