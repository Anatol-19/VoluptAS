"""
Таб: Полный граф связей

Obsidian-style граф со всеми элементами и связями
Связи строятся из атрибутов (parent_id, module, epic, feature)
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import logging

from src.models import FunctionalItem, Relation
from src.utils.graph_builder import build_graph_from_attributes, NODE_COLORS

logger = logging.getLogger(__name__)


class FullGraphTabWidget(QWidget):
    """Таб с полным графом связей"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Используем session из parent (MainWindow)
        self.session = parent.session if parent and hasattr(parent, "session") else None
        self.graph = nx.DiGraph()
        self.pos = None
        self._init_ui()
        self.load_graph()

    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Панель управления
        controls = QHBoxLayout()
        controls.addWidget(QLabel("<b>Граф связей</b>"))

        controls.addStretch()

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(refresh_btn)

        export_btn = QPushButton("💾 Экспорт PNG")
        export_btn.clicked.connect(self.export_graph)
        controls.addWidget(export_btn)

        layout.addLayout(controls)

        # Canvas для matplotlib
        self.figure = Figure(figsize=(14, 8), facecolor="#1e1e1e")
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def toggle_filter(self, rel_type, state):
        """Переключить фильтр"""
        pass  # Пока фильтры отключены

    def load_graph(self):
        """Загрузить граф из БД — связи из атрибутов + Relation таблица"""
        if not self.session:
            return

        self.graph.clear()

        items = self.session.query(FunctionalItem).all()
        
        # Загружаем активные связи из БД
        relations = self.session.query(Relation).filter_by(active=True).all()
        
        logger.info(f"Loading graph: {len(items)} items, {len(relations)} relations")
        
        # Строим граф из атрибутов + связей
        nodes_data, edges_data = build_graph_from_attributes(items, relations)
        
        # Добавляем узлы
        for node in nodes_data:
            self.graph.add_node(
                node['id'],
                label=node['title'],
                funcid=node['funcid'],
                type=node['type'],
                color=node['color'],
                size=node['size'],
            )
        
        # Добавляем рёбра
        for edge in edges_data:
            self.graph.add_edge(
                edge['from'],
                edge['to'],
                type=edge['type'],
                weight=edge['weight'],
            )

        self.refresh_graph()

    def refresh_graph(self):
        """Перерисовать граф"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor="#1e1e1e")
        ax.set_title("Граф связей (из атрибутов)", color="#ffffff", fontsize=14)
        ax.axis('off')

        if len(self.graph.nodes()) == 0:
            ax.text(
                0.5,
                0.5,
                "Нет связей\nПроверьте данные",
                ha="center",
                va="center",
                fontsize=14,
                color="#9ca3af",
            )
            self.canvas.draw()
            return

        # Layout — иерархический
        self.pos = nx.spring_layout(self.graph, k=0.7, iterations=50, seed=42)

        # Рисуем узлы с цветами из graph_builder
        for node_type in NODE_COLORS.keys():
            nodes = [
                n
                for n, d in self.graph.nodes(data=True)
                if d.get("type") == node_type
            ]
            if nodes:
                sizes = [self.graph.nodes[n].get('size', 1000) for n in nodes]
                colors = [self.graph.nodes[n].get('color', NODE_COLORS.get(node_type, '#808080')) for n in nodes]
                nx.draw_networkx_nodes(
                    self.graph,
                    self.pos,
                    nodelist=nodes,
                    node_color=colors,
                    node_size=sizes,
                    alpha=0.9,
                    ax=ax,
                    edgecolors="#4a4a4a",
                    linewidths=1.5,
                )

        # Рисуем рёбра
        edge_colors = {
            'parent-of': '#ffffff',
            'module-of': '#1E90FF',
            'epic-of': '#32CD32',
            'feature-of': '#FFA500',
            'story-of': '#9370DB',
            'page-of': '#FF69B4',
        }
        
        for rel_type, color in edge_colors.items():
            edges = [
                (u, v)
                for u, v, d in self.graph.edges(data=True)
                if d.get("type") == rel_type
            ]
            if edges:
                nx.draw_networkx_edges(
                    self.graph,
                    self.pos,
                    edgelist=edges,
                    edge_color=color,
                    width=1.5,
                    alpha=0.6,
                    arrows=True,
                    arrowsize=20,
                    arrowstyle='-|>',
                    ax=ax,
                )

        # Подписи узлов
        labels = {
            n: d.get('label', str(n))
            for n, d in self.graph.nodes(data=True)
        }
        nx.draw_networkx_labels(
            self.graph,
            self.pos,
            labels=labels,
            font_size=8,
            font_color="#ffffff",
            ax=ax,
        )

        self.canvas.draw()

    def export_graph(self):
        """Экспорт графа в PNG"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить граф", "graph.png", "PNG Files (*.png)"
        )
        if filepath:
            try:
                self.figure.savefig(
                    filepath, dpi=300, bbox_inches="tight", facecolor="#1e1e1e"
                )
                QMessageBox.information(self, "Успех", f"✅ Граф сохранён:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def refresh(self):
        """Обновление данных"""
        self.load_graph()

    def closeEvent(self, event):
        # Session управляется в MainWindow, не закрываем его здесь
        event.accept()
