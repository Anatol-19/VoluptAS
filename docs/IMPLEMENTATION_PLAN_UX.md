# Технический план реализации UX улучшений

**Версия:** v0.4.1  
**Приоритет:** 🔴 Критичный (блокирует UX)

---

## 📋 Задачи

### 1. Двойной клик по строке → открытие редактора

#### Проблема:
Пользователь должен жать кнопку "Редактировать" или Ctrl+E для редактирования. Неинтуитивно.

#### Решение:
Подключить сигнал `cellDoubleClicked` к методу `edit_item()`.

#### Код:
```python
# В MainWindow.init_ui(), после создания таблицы:

# Подключаем двойной клик
self.table.cellDoubleClicked.connect(lambda row, col: self.edit_item())
```

#### Альтернатива (более продвинутая):
```python
# Если нужно игнорировать клики по чекбоксам (столбцы is_crit, is_focus):
def on_cell_double_clicked(self, row, col):
    """Обработчик двойного клика по ячейке"""
    # Колонки 9 и 10 - это чекбоксы, игнорируем их
    if col in [9, 10]:
        return
    self.edit_item()

self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
```

**Время реализации:** 5 минут  
**Риски:** Нет

---

### 2. Интерактивность мини-графа

#### Проблема:
Клик по узлу в мини-графе ничего не делает. Пользователь хочет:
- **Одинарный клик** → перейти к строке в таблице
- **Двойной клик** → открыть полный граф от элемента

#### Решение:
Добавить обработчик событий `pick_event` в matplotlib canvas.

#### Архитектура:
```
MiniGraphWidget (src/ui/mini_graph_widget.py)
  ↓ [emit signal: node_clicked(item_id)]
MainWindow (main.py)
  ↓ [connect signal → on_node_clicked()]
  ↓ [найти строку в таблице и выделить]
```

#### Код для MiniGraphWidget:

```python
# В src/ui/mini_graph_widget.py

from PyQt6.QtCore import pyqtSignal

class MiniGraphWidget(QWidget):
    # Добавляем сигналы
    node_clicked = pyqtSignal(int)  # item_id
    node_double_clicked = pyqtSignal(int)  # item_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = SessionLocal()
        self.current_item_id = None
        self.current_graph = None  # Сохраняем граф для определения кликнутого узла
        self.node_positions = {}  # Сохраняем позиции узлов
        
        self.init_ui()
        
        # Подключаем обработчик кликов
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
    
    def on_canvas_click(self, event):
        """Обработчик кликов по canvas"""
        if event.inaxes is None or self.current_graph is None:
            return
        
        # Определяем ближайший узел к клику
        click_pos = (event.xdata, event.ydata)
        clicked_node = self.find_nearest_node(click_pos)
        
        if clicked_node is not None:
            # Двойной клик
            if event.dblclick:
                self.node_double_clicked.emit(clicked_node)
            # Одинарный клик
            else:
                self.node_clicked.emit(clicked_node)
    
    def find_nearest_node(self, click_pos, threshold=0.05):
        """Находит ближайший узел к позиции клика"""
        if not self.node_positions:
            return None
        
        min_dist = float('inf')
        nearest_node = None
        
        for node_id, pos in self.node_positions.items():
            dist = ((pos[0] - click_pos[0])**2 + (pos[1] - click_pos[1])**2)**0.5
            if dist < min_dist and dist < threshold:
                min_dist = dist
                nearest_node = node_id
        
        return nearest_node
    
    def draw_graph(self, G, center_item):
        """Отрисовать граф (обновлённый метод)"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1e1e1e')
        
        # Сохраняем граф и позиции
        self.current_graph = G
        self.node_positions = nx.spring_layout(G, k=1.5, iterations=30, seed=42)
        
        # ... (остальной код рисования без изменений)
        
        self.canvas.draw()
```

#### Код для MainWindow:

