# Концепция: Мультипроектность в VoluptAS

## 🎯 Цель

Поддержка работы с несколькими проектами одновременно с возможностью быстрого переключения между ними.

## 📋 Use Cases

### 1. Рабочие проекты
- **Project A** (production profile) - основной проект на работе
- **Project B** (production profile) - второй проект на работе
- Оба используют одни и те же credentials для Zoho/Google/Qase

### 2. Песочница
- **VoluptAS Sandbox** (sandbox profile) - проект для тестирования самого VoluptAS
- Использует отдельные тестовые credentials
- Содержит функционал самого приложения как feature-элементы

### 3. Миграция существующего проекта
- Текущая БД `data/voluptas.db` → `data/projects/default/voluptas.db`
- Автоматическая миграция при первом запуске

## 🏗️ Архитектура

```
VoluptAS/
├── data/
│   ├── config/
│   │   ├── projects.json         # Список всех проектов
│   │   ├── profiles.json         # Профили настроек
│   │   └── current_project.txt   # ID текущего активного проекта
│   │
│   └── projects/
│       ├── project_a/
│       │   ├── voluptas.db       # БД проекта A
│       │   ├── bdd_features/
│       │   └── reports/
│       │
│       ├── project_b/
│       │   ├── voluptas.db
│       │   ├── bdd_features/
│       │   └── reports/
│       │
│       └── voluptas_sandbox/
│           ├── voluptas.db       # БД песочницы
│           ├── bdd_features/
│           └── reports/
│
├── credentials/
│   ├── zoho.env                  # Production credentials
│   ├── google_credentials.json
│   ├── qase.env
│   │
│   └── sandbox/                  # Sandbox credentials
│       ├── zoho.env
│       ├── google_credentials.json
│       └── qase.env
```

## 📊 Модели данных

### ProjectConfig
```python
@dataclass
class ProjectConfig:
    id: str                    # Уникальный slug (project_a, project_b)
    name: str                  # Название для UI
    description: str           # Описание проекта
    database_path: Path        # Путь к БД проекта
    bdd_features_dir: Path
    reports_dir: Path
    settings_profile: str      # production | sandbox
    created_at: str
    last_used: str             # Для сортировки по последнему использованию
    is_active: bool
    tags: List[str]            # Тэги для фильтрации
```

### SettingsProfile
```python
@dataclass
class SettingsProfile:
    id: str                    # production | sandbox | custom
    name: str
    description: str
    zoho_env_path: Path
    google_json_path: Path
    qase_env_path: Path
    is_default: bool
```

## 🔄 Workflow

### 1. Первый запуск (миграция)
```
1. Обнаружена старая структура (data/voluptas.db)
2. Создаётся data/config/
3. Создаётся проект "default" с текущей БД
4. Пользователь видит диалог:
   "Обнаружена старая структура. Хотите мигрировать в новую?"
   [Мигрировать] [Отмена]
5. После миграции старый voluptas.db → projects/default/voluptas.db
```

### 2. Создание нового проекта
```
1. Меню → Файл → Новый проект
2. Диалог:
   - Название: "Project B"
   - ID: "project_b" (автоgенерация из названия)
   - Описание: "Второй рабочий проект"
   - Профиль: [Production ▼] | [Sandbox] | [Custom]
   - Теги: work, active
   [Создать] [Отмена]
3. Создаётся структура data/projects/project_b/
4. Инициализируется пустая БД
5. Автопереключение на новый проект
```

### 3. Переключение между проектами
```
# Вариант 1: Меню
Файл → Переключить проект → [Project A] [Project B] [Sandbox]

# Вариант 2: Выпадающий список в toolbar
[🗂️ Project A ▼]  [⚙️ Настройки]
```

### 4. При переключении проекта
```
1. Закрывается текущая session БД
2. Загружается ProjectConfig нового проекта
3. Пересоздаётся engine для новой БД
4. Пересоздаётся SessionLocal
5. Перезагружаются данные в UI
6. Обновляется WindowTitle: "VoluptAS - Project B"
7. Обновляется current_project.txt
```

## 🎨 UI Changes

### 1. Toolbar (новый элемент)
```
┌────────────────────────────────────────┐
│ [🗂️ Project A ▼] [🔄] [⚙️] [ℹ️]      │
└────────────────────────────────────────┘
```

