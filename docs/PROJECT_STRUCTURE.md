# Принципы организации проекта VoluptAS

**Версия:** 1.0  
**Дата:** 2026-02-19  
**Статус:** Требует утверждения

---

## 🎯 Проблема

**Текущее состояние (хаос):**

1. **Дублирование credentials:**
   - `credentials/` (активные)
   - `data/credentials/` (примеры)
   - `src/integrations/zoho/config_zoho.env` (устаревшее)

2. **Мусор в корне:**
   - 5 setup-файлов (setup.bat, setup.ps1, SETUP.md, start_voluptas.bat, bootstrap.ps1)
   - 3 документа по установке (QUICKSTART.md, SETUP.md, README.md с дублированием)

3. **Неясная структура docs/:**
   - CHANGELOG_2025-01-20.md (устарел)
   - UPDATE_2025-01-21.md (устарел)
   - UPDATE_2025-10-21_Dynamic_Edit_Dialog_Improvements.md (устарел)
   - MIGRATION_CONCEPT.md (актуально?)
   - CONCEPT_Multi_Project_Support.md (актуально?)

4. **Пустые папки:**
   - `templates/` — пусто
   - `data/db/` — пусто
   - `data/export/` — пусто

5. **Старые файлы:**
   - `voluptas.db.old` — бэкап БД
   - `__pycache__/` — кэш Python
   - `.venv/` и `venv/` — два виртуальных окружения

6. **Неясное назначение:**
   - `reports/allure-report/` — тестовые отчёты
   - `data/config/` — 3 файла (непонятно какие активные)
   - `data/projects/default/` — структура проектов

---

## 📐 Принципы организации (Best Practices)

### Принцип 1: Единое хранилище credentials

**Правило:** Все credentials хранятся в ОДНОЙ папке.

```
credentials/
├── .gitignore              # Защита (НЕ коммитить!)
├── README.md               # Инструкции (можно коммитить)
├── zoho.env                # Активные Zoho credentials
├── google_credentials.json # Активные Google credentials
└── qase.env                # Активные Qase credentials
```

**Что делать с дублями:**
- `data/credentials/*.example` → переместить в `credentials/templates/`
- `src/integrations/zoho/config_zoho.env` → удалить (устарело)

---

### Принцип 2: Чистота корня

**Правило:** В корне только критичные файлы.

**Допустимо:**
```
VoluptAS/
├── README.md               # Главная документация
├── AGENTS.md               # AI-контракт
├── CONTINUITY.md           # Журнал сессии
├── requirements.txt        # Зависимости
├── main.py                 # Точка входа
├── .gitignore              # Игноры
├── .cursorrules            # AI context
├── setup.bat               # Быстрая установка
└── start_voluptas.bat      # Быстрый запуск
```

**Переместить:**
- `SETUP.md` → `docs/SETUP.md`
- `QUICKSTART.md` → `docs/QUICKSTART.md`
- `setup.ps1` → `scripts/bootstrap.ps1` (объединить)

---

### Принцип 3: Структурированная документация

**Правило:** docs/ разделён на категории.

```
docs/
├── README_INDEX.md         # Оглавление документации
│
├── 01_Getting_Started/     # Быстрый старт
│   ├── QUICKSTART.md
│   ├── SETUP.md
│   └── INSTALLATION.md
│
├── 02_User_Guide/          # Пользователь
│   ├── USER_GUIDE_Projects.md
│   ├── USER_GUIDE_ImportExport.md
│   └── USER_GUIDE_Settings.md
│
├── 03_Developer_Guide/     # Разработчик
│   ├── ARCHITECTURE.md
│   ├── CODE_STYLE.md
│   ├── DATABASE.md
│   └── TESTING.md
│
├── 04_Technical_Spec/      # ТЗ и требования
│   ├── TZ.md               # Техническое задание
│   ├── MVP.md              # MVP критерии
│   └── E2E_TESTS.md        # E2E сценарии
│
├── 05_Roadmap/             # Планы
│   ├── ROADMAP.md
│   ├── TODO.md
│   └── CHANGELOG.md
│
└── 06_Archive/             # Архив (устаревшее)
    ├── CHANGELOG_2025-01-20.md
    ├── UPDATE_2025-01-21.md
    ├── MIGRATION_CONCEPT.md
    └── CONCEPT_Multi_Project_Support.md
```

---

### Принцип 4: Чистые данные

**Правило:** data/ хранит только актуальные данные проектов.

```
data/
├── .gitignore              # Защита БД
├── projects/               # Проекты
│   └── default/
│       ├── project.db      # БД проекта
│       ├── bdd_features/   # BDD сценарии
│       └── reports/        # Отчёты
├── import/                 # Файлы для импорта
│   └── VoluptaS_VRS_reference.xlsx
└── export/                 # Экспорты (авто)
    └── .gitkeep
```

**Удалить:**
- `voluptas.db` (корень) → переместить в `data/projects/default/project.db`
- `voluptas.db.old` → удалить
- `data/db/` → удалить (пустая)
- `data/config/` → переместить в `data/projects/default/config/`
- `data/credentials/` → переместить в `credentials/templates/`

---

### Принцип 5: Одно виртуальное окружение

**Правило:** Только одно `.venv/` в корне.

**Удалить:**
- `venv/` → если дублирует `.venv/`
- `__pycache__/` → везде (игнорируется)

---

### Принцип 6: Чистые скрипты

**Правило:** scripts/ только рабочие утилиты.

```
scripts/
├── bootstrap.ps1           # Установка окружения
├── verify.bat              # Verification loop
├── verify.sh               # Verification loop
├── restore_data.py         # Восстановление данных
├── check_portability.py    # Проверка переносимости
└── README.md               # Документация скриптов
```