```python
# В MainWindow.init_ui(), после создания мини-графа:

# Подключаем сигналы
self.mini_graph.node_clicked.connect(self.on_mini_graph_node_clicked)
self.mini_graph.node_double_clicked.connect(self.on_mini_graph_node_double_clicked)

# Добавляем методы:
def on_mini_graph_node_clicked(self, item_id):
    """Обработчик клика по узлу в мини-графе → переход к строке"""
    # Находим functional_id
    item = self.session.query(FunctionalItem).filter_by(id=item_id).first()
    if not item:
        return
    
    # Ищем строку в таблице
    for row in range(self.table.rowCount()):
        if self.table.item(row, 0).text() == item.functional_id:
            # Выделяем строку
            self.table.selectRow(row)
            self.table.scrollToItem(self.table.item(row, 0))
            self.statusBar().showMessage(f'Выбран: {item.functional_id}', 2000)
            break

def on_mini_graph_node_double_clicked(self, item_id):
    """Обработчик двойного клика → открыть полный граф от элемента"""
    # Открываем полный граф
    from src.ui.graph_view_new import GraphViewWindow
    graph_window = GraphViewWindow(self)
    
    # TODO: Реализовать центрирование на элементе
    # graph_window.center_on_node(item_id)
    
    graph_window.show()
    self.statusBar().showMessage(f'Открыт граф для элемента ID={item_id}')
```

**Время реализации:** 30-40 минут  
**Риски:** Определение ближайшего узла может работать некорректно при плотном графе

---

### 3. Исправить вёрстку фильтров

#### Проблема:
- Неравномерные отступы
- Комбобоксы разной ширины
- Нет визуальной группировки
- Кнопки "не на месте"

#### Решение:
Обернуть фильтры в `QGroupBox`, задать фиксированные размеры, добавить отступы.

#### Визуальная схема:

**До:**
```
[Поиск][_____________][Type][v][Module][v][Epic][v]
[Segment][v][QA][v][Dev][v][Очистить][Сбросить]
```

**После:**
```
┌─ Фильтры ────────────────────────────────────────────────────┐
│ 🔍 Поиск: [____________________]  Type: [_____▼]             │
│ Module: [_____▼]  Epic: [_____▼]  Segment: [_____▼]          │
│ QA: [_____▼]  Dev: [_____▼]           [Очистить] [Сбросить] │
└──────────────────────────────────────────────────────────────┘
```

#### Код:

