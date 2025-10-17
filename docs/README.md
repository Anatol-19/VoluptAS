# 📚 Документация VoluptAS

**Functional Coverage Management & QA Tooling**

---

## 📖 Содержание

### 🎯 Для начала работы
- **[NEW_UI_ARCHITECTURE.md](./NEW_UI_ARCHITECTURE.md)** — Архитектура интерфейса приложения
- **[../README.md](../README.md)** — Основной README проекта

---

## 🌐 Граф связей (Graph View)

### Основная документация:
1. **[TZ_GRAPH.md](./TZ_GRAPH.md)** — Техническое задание: типы связей, визуальная семантика, UX-режимы
2. **[GRAPH_ROADMAP.md](./GRAPH_ROADMAP.md)** — Дорожная карта: поэтапный план разработки графа

### Текущая реализация:
- **Статус:** MVP готов (2025-10-16)
- **Файлы кода:**
  - `src/ui/graph_view_new.py` — Основной граф (вкладка 2)
  - `src/ui/mini_graph_widget.py` — Мини-граф в таблице

### Ключевые возможности (MVP):
- ✅ Отображение 111 элементов + 50 связей
- ✅ Фильтрация по модулям/эпикам/типам
- ✅ Интерактивная навигация (zoom, pan)
- ✅ Экспорт в PNG

### Следующие шаги:
- 🔥 **ЭТАП 1:** Типизация связей (8 типов: hierarchy, functional, POM, service, test, bug, doc, custom)
- 🌟 **ЭТАП 2:** UX-режимы (Hierarchy, Dependency, Combined, POM)
- 🎨 **ЭТАП 3:** Визуальная кодировка нод (цвет, форма, размер, бейджи)

---

## 🧑‍💻 BDD Features (Gherkin)

### Текущая реализация:
- **Статус:** Генератор интегрирован в меню (2025-10-16)
- **Файлы кода:**
  - `src/bdd/feature_generator.py` — Генератор BDD-сценариев
  - `src/ui/dialogs/bdd_manager.py` — Диалог управления BDD
  - `src/ui/widgets/bdd_tab.py` — Вкладка BDD

### Возможности:
- ✅ Генерация Gherkin-сценариев по шаблонам
- ✅ Предпросмотр и редактирование
- ✅ Экспорт в `.feature` файлы
- 🔄 **В планах:** AI-генерация (OpenAI/Claude)

---

## 📋 Матрица трассировок (Coverage Matrix)

### Типы трассировки:
- ✅ Автотесты (ручной ввод QA Lead)
- ✅ Тест-кейсы (ссылки на TestRail/Zoho)
- ✅ Баги (ID из Zoho Projects)
- ✅ Документация (ссылки на Confluence/Notion)

### Метрики:
- Процент покрытия по категориям
- Статусы: ✅ OK | ⚠️ Partial | 🔴 NG
- Фильтрация по модулям/эпикам/критичности

---

## 🏗️ Архитектура проекта

### Структура кода:
```
VoluptAS/
├── src/
│   ├── ui/
│   │   ├── graph_view_new.py       # Основной граф
│   │   ├── mini_graph_widget.py    # Мини-граф
│   │   ├── dialogs/
│   │   │   ├── bdd_manager.py      # BDD диалоги
│   │   │   └── ...
│   │   └── widgets/
│   │       ├── bdd_tab.py          # BDD вкладка
│   │       └── ...
│   ├── bdd/
│   │   └── feature_generator.py    # Генератор BDD
│   ├── database/
│   │   └── models.py               # ORM модели
│   └── main.py                     # Точка входа
├── docs/                           # Документация
│   ├── TZ_GRAPH.md                 # ТЗ графа
│   ├── GRAPH_ROADMAP.md            # Roadmap графа
│   ├── NEW_UI_ARCHITECTURE.md      # Архитектура UI
│   └── README.md                   # Этот файл
├── data/
│   └── voluptas.db                 # База данных
├── requirements.txt                # Зависимости Python
└── start_voluptas.bat              # Launcher (Windows)
```

### Технологии:
- **Backend:** Python 3.12, SQLAlchemy, SQLite
- **Frontend:** PyQt6
- **Визуализация:** matplotlib, networkx
- **BDD:** Jinja2 (шаблоны), планируется OpenAI API

---

## 🔄 История версий

| Дата       | Версия | Изменения                                             |
|------------|--------|-------------------------------------------------------|
| 2025-10-16 | 0.3.0  | Roadmap графа, интеграция ТЗ, улучшения документации  |
| 2025-10-15 | 0.2.0  | MVP графа (111 элементов, 50 связей), BDD генератор   |
| 2025-10-14 | 0.1.0  | Первоначальная структура, таблица, фильтры            |

---

## 🛠️ Для разработчиков

### Запуск проекта:
```bash
# Клонирование репозитория
git clone <repo_url>
cd VoluptAS

# Настройка окружения (автоматически)
start_voluptas.bat  # Windows
# или
./start_voluptas.sh # Linux/Mac

# Ручная установка зависимостей
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Запуск приложения
python main.py
```

### Тестирование:
```bash
# Линтер (если настроен)
ruff check .

# Тайпчекер
mypy src/
```

### Коммиты:
- Используйте конвенцию: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Пример: `feat(graph): add edge type filtering`

---

## 📞 Контакты

- **QA Lead:** [Ваше имя]
- **Репозиторий:** [Git URL]
- **Issues:** [GitHub Issues / Jira]

---

## 📝 Лицензия

[Указать лицензию проекта]

---

**Последнее обновление:** 2025-10-16
