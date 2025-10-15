"""
Граф связей с типизированными связями (MVP)
"""
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.db import SessionLocal
from src.models import FunctionalItem, Relation, RELATION_TYPES


class GraphViewWindow(QMainWindow):
    """Окно графа связей с типизированными рёбрами"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = SessionLocal()
        self.graph = nx.DiGraph()
        self.pos = None
        
        # Фильтры (включены по умолчанию)
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
        
        self.init_ui()
        self.load_graph()
    
    def init_ui(self):
        self.setWindowTitle('Граф связей')
        self.setGeometry(100, 100, 1400, 900)
        
        # Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')
        
        export_action = QAction('💾 Экспорт PNG', self)
        export_action.triggered.connect(self.export_graph)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        close_action = QAction('Закрыть', self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Toolbar с фильтрами
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel('Фильтры связей:'))
        
        # Чекбоксы для каждого типа связи
        self.filter_checks = {}
        for rel_type, config in RELATION_TYPES.items():
            cb = QCheckBox(config['name'])
            cb.setChecked(self.filters[rel_type])
            cb.stateChanged.connect(lambda state, rt=rel_type: self.toggle_filter(rt, state))
            self.filter_checks[rel_type] = cb
            filter_layout.addWidget(cb)
        
        # Кнопка обновления
        refresh_btn = QPushButton('🔄 Обновить')
        refresh_btn.clicked.connect(self.refresh_graph)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Canvas для matplotlib (тёмный фон как в Obsidian)
        self.figure = Figure(figsize=(14, 8), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Легенда
        legend_text = QLabel()
        legend_text.setText(self.build_legend())
        legend_text.setWordWrap(True)
        layout.addWidget(legend_text)
        
        self.statusBar().showMessage('Готов')
    
    def build_legend(self):
        """Построить легенду"""
        legend = "<b>Легенда типов связей:</b><br>"
        for rel_type, config in RELATION_TYPES.items():
            legend += f"<span style='color:{config['color']};'>■</span> {config['name']} — {config['description']}<br>"
        return legend
    
    def toggle_filter(self, rel_type, state):
        """Переключить фильтр типа связи"""
        self.filters[rel_type] = (state == Qt.CheckState.Checked.value)
        self.refresh_graph()
    
    def load_graph(self):
        """Загрузить граф из БД"""
        self.graph.clear()
        
        # Загружаем все элементы
        items = self.session.query(FunctionalItem).all()
        
        # Добавляем ноды
        for item in items:
            self.graph.add_node(
                item.id,
                label=item.alias_tag or item.functional_id.split('.')[-1],
                functional_id=item.functional_id,
                type=item.type,
                is_crit=item.is_crit,
                is_focus=item.is_focus,
                segment=item.segment
            )
        
        # Загружаем связи
        relations = self.session.query(Relation).filter_by(active=True).all()
        
        for rel in relations:
            # Добавляем рёбра с атрибутами
            self.graph.add_edge(
                rel.source_id,
                rel.target_id,
                type=rel.type,
                weight=rel.weight,
                directed=rel.directed,
                metadata=rel.get_metadata()
            )
        
        self.statusBar().showMessage(f'Загружено: {len(items)} узлов, {len(relations)} связей')
    
    def refresh_graph(self):
        """Перерисовать граф"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1e1e1e')
        
        # Фильтруем рёбра по включённым типам
        filtered_graph = self.graph.copy()
        edges_to_remove = []
        
        for u, v, data in filtered_graph.edges(data=True):
            rel_type = data.get('type', 'functional')
            if not self.filters.get(rel_type, False):
                edges_to_remove.append((u, v))
        
        filtered_graph.remove_edges_from(edges_to_remove)
        
        # НЕ удаляем изолированные ноды - показываем все
        # isolated = list(nx.isolates(filtered_graph))
        # filtered_graph.remove_nodes_from(isolated)
        
        if len(filtered_graph.nodes()) == 0:
            ax.text(0.5, 0.5, 'Нет узлов для отображения\nВключите фильтры', 
                   ha='center', va='center', fontsize=14, color='#9ca3af')
            self.canvas.draw()
            return
        
        # Layout
        if self.pos is None or len(self.pos) != len(filtered_graph.nodes()):
            # Используем spring layout для основного расположения
            self.pos = nx.spring_layout(filtered_graph, k=0.5, iterations=50, seed=42)
        
        # Рисуем ноды по типам (Obsidian-стиль: приглушённые пастельные цвета)
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
                # Увеличиваем размер для критичных
                sizes = [style['size'] * 1.5 if filtered_graph.nodes[n].get('is_crit') else style['size'] for n in nodes]
                
                nx.draw_networkx_nodes(
                    filtered_graph, self.pos, nodelist=nodes,
                    node_color=style['color'], node_size=sizes,
                    alpha=0.8, ax=ax, edgecolors='#4a4a4a', linewidths=1.5
                )
        
        # Рисуем рёбра по типам
        for rel_type, config in RELATION_TYPES.items():
            if not self.filters.get(rel_type, False):
                continue
            
            edges = [(u, v) for u, v, d in filtered_graph.edges(data=True) if d.get('type') == rel_type]
            if edges:
                nx.draw_networkx_edges(
                    filtered_graph, self.pos, edgelist=edges,
                    edge_color=config['color'],
                    width=max(0.8, config['width'] * 0.6),
                    style=config['style'],
                    alpha=0.5,
                    arrows=True,
                    arrowsize=8,
                    ax=ax,
                    connectionstyle='arc3,rad=0.1'
                )
        
        # Подписи (светлый текст на тёмном фоне)
        labels = {n: d['label'] for n, d in filtered_graph.nodes(data=True)}
        nx.draw_networkx_labels(
            filtered_graph, self.pos, labels,
            font_size=8, font_weight='normal', font_color='#e5e7eb', ax=ax
        )
        
        ax.axis('off')
        ax.set_title(f'Граф связей ({len(filtered_graph.nodes())} узлов, {len(filtered_graph.edges())} связей)', 
                    fontsize=14, fontweight='normal', color='#d1d5db')
        
        self.canvas.draw()
        self.statusBar().showMessage(f'Отображено: {len(filtered_graph.nodes())} узлов, {len(filtered_graph.edges())} связей')
    
    def export_graph(self):
        """Экспорт графа в PNG"""
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить граф', '', 'PNG Files (*.png)'
        )
        if filename:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight')
            self.statusBar().showMessage(f'✅ Граф сохранён: {filename}')
    
    def closeEvent(self, event):
        self.session.close()
        event.accept()
