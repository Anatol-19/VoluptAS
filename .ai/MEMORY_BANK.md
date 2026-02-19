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

**Last Updated:** 2026-02-19  
**Version:** 0.3.4+
