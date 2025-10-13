# Интеграции VoluptAS

⚠️ **MATURE CODE** - проверенный код из продакшена `ITS_Scripts`

Этот документ описывает готовые интеграции с внешними сервисами, портированные из рабочего проекта.

---

## 📁 Структура

```
src/integrations/
├── google/              # Google Sheets интеграция
│   ├── __init__.py
│   └── google_sheets_client.py
└── zoho/                # Zoho Projects API интеграция
    ├── __init__.py
    ├── Zoho_api_client.py      # Основной API клиент
    ├── User.py                 # Модель пользователей
    ├── TaskStatus.py           # Модель статусов задач
    ├── DefectStatus.py         # Модель статусов дефектов
    ├── portal_data.py          # Хардкод данные портала
    ├── test_zoho.py            # Тестовые скрипты
    ├── config_zoho.env         # Конфигурация (НЕ КОММИТИТЬ!)
    └── BUG.json                # Пример структуры бага

src/services/
└── TestPlanGenerator.py      # Генератор тест-планов релизов
```

---

## 🔧 Google Sheets Integration

**Файл**: `src/integrations/google/google_sheets_client.py`

### Назначение
Клиент для экспорта данных в Google Sheets через сервисный аккаунт.

### Использование

```python
from src.integrations.google import GoogleSheetsClient

# Инициализация
client = GoogleSheetsClient(
    credentials_path="path/to/service_account.json",
    spreadsheet_id="your_spreadsheet_id",
    worksheet_name="Sheet1"
)

# Добавление данных
client.append_result({
    "timestamp": "2025-10-13 12:00",
    "functional_id": "front.splash_page.cookies",
    "test_result": "PASS",
    "tester": "Anatol Kiseleow"
})
```

### Зависимости
- `gspread`
- `google-auth`
- `numpy`

### Особенности
- Автоматическое создание заголовков
- Поддержка numpy типов
- Автоматическое добавление недостающих колонок

---

## 🔧 Zoho Projects API Integration

**Файл**: `src/integrations/zoho/Zoho_api_client.py`

### Назначение
Полноценный клиент для работы с Zoho Projects API.

### Поддерживаемые операции

#### 📋 Задачи (Tasks)
```python
from src.integrations.zoho import ZohoAPI

api = ZohoAPI()

# Получить задачи по мейлстоуну
tasks = api.get_tasks_by_milestone(milestone_id="123456")

# Получить задачи в диапазоне дат
tasks = api.get_tasks_in_date_range("2025-01-01", "2025-01-31")

# Поиск задач по названию таск-листа/мейлстоуна
tasks = api.get_tasks_by_title("Release #19")
```

#### 🐞 Баги (Bugs)
```python
# Получить баги с фильтрами
bugs = api.get_entities_by_filter(
    entity_type="bugs",
    created_after="2025-01-01",
    created_before="2025-01-31",
    owner_id="12345",
    tags=["critical", "regression"]
)

# Создать баг
api.create_bug(
    title="Критичный баг",
    description="Подробное описание",
    assignee_id="12345",
    priority="High"
)
```

#### 👥 Пользователи
```python
from src.integrations.zoho import user_manager

# Получить пользователя по ID
user = user_manager.get_user_by_id(816882747)
print(f"{user.user_name} ({user.role})")  # Anatol Kiseleow (QA)

# Получить пользователя по имени
user = user_manager.get_user_by_name("Anatol Kiseleow")
```

#### 📊 Статусы
```python
from src.integrations.zoho import task_status_manager, defect_status_manager

# Статусы задач
status = task_status_manager.get_status_by_name("In Progress")
print(status.status_color_hexcode)  # #fbc11e

# Статусы дефектов
status = defect_status_manager.get_status_by_name("Open")
```

### Зависимости
- `requests`
- `python-dotenv`

### Конфигурация

Создайте файл `src/integrations/zoho/config_zoho.env`:

