# MEMORY BANK — VoluptAS

> Конвенции проекта, архитектурные решения и стандарты

---

## Code Style

### Именование
- **Классы:** PascalCase (`FunctionalItem`, `DatabaseManager`)
- **Функции:** snake_case (`get_session`, `import_from_csv`)
- **Переменные:** snake_case (`item_type`, `is_active`)
- **Константы:** UPPER_CASE (`MAX_BATCH_SIZE`, `DEFAULT_REGION`)

### Форматирование
- **Длина строки:** до 100 символов
- **Отступы:** 4 пробела
- **Кавычки:** одинарные `'` для строк

### Type Hints
- **Обязательно:** для public API функций и классов
- **Рекомендуется:** для внутренних функций

### Docstrings
- **Стиль:** Google style
- **Обязательно:** для всех public функций

### Комментарии
- **Внутренние заметки:** русский
- **Public API документация:** английский

---

## Архитектурные паттерны

### Слои приложения

```
┌─────────────────┐
│      UI         │  PyQt6, dialogs, widgets
├─────────────────┤
│    Services     │  Business logic, exporters
├─────────────────┤
│  Integrations   │  API clients (Google, Zoho, Qase)
├─────────────────┤
│     Models     │  SQLAlchemy ORM
├─────────────────┤
│   Database     │  SQLite, sessions, migrations
└─────────────────┘
```

### Multi-Project Architecture
- Каждый проект — отдельная БД в `data/projects/{project_id}/`
- Конфиги в `data/config/` (вне git)
- `ProjectManager` управляет переключением

### Database Layer
- **ORM:** SQLAlchemy 2.0
- **Сессии:** через `DatabaseManager.get_session()`
- **Миграции:** автоматические при старте

---

## Logging / Error Handling

### Логи

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Сообщение")
```

**Уровни:**
- `DEBUG` — отладочная информация
- `INFO` — штатные события
- `WARNING` — предупреждения
- `ERROR` — ошибки с traceback
- `CRITICAL` — критичные ошибки

**Файл:** `logs/voluptas.log` (ротация: 10MB, 5 backup)

### Error Handling

```python
# ✅ ПРАВИЛЬНО
try:
    # код
    pass
except SpecificError as e:
    logger.error(f"Ошибка: {e}")
    raise
finally:
    # очистка
    pass

# ❌ НЕПРАВИЛЬНО
try:
    # код
    pass
except:  # bare except
    pass
```

---

## Testing Rules

### Стратегия покрытия
- **Unit тесты:** рядом с кодом (`src/models/` → `tests/test_models.py`)
- **Integration тесты:** в `/tests/integration/`
- **E2E тесты:** через behave (`.feature` файлы)

### Запуск тестов
```bash
pytest                   # все тесты
pytest --cov=src         # с покрытием
pytest tests/test_<module>.py  # конкретный модуль
behave                   # BDD тесты
```

### Best Practices
- **Изоляция:** каждый тест независим
- **Фикстуры:** через `@pytest.fixture`
- **Моки:** `unittest.mock` для внешних зависимостей
- **База данных:** тестовая БД в памяти или временный файл

---

## Database Rules

### Подключение к БД

```python
# ✅ ПРАВИЛЬНО
from src.db import DatabaseManager

session = DatabaseManager.get_session()
try:
    items = session.query(FunctionalItem).all()
    session.commit()
finally:
    session.close()

# ❌ НЕПРАВИЛЬНО
from src.db import SessionLocal
session = SessionLocal()  # Не создавать в UI-виджетах!
```

### Модели
- **Основные:** `FunctionalItem`, `User`, `FunctionalItemRelation`, `Dictionary`
- **Foreign keys:** с `ondelete='CASCADE'`
- **Indexes:** для часто используемых полей
- **`__tablename__`:** в snake_case

---

## UI Patterns (PyQt6)

### Сигналы и слоты
```python
# ✅ ПРАВИЛЬНО
button.clicked.connect(self.on_button_clicked)

@pyqtSlot()
def on_button_clicked(self):
    pass
```

### Потоки (QThread)
```python
# ✅ ПРАВИЛЬНО для долгих операций
class WorkerThread(QThread):
    result_ready = pyqtSignal(object)
    
    def run(self):
        result = long_operation()
        self.result_ready.emit(result)