**Удалить:**
- `import_csv_full.py` → если не используется
- `init_database.py` → если не используется
- `sync_hierarchy_relations.py` → если не используется
- `__pycache__/` → удалить

---

### Принцип 7: Лендер — нужен или нет?

**Вопрос:** Нужен ли `flake8`, `mypy`, `black`?

**Аргументы ЗА:**
- ✅ Автоматическая проверка кода
- ✅ Единый стиль кода
- ✅ Поиск ошибок до запуска

**Аргументы ПРОТИВ:**
- ❌ Требует установки (доп. зависимости)
- ❌ Замедляет разработку (проверка перед коммитом)
- ❌ Ложные срабатывания (особенно mypy для PyQt6)

**Решение (компромисс):**

```python
# requirements-dev.txt — отдельные dev-зависимости
flake8>=7.0.0
black==23.12.1
# mypy — опционально (отключить для PyQt6)
```

**Использование:**
```bash
# Только при коммите (pre-commit hook)
flake8 src/ --max-line-length=100

# Форматирование по требованию
black src/
```

**Рекомендация:** ✅ **НУЖЕН**, но только `flake8` + `black`. `mypy` — опционально.

---

## 📋 План чистки

### Этап 1: Credentials (критично)

1. Создать `credentials/templates/`
2. Переместить `data/credentials/*.example` → `credentials/templates/`
3. Удалить `src/integrations/zoho/config_zoho.env`
4. Обновить документацию (ссылки на credentials)

### Этап 2: Корневые файлы

1. Переместить `SETUP.md` → `docs/01_Getting_Started/SETUP.md`
2. Переместить `QUICKSTART.md` → `docs/01_Getting_Started/QUICKSTART.md`
3. Объединить `setup.ps1` + `bootstrap.ps1` → `scripts/bootstrap.ps1`
4. Удалить дубли инструкций

### Этап 3: Документация

1. Создать структуру `docs/01_*` … `docs/06_*`
2. Переместить файлы по категориям
3. Устаревшие → `docs/06_Archive/`
4. Создать `docs/README_INDEX.md`

### Этап 4: Данные

1. Переместить `voluptas.db` → `data/projects/default/project.db`
2. Удалить `voluptas.db.old`
3. Удалить `data/db/`
4. Переместить `data/config/` → `data/projects/default/config/`
5. Переместить `data/credentials/` → `credentials/templates/`

### Этап 5: Скрипты

1. Проверить используемость скриптов
2. Удалить неиспользуемые
3. Удалить `__pycache__/`
4. Создать `scripts/README.md`

### Этап 6: Виртуальные окружения

1. Сравнить `.venv/` и `venv/`
2. Удалить дубликат
3. Обновить `.gitignore`

### Этап 7: Пустые папки

1. Удалить `templates/`
2. Удалить `data/export/` (если пусто)
3. Проверить `reports/` (нужно?)

### Этап 8: .gitignore

1. Актуализировать правила
2. Добавить новые игноры
3. Удалить устаревшие

---

## 🎯 Итоговая структура

```
VoluptAS/
├── README.md                     # Главная документация
├── AGENTS.md                     # AI-контракт
├── CONTINUITY.md                 # Журнал сессии
├── requirements.txt              # Зависимости
├── requirements-dev.txt          # Dev-зависимости (flake8, black)
├── main.py                       # Точка входа
├── .gitignore                    # Игноры
├── .cursorrules                  # AI context
├── setup.bat                     # Установка (Windows)
├── start_voluptas.bat            # Запуск
│
├── docs/                         # Документация
│   ├── README_INDEX.md
│   ├── 01_Getting_Started/
│   ├── 02_User_Guide/
│   ├── 03_Developer_Guide/
│   ├── 04_Technical_Spec/
│   ├── 05_Roadmap/
│   └── 06_Archive/
│
├── credentials/                  # Credentials
│   ├── README.md
│   ├── zoho.env
│   ├── google_credentials.json
│   ├── qase.env
│   └── templates/                # Шаблоны (*.example)
│
├── data/
│   ├── .gitignore
│   ├── projects/
│   │   └── default/
│   │       ├── project.db
│   │       ├── config/
│   │       ├── bdd_features/
│   │       └── reports/
│   └── import/
│
├── scripts/
│   ├── bootstrap.ps1
│   ├── verify.bat
│   ├── verify.sh
│   ├── restore_data.py
│   ├── check_portability.py
│   └── README.md
│
├── src/                          # Исходный код
│   ├── models/
│   ├── db/
│   ├── ui/
│   ├── integrations/
│   ├── services/
│   ├── utils/
│   └── bdd/
│
└── tests/                        # Тесты
    ├── test_*.py
    └── features/                 # BDD
```

---

## ⚠️ Риски

1. **Сломанные ссылки** — обновить документацию
2. **Потеря данных** — сделать backup перед чисткой
3. **Неworking скрипты** — протестировать после перемещения
4. **Credentials** — убедиться, что активные файлы не удалены

---

## ✅ Чек-лист

- [ ] Backup данных
- [ ] Проверка используемости файлов
- [ ] Поэтапная чистка
- [ ] Тестирование после каждого этапа
- [ ] Обновление документации
- [ ] Финальная проверка

---

**Гипотезы и сомнения (не факты!):**

- 🤔 `reports/allure-report/` — возможно нужно для CI/CD?
- 🤔 `templates/` — планировалось для шаблонов отчётов?
- 🤔 `data/projects/default/bdd_features/` — используется ли BDD?
- 🤔 `scripts/import_csv_full.py` — legacy или нужен?

---

**Требует обсуждения!**
