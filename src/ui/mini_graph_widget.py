"""
Мини-граф для отображения связей выбранного элемента на главном экране
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import networkx as nx
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.models import FunctionalItem, Relation, RELATION_TYPES


class MiniGraphWidget(QWidget):
    """Виджет мини-графа для показа связей элемента"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Используем session из parent (MainWindow)
        self.session = parent.session if parent and hasattr(parent, 'session') else None
        self.current_item_id = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок
        self.title_label = QLabel("Граф связей")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(self.title_label)
        
        # Canvas (тёмный фон как в Obsidian)
        self.figure = Figure(figsize=(4, 3), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Подсказка
        self.hint_label = QLabel("Выберите элемент в таблице")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(self.hint_label)
    
    def update_graph(self, item_id):
        """Обновить граф для выбранного элемента"""
        if not self.session or not item_id:
            self.clear_graph()
            return
        
        self.current_item_id = item_id
        
        # Загружаем элемент
        item = self.session.query(FunctionalItem).filter_by(id=item_id).first()
        if not item:
            self.clear_graph()
            return
        
        # Загружаем связи (исходящие и входящие)
        outgoing = self.session.query(Relation).filter_by(source_id=item_id, active=True).all()
        incoming = self.session.query(Relation).filter_by(target_id=item_id, active=True).all()
        
        if not outgoing and not incoming:
            self.show_no_relations(item)
            return
        
        # Строим граф
        G = nx.DiGraph()
        
        # Добавляем центральный узел
        G.add_node(item.id, label=item.alias_tag or item.functional_id.split('.')[-1], 
                   type=item.type, center=True)
        
        # Добавляем связанные узлы
        related_items = {}
        
        for rel in outgoing:
            target = self.session.query(FunctionalItem).filter_by(id=rel.target_id).first()
            if target:
                G.add_node(target.id, label=target.alias_tag or target.functional_id.split('.')[-1],
                          type=target.type, center=False)
                G.add_edge(item.id, target.id, type=rel.type, weight=rel.weight)
                related_items[target.id] = target
        
        for rel in incoming:
            source = self.session.query(FunctionalItem).filter_by(id=rel.source_id).first()
            if source:
                G.add_node(source.id, label=source.alias_tag or source.functional_id.split('.')[-1],
                          type=source.type, center=False)
                G.add_edge(source.id, item.id, type=rel.type, weight=rel.weight)
                related_items[source.id] = source
        
        # Рисуем
        self.draw_graph(G, item)
    
    def draw_graph(self, G, center_item):
        """Отрисовать граф"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1e1e1e')
        
        # Layout: центральный узел в центре, остальные вокруг
        pos = nx.spring_layout(G, k=1.5, iterations=30, seed=42)
        
        # Цвета нод (Obsidian-стиль)
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            node_data = G.nodes[node]
            if node_data.get('center'):
                node_colors.append('#ff7eb6')  # Мягкий розовый для центрального
                node_sizes.append(700)
            else:
                # Цвет по типу
                node_type = node_data.get('type', 'Feature')
                type_colors = {
                    'Module': '#9580ff', 'Epic': '#7c98f6', 'Feature': '#6dd8b1',
                    'Story': '#b4dcc7', 'Service': '#d19afd', 'Page': '#ffb86c', 'Element': '#ffd97d'
                }
                node_colors.append(type_colors.get(node_type, '#6dd8b1'))
                node_sizes.append(450)
        
        # Рисуем узлы
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                               alpha=0.8, ax=ax, edgecolors='#4a4a4a', linewidths=1.5)
        
        # Рисуем рёбра по типам
        for rel_type, config in RELATION_TYPES.items():
            edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == rel_type]
            if edges:
                nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=config['color'],
                                      width=1.2, style=config['style'], alpha=0.5,
                                      arrows=True, arrowsize=6, ax=ax,
                                      connectionstyle='arc3,rad=0.1')
        
        # Подписи (светлый текст на тёмном фоне)
        labels = {n: d['label'] for n, d in G.nodes(data=True)}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='normal', font_color='#e5e7eb', ax=ax)
        
        ax.axis('off')
        ax.set_title(f'{center_item.alias_tag or center_item.functional_id}', 
                    fontsize=10, fontweight='normal', color='#d1d5db')
        
        self.canvas.draw()
        
        # Обновляем подсказку
        total_relations = len(list(G.edges()))
        self.hint_label.setText(f"{total_relations} связей")
    
    def show_no_relations(self, item):
        """Показать, что нет связей"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1e1e1e')
        ax.text(0.5, 0.5, f'{item.alias_tag or item.functional_id}\n\nНет связей', 
               ha='center', va='center', fontsize=10, color='#9ca3af')
        ax.axis('off')
        self.canvas.draw()
        self.hint_label.setText("Элемент не имеет связей")
    
    def clear_graph(self):
        """Очистить граф"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1e1e1e')
        ax.text(0.5, 0.5, 'Выберите элемент\nв таблице', 
               ha='center', va='center', fontsize=10, color='#9ca3af')
        ax.axis('off')
        self.canvas.draw()
        self.hint_label.setText("Выберите элемент в таблице")
    
    def closeEvent(self, event):
        # Session управляется в MainWindow, не закрываем его здесь
        event.accept()