```python
# В MainWindow.init_ui(), заменить создание фильтров:

# Группа фильтров
filter_group = QGroupBox('🔍 Фильтры')
filter_group_layout = QVBoxLayout()
filter_group_layout.setSpacing(8)
filter_group_layout.setContentsMargins(10, 15, 10, 10)

# Строка 1: Поиск + Type
filter_row1 = QHBoxLayout()
filter_row1.setSpacing(10)

filter_row1.addWidget(QLabel('Поиск:'))
self.search_input = QLineEdit()
self.search_input.setPlaceholderText('Functional ID, Alias, Title...')
self.search_input.setMinimumWidth(300)
self.search_input.textChanged.connect(self.filter_table)
filter_row1.addWidget(self.search_input)

filter_row1.addWidget(QLabel('Type:'))
self.type_filter = QComboBox()
self.type_filter.setFixedWidth(120)
self.type_filter.currentTextChanged.connect(self.filter_table)
filter_row1.addWidget(self.type_filter)

filter_row1.addStretch()  # Отталкивает остальные элементы влево
filter_group_layout.addLayout(filter_row1)

# Строка 2: Module, Epic, Segment
filter_row2 = QHBoxLayout()
filter_row2.setSpacing(10)

filter_row2.addWidget(QLabel('Module:'))
self.module_filter = QComboBox()
self.module_filter.setFixedWidth(120)
self.module_filter.currentTextChanged.connect(self.filter_table)
filter_row2.addWidget(self.module_filter)

filter_row2.addWidget(QLabel('Epic:'))
self.epic_filter = QComboBox()
self.epic_filter.setFixedWidth(120)
self.epic_filter.currentTextChanged.connect(self.filter_table)
filter_row2.addWidget(self.epic_filter)

filter_row2.addWidget(QLabel('Segment:'))
self.segment_filter = QComboBox()
self.segment_filter.setFixedWidth(120)
self.segment_filter.currentTextChanged.connect(self.filter_table)
filter_row2.addWidget(self.segment_filter)

filter_row2.addStretch()
filter_group_layout.addLayout(filter_row2)

# Строка 3: QA, Dev, Кнопки
filter_row3 = QHBoxLayout()
filter_row3.setSpacing(10)

filter_row3.addWidget(QLabel('QA:'))
self.qa_filter = QComboBox()
self.qa_filter.setFixedWidth(150)
self.qa_filter.currentTextChanged.connect(self.filter_table)
filter_row3.addWidget(self.qa_filter)

filter_row3.addWidget(QLabel('Dev:'))
self.dev_filter = QComboBox()
self.dev_filter.setFixedWidth(150)
self.dev_filter.currentTextChanged.connect(self.filter_table)
filter_row3.addWidget(self.dev_filter)

filter_row3.addStretch()  # Отодвигает кнопки вправо

clear_btn = QPushButton('🗑️ Очистить')
clear_btn.clicked.connect(self.clear_filters)
clear_btn.setMaximumWidth(100)
filter_row3.addWidget(clear_btn)

reset_btn = QPushButton('🔄 Сбросить')
reset_btn.clicked.connect(self.reset_table)
reset_btn.setMaximumWidth(100)
filter_row3.addWidget(reset_btn)

filter_group_layout.addLayout(filter_row3)

filter_group.setLayout(filter_group_layout)
layout.addWidget(filter_group)
```

**Время реализации:** 20 минут  
**Риски:** Нет

---

### 4. Подсказки segment по типам

#### Проблема:
Пользователь не знает, какие segment подходят для каждого типа.

#### Решение:
Динамически обновлять hint под `segment_combo` при смене типа.

#### Словарь подсказок:

```python
TYPE_SEGMENT_HINTS = {
    'Module': 'Segment не применяется к Module',
    'Epic': 'Segment не применяется к Epic',
    'Feature': '💡 Рекомендуется: UI, API, Backend, Database',
    'Story': '💡 Рекомендуется: UI, API, Backend',
    'Service': '💡 Рекомендуется: API, Backend, Database, Integration',
    'Page': '💡 Рекомендуется: UI',
    'Element': '💡 Рекомендуется: UI'
}
```

#### Код:

```python
# В DynamicEditDialog.__init__():

# Создаём label для подсказки
self.segment_hint = QLabel()
self.segment_hint.setStyleSheet('color: #888; font-size: 9pt; font-style: italic;')
self.segment_hint.setWordWrap(True)
basic_layout.addRow('', self.segment_hint)

# В on_type_changed():
def on_type_changed(self, item_type):
    config = get_field_config_for_type(item_type)
    
    # ... (существующий код)
    
    # Обновляем подсказку segment
    hint_text = TYPE_SEGMENT_HINTS.get(item_type, '')
    self.segment_hint.setText(hint_text)
    
    # Если segment не применяется, делаем поле disabled
    if not config['has_segment']:
        self.segment_combo.setEnabled(False)
        self.segment_combo.setCurrentText('')
    else:
        self.segment_combo.setEnabled(True)
```

**Время реализации:** 10 минут  
**Риски:** Нет

---

### 5. Шаблоны functional_id

#### Проблема:
Пользователь не знает формат functional_id для каждого типа.

#### Решение:
Показывать placeholder в поле `functional_id` с примером.

#### Словарь шаблонов:

```python
TYPE_FUNCID_TEMPLATES = {
    'Module': 'MOD.название (напр.: AUTH.Login)',
    'Epic': 'MOD.EP.название (напр.: AUTH.Login.EP.FreeTier)',
    'Feature': 'MOD.EP.FT.название (напр.: AUTH.Login.FT.EmailAuth)',
    'Story': 'MOD.EP.FT.ST.название (напр.: AUTH.Login.FT.EmailAuth.ST.Validation)',
    'Service': 'SVC.название (напр.: SVC.PaymentGateway)',
    'Page': 'PG.название (напр.: PG.LoginPage)',
    'Element': 'PG.EL.название (напр.: PG.LoginPage.EL.EmailInput)'
}
```

#### Код:

```python
# В on_type_changed():

def on_type_changed(self, item_type):
    config = get_field_config_for_type(item_type)
    
    # ... (существующий код)
    
    # Обновляем placeholder для functional_id
    if self.is_new:  # Только для новых элементов
        template = TYPE_FUNCID_TEMPLATES.get(item_type, 'Введите functional_id')
        self.functional_id_edit.setPlaceholderText(template)
```

**Время реализации:** 5 минут  
**Риски:** Нет

---

## 📊 Итоговая оценка

| Задача | Время | Сложность | Приоритет |
|--------|-------|-----------|-----------|
| 1. Двойной клик по строке | 5 мин | Низкая | 🔴 Критичный |
| 2. Интерактивность мини-графа | 40 мин | Средняя | 🔴 Критичный |
| 3. Вёрстка фильтров | 20 мин | Низкая | 🔴 Критичный |
| 4. Подсказки segment | 10 мин | Низкая | 🟡 Важный |
| 5. Шаблоны functional_id | 5 мин | Низкая | 🟡 Важный |
| **ИТОГО** | **~1.5 часа** | - | - |

---

## 🎯 Порядок реализации

### Фаза 1: Быстрые победы (20 минут)
1. Двойной клик по строке
2. Подсказки segment
3. Шаблоны functional_id

### Фаза 2: Вёрстка (20 минут)
4. Исправить фильтры

### Фаза 3: Интерактивность (40 минут)
5. Мини-граф с кликами

---

## 🧪 Тестирование

### Чеклист:
- [ ] Двойной клик по строке открывает редактор
- [ ] Двойной клик по чекбоксу не открывает редактор (опционально)
- [ ] Клик по узлу в мини-графе выделяет строку
- [ ] Двойной клик по узлу открывает полный граф
- [ ] Фильтры выровнены и выглядят аккуратно
- [ ] Комбобоксы одинаковой ширины
- [ ] Кнопки справа
- [ ] Подсказка segment меняется при смене типа
- [ ] Placeholder functional_id показывает шаблон

---

## 📝 Следующие шаги (после реализации)

1. Коммит с описанием: "UX improvements: double-click, mini-graph interaction, filters layout, hints"
2. Тестирование всех функций
3. Запуск monkey testing
4. Переход к редизайну меню (средний приоритет)

---

---

## 🏛️ МЕНЮ (Menubar) - ТЕКУЩАЯ СТРУКТУРА

### Текущая структура (main.py, строки 617-665):

```
┌─ MenuBar ────────────────────────────────────────────────────────┐
│ 📁 Файл         ✏️ Правка     🔧 Инструменты     🕸️ Граф     ⚙️ Настройки │
└───────────────────────────────────────────────────────────────┘

📁 Файл
  └─ Выход

✏️ Правка
  └─ ➕ Добавить

🔧 Инструменты
  ├─ 📦 Редактор сущностей
  ├─ 👥 Управление пользователями
  ├─ ────────────────────
  ├─ 📚 Справочники
  ├─ ────────────────────
  ├─ 🧑‍💻 BDD Feature Manager
  └─ 📝 Генерация BDD (batch)

🕸️ Граф
  └─ 🌐 Открыть граф

⚙️ Настройки
  └─ ⚙️ Zoho API
```

### Проблемы:
- ❓ **"Редактор сущностей"** - что это? (не используется)
- ❌ Нет **Импорт/Экспорт**
- ❌ Нет **Матрицы трассировки/Покрытия**
- ❌ Нет **Метрик**
- ❌ Нет **Помощь/О программе**
- ❌ BDD разбросан (Manager + batch)