- **🗂️ Project A ▼** - выпадающий список проектов
- **🔄** - обновить данные
- **⚙️** - настройки проекта
- **ℹ️** - информация о проекте

### 2. Project Selector Dialog
```
┌─────────────────────────────────────────┐
│ Выбор проекта                           │
├─────────────────────────────────────────┤
│                                         │
│ 🔍 [Поиск...]                           │
│                                         │
│ ┌───────────────────────────────────┐   │
│ │ 📁 Project A (production)         │ ← │
│ │    Основной рабочий проект        │   │
│ │    Последнее изменение: 2 ч назад │   │
│ │    ────────────────────────────   │   │
│ │ 📁 Project B (production)         │   │
│ │    Второй проект                  │   │
│ │    Последнее изменение: 1 день    │   │
│ │    ────────────────────────────   │   │
│ │ 🧪 VoluptAS Sandbox (sandbox)     │   │
│ │    Тестовая песочница             │   │
│ │    Последнее изменение: 3 дня     │   │
│ └───────────────────────────────────┘   │
│                                         │
│ [➕ Новый проект] [Отмена]              │
└─────────────────────────────────────────┘
```

### 3. Project Settings Dialog
```
┌─────────────────────────────────────────┐
│ Настройки проекта: Project A            │
├─────────────────────────────────────────┤
│ Вкладки: [Основные] [Профиль] [Пути]   │
│                                         │
│ === Основные ===                        │
│ Название: [Project A              ]    │
│ ID:       [project_a] (readonly)       │
│ Описание: [Основной рабочий проект]    │
│ Теги:     [work] [active] [+]          │
│ Активен:  ☑                            │
│                                         │
│ === Профиль настроек ===               │
│ [●] Production (Zoho, Google, Qase)    │
│ [ ] Sandbox                            │
│ [ ] Custom                             │
│                                         │
│ [💾 Сохранить] [Отмена]                │
└─────────────────────────────────────────┘
```

## 🔧 Технические детали

### 1. Изменения в database.py
```python
# До
DATABASE_PATH = DATA_DIR / 'voluptas.db'
engine = create_engine(DATABASE_URL, ...)

# После
class DatabaseManager:
    def __init__(self, project_manager: ProjectManager):
        self.project_manager = project_manager
        self.engine = None
        self.SessionLocal = None
    
    def connect_to_project(self, project_id: str):
        project = self.project_manager.projects[project_id]
        DATABASE_URL = f'sqlite:///{project.database_path}'
        self.engine = create_engine(DATABASE_URL, ...)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_current_session(self):
        return self.SessionLocal()
```

### 2. Изменения в MainWindow
```python
class MainWindow(QMainWindow):
    def __init__(self):
        self.project_manager = ProjectManager(config_dir)
        self.db_manager = DatabaseManager(self.project_manager)
        
        # Загрузка текущего проекта
        current_project = self.project_manager.get_current_project()
        if not current_project:
            self.show_project_selector()
        else:
            self.db_manager.connect_to_project(current_project.id)
            self.session = self.db_manager.get_current_session()
        
        self.init_ui()
        self.load_data()
    
    def switch_project(self, project_id: str):
        # Закрываем текущую сессию
        self.session.close()
        
        # Переключаемся на новый проект
        self.project_manager.switch_project(project_id)
        self.db_manager.connect_to_project(project_id)
        self.session = self.db_manager.get_current_session()
        
        # Обновляем UI
        self.load_data()
        self.update_window_title()
```

### 3. Settings Dialog изменения
```python
class SettingsDialog(QDialog):
    def __init__(self, project_manager, parent=None):
        self.project_manager = project_manager
        self.current_project = project_manager.get_current_project()
        self.profile = project_manager.get_profile(
            self.current_project.settings_profile
        )
        
        # Загружаем credentials из путей профиля
        self.zoho_env_path = self.profile.zoho_env_path
        # ...
```

## 🚀 Этапы реализации

### Этап 1: Модели и менеджер (✅ Готово)
- [x] ProjectConfig dataclass
- [x] SettingsProfile dataclass
- [x] ProjectManager class

