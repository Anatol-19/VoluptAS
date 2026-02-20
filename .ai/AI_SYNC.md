# 🔄 AI AGENTS SYNCHRONIZATION

**Дата:** 2026-02-20  
**Статус:** ACTIVE  
**Версия:** 1.1

---

## 🎯 ТЕКУЩИЙ СТАТУС (State of Truth)

### ✅ ВЫПОЛНЕНО (Done)

| ID | Задача | Файлы | Статус | Дата |
|----|--------|-------|--------|------|
| **G-01** | Graph MVP — связи из атрибутов | `src/utils/graph_builder.py`, `src/ui/widgets/full_graph_tab.py` | ✅ DONE | 2026-02-20 |
| **G-02** | Graph — поддержка Relation table | `src/utils/graph_builder.py` | ✅ DONE | 2026-02-20 |
| **G-03** | Graph — improved find_parent_by_title | `src/utils/graph_builder.py` | ✅ DONE | 2026-02-20 |
| **Z-01** | Zoho Authorization Code — save/load | `src/ui/dialogs/settings_dialog.py` | ✅ DONE | 2026-02-20 |
| **P-01** | Project Deletion — backend | `src/models/project_config.py` | ✅ DONE | 2026-02-20 |
| **P-02** | Project Deletion — UI menu | `main.py` | ✅ DONE | 2026-02-20 |
| **F-01** | Filters — always filter from all items | `main.py` | ✅ DONE | 2026-02-20 |
| **D-01** | Copilot Instructions | `.github/copilot-instructions.md` | ✅ DONE | 2026-02-20 |
| **D-02** | AI Sync Documentation | `.ai/AI_SYNC.md`, `.ai/AI_WORKFLOW.md` | ✅ DONE | 2026-02-20 |

### 🔧 ИСПРАВЛЕНО (Fixed Bugs)

| Баг | Описание | Решение | Commit |
|-----|----------|---------|--------|
| **Graph не показывал связи** | Использовал только Relation table (пустая) | `build_graph_from_attributes()` из parent_id, module, epic, feature | `0becfbd` |
| **Граф только 1 уровень** | `find_parent_by_title()` не искал без префиксов | Partial match + functional_id match | `6d02e44` |
| **Фильтры из отфильтрованного** | `filter_table()` пропускал скрытые строки | Убран `if isRowHidden: continue` | `cc0bba8` |
| **Zoho Auth Code не сохранялся** | Поле было в UI, но не в zoho.env | Добавлено save/load | `1588b29` |
| **Нельзя удалить проект** | Не было метода удаления | `ProjectManager.delete_project()` + меню | `5f185cf` |

### ⏸️ В РАБОТЕ (In Progress)

| ID | Задача | Файлы | Статус | Дата |
|----|--------|-------|--------|------|
| **G-04** | Git Sync (diverged fix) | `.ai/PLANS/PLAN_002_GIT_SYNC.md` | 🟡 **IN PROGRESS** | 2026-02-20 |
| **Q-01** | Qase Integration — API client | `src/integrations/qase.py` (new) | ✅ **DONE** | 2026-02-20 |

**Исполнитель:** GitHub Copilot  
**Промт:** См. `.ai/PLANS/PLAN_002_GIT_SYNC.md`

### 📋 ПЛАН (Backlog) — COMPREHENSIVE

| Этап | ID | Задача | SP | Приоритет | Статус | Файл |
|------|----|--------|----|-----------|--------|------|
| **0** | G-04 | Git Sync (diverged fix) | 1 | 🔴 P0 | ✅ **DONE** | `.ai/PLANS/PLAN_002_GIT_SYNC.md` |
| **1** | CQ-01 | Code Quality (flake8, black) | 3 | 🔴 P1 | 🟡 **IN PROGRESS** | `.ai/PLANS/PLAN_003_CODE_QUALITY.md` |
| **2** | G-05 | Graph N:M relations | 3 | 🔴 P0 | ⏸️ BACKLOG | `.ai/PLANS/PLAN_004_GRAPH_ZOHO.md` |
| **2** | Z-02 | Zoho users sync | 1 | 🟡 P1 | ⏸️ BACKLOG | `.ai/PLANS/PLAN_004_GRAPH_ZOHO.md` |
| **2** | Z-03 | Zoho defects sync | 1 | 🟡 P1 | ⏸️ BACKLOG | `.ai/PLANS/PLAN_004_GRAPH_ZOHO.md` |
| **3** | T-01 | Comprehensive tests | 2 | 🔴 P1 | ⏸️ BACKLOG | `.ai/PLANS/PLAN_005_TESTS.md` |
| **4** | D-03 | Documentation update | 1 | 🟢 P2 | ⏸️ BACKLOG | `.ai/PLANS/PLAN_006_DOCS.md` |
| **UI** | UI-01 | PyQt-Fluent-Widgets | 1 | 🔴 P1 | ⏸️ BACKLOG | — |
| **SB** | SB-01 | Sandbox Protection | 3 | 🟡 P2 | ⏸️ BACKLOG | — |
| **SD** | SD-01 | Safe Delete (soft delete) | 5 | 🔴 P1 | ⏸️ BACKLOG | — |

