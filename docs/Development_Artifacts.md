

---

## 1. **Структура импорта (CSV → класс FunctionalItem)**

**Шаблон для сопоставления колонок:**

| CSV Field                | FunctionalItem Field         | Преобразование/Комментарий                |
|--------------------------|-----------------------------|-------------------------------------------|
| id (или пусто)           | id (Functional ID)          | Если пусто — генерировать по структуре    |
| Title                    | title                       |                                           |
| Type                     | type                        | Enum (Module, Epic, Feature, ...)         |
| Module                   | module                      |                                           |
| Epic                     | epic                        |                                           |
| Feature                  | feature                     |                                           |
| Stories                  | stories                     | Массив, парсить через “,”                 |
| Segment                  | segment                     | Enum, парсить (UI, UX/CX, API, ...)       |
| Description              | description                 |                                           |
| Tags and Aliases         | tags, aliases               | Разделять: known tags → tags, остальное → aliases |
| Roles                    | responsible_qa/dev/…        | Парсить по имени, только если есть в справочнике |
| isFocus                  | isFocus                     | TRUE/FALSE → bool                         |
| isCrit                   | isCrit                      | TRUE/FALSE → bool                         |
| Responsible (QA)         | responsible_qa              | Только из справочника                     |
| Responsible (Dev)        | responsible_dev             | Только из справочника                     |
| Accountable              | accountable                 | Только из справочника                     |
| Consulted                | consulted                   | Только из справочника, массив             |
| Informed                 | informed                    | Только из справочника, массив             |
| Automation Status        | automation_status           | Enum                                      |
| Maturity                 | maturity                    | Enum                                      |
| Container                | container                   |                                           |
| Database                 | database                    |                                           |
| Subsystems involved      | subsystems_involved         | Массив                                    |
| External Services        | external_services           | Массив                                    |

---

## 2. **Псевдокод парсера CSV**

```python
for row in csv_rows:
    item = FunctionalItem()
    item.id = row['id'] or generate_functional_id(row)
    item.title = row['Title']
    item.type = parse_enum(row['Type'])
    item.module = row['Module']
    item.epic = row['Epic']
    item.feature = row['Feature']
    item.stories = parse_list(row['Stories'])
    item.segment = parse_enum(row['Segment'])
    item.description = row['Description']
    tags, aliases = parse_tags_aliases(row['Tags and Aliases'])
    item.tags = tags
    item.aliases = aliases
    item.isFocus = parse_bool(row['isFocus'])
    item.isCrit = parse_bool(row['isCrit'])
    item.responsible_qa = find_user(row['Responsible (QA)'])
    item.responsible_dev = find_user(row['Responsible (Dev)'])
    item.accountable = find_user(row['Accountable'])
    item.consulted = parse_users(row['Consulted'])
    item.informed = parse_users(row['Informed'])
    item.automation_status = parse_enum(row['Automation Status'])
    item.maturity = parse_enum(row['Maturity'])
    item.container = row['Container']
    item.database = row['Database']
    item.subsystems_involved = parse_list(row['Subsystems involved'])
    item.external_services = parse_list(row['External Services'])
    item.status = "Approved" # по умолчанию
    validate(item)
    save_to_db(item)
```

---

## 3. **UML/ER-диаграмма (текстовая)**

```
+---------------------+       +------------+         +------------+
|   FunctionalItem    |<>-----|    User    |<>-------|   RACI     |
+---------------------+       +------------+         +------------+
| id (Functional ID)  |       | id         |         | functional_|
| type (enum)         |       | name       |         | item_id    |
| ...                 |       | ...        |         | ...        |
| tags  [*]           |                             /
| aliases [*]         |---------------------------/
| stories [*]         |
| responsible_qa (1)  |
| responsible_dev (1) |
| accountable (0..1)  |
| consulted [*]       |
| informed  [*]       |
| ...                 |
+---------------------+
```

---

## 4. **REST API endpoints (OpenAPI-псевдо)**

```yaml
GET /functional-items
  params: filter (type, segment, isCrit, isFocus, responsible_qa, status)
  returns: [FunctionalItem]

POST /functional-items
  body: FunctionalItem
  returns: FunctionalItem

GET /users
  returns: [User]

POST /users
  body: User
  returns: User

GET /matrix
  params: filter (isCrit, isFocus, status, ...)
  returns: matrix, metrics

GET /export
  params: format (csv, xlsx, md), filter
  returns: file

# Пример эндпоинта для метрик покрытия:
GET /metrics
  params: filter (segment, status, isCrit, ...)
  returns: { total, covered_by_tc, covered_by_auto, covered_by_docs, ... }
```

---

## 5. **Wireframe UX — Импорт и валидация**

```
+---------------- Импорт CSV ----------------+
| [Выбрать файл]                            |
| [ ] Первый ряд — заголовки                |
| [Старт]                                   |
+-------------------------------------------+
| [Показать логи импорта]                   |
| - Дублирующиеся Functional ID: ...        |
| - Не найден Responsible QA: ...           |
| - Неизвестный сегмент: ...                |
| - Пустой тег: ...                         |
| ...                                       |
| [Отменить] [Импортировать валидные]       |
+-------------------------------------------+
```

---

## 6. **Шаблон для документации/README (пример для новых проектов)**

```
# Импорт функционала — структура и правила

1. CSV должен содержать следующие поля:
   - id, Title, Type, Module, Epic, Feature, Stories, Segment, Description, Tags and Aliases, Roles, isFocus, isCrit, Responsible (QA), Responsible (Dev), Accountable, Consulted, Informed, Automation Status, Maturity, Container, Database, Subsystems involved, External Services
2. Поля типа enum (Type, Segment, Automation Status, Maturity) — строго по справочнику.
3. Functional ID уникален. Повторы — ошибка.
4. Ответственные — только те, что заведены в справочнике сотрудников.
5. Статус по умолчанию: Approved
6. Даты (created_at, updated_at) — если нет, подставляются автоматически.
7. Все ошибки при импорте отображаются до загрузки в систему.
```

---

**Эти артефакты гарантируют, что твой ИИ-ассистент, разработчик или проектная команда смогут быстро стартовать работу, не тратя время на расшифровку структуры и маппинга.**