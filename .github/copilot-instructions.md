# GitHub Copilot Instructions — VoluptAS

**Версия:** 1.0  
**Дата:** 2026-02-19

---

## 📋 Контекст проекта

**VoluptAS** — система управления функционалом и покрытием QA.

**Назначение:**
- Декомпозиция функционала (Module → Epic → Feature → Story)
- Управление покрытием (тест-кейсы, автотесты, документация)
- RACI матрица (ответственные QA/Dev)
- Граф связей
- BDD сценарии
- Интеграции (Google Sheets, Zoho Projects, Qase)

---

## 🛠️ Технологии

| Категория | Технологии |
|-----------|------------|
| **GUI** | PyQt6 |
| **ORM** | SQLAlchemy 2.0 |
| **БД** | SQLite |
| **Графы** | NetworkX + Matplotlib |
| **Данные** | Pandas, OpenPyXL |
| **Интеграции** | Google API, Zoho API, requests |
| **BDD** | Behave, Gherkin |
| **Тесты** | pytest, pytest-qt |

---

## 📁 Архитектура

```
VoluptAS/
├── main.py                    # Главное окно (MainWindow)
├── requirements.txt           # Зависимости
├── start_voluptas.bat         # Лаунчер
│
├── src/
│   ├── models/
│   │   ├── functional_item.py # FunctionalItem модель
│   │   ├── user.py            # User модель
│   │   └── relation.py        # Relation модель (связи)
│   │
│   ├── ui/
│   │   ├── widgets/
│   │   │   ├── full_graph_tab.py      # Вкладка "Граф"
│   │   │   └── coverage_matrix_tab.py # Матрица покрытия
│   │   ├── dialogs/
│   │   │   ├── starter_wizard.py      # Мастер наполнения
│   │   │   └── item_editor.py         # Редактор элементов
│   │   └── mini_graph_widget.py       # Мини-граф справа
│   │
│   ├── utils/
│   │   ├── graph_builder.py           # Построение графа
│   │   ├── funcid_generator.py        # Генерация FuncID
│   │   └── migration.py               # Миграции БД
│   │
│   ├── db/
│   │   ├── database.py                # Подключение к БД
│   │   └── database_manager.py        # Менеджер БД
│   │
│   └── integrations/
│       ├── google.py                  # Google Sheets
│       └── zoho.py                    # Zoho Projects
│
├── data/
│   ├── projects/
│   │   └── sandbox/                   # Sandbox проект
│   │       └── sandbox.db
│   └── config/
│       └── projects.json              # Конфиг проектов
│
└── docs/
    ├── TZ.md                          # Техническое задание
    ├── DEV_PLAN_v0.5.md               # План разработки
    └── INTERFACE_GUIDE.md             # Гид по интерфейсу
```

---

## 🔑 Ключевые принципы

### 1. Связи из атрибутов

Связи **не хранятся** в отдельной таблице, а извлекаются из атрибутов:
- `parent_id` — явная связь parent-of
- `module`, `epic`, `feature` — иерархические связи

```python
# graph_builder.py
def build_graph_from_attributes(items):
    for item in items:
        if item.parent_id:
            edges.append({'from': item.parent_id, 'to': item.id})
        if item.module:
            parent = find_parent_by_title(items, item.module, 'Module')
            if parent:
                edges.append({'from': parent.id, 'to': item.id})
```

### 2. FuncID генерируется автоматически

```python
# funcid_generator.py
def generate_funcid(item_type, title, module, epic, feature):
    # MOD:NAME, EPIC:MOD.NAME, FEAT:MOD.EPIC.NAME
    parts = [module, epic, feature, title]
    return f"{type_prefix}:{'.'.join(parts)}"
```

### 3. Inline редактирование

Двойной клик на ячейку → редактирование:
- Title, Alias, Segment — текст
- isCrit, isFocus — checkbox
- Module, Epic, Feature — dropdown с созданием нового

### 4. Sandbox проект

Учебный проект:
- Нельзя удалить
- Кнопка "Reset Sandbox" (в плане)
- Шаблон по умолчанию: VoluptAS Documentation

---

## 💻 Стили кода

### Type hints обязательно

```python
from typing import List, Dict, Optional

def build_graph_from_attributes(items: List[FunctionalItem]) -> Tuple[List[Dict], List[Dict]]:
    """Построение графа"""
    ...
```