---

## 🔲 СТЕЙДЖИ (Экраны) - ТЕКУЩЕЕ СОСТОЯНИЕ

### 1. Главный экран (MainWindow)

**Лаяут:**
```
┌───────────────────────────────────────────────────────────────┐
│ MenuBar: Файл | Правка | Инструменты | Граф | Настройки              │
├───────────────────────────────────────────────────────────────┤
│ Toolbar: 🔄 | ➕ | ✏️ | 🗑️ | 📋 Все | 🔴 Крит | 🎯 Фокус                  │
├───────────────────────────────────────────────────────────────┤
│ Фильтры (Строка 1):                                                  │
│ 🔍 Поиск: [___________________] Type: [▼] Module: [▼] Epic: [▼]  │
│ Фильтры (Строка 2):                                                  │
│ Segment: [▼] QA: [▼] Dev: [▼]          [❌ Сбросить фильтры]   │
├───────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────┐  ┌──────────────────┐  │
│ │ ТАБЛИЦА (70%)                      │  │ МИНИ-ГРАФ (30%) │  │
│ │ FuncID | Alias | Title | Type...  │  │                  │  │
│ │ ------------------------------------│  │   [graph]       │  │
│ │ AUTH.Login | Login | ... | Feature │  │                  │  │
│ │ AUTH.Reg | Reg | ... | Feature     │  │   связи        │  │
│ │ ... (inline-edit: alias, title,   │  │   выбранного    │  │
│ │      segment, checkboxes)          │  │   элемента      │  │
│ └──────────────────────────────────────┘  └──────────────────┘  │
├───────────────────────────────────────────────────────────────┤
│ StatusBar: ✅ Загружено: 156 записей                                    │
└───────────────────────────────────────────────────────────────┘
```

**Переходы:**
- ❌ **Двойной клик по строке** → Редактор элемента (не работает)
- ❌ **Клик по узлу в мини-графе** → Выделение строки (не работает)
- ❌ **Двойной клик по узлу** → Полный граф от элемента (не работает)

---

### 2. Редактор элемента (DynamicEditDialog)

**Лаяут:**
```
┌─ Редактирование: AUTH.Login ─────────────────────────────┐
│ ┌─ Вкладки ────────────────────────────────────────────────┐ │
│ │ 📋 Основные | 👥 Ответственные | ✅ Покрытие | 🧑‍💻 BDD       │ │
│ ├───────────────────────────────────────────────────────┤ │
│ │ * FuncID: [AUTH.Login]                                         │ │
│ │ Alias Tag: [Login]                                            │ │
│ │ * Title: [Login to account]                                  │ │
│ │ * Type: [Feature ▼]                                         │ │
│ │ Segment: [UI ▼] 💡 Рекомендуется: UI, API, Backend         │ │
│ │ ...                                                           │ │
│ └───────────────────────────────────────────────────────┘ │
│ [💾 Сохранить]  [❌ Отмена]                                         │
└────────────────────────────────────────────────────────────────┘
```

**Открывается из:**
- ✅ Кнопка "✏️ Редактировать" в Toolbar
- ✅ Меню "Правка → Добавить"
- ❌ Двойной клик по строке (не работает)

---

### 3. Полный граф (GraphViewWindow)

```
┌─ Граф связей ─────────────────────────────────────────────┐
│ MenuBar: Файл | Экспорт                                                │
│ Фильтры: ☐ Иерархия ☑ Функционал ☐ POM ... [🔄 Обновить]     │
├───────────────────────────────────────────────────────────┤
│                                                                       │
│         [Obsidian-стиль граф с узлами и связями]            │
│                                                                       │
├───────────────────────────────────────────────────────────┤
│ Легенда: ◼ Иерархия | ◼ Функционал | ◼ Service...            │
└───────────────────────────────────────────────────────────┘
```

**Открывается из:**
- ✅ Меню "🕸️ Граф → 🌐 Открыть граф"
- ❌ Двойной клик по узлу в мини-графе (не работает)

