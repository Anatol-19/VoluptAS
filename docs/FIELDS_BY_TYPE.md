# Карта полей по типам сущностей

## Иерархия типов
```
Module (Модуль)
  └── Epic (Эпик)
       └── Feature (Фича)
            └── Story (Сторис)

+ Page (Страница) - может быть связана с Feature/Epic
+ Element (Элемент) - может быть связан с Page/Feature
+ Service (Сервис) - может быть связан с Module/Epic
```

---

## Поля для каждого типа

### 🔷 **Module (Модуль)** - высший уровень
**Доступные поля:**
- ✅ functional_id (auto)
- ✅ title
- ✅ type = "Module"
- ✅ description
- ✅ segment
- ✅ is_crit
- ✅ is_focus
- ✅ responsible_qa (обязательно)
- ✅ responsible_dev (обязательно)
- ✅ accountable, consulted, informed
- ✅ documentation_links
- ✅ tags, aliases

**Скрытые поля:**
- ❌ module (это сам модуль)
- ❌ epic
- ❌ feature
- ❌ stories

**Связи:**
- **Дочерние:** Epic (выбор из списка эпиков этого модуля)

---

### 🔷 **Epic (Эпик)** - второй уровень
**Доступные поля:**
- ✅ functional_id (auto)
- ✅ title
- ✅ type = "Epic"
- ✅ description
- ✅ **module** (выбор из списка модулей) ← родитель
- ✅ segment
- ✅ is_crit
- ✅ is_focus
- ✅ responsible_qa (обязательно)
- ✅ responsible_dev (обязательно)
- ✅ accountable, consulted, informed
- ✅ documentation_links
- ✅ tags, aliases

**Скрытые поля:**
- ❌ epic (это сам эпик)
- ❌ feature
- ❌ stories

**Связи:**
- **Родитель:** Module
- **Дочерние:** Feature (выбор из списка фич этого эпика)
- **Связанные:** Page, Service (N:M)

---

### 🔷 **Feature (Фича)** - третий уровень
**Доступные поля:**
- ✅ functional_id (auto)
- ✅ title
- ✅ type = "Feature"
- ✅ description
- ✅ **module** (выбор из списка модулей)
- ✅ **epic** (выбор из списка эпиков этого модуля) ← родитель
- ✅ segment
- ✅ is_crit
- ✅ is_focus
- ✅ responsible_qa (обязательно)
- ✅ responsible_dev (обязательно)
- ✅ accountable, consulted, informed
- ✅ test_cases_linked
- ✅ automation_status
- ✅ documentation_links
- ✅ tags, aliases

**Скрытые поля:**
- ❌ feature (это сама фича)
- ❌ stories (отображаются как дочерние связи)

**Связи:**
- **Родитель:** Epic
- **Дочерние:** Story (список stories)
- **Связанные:** Page, Element (N:M)

---

### 🔷 **Story (Сторис)** - четвёртый уровень
**Доступные поля:**
- ✅ functional_id (auto)
- ✅ title
- ✅ type = "Story"
- ✅ description
- ✅ **module** (выбор из списка)
- ✅ **epic** (выбор из списка)
- ✅ **feature** (выбор из списка) ← родитель
- ✅ segment
- ✅ is_crit
- ✅ is_focus
- ✅ responsible_qa (обязательно)
- ✅ responsible_dev (обязательно)
- ✅ accountable, consulted, informed
- ✅ test_cases_linked
- ✅ automation_status
- ✅ documentation_links
- ✅ tags, aliases

**Связи:**
- **Родитель:** Feature
- **Связанные:** Page, Element (N:M)

---

### 🔷 **Page (Страница)** - специальный тип
**Описание:** Представляет UI страницу, может быть связана с Feature/Epic

**Доступные поля:**
- ✅ functional_id (auto)
- ✅ title
- ✅ type = "Page"
- ✅ description
- ✅ **module** (опционально)
- ✅ **epic** (опционально)
- ✅ segment = "UI" (по умолчанию)
- ✅ is_crit
- ✅ is_focus
- ✅ responsible_qa (обязательно)
- ✅ responsible_dev (обязательно)
- ✅ accountable, consulted, informed
- ✅ test_cases_linked
- ✅ automation_status
- ✅ documentation_links
- ✅ tags, aliases