### Docstrings для всех функций

```python
def find_parent_by_title(items: List[FunctionalItem], title: str, type_filter: str) -> Optional[FunctionalItem]:
    """
    Поиск родителя по названию и типу
    
    Args:
        items: Список элементов
        title: Название для поиска
        type_filter: Тип элемента (Module, Epic...)
    
    Returns:
        Элемент или None
    """
```

### Логирование через logging

```python
import logging

logger = logging.getLogger(__name__)

def build_graph_from_attributes(items):
    logger.info(f"Building graph from {len(items)} items")
    ...
    logger.info(f"Graph built: {len(nodes)} nodes, {edges_created} edges")
```

---

## 🎨 UI/UX паттерны

### Inline vs Dialog

| Поле | Режим | Виджет |
|------|-------|--------|
| Title | Inline | QLineEdit |
| Segment | Inline | QLineEdit |
| isCrit | Inline | QCheckBox |
| Module | Dialog | QComboBox (с созданием нового) |
| Epic | Dialog | QComboBox (с созданием нового) |

### Создание дочерних элементов

**Контекстное меню (ПКМ):**
```
➕ Создать дочерний:
  → Epic (для Module)
  → Feature (для Epic)
  → Story, Page, Element (для Feature)
```

**Редактор (вкладка "👶 Дочерние"):**
- Кнопки: `[Epic]` `[Feature]` `[Story]`
- Авто-заполнение иерархии
- Авто-сегмент по типу

---

## 📊 Модели данных

### FunctionalItem

```python
class FunctionalItem(Base):
    id = Column(Integer, primary_key=True)
    functional_id = Column(String(500), unique=True)  # MOD:FRONT.EPIC.FEAT
    alias_tag = Column(String(200), unique=True)      # Короткий алиас
    title = Column(String(500), nullable=False)
    type = Column(String(50))  # Module, Epic, Feature...
    
    # Иерархия
    parent_id = Column(Integer, ForeignKey('functional_items.id'))
    module = Column(String(200))
    epic = Column(String(200))
    feature = Column(String(200))
    
    # Сегмент
    segment = Column(String(100))  # UI, UX/CX, API...
    
    # Приоритеты
    is_crit = Column(Integer, default=0)
    is_focus = Column(Integer, default=0)
    
    # RACI
    responsible_qa_id = Column(Integer, ForeignKey('users.id'))
    responsible_dev_id = Column(Integer, ForeignKey('users.id'))
```

### User

```python
class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True)
    position = Column(String(200))
    role = Column(String(100))  # QA, Dev, BA...
    is_active = Column(Integer, default=1)
```

---

## 🔧 Интеграции

### Google Sheets

```python
# src/integrations/google.py
class GoogleSheetsClient:
    def __init__(self, credentials_path, spreadsheet_id):
        ...
    
    def export_all_tables(self):
        # Экспорт FunctionalItem, User, Relation
```

### Zoho Projects

```python
# src/integrations/zoho.py
class ZohoProjectsClient:
    def get_sprints(self, project_id):
        # Список спринтов
    
    def get_tasks(self, sprint_id):
        # Задачи спринта
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
pytest tests/ -v
pytest tests/test_graph_builder.py -v
```

### Пример теста

```python
def test_find_parent_by_title():
    items = [
        FunctionalItem(id=1, title="[Module]: FRONT", type="Module"),
        FunctionalItem(id=2, title="FRONTEND", type="Module"),
    ]
    
    # Точное совпадение
    parent = find_parent_by_title(items, "[Module]: FRONT", "Module")
    assert parent.id == 1
    
    # Без префикса
    parent = find_parent_by_title(items, "FRONT", "Module")
    assert parent.id == 1
```

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| `docs/TZ.md` | Техническое задание |
| `docs/DEV_PLAN_v0.5.md` | План разработки v0.5 |
| `docs/INTERFACE_GUIDE.md` | Гид по интерфейсу |
| `docs/ACCEPTANCE_CASES.html` | Приёмочные кейсы |
| `docs/E2E_TEST_PLAN.md` | План E2E тестов |

---

## 🚀 Быстрый старт

```bash
# Установка
start_voluptas.bat

# Запуск тестов
pytest tests/ -v

# Проверка типов
mypy src/
```

---

**Последнее обновление:** 2026-02-19  
**Версия:** 0.4 (Graph MVP)
