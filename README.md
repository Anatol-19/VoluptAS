# VoluptAS

**Универсальный инструмент для управления функционалом и покрытием QA**

## Описание

VoluptAS - это десктопное приложение (MVP) для управления декомпозицией, трассировкой, покрытием и ответственностью за функциональные элементы продукта (фичи, эпики, страницы и т.д.), с поддержкой QA-отчётности, интеграции с BDD/feature-файлами и возможностью экспорта в Google Sheets, Markdown и Zoho.

## Ключевые возможности

- 📊 **Матрица покрытия** - отслеживание покрытия тест-кейсами, автотестами и документацией
- 🎯 **Крит и Фокус-листы** - выделение критичного и приоритетного функционала
- 👥 **RACI матрица** - управление ответственностью (Responsible, Accountable, Consulted, Informed)
- 🔗 **Граф связей** - визуализация иерархии и связей между элементами
- 📝 **BDD/Feature файлы** - генерация и управление Gherkin сценариями
- 📤 **Экспорт** - Google Sheets, Markdown, Zoho
- 🏷️ **Теги и алиасы** - гибкая система тегирования и поиска

## Архитектура

### Три ключевых экрана:

1. **Таблица (главный экран)**
   - Inline-редактирование
   - Фильтрация/поиск/сортировка
   - Быстрые фильтры по критичности и фокусу

2. **Граф связей**
   - Визуализация структуры и иерархии
   - N:M связи между сущностями
   - Интерактивная навигация

3. **Редактор сущности**
   - Динамический набор полей
   - Управление связями и тегами
   - RACI-роли

## Основные сущности

### FunctionalItem (фича-строка)

- `id` (Functional ID) - автогенерируемый уникальный составной тег
- `type` - Module, Epic, Feature, Page, Service, Element, Story
- `title`, `description`
- `module`, `epic`, `feature`, `stories`
- `segment` - UI, UX/CX, API, Backend, Database, etc.
- `tags`, `aliases` - система тегирования
- `isCrit`, `isFocus` - маркеры критичности и фокуса
- `responsible_qa`, `responsible_dev` - обязательные ответственные
- `accountable`, `consulted`, `informed` - RACI роли
- `test_cases_linked` - связанные тест-кейсы
- `automation_status` - статус автоматизации
- `documentation_links` - ссылки на документацию

### User (справочник сотрудников)

- `id`, `name`, `position`, `email`, `zoho_id`

## Метрики покрытия

- % покрытых тест-кейсами, автотестами, документацией
- % критичного/фокусного функционала с покрытием
- Количество "дыр" (без покрытия)
- Отдельная статистика по критичным элементам

## Экспорт и интеграция

- **Google Sheets** - импорт/экспорт с фильтрацией
- **Markdown** - структуры, матрицы, отчёты
- **Zoho** - экспорт сотрудников и матриц
- **CSV** - базовый импорт

## Статус проекта

🚧 **MVP в разработке**

## Технический стек

_(будет определён при старте разработки)_

## Документация

- [Техническое задание](docs/TZ/)
- [Интеграции (MATURE CODE)](docs/INTEGRATIONS.md) - Google Sheets, Zoho API, TestPlanGenerator

## Конфигурация

### Zoho API

Файл `src/integrations/zoho/config_zoho.env` уже настроен:
- ✅ Portal: vrbgroup
- ✅ Region: com
- ✅ Токены действительны

⚠️ **НЕ КОММИТИТЬ** `.env` файлы! (уже в .gitignore)

### Google Sheets

Для использования Google Sheets API:
1. Создайте service account в Google Cloud Console
2. Скачайте JSON credentials
3. Сохраните как `service_account.json` (уже в .gitignore)

## Структура проекта

```
VoluptAS/
├── src/
│   ├── models/              # ✅ SQLAlchemy модели
│   │   ├── functional_item.py
│   │   └── user.py
│   ├── integrations/        # ✅ MATURE CODE (из ITS_Scripts)
│   │   ├── google/          # Google Sheets API
│   │   └── zoho/            # Zoho Projects API
│   ├── services/            # ✅ MATURE CODE
│   │   └── TestPlanGenerator.py
│   ├── db/                  # 🟡 В процессе
│   ├── import/              # ⏳ TODO - Excel → SQLite
│   ├── export/              # ⏳ TODO - экспорт данных
│   └── ui/                  # ⏳ TODO - PyQt6 UI
├── data/
│   └── import/
│       └── VoluptaS_VRS_reference.xlsx
├── docs/
│   ├── TZ/                  # Техническое задание
│   └── INTEGRATIONS.md      # Документация интеграций
├── requirements.txt         # ✅ Зависимости
└── .gitignore               # ✅ Защита секретов
```

## Лицензия

_(будет определена)_

## Автор

Anatol-19 (beast.19k@gmail.com)

---

**Дата создания:** 2025-10-13  
**Версия:** 0.1.0 (MVP Planning)
