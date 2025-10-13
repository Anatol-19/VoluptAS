"""
Интерактивный граф связей функциональных элементов

Визуализирует иерархию Module → Epic → Feature → Story
и связи между элементами (RACI, тест-кейсы, etc.)
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import matplotlib
matplotlib.use('QtAgg')  # Используем Qt6 backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import networkx as nx
from src.db import SessionLocal
from src.models import FunctionalItem


class GraphViewWindow(QMainWindow):
    """Окно визуализации графа связей"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = SessionLocal()
        self.graph = nx.DiGraph()
        self.pos = None
        self.node_colors = []
        self.node_sizes = []
        
        # Настройки фильтров
        self.show_types = {
            'Module': True,
            'Epic': True,
            'Feature': True,
            'Story': True,
            'Page': True,
            'Element': True,
            'Service': True
        }
        self.start_from = None  # Начальная нода для отображения
        self.max_depth = 3  # Максимальная глубина отображения
        
        self.init_ui()
        self.build_graph()
        self.draw_graph()
    
    def init_ui(self):
        self.setWindowTitle('Граф связей функциональных элементов')
        self.setGeometry(100, 100, 1400, 900)
        
        # Меню
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('Файл')
        export_action = QAction('💾 Экспорт PNG', self)
        export_action.triggered.connect(self.export_graph)
        file_menu.addAction(export_action)
        
        close_action = QAction('❌ Закрыть', self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        view_menu = menubar.addMenu('Вид')
        reset_view_action = QAction('🔄 Сбросить вид', self)
        reset_view_action.triggered.connect(self.reset_view)
        view_menu.addAction(reset_view_action)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # === LEFT PANEL: CONTROLS ===
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        
        # Фильтры по типам
        types_group = QGroupBox('📋 Типы элементов')
        types_layout = QVBoxLayout(types_group)
        
        self.type_checkboxes = {}
        for type_name in ['Module', 'Epic', 'Feature', 'Story', 'Page', 'Element', 'Service']:
            checkbox = QCheckBox(type_name)
            checkbox.setChecked(self.show_types.get(type_name, True))
            checkbox.stateChanged.connect(self.on_filter_changed)
            types_layout.addWidget(checkbox)
            self.type_checkboxes[type_name] = checkbox
        
        left_layout.addWidget(types_group)
        
        # Начальная нода
        start_group = QGroupBox('🎯 Начать с элемента')
        start_layout = QVBoxLayout(start_group)
        
        self.start_combo = QComboBox()
        self.start_combo.addItem('(Показать всё)', None)
        self.populate_start_combo()
        self.start_combo.currentIndexChanged.connect(self.on_filter_changed)
        start_layout.addWidget(self.start_combo)
        
        clear_start_btn = QPushButton('🗑️ Сбросить')
        clear_start_btn.clicked.connect(lambda: self.start_combo.setCurrentIndex(0))
        start_layout.addWidget(clear_start_btn)
        
        left_layout.addWidget(start_group)
        
        # Глубина отображения
        depth_group = QGroupBox('📏 Глубина')
        depth_layout = QFormLayout(depth_group)
        
        self.depth_spin = QSpinBox()
        self.depth_spin.setMinimum(1)
        self.depth_spin.setMaximum(10)
        self.depth_spin.setValue(3)
        self.depth_spin.valueChanged.connect(self.on_filter_changed)
        depth_layout.addRow('Уровней:', self.depth_spin)
        
        left_layout.addWidget(depth_group)
        
        # Статистика
        stats_group = QGroupBox('📊 Статистика')
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel('Загрузка...')
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        left_layout.addWidget(stats_group)
        
        # Кнопки
        refresh_btn = QPushButton('🔄 Обновить граф')
        refresh_btn.clicked.connect(self.refresh_graph)
        left_layout.addWidget(refresh_btn)
        
        left_layout.addStretch()
        
        main_layout.addWidget(left_panel)
        
        # === RIGHT PANEL: GRAPH ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Matplotlib canvas
        self.figure = plt.Figure(figsize=(12, 8), facecolor='#f0f0f0')
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        main_layout.addWidget(right_panel)
        
        # Подключаем клик по ноде
        self.canvas.mpl_connect('button_press_event', self.on_node_click)
        
        self.statusBar().showMessage('Готов')
    
    def populate_start_combo(self):
        """Заполнить комбобокс начальных элементов"""
        items = self.session.query(FunctionalItem).order_by(FunctionalItem.functional_id).all()
        for item in items:
            self.start_combo.addItem(f'{item.functional_id} ({item.type})', item.functional_id)
    
    def build_graph(self):
        """Построить граф из БД"""
        self.graph.clear()
        
        # Получаем все элементы
        items = self.session.query(FunctionalItem).all()
        
        # Фильтруем по типам
        filtered_items = [
            item for item in items 
            if self.show_types.get(item.type, True)
        ]
        
        # Если указана начальная нода, фильтруем по глубине
        if self.start_from:
            filtered_items = self.filter_by_start_node(filtered_items, self.start_from, self.max_depth)
        
        # Добавляем ноды
        for item in filtered_items:
            self.graph.add_node(
                item.functional_id,
                label=item.title or item.functional_id,
                type=item.type,
                is_crit=item.is_crit,
                is_focus=item.is_focus,
                item=item
            )
        
        # Добавляем рёбра (иерархия)
        for item in filtered_items:
            # Module → Epic
            if item.type == 'Epic' and item.module:
                parent = self.find_item_by_name(filtered_items, item.module, 'Module')
                if parent and parent.functional_id in self.graph:
                    self.graph.add_edge(parent.functional_id, item.functional_id, relation='hierarchy')
            
            # Epic → Feature
            if item.type == 'Feature' and item.epic:
                parent = self.find_item_by_name(filtered_items, item.epic, 'Epic')
                if parent and parent.functional_id in self.graph:
                    self.graph.add_edge(parent.functional_id, item.functional_id, relation='hierarchy')
            
            # Feature → Story
            if item.type == 'Story' and item.feature:
                parent = self.find_item_by_name(filtered_items, item.feature, 'Feature')
                if parent and parent.functional_id in self.graph:
                    self.graph.add_edge(parent.functional_id, item.functional_id, relation='hierarchy')
        
        self.update_stats()
    
    def find_item_by_name(self, items, name, type_filter=None):
        """Найти элемент по имени"""
        for item in items:
            if type_filter and item.type != type_filter:
                continue
            if item.title == name or item.functional_id == name:
                return item
        return None
    
    def filter_by_start_node(self, items, start_id, max_depth):
        """Фильтровать элементы по начальной ноде и глубине"""
        # Строим временный граф для поиска
        temp_graph = nx.DiGraph()
        
        for item in items:
            temp_graph.add_node(item.functional_id, item=item)
        
        for item in items:
            if item.type == 'Epic' and item.module:
                parent = self.find_item_by_name(items, item.module, 'Module')
                if parent:
                    temp_graph.add_edge(parent.functional_id, item.functional_id)
            
            if item.type == 'Feature' and item.epic:
                parent = self.find_item_by_name(items, item.epic, 'Epic')
                if parent:
                    temp_graph.add_edge(parent.functional_id, item.functional_id)
            
            if item.type == 'Story' and item.feature:
                parent = self.find_item_by_name(items, item.feature, 'Feature')
                if parent:
                    temp_graph.add_edge(parent.functional_id, item.functional_id)
        
        # Получаем всех потомков начальной ноды в пределах глубины
        if start_id not in temp_graph:
            return items
        
        result_ids = {start_id}
        current_level = {start_id}
        
        for _ in range(max_depth):
            next_level = set()
            for node in current_level:
                successors = list(temp_graph.successors(node))
                next_level.update(successors)
                result_ids.update(successors)
            current_level = next_level
            if not current_level:
                break
        
        # Также добавляем предков начальной ноды
        try:
            ancestors = nx.ancestors(temp_graph, start_id)
            result_ids.update(ancestors)
        except:
            pass
        
        return [item for item in items if item.functional_id in result_ids]
    
    def draw_graph(self):
        """Отрисовать граф"""
        self.ax.clear()
        
        if self.graph.number_of_nodes() == 0:
            self.ax.text(0.5, 0.5, 'Нет данных для отображения\nПопробуйте изменить фильтры',
                        ha='center', va='center', fontsize=14, color='gray')
            self.canvas.draw()
            return
        
        # Layout (используем spring_layout для всех размеров)
        try:
            # Для маленьких графов используем больше итераций
            if self.graph.number_of_nodes() < 20:
                self.pos = nx.spring_layout(self.graph, k=2, iterations=100, seed=42)
            elif self.graph.number_of_nodes() < 50:
                self.pos = nx.spring_layout(self.graph, k=1.5, iterations=50, seed=42)
            else:
                # Для больших графов используем меньше итераций
                self.pos = nx.spring_layout(self.graph, k=1, iterations=30, seed=42)
        except Exception as e:
            # Fallback на простой circular layout
            self.pos = nx.circular_layout(self.graph)
        
        # Цвета нод по типу
        type_colors = {
            'Module': '#FF6B6B',      # Красный
            'Epic': '#4ECDC4',        # Бирюзовый
            'Feature': '#45B7D1',     # Голубой
            'Story': '#96CEB4',       # Зелёный
            'Page': '#FFEAA7',        # Жёлтый
            'Element': '#DFE6E9',     # Серый
            'Service': '#A29BFE'      # Фиолетовый
        }
        
        self.node_colors = []
        self.node_sizes = []
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            node_type = node_data.get('type', 'Feature')
            is_crit = node_data.get('is_crit', False)
            is_focus = node_data.get('is_focus', False)
            
            # Цвет
            color = type_colors.get(node_type, '#95A5A6')
            self.node_colors.append(color)
            
            # Размер (критичные больше)
            size = 3000 if is_crit else (2500 if is_focus else 2000)
            self.node_sizes.append(size)
        
        # Рисуем рёбра
        nx.draw_networkx_edges(
            self.graph, self.pos,
            edge_color='#BDC3C7',
            width=2,
            alpha=0.6,
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            ax=self.ax
        )
        
        # Рисуем ноды
        nx.draw_networkx_nodes(
            self.graph, self.pos,
            node_color=self.node_colors,
            node_size=self.node_sizes,
            alpha=0.9,
            linewidths=2,
            edgecolors='white',
            ax=self.ax
        )
        
        # Подписи
        labels = {}
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            label = node  # Functional ID
            labels[node] = label
        
        nx.draw_networkx_labels(
            self.graph, self.pos,
            labels=labels,
            font_size=8,
            font_weight='bold',
            font_color='#2C3E50',
            ax=self.ax
        )
        
        # Легенда
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=color, edgecolor='white', label=type_name)
            for type_name, color in type_colors.items()
            if any(self.graph.nodes[n].get('type') == type_name for n in self.graph.nodes())
        ]
        self.ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
        
        self.ax.set_title(
            'Граф связей функциональных элементов\n'
            '(Размер = критичность, Цвет = тип)',
            fontsize=14, fontweight='bold', pad=20
        )
        self.ax.axis('off')
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        self.statusBar().showMessage(
            f'Отображено нод: {self.graph.number_of_nodes()}, рёбер: {self.graph.number_of_edges()}'
        )
    
    def update_stats(self):
        """Обновить статистику"""
        total = self.graph.number_of_nodes()
        edges = self.graph.number_of_edges()
        
        type_counts = {}
        crit_count = 0
        focus_count = 0
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            node_type = node_data.get('type', 'Unknown')
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
            
            if node_data.get('is_crit'):
                crit_count += 1
            if node_data.get('is_focus'):
                focus_count += 1
        
        stats_text = f"""<b>Всего элементов:</b> {total}
<b>Связей:</b> {edges}

<b>По типам:</b>
"""
        for type_name, count in sorted(type_counts.items()):
            stats_text += f"• {type_name}: {count}\n"
        
        stats_text += f"""
<b>Критичные:</b> {crit_count}
<b>Фокусные:</b> {focus_count}
"""
        
        self.stats_label.setText(stats_text)
    
    def on_filter_changed(self):
        """Обработка изменения фильтров"""
        # Обновляем фильтры типов
        for type_name, checkbox in self.type_checkboxes.items():
            self.show_types[type_name] = checkbox.isChecked()
        
        # Обновляем начальную ноду
        self.start_from = self.start_combo.currentData()
        
        # Обновляем глубину
        self.max_depth = self.depth_spin.value()
        
        # Перестраиваем граф
        self.refresh_graph()
    
    def on_node_click(self, event):
        """Обработка клика по ноде"""
        if event.inaxes != self.ax:
            return
        
        # Находим ближайшую ноду к клику
        click_pos = (event.xdata, event.ydata)
        min_dist = float('inf')
        clicked_node = None
        
        for node, pos in self.pos.items():
            dist = ((pos[0] - click_pos[0])**2 + (pos[1] - click_pos[1])**2)**0.5
            if dist < min_dist:
                min_dist = dist
                clicked_node = node
        
        # Если кликнули близко к ноде (в пределах 0.1)
        if min_dist < 0.1:
            self.show_node_info(clicked_node)
    
    def show_node_info(self, node_id):
        """Показать информацию о ноде"""
        node_data = self.graph.nodes.get(node_id, {})
        item = node_data.get('item')
        
        if not item:
            return
        
        info = f"""<b>Functional ID:</b> {item.functional_id}
<b>Title:</b> {item.title or 'N/A'}
<b>Type:</b> {item.type or 'N/A'}
<b>Module:</b> {item.module or 'N/A'}
<b>Epic:</b> {item.epic or 'N/A'}
<b>Feature:</b> {item.feature or 'N/A'}
<b>Critical:</b> {'✓' if item.is_crit else '—'}
<b>Focus:</b> {'✓' if item.is_focus else '—'}
<b>QA:</b> {item.responsible_qa.name if item.responsible_qa else 'N/A'}
<b>Dev:</b> {item.responsible_dev.name if item.responsible_dev else 'N/A'}
"""
        
        msg = QMessageBox(self)
        msg.setWindowTitle(f'Информация: {node_id}')
        msg.setText(info)
        msg.setIcon(QMessageBox.Icon.Information)
        
        # Кнопка "Открыть в редакторе"
        open_btn = msg.addButton('📝 Открыть в редакторе', QMessageBox.ButtonRole.ActionRole)
        msg.addButton('❌ Закрыть', QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == open_btn:
            self.open_in_editor(item)
    
    def open_in_editor(self, item):
        """Открыть элемент в редакторе (TODO: интеграция с главным окном)"""
        QMessageBox.information(
            self, 'TODO', 
            f'Открытие в редакторе:\n{item.functional_id}\n\n(Функция в разработке)'
        )
    
    def refresh_graph(self):
        """Обновить граф"""
        self.statusBar().showMessage('🔄 Обновление графа...')
        self.build_graph()
        self.draw_graph()
        self.statusBar().showMessage('✅ Граф обновлён')
    
    def reset_view(self):
        """Сбросить вид графа"""
        self.toolbar.home()
        self.statusBar().showMessage('✅ Вид сброшен')
    
    def export_graph(self):
        """Экспорт графа в PNG"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Экспорт графа', 
            'functional_graph.png',
            'PNG Images (*.png);;All Files (*)'
        )
        
        if file_path:
            try:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white')
                QMessageBox.information(self, 'Успех', f'✅ Граф сохранён:\n{file_path}')
                self.statusBar().showMessage(f'✅ Экспортировано: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить:\n{e}')
    
    def closeEvent(self, event):
        """Закрытие окна"""
        plt.close(self.figure)
        self.session.close()
        event.accept()
