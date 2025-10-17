"""
Таб: Полный граф связей

Obsidian-style граф со всеми элементами и связями
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.db import SessionLocal
from src.models import FunctionalItem, Relation, RELATION_TYPES


class FullGraphTabWidget(QWidget):
    """Таб с полным графом связей"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = SessionLocal()
        self.graph = nx.DiGraph()
        self.pos = None
        self.filters = {
            'hierarchy': True,
            'functional': True,
            'page_element': True,
            'service_dependency': True,
            'test_coverage': False,
            'bug_link': False,
            'doc_link': False,
            'custom': False
        }
        self._init_ui()
        self.load_graph()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Панель управления
        controls = QHBoxLayout()
        controls.addWidget(QLabel("<b>Типы связей:</b>"))
        
        # Чекбоксы фильтров
        self.filter_checks = {}
        for rel_type, config in RELATION_TYPES.items():
            cb = QCheckBox(config['name'])
            cb.setChecked(self.filters[rel_type])
            cb.stateChanged.connect(lambda state, rt=rel_type: self.toggle_filter(rt, state))
            self.filter_checks[rel_type] = cb
            controls.addWidget(cb)
        
        controls.addStretch()
        
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(refresh_btn)
        
        export_btn = QPushButton("💾 Экспорт PNG")
        export_btn.clicked.connect(self.export_graph)
        controls.addWidget(export_btn)
        
        layout.addLayout(controls)
        
        # Canvas для matplotlib
        self.figure = Figure(figsize=(14, 8), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
    
    def toggle_filter(self, rel_type, state):
        """Переключить фильтр"""
        self.filters[rel_type] = (state == Qt.CheckState.Checked.value)
        self.refresh_graph()
    
    def load_graph(self):
        """Загрузить граф из БД"""
        self.graph.clear()
        
        items = self.session.query(FunctionalItem).all()
        for item in items:
            self.graph.add_node(
                item.id,
                label=item.alias_tag or item.functional_id.split('.')[-1],
                functional_id=item.functional_id,
                type=item.type,
                is_crit=item.is_crit,
                is_focus=item.is_focus
            )
        
        relations = self.session.query(Relation).filter_by(active=True).all()
        for rel in relations:
            self.graph.add_edge(
                rel.source_id,
                rel.target_id,
                type=rel.type,
                weight=rel.weight
            )
        
        self.refresh_graph()
    
    def refresh_graph(self):
        """Перерисовать граф"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1e1e1e')
        
        # Фильтруем рёбра
        filtered_graph = self.graph.copy()
        edges_to_remove = []
        for u, v, data in filtered_graph.edges(data=True):
            rel_type = data.get('type', 'functional')
            if not self.filters.get(rel_type, False):
                edges_to_remove.append((u, v))
        filtered_graph.remove_edges_from(edges_to_remove)
        
        if len(filtered_graph.nodes()) == 0:
            ax.text(0.5, 0.5, 'Нет узлов\nВключите фильтры', 
                   ha='center', va='center', fontsize=14, color='#9ca3af')
            self.canvas.draw()
            return
        
        # Layout
        if self.pos is None or len(self.pos) != len(filtered_graph.nodes()):
            self.pos = nx.spring_layout(filtered_graph, k=0.5, iterations=50, seed=42)
        
        # Рисуем узлы (Obsidian-стиль)
        node_types = {
            'Module': {'color': '#9580ff', 'size': 700},
            'Epic': {'color': '#7c98f6', 'size': 550},
            'Feature': {'color': '#6dd8b1', 'size': 450},
            'Story': {'color': '#b4dcc7', 'size': 350},
            'Service': {'color': '#d19afd', 'size': 450},
            'Page': {'color': '#ffb86c', 'size': 450},
            'Element': {'color': '#ffd97d', 'size': 280}
        }
        
        for node_type, style in node_types.items():
            nodes = [n for n, d in filtered_graph.nodes(data=True) if d.get('type') == node_type]
            if nodes:
                sizes = [style['size'] * 1.5 if filtered_graph.nodes[n].get('is_crit') else style['size'] for n in nodes]
                nx.draw_networkx_nodes(
                    filtered_graph, self.pos, nodelist=nodes,
                    node_color=style['color'], node_size=sizes,
                    alpha=0.8, ax=ax, edgecolors='#4a4a4a', linewidths=1.5
                )
        
        # Рисуем рёбра
        for rel_type, config in RELATION_TYPES.items():
            edges = [(u, v) for u, v, d in filtered_graph.edges(data=True) if d.get('type') == rel_type]
            if edges:
                nx.draw_networkx_edges(filtered_graph, self.pos, edgelist=edges, edge_color=config['color'],
                                      width=1.2, style=config['style'], alpha=0.5,
                                      arrows=True, arrowsize=6, ax=ax,
                                      connectionstyle='arc3,rad=0.1')
        
        # Подписи
        labels = {n: d['label'] for n, d in filtered_graph.nodes(data=True)}
        nx.draw_networkx_labels(filtered_graph, self.pos, labels, font_size=8, font_color='#e5e7eb', ax=ax)
        
        ax.axis('off')
        self.canvas.draw()
    
    def export_graph(self):
        """Экспорт графа в PNG"""
        filepath, _ = QFileDialog.getSaveFileName(self, 'Сохранить граф', 'graph.png', 'PNG Files (*.png)')
        if filepath:
            try:
                self.figure.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
                QMessageBox.information(self, 'Успех', f'✅ Граф сохранён:\n{filepath}')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
    
    def refresh(self):
        """Обновление данных"""
        self.load_graph()
    
    def closeEvent(self, event):
        self.session.close()
        event.accept()
