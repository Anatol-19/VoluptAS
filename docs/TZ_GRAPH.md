# Техническое задание: Граф связей (Graph View)
## Поддержка гетерогенных связей и интерактивная визуализация

---

## 1. Ключевая идея

**Граф в VoluptAS — это не просто дерево.**  
Он должен одновременно отображать:

- **Строгую иерархию** (Module → Epic → Feature → Story)
- **Локальные "поместные" иерархии** (Page → Element — POM)
- **Кросс-связи** (Feature ↔ Service, Story ↔ Page/Element, Feature ↔ Feature)
- **Связи с внешними системами** (Zoho задачи, Qase тест-кейсы, документация)

И делать разницу между ними **очевидной визуально и интерактивно**.

---

## 2. Типы связей (Edge Types)

### 2.1 Обязательные типы связей

Каждая связь должна иметь поле `type` (enum):

| Type | Описание | Визуализация | Пример |
|------|----------|--------------|--------|
| `hierarchy` | Parent-child иерархия | Толстая сплошная линия, направленная | Module → Epic → Feature |
| `functional` | N:M функциональные связи | Тонкая линия с маркером | Feature ↔ Feature |
| `page_element` | POM-иерархия | Пунктирная тонкая линия | Page → Element |
| `service_dependency` | Зависимость от сервиса | Линия с иконкой сервиса | Feature → Service |
| `test_coverage` | Связь с тест-кейсами | Зелёная пунктирная | Feature → TestCase |
| `bug_link` | Связь с багами/задачами | Красная волнистая | Feature → ZohoBug |
| `doc_link` | Ссылка на документацию | Синяя тонкая | Feature → Doc |
| `custom` | Пользовательская связь | Настраиваемая | любая |

### 2.2 Атрибуты связи

Каждая связь имеет метаданные:

```python
{
    "type": "functional",           # Тип связи
    "directed": True,               # Направленная или нет
    "weight": 1.0,                  # Вес/важность (опционально)
    "origin": "zoho",               # Источник: manual, zoho, csv, qase, import
    "created_at": "2025-10-15",     # Дата создания
    "created_by": "user_id",        # Автор
    "notes": "Описание связи",      # Комментарий
    "provenance": {...}             # Метаданные источника
}
```

---

## 3. Визуальная семантика (обязательная)

### 3.1 Отображение рёбер (Edge Encoding)

**Правила:**
1. **Тип → Стиль линии**
   - `hierarchy`: сплошная толстая (`linewidth=3`, `solid`)
   - `functional`: сплошная средняя (`linewidth=1.5`, `solid`)
   - `page_element`: пунктирная тонкая (`linewidth=1`, `dashed`)
   - `service_dependency`: пунктирная толстая (`linewidth=2`, `dotted`)
   - `test_coverage`: пунктирная средняя (`linewidth=1.5`, `dashed`, зелёный)
   - `bug_link`: волнистая (`linewidth=1.5`, красный)
   - `doc_link`: тонкая (`linewidth=1`, синий)

2. **Важность → Толщина**
   - `weight` влияет на толщину линии (умножение базового linewidth)

