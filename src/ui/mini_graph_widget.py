"""
Мини-граф для отображения связей выбранного элемента на главном экране
Связи строятся из атрибутов (parent_id, module, epic, feature)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import networkx as nx
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.models import FunctionalItem
from src.utils.graph_builder import get_item_neighbors, NODE_COLORS


class MiniGraphWidget(QWidget):
    """Виджет мини-графа для показа связей элемента"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Используем session из parent (MainWindow)
        self.session = parent.session if parent and hasattr(parent, "session") else None
        self.current_item_id = None
        self.all_items = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Заголовок
        self.title_label = QLabel("Граф связей")
        self.title_label.setStyleSheet(
            "font-weight: bold; font-size: 11pt; color: #ffffff;"
        )
        layout.addWidget(self.title_label)

        # Canvas (тёмный фон как в Obsidian)
        self.figure = Figure(figsize=(4, 3), facecolor="#1e1e1e")
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Подсказка
        self.hint_label = QLabel("Выберите элемент в таблице")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(self.hint_label)

    def update_graph(self, item_id):
        """Обновить граф для выбранного элемента — связи из атрибутов"""
        if not self.session or not item_id:
            self.clear_graph()
            return

        self.current_item_id = item_id

        # Загружаем элемент
        item = self.session.query(FunctionalItem).filter_by(id=item_id).first()
        if not item:
            self.clear_graph()
            return

        # Загружаем все элементы для поиска связей
        self.all_items = self.session.query(FunctionalItem).all()

        # Получаем соседей из атрибутов
        parents, children = get_item_neighbors(item, self.all_items)

        if not parents and not children:
            self.show_no_relations(item)
            return

        # Строим граф
        G = nx.DiGraph()

        # Добавляем центральный узел
        G.add_node(
            item.id,
            label=item.title,
            type=item.type,
            color=NODE_COLORS.get(item.type, "#808080"),
            size=2000,
            center=True,
        )

        # Добавляем родителей
        for parent in parents:
            G.add_node(
                parent.id,
                label=parent.title,
                type=parent.type,
                color=NODE_COLORS.get(parent.type, "#808080"),
                size=1500,
                center=False,
            )
            G.add_edge(parent.id, item.id, type="parent-of")

        # Добавляем детей
        for child in children:
            G.add_node(
                child.id,
                label=child.title,
                type=child.type,
                color=NODE_COLORS.get(child.type, "#808080"),
                size=1000,
                center=False,
            )
            G.add_edge(item.id, child.id, type="parent-of")

        # Рисуем
        self.draw_graph(G, item)

    def draw_graph(self, G, center_item):
        """Отрисовать граф"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor="#1e1e1e")
        ax.set_title(f"{center_item.title}", fontsize=10, color="#ffffff")

        # Layout: spring
        pos = nx.spring_layout(G, k=1.5, iterations=30, seed=42)

        # Цвета нод из графа
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            node_data = G.nodes[node]
            node_colors.append(node_data.get("color", "#808080"))
            node_sizes.append(node_data.get("size", 1000))

        # Рисуем узлы
        nx.draw_networkx_nodes(
            G,
            pos,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.9,
            ax=ax,
            edgecolors="#4a4a4a",
            linewidths=1.5,
        )

        # Рисуем рёбра
        edges = G.edges()
        if edges:
            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=edges,
                edge_color="#ffffff",
                width=1.5,
                alpha=0.6,
                arrows=True,
                arrowsize=15,
                arrowstyle="-|>",
                ax=ax,
            )

        # Подписи (светлый текст на тёмном фоне)
        labels = {n: d["label"] for n, d in G.nodes(data=True)}
        nx.draw_networkx_labels(
            G,
            pos,
            labels,
            font_size=8,
            font_weight="normal",
            font_color="#e5e7eb",
            ax=ax,
        )

        ax.axis("off")
        ax.set_title(
            f"{center_item.title}",
            fontsize=10,
            fontweight="normal",
            color="#d1d5db",
        )

        self.canvas.draw()

        # Обновляем подсказку
        total_relations = len(list(G.edges()))
        self.hint_label.setText(f"{total_relations} связей")

    def show_no_relations(self, item):
        """Показать, что нет связей"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor="#1e1e1e")
        ax.text(
            0.5,
            0.5,
            f"{item.alias_tag or item.functional_id}\n\nНет связей",
            ha="center",
            va="center",
            fontsize=10,
            color="#9ca3af",
        )
        ax.axis("off")
        self.canvas.draw()
        self.hint_label.setText("Элемент не имеет связей")

    def clear_graph(self):
        """Очистить граф"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor="#1e1e1e")
        ax.text(
            0.5,
            0.5,
            "Выберите элемент\nв таблице",
            ha="center",
            va="center",
            fontsize=10,
            color="#9ca3af",
        )
        ax.axis("off")
        self.canvas.draw()
        self.hint_label.setText("Выберите элемент в таблице")

    def closeEvent(self, event):
        # Session управляется в MainWindow, не закрываем его здесь
        event.accept()