```env
ZOHO_CLIENT_ID=your_client_id
ZOHO_CLIENT_SECRET=your_client_secret
ZOHO_REFRESH_TOKEN=your_refresh_token
ZOHO_ACCESS_TOKEN=your_access_token
ZOHO_PROJECT_ID=your_project_id
ZOHO_PORTAL_NAME=your_portal_name
ZOHO_REGION=eu
ZOHO_AUTHORIZATION_CODE=your_auth_code
ZOHO_REDIRECT_URI=https://your-redirect-uri.com
```

⚠️ **НЕ КОММИТИТЬ `.env` ФАЙЛЫ В GIT!**

### Автоматическое обновление токенов
API клиент автоматически:
- Проверяет валидность `access_token`
- Обновляет токен через `refresh_token`
- Сохраняет новые токены в `config_zoho.env`

---

## 📝 Test Plan Generator

**Файл**: `src/services/TestPlanGenerator.py`

### Назначение
Генерирует Markdown тест-планы релизов на основе данных из Zoho Projects.

### Использование

```python
from src.services import TestPlanGenerator
from src.integrations.zoho import user_manager, task_status_manager, defect_status_manager, ZohoAPI

# Инициализация
generator = TestPlanGenerator(
    users_mngr=user_manager,
    task_status_mngr=task_status_manager,
    defect_status_mngr=defect_status_manager
)

# Установка дат спринта
generator.set_dates("2025-01-01", "2025-01-31")

# Сбор задач из мейлстоунов
api = ZohoAPI()
all_tasks = []
for milestone_name in ["Release #19", "Release #19 hot fix"]:
    tasks = api.get_tasks_by_title(milestone_name)
    all_tasks.extend(tasks)

# Генерация тест-плана
generator.generate_plan_for_tasks(all_tasks, output_file="test_plan.md")
```

### Генерируемые секции

1. **Затронутый функционал** - автоматически на основе тегов задач
2. **Фокус-лист** - критичные области для тестирования
3. **Таблица задач** - с мейлстоунами, приоритетами, ответственными
4. **Расписание тестирования** - автоматически по датам спринта
5. **Отчёт по дефектам** - обнаруженные и закрытые баги

### Пример вывода

```markdown
## 2. Задачи в рамках релиза

| Задача (ID, название) | Мейлстоун/Таск-лист | Приоритет | QA  | Dev  | Статус   |
| --------------------- | ------------------- | --------- | --- | ---- | -------- |
| [TSK-123](https://...) - Новая фича | Release #19 / Frontend | High | Anatol Kiseleow | Danil Babenkov | Testing |
```

---

## 🔐 Безопасность

### Секреты
- ❌ **НЕ КОММИТИТЬ** `.env` файлы
- ❌ **НЕ КОММИТИТЬ** `service_account.json` для Google
- ✅ Добавить в `.gitignore`:
  ```
  *.env
  service_account*.json
  config_*.env
  ```

### Токены Zoho
- Хранятся в `config_zoho.env`
- Автоматически обновляются через API
- Требуют однократной настройки через OAuth

---

## 📦 Зависимости для интеграций

Добавить в `requirements.txt`:

```txt
# Google Sheets
gspread>=5.12.0
google-auth>=2.27.0
numpy>=1.26.0

# Zoho API
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## 🚀 Следующие шаги

### Адаптация под VoluptAS

1. **Использовать Zoho API для импорта данных**:
   - Задачи → FunctionalItem (module/epic/feature)
   - Баги → связь с FunctionalItem через теги
   - Пользователи → User модель (RACI роли)

2. **Экспорт в Google Sheets**:
   - Coverage Reports
   - Test Results
   - Analytics Dashboards

3. **Автоматизация тест-планов**:
   - Интеграция с существующим TestPlanGenerator
   - Экспорт тест-планов в Markdown/PDF
   - Интеграция с CI/CD

---

## 📚 Дополнительные ресурсы

- [Zoho Projects API Docs](https://www.zoho.com/projects/help/rest-api/zoho-projects-rest-api.html)
- [Google Sheets API Guide](https://developers.google.com/sheets/api)
- [Оригинальные скрипты](C:\ITS_QA\ITS_Scripts)

---

**Статус**: ✅ MATURE CODE - готов к использованию
**Последнее обновление**: 2025-10-13
**Автор портирования**: Anatol Kiseleow (QA)