**Связи:**
- **Связанные:** Feature, Epic, Element (N:M)

---

### 🔷 **Element (Элемент)** - UI компонент
**Описание:** UI элемент (кнопка, форма, модальное окно и т.д.)

**Доступные поля:**
- ✅ functional_id (auto)
- ✅ title
- ✅ type = "Element"
- ✅ description
- ✅ segment = "UI" (по умолчанию)
- ✅ is_crit
- ✅ is_focus
- ✅ responsible_qa (обязательно)
- ✅ responsible_dev (обязательно)
- ✅ accountable, consulted, informed
- ✅ test_cases_linked
- ✅ automation_status
- ✅ documentation_links
- ✅ tags, aliases

**Связи:**
- **Связанные:** Page, Feature (N:M)

---

### 🔷 **Service (Сервис)** - backend сервис
**Описание:** Backend сервис, микросервис, API

**Доступные поля:**
- ✅ functional_id (auto)
- ✅ title
- ✅ type = "Service"
- ✅ description
- ✅ **module** (опционально)
- ✅ segment = "Backend"/"API" (по умолчанию)
- ✅ is_crit
- ✅ is_focus
- ✅ responsible_qa (обязательно)
- ✅ responsible_dev (обязательно)
- ✅ accountable, consulted, informed
- ✅ test_cases_linked
- ✅ automation_status
- ✅ documentation_links
- ✅ container
- ✅ database
- ✅ tags, aliases

**Связи:**
- **Связанные:** Module, Epic, Feature (N:M)

---

## Правила отображения полей в UI

### 1. **Иерархические поля (module/epic/feature)**
- Показываются **только для выбора родителя**
- Module — не показывает ничего
- Epic — показывает module (выбор родителя)
- Feature — показывает module + epic (выбор родителя)
- Story — показывает module + epic + feature (выбор родителя)

### 2. **Связанные элементы**
- Для всех типов — секция "Связанные элементы" (N:M)
- Можно выбрать несколько элементов любого типа
- Отображается список с возможностью добавления/удаления

### 3. **Обязательные поля**
- **Всегда:** functional_id, title, type, responsible_qa, responsible_dev
- **Валидация:** нельзя сохранить без QA и Dev

### 4. **Покрытие (test_cases, automation, docs)**
- Показывается для: Feature, Story, Page, Element, Service
- НЕ показывается для: Module, Epic

---

## Добавление поля parent_id в модель

Для отслеживания иерархических связей добавим:
```python
parent_id = Column(Integer, ForeignKey('functional_items.id'), nullable=True, index=True)
parent = relationship("FunctionalItem", remote_side=[id], backref="children")
```

---

## Добавление таблицы связей (N:M)

Для связанных элементов (не иерархических):
```python
# В models/functional_item.py
related_items = Table('functional_item_relations',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('functional_items.id')),
    Column('related_item_id', Integer, ForeignKey('functional_items.id'))
)
```

---

## Автогенерация functional_id

### Правила:
- **Module:** `<module_name>` → "front", "backend"
- **Epic:** `<module>.<epic_name>` → "front.splash_page"
- **Feature:** `<module>.<epic>.<feature_name>` → "front.splash_page.cookies"
- **Story:** `<module>.<epic>.<feature>.<story_name>` → "front.splash_page.cookies.set_age"
- **Page:** `page.<page_name>` → "page.login"
- **Element:** `element.<element_name>` → "element.login_button"
- **Service:** `service.<service_name>` → "service.auth_api"

---

## Следующие шаги реализации:
1. ✅ Обновить модель FunctionalItem (добавить parent_id, related_items)
2. ✅ Создать миграцию БД
3. ✅ Обновить диалог редактирования (динамические поля по типу)
4. ✅ Создать User Manager
5. ✅ Создать редактор сущностей с фильтрами по типу
6. ✅ Добавить быстрые фильтры
