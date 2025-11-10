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
from PyQt6.QtCore import pyqtSignal


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
        
        # Создание виджета с вкладками
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)

        # Таб с таблицей и мини-графом
        from src.ui.views.table_view import TableView
        from src.ui.mini_graph_widget import MiniGraphWidget

        table_widget = TableView(self)
        mini_graph = MiniGraphWidget(self)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.addWidget(table_widget, stretch=2)
        table_layout.addWidget(mini_graph, stretch=1)
        self.tab_widget.addTab(table_container, "Таблица")

        # Таб с большим графом
        from src.ui.graph_view_new import GraphView
        graph_widget = GraphView(self)
        self.tab_widget.addTab(graph_widget, "Граф")

        # Таб с BDD Features
        from src.ui.views.bdd_view import BDDView
        bdd_widget = BDDView(self)
        self.tab_widget.addTab(bdd_widget, "BDD")

        # Таб с матрицей трассировок
        from src.ui.views.coverage_view import CoverageMatrixView
        coverage_widget = CoverageMatrixView(self)
        self.tab_widget.addTab(coverage_widget, "Трассировка")

        # Таб с INFRA Maturity
        from src.ui.views.infra_view import InfraMaturityView
        infra_widget = InfraMaturityView(self)
        self.tab_widget.addTab(infra_widget, "Инфраструктура")

        # Подключение сигналов
        self.tab_widget.currentChanged.connect(self._tab_changed)
        table_widget.item_selected.connect(self.item_selected)
        graph_widget.item_selected.connect(self.item_selected)

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
    
    def _tab_changed(self, index):
        """Обработчик смены активного таба"""
        tab_names = ["Таблица", "Граф", "BDD", "Трассировка", "Инфраструктура"]
        self.tab_changed.emit(index, tab_names[index])

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

        # Ctrl+Tab - следующий таб
        next_tab = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab.activated.connect(self._next_tab)

        # Ctrl+Shift+Tab - предыдущий таб
        prev_tab = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab.activated.connect(self._prev_tab)

    def _next_tab(self):
        """Переключение на следующий таб"""
        current = self.tab_widget.currentIndex()
        self.tab_widget.setCurrentIndex((current + 1) % self.tab_widget.count())

    def _prev_tab(self):
        """Переключение на предыдущий таб"""
        current = self.tab_widget.currentIndex()
        self.tab_widget.setCurrentIndex((current - 1) % self.tab_widget.count())

    def load_data(self):
        """Загрузка данных во все табы"""
        # В будущем здесь будет логика загрузки данных из БД
        pass
    
    def refresh_all(self):
        """Обновление всех компонентов"""
        # Перезагружаем данные во всех вкладках
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'refresh'):
                widget.refresh()
            elif hasattr(widget, 'layout'):
                # Для составных виджетов (как таблица + мини-граф)
                for j in range(widget.layout().count()):
                    child = widget.layout().itemAt(j).widget()
                    if hasattr(child, 'refresh'):
                        child.refresh()