### Этап 2: Миграция БД
- [ ] DatabaseManager class
- [ ] Логика переподключения к БД
- [ ] Автомиграция старой структуры
- [ ] Тесты миграции

### Этап 3: UI для управления проектами
- [ ] ProjectSelectorDialog
- [ ] ProjectSettingsDialog
- [ ] Toolbar с выпадающим списком проектов
- [ ] Меню "Файл → Новый проект"

### Этап 4: Интеграция в MainWindow
- [ ] Инициализация ProjectManager
- [ ] Переключение проектов
- [ ] Обновление WindowTitle
- [ ] Сохранение last_used

### Этап 5: Обновление SettingsDialog
- [ ] Загрузка credentials из профиля проекта
- [ ] Поддержка нескольких профилей

### Этап 6: Тестирование
- [ ] Unit-тесты ProjectManager
- [ ] Integration-тесты переключения проектов
- [ ] Миграция реального проекта

### Этап 7: Документация
- [ ] Обновление README с multi-project
- [ ] User Guide: "Работа с проектами"
- [ ] Migration Guide для существующих пользователей

## 💡 Дополнительные возможности

### 1. Импорт/экспорт проекта
```
Файл → Экспорт проекта → voluptas_project_a.zip
  ├── voluptas.db
  ├── bdd_features/
  └── reports/

Файл → Импорт проекта → [Выбрать ZIP]
```

### 2. Клонирование проекта
```
Создать копию Project A → Project A (Copy)
- Копируется вся БД
- Создаётся новый ID
```

### 3. Архивация проекта
```
- Проект помечается is_active=False
- Скрывается из списка активных
- Доступен через "Показать архивные"
```

### 4. Теги и фильтрация
```
Теги: work, personal, archive, sandbox
Фильтр по тегам в Project Selector
```

### 5. Статистика проекта
```
Project Info:
- Количество функциональных элементов
- Покрытие тестами
- Дата создания / последнего изменения
- Размер БД
```

## 🔒 Безопасность

- Credentials хранятся вне projects/
- Профили могут иметь разные credentials
- Sandbox изолирован от production

## 📝 Ответы на вопросы

### 1. "У меня два рабочих проекта"
✅ Создаёшь Project A и Project B, оба с профилем "production"  
✅ Переключаешься через выпадающий список в toolbar  
✅ Оба используют одни Zoho/Google credentials

### 2. "Песочница для самого VoluptAS"
✅ Создаёшь "VoluptAS Sandbox" с профилем "sandbox"  
✅ Заполняешь функционал самого VoluptAS как features  
✅ Используешь для экспериментов и тестов

### 3. "Настройки при смене проекта"
✅ Профиль настроек привязан к проекту  
✅ Production-проекты используют production credentials  
✅ Sandbox использует отдельные тестовые credentials

### 4. "Переключение между проектами"
✅ Toolbar: выпадающий список проектов  
✅ Меню: Файл → Переключить проект  
✅ Горячие клавиши: Ctrl+Shift+P (Quick Switch)

## 📊 Шаблоны отчётов

### Где находятся?
```
Инструменты → 📋 Шаблоны отчётов
```

### Модель
- Таблица: `report_templates`
- Markdown контент с placeholders
- Типы: test_plan, bug_report, sprint_report, custom

### Editor
- Левая панель: Markdown Editor
- Правая панель: Preview
- Placeholder'ы: `{{milestone_name}}`, `{{task_count}}`, etc.

### Пример шаблона
```markdown
# Тест-план спринта {{milestone_name}}

> Дата: {{date}}
> QA Lead: {{qa_name}}

## 1. Функциональность в релизе
{{feature_list}}

## 2. Задачи
| ID | Задача | Приоритет | QA | Status |
|----|--------|-----------|-----|--------|
{{task_table}}

## 3. Метрики
- Всего задач: {{task_count}}
- Найдено багов: {{bug_count}}
- Покрытие: {{coverage}}%
```

### Генерация
```
Инструменты → 📊 Генератор отчётов
1. Выбрать шаблон
2. Выбрать данные (features, tasks, bugs)
3. Сгенерировать
4. Экспорт в .md / Google Docs
```

---

**Статус:** 🟡 В разработке (Этап 1 завершён)  
**Автор:** AI Assistant  
**Дата:** 2025-10-22