**Всего:** 12 SP (Этапы 0-4) + 9 SP (UI/SB/SD) = **21 SP**

---

## 📚 ДОКУМЕНТАЦИЯ

### Планы

| Файл | Описание | Статус |
|------|----------|--------|
| `.ai/COPILOT_MASTER_PLAN.md` | Сводный план всех этапов | ✅ ACTIVE |
| `.ai/PLANS/PLAN_002_GIT_SYNC.md` | Этап 0: Git Sync | ✅ DONE |
| `.ai/PLANS/PLAN_003_CODE_QUALITY.md` | Этап 1: Code Quality | 🟡 IN PROGRESS |
| `.ai/PLANS/PLAN_004_GRAPH_ZOHO.md` | Этап 2: Graph + Zoho | ⏸️ DRAFT |
| `.ai/PLANS/PLAN_005_TESTS.md` | Этап 3: Tests | ⏸️ DRAFT |
| `.ai/PLANS/PLAN_006_DOCS.md` | Этап 4: Documentation | ⏸️ DRAFT |

### Контекст

| Файл | Назначение |
|------|------------|
| `.ai/CONTINUITY.md` | State для Qwen Code |
| `.github/copilot-instructions.md` | Контекст для GitHub Copilot |
| `.ai/AI_WORKFLOW.md` | Process: Plan → Execute |
| `.ai/HANDOFF_TO_COPILOT.md` | Handoff документ |

---

## 🤖 AI WORKFLOW (NEW)

**Режим:** Qwen (Plan) → Copilot (Execute)

**Файлы:**
- `.ai/AI_WORKFLOW.md` — описание процесса
- `.ai/PLANS/` — планы задач
- `.ai/PLANS/PLAN_001_QASE_INTEGRATION.md` — первый план

**Процесс:**
1. Qwen создаёт план → User утверждает
2. Copilot реализует в IDE
3. Qwen тестирует + документит
4. Git commit

**Следующий план:** PLAN_001: Qase Integration (ждёт "Погнали")

---

## 📚 ДОКУМЕНТАЦИЯ (Single Source of Truth)

### Основные файлы

| Файл | Назначение | Актуальность |
|------|------------|--------------|
| `.ai/CONTINUITY.md` | State для Qwen Code | ✅ ACTIVE |
| `.ai/AGENTS.md` | Контракт для AI агентов | ✅ ACTIVE |
| `.github/copilot-instructions.md` | Контекст для GitHub Copilot | ✅ ACTIVE |
| `docs/DEV_PLAN_v0.5.md` | План разработки | ✅ UPDATED 2026-02-20 |
| `docs/INTERFACE_GUIDE.md` | Гид по интерфейсу | ⚠️ NEEDS UPDATE |
| `README.md` | Общая документация | ⚠️ NEEDS UPDATE |

### Ключевые изменения (v0.4)

**Graph:**
- `src/utils/graph_builder.py` — построение из атрибутов + Relation table
- `src/ui/widgets/full_graph_tab.py` — загрузка связей
- Цвета: Module=синий, Epic=зелёный, Feature=оранжевый
- Стрелки: parent-of (белые), module-of (синие), epic-of (зелёные), feature-of (оранжевые)

**Project Deletion:**
- `src/models/project_config.py` — `delete_project()` метод
- `main.py` — меню "🗂️ Проект → 🗑️ Удалить проект..."
- Защита: нельзя удалить последний/текущий проект