3. **Цвет по типу**
   - `hierarchy`: серый (#555555)
   - `functional`: оранжевый (#FF8C00)
   - `page_element`: голубой (#87CEEB)
   - `service_dependency`: фиолетовый (#9370DB)
   - `test_coverage`: зелёный (#32CD32)
   - `bug_link`: красный (#DC143C)
   - `doc_link`: синий (#4169E1)

4. **Стрелки (направление)**
   - Направленные связи имеют стрелку на конце
   - Двунаправленные — стрелки с обеих сторон или без стрелок

### 3.2 Отображение нод (Node Encoding)

**Правила:**
1. **Цвет по типу элемента:**
   - `Module`: тёмно-синий (#1E3A8A)
   - `Epic`: синий (#3B82F6)
   - `Feature`: зелёный (#10B981)
   - `Story`: светло-зелёный (#6EE7B7)
   - `Service`: фиолетовый (#8B5CF6)
   - `Page`: оранжевый (#F59E0B)
   - `Element`: жёлтый (#FBBF24)

2. **Форма по сегменту:**
   - UI/UX: круг (⭕)
   - Backend/API: квадрат (◼️)
   - Database: ромб (◆)
   - Service: шестиугольник (⬡)

3. **Размер по критичности:**
   - `is_crit`: увеличенный размер × 1.5
   - `is_focus`: толстая граница

4. **Бейджи/иконки:**
   - 🔗 если есть кросс-связи
   - ⚠️ если критичный
   - 🎯 если фокусный
   - ✅ если покрыт тестами

### 3.3 Edge metadata on hover/click

**Hover над связью:**
- Tooltip с информацией:
  ```
  Тип: Functional (N:M)
  Источник: Zoho Import
  Создано: 2025-10-13
  Автор: Anatol K.
  Вес: 0.8
  Комментарий: Фича использует сервис авторизации
  ```

**Click по связи:**
- Открыть боковую панель для редактирования метаданных
- Возможность добавить комментарий, изменить вес, тип

---

## 4. UX-режимы (View Modes) — обязательные

### 4.1 Hierarchy Mode (Иерархический)

**Цель:** Понять структуру Module → Epic → Feature → Story

**Настройки:**
- Показывать только `hierarchy` связи
- Layout: **layered** (Sugiyama algorithm)
- Drill-down по уровням
- Collapse/expand узлов уровня

**UX:**
```
Module
  ├─ Epic 1
  │   ├─ Feature 1.1
  │   │   ├─ Story 1.1.1
  │   │   └─ Story 1.1.2
  │   └─ Feature 1.2
  └─ Epic 2
```

### 4.2 Dependency / Architecture Mode (Архитектурный)

**Цель:** Увидеть архитектурные зависимости, кросс-связи между фичами/сервисами

**Настройки:**
- Показывать `service_dependency`, `functional`, `page_element`
- Опционально скрыть `hierarchy`
- Layout: **force-directed** с группировкой по модулям
- Compound nodes (узлы одного модуля держать вместе)

**UX:**
- Сервисы выделены отдельно
- Зависимости между фичами видны явно
- Можно фильтровать "только кросс-модульные"

### 4.3 Combined Mode (Комбинированный)

**Цель:** Обзор всего проекта

**Настройки:**
- Все типы связей
- Smart-clustering / агрегирование при большом объёме
- Layout: гибридный (layered для иерархии + force для кросс-связей)

**UX:**
- При >500 нодах — агрегация в супер-узлы
- Level-of-detail: zoom in → развернуть детали

### 4.4 Page / POM Mode (Page Object Model)

**Цель:** Быстрый просмотр POM без нагромождения глобального графа

**Настройки:**
- Показать только `page_element` связи
- Layout: древовидный (tree layout)
- Отдельная вкладка/инсет

**UX:**
```
Page: Login
  ├─ Element: Email input
  ├─ Element: Password input
  ├─ Element: Submit button
  └─ Element: Forgot password link
```

---

## 5. Фильтрация и Highlight (обязательные)

### 5.1 Фильтры по связям

**Toolbar фильтров:**
- ☑️ Hierarchy (иерархия)
- ☑️ Functional (функциональные N:M)
- ☑️ Service Dependency (зависимости от сервисов)
- ☑️ Page → Element (POM)
- ☑️ Test Coverage (покрытие тестами)
- ☑️ Bug Links (связи с багами)
- ☑️ Documentation (документация)

**Действия:**
- Включить/выключить показ каждого типа
- Сохранить пресет фильтра ("Только архитектура", "Feature Map", "POM")

### 5.2 Edge-centric фильтры

**Специальные фильтры:**
- "Показать только кросс-модули" (edges connecting nodes разных Module)
- "Показать только связи из/в элемент X"
- "Показать путь от A до B"

### 5.3 Highlight Path

**Функция:**
1. Выбрать два узла (Start + End)
2. Подсветить все пути между ними
3. Показать типы рёбер на каждом шаге:
   ```
   Feature A —[functional]→ Service B —[hierarchy]→ Module C
   ```

### 5.4 Сохранение пресетов

**Пользовательские виды:**
- "Только зависимости сервисов"
- "Нисходящая иерархия + функциональные связи"
- "POM для страницы X"
- "Критичные элементы с покрытием"

---

## 6. Поведение при взаимодействиях

### 6.1 Hover над связью (Edge Hover)

**Действия:**
- Подсветить edge (увеличить толщину × 2)
- Показать tooltip с metadata
- Затенить все остальные edges

### 6.2 Click по связи (Edge Click)

**Действия:**
- Открыть боковую панель "Информация о связи"
- Показать:
  - Тип, источник, дата создания, автор
  - Комментарий (редактируемый)
  - Вес/важность (редактируемый)
  - Кнопки: "Удалить связь", "Экспорт связи"

### 6.3 Right-click по связи

**Контекстное меню:**
- "Показать только этот тип связей"
- "Скрыть все связи этого типа"
- "Экспорт подграфа по этой связи"
- "Добавить комментарий"

### 6.4 Hover над нодой (Node Hover)

**Действия:**
- Подсветить node (увеличить размер × 1.2)
- Подсветить все инцидентные edges (разным цветом по типу)
- Показать tooltip:
  ```
  Feature: User Login
  Type: Feature
  Critical: ✅
  Focus: 🎯
  QA: John Doe
  Dev: Jane Smith
  Test Coverage: 85%
  Links: 5 functional, 2 services, 3 tests
  ```

### 6.5 Click по ноде (Node Click)

**Действия:**
- Центрирование на ноде
- Подсветка соседей
- Показать боковую панель "Информация об элементе":
  - Все поля элемента
  - Вкладка "Связи" со списком всех edges (с типами и источником)

### 6.6 Double-click по ноде

**Действия:**
- Переход в редактор элемента (открыть диалог ItemEditor)

---

## 7. Визуальные подсказки для быстрого чтения

### 7.1 Легенда (всегда доступна)

**Расположение:** плавающая панель или в toolbar

**Содержимое:**
- Цвета нод по типам (Module, Epic, Feature, etc.)
- Стили рёбер по типам (hierarchy, functional, etc.)
- Размеры и бейджи (критичность, фокус, покрытие)

### 7.2 Edge labels (опционально)

**Короткие метки на рёбрах:**
- `uses`, `affects`, `implemented_by`, `covers`, `depends_on`

### 7.3 Color strip / mini-key

**Показывает:**
- Какие типы связей сейчас включены
- Цветовая полоса с активными фильтрами

### 7.4 Edge bundling

**Для уменьшения визуального шума:**
- При большом числе перекрёстных связей — группировать рёбра в пучки

---

## 8. UX-флоу для ключевых задач

### Flow A: "Найти все сервисы, от которых зависит Feature X"

**Шаги:**
1. Пользователь ищет Feature X → фокус на ноде
2. Применяет фильтр `service_dependency` (включить) и `hierarchy` (выключить)
3. Граф показывает все сервисы, с которыми Feature X связана
4. Толщина рёбер = степень зависимости (если задано)
5. Hover показывает source (Zoho/import), возможные баги/доки в метаданных
6. Экспорт результата в JSON/CSV

### Flow B: "Понять, какие Stories задействуют Page Y (и элементы)"

**Шаги:**
1. Включить `page_element` и `functional` связи; опционально включить `hierarchy`
2. Фокус на Page Y → разворачиваются связанные Elements и Stories
3. Path highlight от Story → Element показывает цепочку:
   ```
   Story —[functional]→ Feature —[uses]→ Page —[contains]→ Element
   ```

### Flow C: "Показать кросс-модуль влияние"

**Шаги:**
1. Включить фильтр "edges connecting different Modules"
2. Граф сгруппирует узлы по Module (compound nodes)
3. Покажет межмодульные рёбра
4. Юзер видит узлы/Services, которые создают наибольшую сетевую "нагрузку" (degree centrality)

---

## 9. Технические требования

### 9.1 Модель данных

**Таблица `functional_item_relations` должна содержать:**

```sql
CREATE TABLE functional_item_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,           -- FK → functional_items.id
    target_id INTEGER NOT NULL,           -- FK → functional_items.id
    type VARCHAR(50) NOT NULL,            -- Enum: hierarchy, functional, page_element, service_dependency, etc.
    directed BOOLEAN DEFAULT TRUE,        -- Направленная или нет
    weight REAL DEFAULT 1.0,              -- Вес/важность
    metadata TEXT,                        -- JSON: origin, notes, created_by, created_at, provenance
    active BOOLEAN DEFAULT TRUE,          -- Активна ли связь
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_id) REFERENCES functional_items(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES functional_items(id) ON DELETE CASCADE,
    
    UNIQUE(source_id, target_id, type)    -- Одна связь одного типа между двумя элементами
);

-- Индексы для быстрых выборок
CREATE INDEX idx_relations_source ON functional_item_relations(source_id);
CREATE INDEX idx_relations_target ON functional_item_relations(target_id);
CREATE INDEX idx_relations_type ON functional_item_relations(type);
CREATE INDEX idx_relations_active ON functional_item_relations(active);
```

**Важно:** Миграция `parent_id`:
- При старте приложения: если есть `parent_id`, автоматически создавать `hierarchy` relation

### 9.2 Сервисная логика

**При импорте/синхронизации:**
- Создавать relations с правильным `type` и `provenance`
- Пример: импорт из Zoho → `origin="zoho"`, `created_at=now()`

**При ручном создании:**
- UI должен предлагать выбор типа связи
- Валидация: нельзя создать дублирующую связь

### 9.3 Рендеринг и интерактивность

**Текущий стек:**
- NetworkX + Matplotlib — подходит для базовой визуализации
- ⚠️ **Проблема:** недостаточно интерактивности для требуемых функций

**Рекомендация:**
- Для small graphs (≤300 узлов): Matplotlib
- Для interactive mode: **webview + Cytoscape.js / vis.js / sigma.js**
  - Преимущества: полная интерактивность, edge hover/click, плавные анимации
  - Интеграция: PyQt6 QWebEngineView

**Гибридный подход:**
```python
if len(nodes) < 300:
    use_matplotlib()  # Быстро, но статично
else:
    use_webview_cytoscape()  # Медленнее старт, но интерактивно
```

### 9.4 Layout алгоритмы

**Поддержать гибридные layout:**

| Режим | Layout | Библиотека |
|-------|--------|-----------|
| Hierarchy | Layered (Sugiyama) | NetworkX `multipartite_layout` |
| Dependency | Force-directed | NetworkX `spring_layout` с constraints |
| Combined | Hybrid | Layered для hierarchy + force для кросс-связей |
| POM | Tree | NetworkX `tree_layout` |

**Constraints:**
- Nodes из одного Module держать ближе друг к другу
- Использовать `pos` hints для устойчивости layout

### 9.5 Производительность

**Цель:** Интерактивность для 500–2000 узлов с 2–5k рёбрами

**Методы:**
1. **Кэширование позиций** (сохранять `pos` в БД или файл)
2. **Lazy-load** (загружать граф по частям при zoom/pan)
3. **Level-of-detail** (агрегация в супер-узлы при zoom out)
4. **Серверная предагрегация** (предрасчёт метрик и кластеров)
5. **GPU ускорение** (если WebGL через vis.js/cytoscape.js)

---

## 10. Мини-спецификация задач (TODO для разработки)

### 🔥 Критично (обязательно):

1. ✅ **Миграция модели `functional_item_relations`**
   - Добавить поля: `type`, `directed`, `weight`, `metadata`, `active`
   - Создать индексы
   - Миграция `parent_id` → `hierarchy` relations

2. ✅ **UI: Фильтрация по типу связей**
   - Чекбоксы для каждого типа связи
   - Режимы просмотра: Hierarchy / Dependency / Combined / POM

3. ✅ **Edge hover и edge click**
   - Показывать metadata в tooltip
   - Боковая панель для редактирования связи

4. ✅ **Легенда и экспорт**
   - Легенда типов связей и нод
   - Экспорт подграфов по типам связей

5. ✅ **Цветовое кодирование**
   - Рёбра по типу (цвет + стиль линии)
   - Ноды по типу элемента

### 📐 Важно (высокий приоритет):

6. ⚠️ **Рассмотреть webview + Cytoscape.js**
   - Для интерактивных режимов (>300 нод)
   - Интеграция через QWebEngineView

7. ⚠️ **Hybrid layouts**
   - Layered для иерархии
   - Force-directed для зависимостей
   - Constraints для группировки по модулям

### 🎯 Желательно (средний приоритет):

8. 📊 **Тестовые сценарии (QA)**
   - Случаи с мультипальными типами связей
   - Кросс-модульные рёбра
   - Миграция parent→relations

9. 🎨 **UX-фишки**
   - "Почему связаны?" — кнопка для показа всех причин
   - Индикация provenance (Zoho / CSV / ручной ввод)
   - Сохранение/восстановление видов (presets)
   - Кнопка "свернуть page-elements"

---

## 11. Этапы реализации (Roadmap)

### Этап 1: Модель и миграция (1-2 дня)
- [ ] Обновить модель `functional_item_relations`
- [ ] Миграция `parent_id` → `hierarchy` relations
- [ ] Тесты миграции

### Этап 2: Базовая визуализация (2-3 дня)
- [ ] Цветовое кодирование рёбер по типу
- [ ] Фильтры по типам связей
- [ ] Режим Hierarchy Mode (layered layout)

### Этап 3: Интерактивность (3-4 дня)
- [ ] Edge hover/click с metadata
- [ ] Node hover/click с боковой панелью
- [ ] Легенда и tooltips

### Этап 4: Дополнительные режимы (2-3 дня)
- [ ] Dependency Mode (force-directed)
- [ ] POM Mode (tree layout)
- [ ] Combined Mode (hybrid)

### Этап 5: Продвинутые функции (3-5 дней)
- [ ] Path highlight
- [ ] Edge-centric фильтры
- [ ] Сохранение пресетов
- [ ] Экспорт подграфов

### Этап 6: Оптимизация (2-3 дня)
- [ ] Кэширование позиций
- [ ] Lazy-load для больших графов
- [ ] Рассмотреть webview + Cytoscape.js

---

## 12. Критерии приёмки (Definition of Done)

### Минимум (MVP):
- ✅ Граф отображает все типы связей с правильным визуальным кодированием
- ✅ Фильтрация по типам связей работает
- ✅ Hover над связью показывает metadata
- ✅ Click по ноде переходит в редактор
- ✅ Режим Hierarchy Mode работает корректно
- ✅ Легенда доступна и понятна

### Полная реализация:
- ✅ Все 4 режима работают (Hierarchy / Dependency / Combined / POM)
- ✅ Edge click открывает панель редактирования
- ✅ Path highlight между нодами
- ✅ Сохранение/загрузка пресетов
- ✅ Экспорт подграфов
- ✅ Производительность: 500+ нод без лагов

---

## 13. Примеры использования

### Пример 1: QA хочет понять покрытие Feature X

**Действия:**
1. Открыть граф
2. Найти Feature X (поиск или из таблицы)
3. Включить фильтр `test_coverage` (показать только связи с тестами)
4. Граф показывает:
   - Связанные тест-кейсы (зелёные рёбра)
   - Покрытие в % (tooltip)
   - Автотесты (automation_status)

### Пример 2: Архитектор хочет увидеть зависимости сервисов

**Действия:**
1. Открыть граф
2. Переключиться в Dependency Mode
3. Включить фильтр `service_dependency`
4. Граф показывает:
   - Все сервисы (фиолетовые ноды)
   - Зависимости между фичами и сервисами
   - Кросс-модульные связи (если включить фильтр)

### Пример 3: Тестировщик хочет проверить POM для страницы Login

**Действия:**
1. Открыть граф
2. Переключиться в POM Mode
3. Выбрать "Start from: Page Login"
4. Граф показывает:
   - Page Login (корень)
   - Все Elements (дочерние ноды)
   - Древовидная структура

---

**Документ готов для передачи в разработку.**  
**Приоритет: КРИТИЧНЫЙ — граф является центральной фичей VoluptAS.**
