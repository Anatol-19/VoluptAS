"""
Главное окно приложения VoluptAS

Содержит основной интерфейс с таблицей, графом и панелями управления
"""

from PyQt6.QtWidgets import QMainWindow, QStatusBar, QToolBar, QPushButton, QMessageBox, QDialog
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction
from src.config import Config
from src.ui.widgets.main_tabs_widget import MainTabsWidget
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.dialogs.report_generator_dialog import ReportGeneratorDialog
from src.ui.dialogs.zoho_sync_dialog import ZohoSyncDialog
from src.ui.dialogs.entity_editor import EntityEditorDialog  # Добавлен импорт
from src.ui.dialogs.import_dialogs import ImportFromCsvDialog
from src.ui.dialogs.export_dialogs import ExportToCsvDialog
from src.ui.dialogs.project_dialogs import ProjectManagerDialog
from src.ui.dialogs.bdd_manager import BDDManagerDialog


class MainWindow(QMainWindow):
    """
    Главное окно приложения
    """
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.setWindowTitle(self.config.WINDOW_TITLE)
        self.setGeometry(100, 100, self.config.WINDOW_WIDTH, self.config.WINDOW_HEIGHT)
        
        # Создание центрального виджета
        self.main_tabs = MainTabsWidget(self)
        self.setCentralWidget(self.main_tabs)

        # Создание меню
        self._create_menu_bar()
        
        # Создание тулбара
        self._create_toolbar()
        
        # Создание статус-бара
        self._create_status_bar()

        # Подключение сигналов
        self.main_tabs.tab_changed.connect(self._on_tab_changed)
        
        # Настройка горячих клавиш
        self.main_tabs.setup_hotkeys()
    
    def _create_menu_bar(self):
        """Создание главного меню приложения"""
        menubar = self.menuBar()
        
        # === Меню "Проект" ===
        project_menu = menubar.addMenu("Проект")

        project_manager_action = QAction("Управление проектами", self)
        project_manager_action.setStatusTip("Управление проектами и их настройками")
        project_manager_action.triggered.connect(self.open_project_manager)
        project_menu.addAction(project_manager_action)

        entity_editor_action = QAction("Управление сущностями", self)
        entity_editor_action.setStatusTip("Редактирование иерархии сущностей")
        entity_editor_action.triggered.connect(self.open_entity_editor)
        project_menu.addAction(entity_editor_action)

        settings_action = QAction("Настройки", self)
        settings_action.setStatusTip("Настройки проекта и интеграций")
        settings_action.triggered.connect(self.open_settings)
        project_menu.addAction(settings_action)

        # === Меню "Данные" ===
        data_menu = menubar.addMenu("Данные")

        import_action = QAction("Импортировать из...", self)
        import_action.triggered.connect(self.open_import_dialog)
        data_menu.addAction(import_action)

        export_action = QAction("Экспортировать в...", self)
        export_action.triggered.connect(self.open_export_dialog)
        data_menu.addAction(export_action)

        # === Меню "Интеграции" ===
        integrations_menu = menubar.addMenu("Интеграции")

        zoho_sync_action = QAction("Синхронизация с Zoho", self)
        zoho_sync_action.triggered.connect(self.open_zoho_sync)
        integrations_menu.addAction(zoho_sync_action)

        # === Меню "BDD" ===
        bdd_menu = menubar.addMenu("BDD")

        bdd_manager_action = QAction("Генератор Feature файлов", self)
        bdd_manager_action.triggered.connect(self.open_bdd_manager)
        bdd_menu.addAction(bdd_manager_action)

        # === Меню "Отчеты" ===
        reports_menu = menubar.addMenu("Отчеты")

        report_action = QAction("Генератор отчетов", self)
        report_action.triggered.connect(self.open_report_generator)
        reports_menu.addAction(report_action)

        # === Меню "Справка" ===
        help_menu = menubar.addMenu("Справка")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Создание тулбара с основными действиями"""
        toolbar = QToolBar("Главная панель")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Кнопки будут добавлены позже
        pass

    def _create_status_bar(self):
        """Создание статус-бара"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Готов к работе")

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
        )

    def _on_tab_changed(self, index: int, tab_name: str):
        """Обработка смены таба"""
        self.statusBar().showMessage(f"Активная вкладка: {tab_name}")

    def closeEvent(self, event):
        """Обработка закрытия окна"""
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
        if dlg.exec() == QDialog.DialogCode.Accepted:  # Проект был переключен
            # Перезагружаем компоненты с новым проектом
            self.main_tabs.refresh_all()
            self.statusBar().showMessage(f"Текущий проект: {Config.CURRENT_PROJECT}")
            self.setWindowTitle(f"{self.config.WINDOW_TITLE} - {Config.CURRENT_PROJECT}")

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
