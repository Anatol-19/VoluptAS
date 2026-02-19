"""
Таб: Таблица функциональных элементов + Мини-граф связей

Содержит:
- Панель фильтров
- Таблица функциональных элементов (70%)
- Мини-граф связей выбранного элемента (30%)
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal


class TableGraphTabWidget(QWidget):
    """
    Таб с таблицей и мини-графом

    Signals:
        item_selected: Выбран элемент (func_id)
        item_double_clicked: Двойной клик по элементу (func_id)
    """

    item_selected = pyqtSignal(str)
    item_double_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Панель фильтров
        filters_widget = self._create_filters()
        layout.addWidget(filters_widget)

        # Splitter для таблицы и мини-графа
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Таблица (70%)
        table_widget = self._create_table()
        splitter.addWidget(table_widget)

        # Мини-граф (30%)
        mini_graph_widget = self._create_mini_graph()
        splitter.addWidget(mini_graph_widget)

        # Пропорции 70/30
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, 1)

    def _create_filters(self) -> QWidget:
        """Создание панели фильтров"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Строка 1: Поиск, Type, Module, Epic, Segment
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("🔍 Поиск:"))
        row1.addWidget(QLineEdit())
        row1.addWidget(QLabel("Type:"))
        row1.addWidget(QComboBox())
        row1.addWidget(QLabel("Module:"))
        row1.addWidget(QComboBox())
        row1.addWidget(QLabel("Epic:"))
        row1.addWidget(QComboBox())
        row1.addStretch()
        layout.addLayout(row1)

        # Строка 2: Segment, QA, Dev, Кнопки
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Segment:"))
        row2.addWidget(QComboBox())
        row2.addWidget(QLabel("QA:"))
        row2.addWidget(QComboBox())
        row2.addWidget(QLabel("Dev:"))
        row2.addWidget(QComboBox())
        row2.addWidget(QPushButton("❌ Сбросить фильтры"))
        row2.addStretch()
        layout.addLayout(row2)

        return widget

    def _create_table(self) -> QWidget:
        """Создание таблицы функциональных элементов"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>📊 ТАБЛИЦА ФУНКЦИОНАЛЬНЫХ ЭЛЕМЕНТОВ</b>"))

        # Placeholder
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels(
            [
                "FuncID",
                "Alias",
                "Title",
                "Type",
                "Module",
                "Epic",
                "QA",
                "Dev",
                "Crit",
                "Focus",
            ]
        )
        layout.addWidget(table)

        return widget

    def _create_mini_graph(self) -> QWidget:
        """Создание мини-графа"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<b>🔗 МИНИ-ГРАФ СВЯЗЕЙ</b>"))

        # Placeholder
        placeholder = QLabel(
            "Граф связей выбранного элемента\n\n"
            "🖱️ Клик → выделить строку\n"
            "🖱️ 2x клик → редактор\n"
            "🖱️ 3x клик → полный граф"
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder, 1)

        return widget

    def refresh(self):
        """Обновление данных"""
        # TODO: Загрузка данных из БД
        pass