**Zoho:**
- `src/ui/dialogs/settings_dialog.py` — save/load `ZOHO_AUTHORIZATION_CODE`
- Файл: `credentials/zoho.env`

**Filters:**
- `main.py` — `filter_table()` фильтрует из ВСЕХ элементов

---

## 🤖 КАК ИСПОЛЬЗОВАТЬ ОБА AI

### GitHub Copilot vs Qwen Code

| Аспект | GitHub Copilot | Qwen Code (CLI) |
|--------|----------------|-----------------|
| **Режим** | Автодополнение в редакторе | Чат + выполнение кода |
| **Контекст** | `.github/copilot-instructions.md` | `.ai/` директория |
| **Сильная сторона** | Быстрые правки, генерация кода | Сложные задачи, рефакторинг |
| **Язык** | Английский | Русский + Английский |
| **Доступ к ФС** | ❌ Нет | ✅ Да (чтение/запись) |
| **Тестирование** | ❌ Нет | ✅ Да (запуск команд) |

### 🎯 Эффективное использование

**1. Разделение задач:**

```
GitHub Copilot:
├── Автодополнение кода (в редакторе)
├── Генерация boilerplate
├── Быстрые правки (1-5 строк)
└── Рефакторинг функций

Qwen Code:
├── Сложные задачи (10+ файлов)
├── Рефакторинг архитектуры
├── Тестирование (запуск команд)
├── Работа с ФС (чтение/запись)
└── Документирование
```

**2. Синхронизация контекста:**

```bash
# Перед началом сессии:
1. Прочитать .ai/CONTINUITY.md (Qwen)
2. Прочитать .github/copilot-instructions.md (Copilot)
3. Обновить State.Done после задачи
```

**3. Обновление документации:**

```
После каждой задачи:
1. Qwen: Обновить .ai/CONTINUITY.md → State.Done
2. Qwen: Сделать git commit
3. Copilot: Может проверить .github/copilot-instructions.md
```

---

## 🔄 СИНХРОНИЗАЦИЯ МЕЖДУ AI

### Проблема

**GitHub Copilot говорит о других багах** потому что:
1. Разные файлы контекста (`.github/` vs `.ai/`)
2. Разная частота обновления
3. Нет автоматического синка

### Решение

**Единый источник правды:** `.ai/CONTINUITY.md`

**Правила:**
1. **Qwen Code** обновляет `.ai/CONTINUITY.md` после каждой задачи
2. **GitHub Copilot** читает `.github/copilot-instructions.md` (статичный)
3. **Пользователь** синхронизирует при необходимости

**Команда для синка:**
```bash
# После завершения задачи Qwen:
git add .ai/CONTINUITY.md
git commit -m "docs: Update CONTINUITY.md — [task name] done"
```

---

## 📝 ШАБЛОН ОБНОВЛЕНИЯ CONTINUITY.md

```markdown
## [DATE] — [TASK NAME]

### Done
- [x] Task description
- Files changed: `file1.py`, `file2.py`
- Commit: `abc1234`

### Next
- [ ] Next task
- Blocked by: none
```

---

## 🎯 CHECKLIST ПЕРЕД НАЧАЛОМ СЕССИИ

**Qwen Code:**
- [ ] Прочитать `.ai/AGENTS.md` (контракт)
- [ ] Прочитать `.ai/CONTINUITY.md` (State)
- [ ] Проверить `.ai/MEMORY_BANK.md` (project knowledge)
- [ ] Обновить State.Now перед задачей
- [ ] Обновить State.Done после задачи

**GitHub Copilot:**
- [ ] Открыть `.github/copilot-instructions.md`
- [ ] Держать открытыми relevant файлы
- [ ] Использовать комментарии для контекста

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

**Ближайшие задачи (Спринт 2):**

1. **UI Polish** (3 SP)
   - Установить `PyQt-Fluent-Widgets`
   - Установить `qdarkstyle`
   - Применить к кнопкам и меню

2. **Sandbox Protection** (3 SP)
   - Флаг `is_sandbox = True`
   - Нельзя удалить
   - Кнопка "Reset Sandbox"

3. **Safe Delete** (5 SP)
   - Soft delete (`is_deleted` flag)
   - Trash bin (восстановление)
   - Hard delete (полное стирание)

---

**Последнее обновление:** 2026-02-20  
**Следующее обновление:** После каждой задачи  
**Ответственный:** Qwen Code
