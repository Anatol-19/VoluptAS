"""
Главное окно приложения VoluptAS

Содержит основной интерфейс с таблицей, графом и панелями управления
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStatusBar,
    QMenuBar,
    QMenu,
    QToolBar,
    QPushButton,
    QMessageBox,
    QDialog,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon
from src.config import Config
from src.ui.widgets.main_tabs_widget import MainTabsWidget
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.dialogs.report_generator_dialog import ReportGeneratorDialog
from src.ui.dialogs.zoho_sync_dialog import ZohoSyncDialog
from src.ui.dialogs.entity_editor import EntityEditorDialog  # Добавлен импорт
from src.ui.dialogs.import_dialogs import ImportFromCsvDialog
from src.ui.dialogs.export_dialogs import ExportToCsvDialog
from src.ui.dialogs.project_dialogs import ProjectSelectorDialog as ProjectManagerDialog
from src.ui.dialogs.bdd_manager import BDDManagerDialog


class MainWindow(QMainWindow):
    """
    Главное окно приложения

    Инкремент 0: Базовое пустое окно с заголовком и статус-баром
    В следующих инкрементах добавим:
    - Таблицу функциональных элементов
    - Граф связей
    - Панели фильтрации
    - Меню и тулбары
    """

    def __init__(self, config: Config):
        """
        Инициализация главного окна

        Args:
            config: Объект конфигурации приложения
        """
        super().__init__()
        self.config = config
        self._init_ui()

    def _init_ui(self):
        """
        Инициализация пользовательского интерфейса
        """
        # Основные настройки окна
        self.setWindowTitle(self.config.WINDOW_TITLE)
        self.setGeometry(100, 100, self.config.WINDOW_WIDTH, self.config.WINDOW_HEIGHT)

        # Создание центрального виджета
        self._create_central_widget()

        # Создание меню
        self._create_menu_bar()

        # Создание тулбара
        self._create_toolbar()

        # Создание статус-бара
        self._create_status_bar()

    def _create_central_widget(self):
        """
        Создание центрального виджета с табами

        Новая архитектура: 5 табов для разных представлений
        """
        from src.ui.widgets.main_tabs_widget import MainTabsWidget

        # Создание главного виджета с табами
        self.main_tabs = MainTabsWidget()
        self.setCentralWidget(self.main_tabs)

        # Подключение сигналов
        self.main_tabs.tab_changed.connect(self._on_tab_changed)

        # Настройка горячих клавиш (Ctrl+1/2/3/4/5)
        self.main_tabs.setup_hotkeys()

    def _create_menu_bar(self):
        """
        Создание меню приложения

        В Инкременте 0 - базовые пункты меню
        """
        menubar = self.menuBar()

        # Меню "Файл"
        file_menu = menubar.addMenu("&Файл")

        exit_action = QAction("&Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Выход из приложения")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Справка"
        help_menu = menubar.addMenu("&Справка")

        about_action = QAction("&О программе", self)
        about_action.setStatusTip("Информация о программе")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """
        Создание тулбара с основными действиями

        В Инкременте 0 - пустой тулбар
        В следующих инкрементах добавим кнопки
        """
        toolbar = QToolBar("Главная панель")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Placeholder кнопка
        placeholder_button = QPushButton("Функции появятся в следующих инкрементах")
        placeholder_button.setEnabled(False)
        toolbar.addWidget(placeholder_button)

    def _create_status_bar(self):
        """Создание статус-бара"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Готов к работе | Инкремент 0: Окружение настроено ✓")

    def _show_about(self):
        """Показать диалог "О программе" """
        QMessageBox.about(
            self,
            "О программе VoluptAS",
            "<h2>VoluptAS v0.1.0</h2>"
            "<p>Универсальный инструмент для управления функционалом и покрытием QA</p>"
            "<p><b>Автор:</b> Anatol-19</p>"
            "<p><b>GitHub:</b> <a href='https://github.com/Anatol-19/VoluptAS'>"
            "github.com/Anatol-19/VoluptAS</a></p>"
            "<hr>"
            "<p><b>Технологии:</b></p>"
            "<ul>"
            "<li>Python 3.11+</li>"
            "<li>PyQt6</li>"
            "<li>SQLite</li>"
            "<li>SQLAlchemy</li>"
            "</ul>",
        )

    def _on_tab_changed(self, index: int, tab_name: str):
        """
        Обработка смены таба

        Args:
            index: Индекс нового таба
            tab_name: Название таба
        """
        self.statusBar().showMessage(f"Активная вкладка: {tab_name}")

    def closeEvent(self, event):
        """
        Обработка закрытия окна

        Args:
            event: Событие закрытия
        """
        # В будущих инкрементах добавим проверку несохранённых изменений
        event.accept()

    # === Обработчики меню ===
    def open_settings(self):
        """Открытие настроек проекта и интеграций"""
        dlg = SettingsDialog(parent=self)
        dlg.exec()

    def open_zoho_sync(self):
        """Синхронизация с Zoho"""
        dlg = ZohoSyncDialog(None, self)
        dlg.exec()

    def open_report_generator(self):
        """Открытие генератора отчетов"""
        from src.db import SessionLocal

        dlg = ReportGeneratorDialog(SessionLocal(), self)
        dlg.exec()

    # === Новые обработчики меню ===
    def open_project_manager(self):
        """Открытие менеджера проектов"""
        dlg = ProjectManagerDialog(self)
        if dlg.exec() == QDialog.Accepted:  # Проект был переключен
            # Перезагружаем компоненты с новым проектом
            self.main_tabs.refresh_all()
            self.statusBar().showMessage(f"Текущий проект: {Config.CURRENT_PROJECT}")
            self.setWindowTitle(
                f"{self.config.WINDOW_TITLE} - {Config.CURRENT_PROJECT}"
            )

    def open_entity_editor(self):
        """Открытие редактора сущностей"""
        dlg = EntityEditorDialog(self)
        dlg.exec()

    def open_import_dialog(self):
        """Открытие диалога импорта"""
        dlg = ImportFromCsvDialog(self)
        dlg.exec()

    def open_export_dialog(self):
        """Открытие диалога экспорта"""
        dlg = ExportToCsvDialog(self)
        dlg.exec()

    def open_bdd_manager(self):
        """Открытие менеджера BDD"""
        dlg = BDDManagerDialog(self)
        dlg.exec()

    def refresh_all(self):
        """Обновление всех компонентов"""
        self.main_tabs.refresh_all()