---

### 4. BDD Feature Manager

```
┌─ BDD Feature Manager ─────────────────────────────────────────┐
│ Фильтры: [🔍 Поиск] [Type] [Segment] ☐Crit ☐Focus        │
├──────────────────────────────────────────────────────────────┤
│ ┌─ Список элементов ────┐  ┌─ Предпросмотр Gherkin ───────┐ │
│ │ FuncID | Title | Type  │  │ Feature: Login           │ │
│ │ ---------------------  │  │   Scenario: Valid login  │ │
│ │ AUTH.Login | ...      │  │     Given user at /    │ │
│ │ ...                   │  │     When enter creds   │ │
│ └───────────────────────┘  └────────────────────────────┘ │
│ [🛠️ Генерировать]  [💾 Экспорт]                                    │
└──────────────────────────────────────────────────────────────┘
```

**Открывается из:**
- ✅ Меню "Инструменты → 🧑‍💻 BDD Feature Manager"

---

### 5. Управление пользователями (UserManagerWindow)

**Открывается из:**
- ✅ Меню "Инструменты → 👥 Управление пользователями"

---

### 6. Справочники (DictionaryManagerWindow)

**Открывается из:**
- ✅ Меню "Инструменты → 📚 Справочники"

---

## 📋 МАТРИЦА ТРАССИРОВКИ/ПОКРЫТИЯ

### Статус: ❌ **НЕТ ОТДЕЛЬНОГО ЭКРАНА**

### Где должна быть:

**Вариант 1: Отдельное окно**
```
┌─ Матрица покрытия ──────────────────────────────────────────┐
│ Фильтры: [Module] [Epic] [Feature] ☐Crit ☐Focus                      │
├─────────────────────────────────────────────────────────────────┤
│ FuncID         | Тест-кейсы | Автотесты | Документация | Покрытие %  │
│ ---------------+---------------+-------------+----------------+--------------│
│ AUTH.Login     | TC-001, TC-02 | ✅ Auto     | 📝 Doc       | 100% ✅      │
│ AUTH.Reg       | TC-003        | ❌ None     | ❌ None      | 33% ⚠️       │
│ DASH.Settings  | ❌ None        | ❌ None     | 📝 Doc       | 33% ⚠️       │
├─────────────────────────────────────────────────────────────────┤
│ 📈 Метрики:                                                            │
│   - Всего элементов: 156                                                │
│   - С тест-кейсами: 87 (56%)                                          │
│   - С автотестами: 45 (29%)                                           │
│   - С документацией: 120 (77%)                                      │
│   - Без покрытия: 23 (15%) 🔴                                        │
└─────────────────────────────────────────────────────────────────┘
```

**Вариант 2: Вкладка в главном окне**
- Добавить QTabWidget в MainWindow
- Вкладки: "📋 Таблица", "📋 Матрица покрытия", "📈 Метрики"

### Текущие данные покрытия в БД:
- ✅ `test_cases_linked` (TEXT) - список тест-кейсов
- ✅ `automation_status` (TEXT) - Not Started, In Progress, Automated, etc.
- ✅ `documentation_links` (TEXT) - ссылки на доки

**Данные есть, но нет UI для их отображения!**

---

## 🎯 ДОПОЛНЕННЫЕ ЗАДАЧИ

### 6. Матрица трассировки/покрытия

#### Проблема:
Нет экрана для просмотра покрытия. Данные есть, но не визуализированы.

#### Решение:
Создать отдельное окно `CoverageMatrixWindow` с:
- Таблица с колонками: FuncID, Test Cases, Automation, Docs, Coverage %
- Фильтры: Module, Epic, Crit, Focus, Без покрытия
- Метрики внизу: всего, с тестами, с автотестами, без покрытия
- Экспорт в Excel/CSV

**Время реализации:** 1-1.5 часа  
**Приоритет:** 🟡 Важный

---

**Готов к реализации?** Начинаем с Фазы 1 (быстрые победы).
