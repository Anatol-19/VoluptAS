"""
Главный виджет с табами для основных представлений VoluptAS

Содержит 5 табов:
1. Таблица + Мини-граф
2. Большой граф
3. BDD Features
4. Матрица трассировок
5. INFRA Maturity
"""

from PyQt6.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon


class MainTabsWidget(QWidget):
    """
    Главный виджет с табами
    
    Signals:
        tab_changed: Сигнал при смене таба (индекс, название)
        item_selected: Сигнал при выборе элемента (func_id)
    """
    
    tab_changed = pyqtSignal(int, str)  # индекс, название
    item_selected = pyqtSignal(str)  # func_id
    
    # Константы для индексов табов
    TAB_TABLE = 0
    TAB_GRAPH = 1
    TAB_BDD = 2
    TAB_COVERAGE = 3
    TAB_INFRA = 4
    
    def __init__(self, parent=None):
        """
        Инициализация виджета табов
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.tab_widget = None
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Создание QTabWidget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)  # Более плоский стиль
        
        # Добавление табов (пока с placeholder виджетами)
        self._add_tabs()
        
        layout.addWidget(self.tab_widget)
    
    def _add_tabs(self):
        """Добавление всех табов"""
        from src.ui.widgets.table_graph_tab import TableGraphTabWidget
        from src.ui.widgets.full_graph_tab import FullGraphTabWidget
        from src.ui.widgets.bdd_tab import BddTabWidget
        from src.ui.widgets.coverage_matrix_tab import CoverageMatrixTabWidget
        from src.ui.widgets.infra_maturity_tab import InfraMaturityTabWidget
        
        # Таб 1: Таблица + Мини-граф
        self.table_graph_tab = TableGraphTabWidget(self)
        self.tab_widget.addTab(self.table_graph_tab, "📊 Таблица")
        
        # Таб 2: Большой граф
        self.full_graph_tab = FullGraphTabWidget(self)
        self.tab_widget.addTab(self.full_graph_tab, "🌐 Граф")
        
        # Таб 3: BDD Features
        self.bdd_tab = BddTabWidget(self)
        self.tab_widget.addTab(self.bdd_tab, "🧑‍💻 BDD")
        
        # Таб 4: Матрица трассировок
        self.coverage_tab = CoverageMatrixTabWidget(self)
        self.tab_widget.addTab(self.coverage_tab, "📋 Трассировки")
        
        # Таб 5: INFRA Maturity
        self.infra_tab = InfraMaturityTabWidget(self)
        self.tab_widget.addTab(self.infra_tab, "🏗️ INFRA")
    
    def _connect_signals(self):
        """Подключение сигналов"""
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _on_tab_changed(self, index: int):
        """
        Обработка смены таба
        
        Args:
            index: Индекс нового таба
        """
        tab_name = self.tab_widget.tabText(index)
        self.tab_changed.emit(index, tab_name)
    
    def switch_to_tab(self, index: int):
        """
        Переключение на указанный таб
        
        Args:
            index: Индекс таба (использовать константы TAB_*)
        """
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)
    
    def get_current_tab(self) -> int:
        """
        Получить индекс текущего таба
        
        Returns:
            Индекс текущего таба
        """
        return self.tab_widget.currentIndex()
    
    def setup_hotkeys(self):
        """
        Настройка горячих клавиш для переключения табов
        
        Ctrl+1/2/3/4/5 для быстрого переключения
        """
        from PyQt6.QtGui import QShortcut, QKeySequence
        
        shortcuts = [
            (QKeySequence("Ctrl+1"), self.TAB_TABLE),
            (QKeySequence("Ctrl+2"), self.TAB_GRAPH),
            (QKeySequence("Ctrl+3"), self.TAB_BDD),
            (QKeySequence("Ctrl+4"), self.TAB_COVERAGE),
            (QKeySequence("Ctrl+5"), self.TAB_INFRA),
        ]
        
        for key_seq, tab_index in shortcuts:
            shortcut = QShortcut(key_seq, self)
            shortcut.activated.connect(lambda idx=tab_index: self.switch_to_tab(idx))
    
    def load_data(self):
        """Загрузка данных во все табы"""
        # В будущем здесь будет логика загрузки данных из БД
        pass
    
    def refresh_all(self):
        """Обновление данных во всех табах"""
        self.table_graph_tab.refresh()
        self.full_graph_tab.refresh()
        self.bdd_tab.refresh()
        self.coverage_tab.refresh()
        self.infra_tab.refresh()
