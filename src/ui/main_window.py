"""
Главное окно приложения VoluptAS

Содержит основной интерфейс с таблицей, графом и панелями управления
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStatusBar, QMenuBar, QMenu, QToolBar,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon
from src.config import Config


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
        """
        Создание статус-бара
        """
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Готов к работе | Инкремент 0: Окружение настроено ✓")
    
    def _show_about(self):
        """
        Показать диалог "О программе"
        """
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
            "</ul>"
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