```

### Локализация
- **UI текст:** Русский
- **Ошибки:** Русский с техническими деталями
- **Логи:** Английский

---

## Integration Rules

### Google Sheets
- **Клиент:** `GoogleSheetsClient`
- **Правила:** Batch processing, автообновление токенов

### Zoho Projects
- **Клиент:** `ZohoClient`
- **Правила:** OAuth 2.0, умное слияние данных

### Qase.io
- **Клиент:** `QaseClient`
- **Правила:** Работа с attachments, suites, milestones

---

## Security

### Защищённые пути
```
credentials/*.json
credentials/*.env
**/.env
**/*key*
**/secrets/**
```

### Запрещено
- ❌ Чтение credentials
- ❌ Коммит `.env` файлов
- ❌ Логирование секретов
- ❌ Хардкод токенов

---

## Протокол ведения CONTINUITY.md

- ✅ Обновлять только при реальных изменениях (цель, статус, решения)
- ✅ Не хранить пересказ диалога — только факты
- ✅ При потере контекста — восстановить из CONTINUITY.md
- ✅ Не дублировать информацию из README.md
- ✅ Не хранить гипотезы как факты — помечать `UNCONFIRMED`

---

## Project-Specific Knowledge (VoluptAS)

### Архитектура VoluptAS

**VoluptAS** — PyQt6 приложение для управления QA coverage, иерархией функционала, RACI матрицей.  
**Стек:** Python 3.11+, PyQt6, SQLAlchemy, SQLite  
**Интеграции:** Google Sheets, Zoho Projects, Qase.io

### Модели данных (SQLAlchemy ORM)

#### FunctionalItem — основная сущность
```python
functional_id      # "front.splash_page.cookies" (УНИКАЛЬНЫЙ, key!)
type                # enum: Module, Epic, Feature, Story, Page, Element, Service
segment             # enum: UI, API, Backend, Database, Security, etc
parent_id           # Иерархия (для Module→Epic→Feature→Story)

# RACI роли
responsible_qa_id   # FK User (кто делает тесты)
responsible_dev_id  # FK User (кто разрабатывает)
accountable_id      # FK User (кто отвечает)
consulted_ids       # JSON array (кого спросить)
informed_ids        # JSON array (кого уведомить)

# Приоритизация
is_crit, is_focus
```

#### Relation — связи между элементами
```python
# Типы: hierarchy, functional, page_element, service_dependency, test_coverage, bug_link, doc_link
type                # enum для типа связи
source_id, target_id  # FK к FunctionalItem
is_bidirectional    # двусторонняя ли
```

### Multi-Project Support

**Ключевой класс: `ProjectManager` и `DatabaseManager`**

```python
# Получить текущий проект
pm = ProjectManager(config_dir)
current = pm.get_current_project()  # ProjectConfig

# Подключить БД проекта
db_manager = DatabaseManager()
db_manager.connect_to_database(current.database_path)
session = db_manager.get_session()

# Переключиться на другой проект
pm.set_current_project("sandbox")
db_manager.connect_to_database(...)  # новое подключение
```

**Файлы конфигов:**
- `data/config/projects.json` — реестр всех проектов (id, name, db_path, profile)
- `data/config/profiles.json` — профили (production/sandbox/custom) с путями к credentials
- `data/config/current_project.txt` — текущий активный проект

### Credentials Pattern

```python
from src.config import Config
from dotenv import load_dotenv

# Правило: всегда через Config.get_credentials_path()
zoho_env = Config.get_credentials_path("zoho.env")
google_json = Config.get_credentials_path("google_credentials.json")

load_dotenv(zoho_env)
client_id = os.getenv("ZOHO_CLIENT_ID")
```

**Структура:**
```
credentials/
├── zoho.env                    # ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_AUTHORIZATION_CODE
├── google_credentials.json     # Google OAuth JSON
├── qase.env                    # QASE_API_TOKEN
└── templates/                  # *.example для новичков
```

### Common Patterns

#### Создание + сохранение
```python
item = FunctionalItem(functional_id="...", title="...", type="Feature")
session.add(item)
session.commit()
```

#### Фильтрация с условиями
```python
from sqlalchemy import and_
items = session.query(FunctionalItem).filter(
    and_(
        FunctionalItem.type == "Feature",
        FunctionalItem.is_crit == True
    )
).all()
```

#### RACI назначение
```python
item.responsible_qa_id = user.id
item.accountable_id = lead_user.id
session.commit()
```

### Logging (обязательно!)

```python
logger = logging.getLogger(__name__)
logger.debug("debug info")
logger.info("normal event")
logger.error(f"error: {e}", exc_info=True)
```

**Файл:** `logs/voluptas.log` (ротация: 10MB × 5 backup)

### UI (PyQt6)

- **main_window.py** → Menu + Toolbar + Tabs + StatusBar
- **settings_dialog.py** → Интеграции (Google, Zoho, Qase) ← **ДОБАВИТЬ ZOHO CODE FIELD**
- **table_view.py** → Таблица функционала
- **import/export_dialog.py** → Диалоги

### Critical Bugs (TODO)

1. **Zoho Authorization Code in settings UI** (30 min)
   - Файл: `src/ui/dialogs/settings_dialog.py`
   - Добавить QLineEdit для `ZOHO_AUTHORIZATION_CODE`

2. **Project Deletion** (1+ hour)
   - Меню + диалог + удаление из projects.json + удаление папки

### Verification Loop

```bash
python -m py_compile main.py              # Компиляция
flake8 src/ --max-line-length=100         # Линтинг
black src/ --check                        # Форматирование
pytest tests/ --cov=src                   # Тесты
```

---

**Last Updated:** 2026-02-20  
**Version:** 0.3.4+  
**Project-Specific Knowledge:** ✅ Added
