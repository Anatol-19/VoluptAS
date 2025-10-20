# 🗺️ ROADMAP VoluptAS

План доработки проекта на основе текущего состояния и требований пользователя.

---

## 📊 Текущее состояние (v0.3.4)

### ✅ Реализовано:
- ✅ SQLite БД с автоинициализацией
- ✅ CRUD функциональных элементов через UI
- ✅ Иерархия и граф связей (базовый)
- ✅ RACI матрица (назначение ответственных)
- ✅ Фильтры и поиск
- ✅ Импорт/Экспорт CSV
- ✅ Google Sheets клиент (MATURE CODE)
- ✅ Zoho API клиент (MATURE CODE)
- ✅ Qase.io интеграция (базовая)
- ✅ OAuth Wizard для Zoho

### ⚠️ В процессе:
- 🚧 Полноценная матрица трассировок
- 🚧 Экспорт в Google Sheets (не интегрирован в UI)
- 🚧 Синхронизация с Zoho (только импорт пользователей)
- 🚧 BDD генератор feature файлов

### ❌ Не реализовано:
- ❌ Экспорт таблиц БД в Google Sheets по вкладкам
- ❌ Получение тасок текущего спринта из Zoho
- ❌ Механизм перераспределения тасок по QA
- ❌ Шаблоны отчётов для Zoho
- ❌ Хранение и синхронизация тасок Zoho в VoluptAS
- ❌ Dashboard с метриками
- ❌ Автоматические тест-планы

---

## 🎯 Приоритет 1: Интеграция Google Sheets (v0.4.0)

### Цель:
Экспорт всех таблиц БД в Google Sheets с разбивкой по вкладкам для анализа и отчётности.

### Задачи:

#### 1.1. Создать сервис экспорта БД → Google Sheets
**Файл:** `src/services/GoogleSheetsExporter.py`

```python
class GoogleSheetsExporter:
    """Экспорт данных VoluptAS в Google Sheets"""
    
    def export_all_tables(self, spreadsheet_id: str):
        """Экспорт всех таблиц БД в отдельные листы"""
        - functional_items → лист "Функционал"
        - users → лист "Сотрудники"
        - functional_item_relations → лист "Связи"
        - dictionaries → лист "Справочники"
    
    def export_coverage_matrix(self, spreadsheet_id: str):
        """Матрица покрытия с цветовым кодированием"""
        - Строки: функциональные элементы
        - Колонки: TC, автотесты, документация, баги
        - Цвета: покрыто/не покрыто/частично
    
    def export_raci_matrix(self, spreadsheet_id: str):
        """RACI матрица по функционалу"""
        - Строки: функциональные элементы
        - Колонки: сотрудники
        - Значения: R/A/C/I
    
    def export_test_plan(self, spreadsheet_id: str, filters: dict):
        """Тест-план для конкретного спринта/релиза"""
        - Фильтр по критичности, ответственным, статусу
```

**Зависимости:**
- ✅ `GoogleSheetsClient` уже есть (MATURE CODE)
- Нужно добавить форматирование (цвета, границы, формулы)

#### 1.2. Интеграция в UI
**Файл:** `src/ui/dialogs/google_export_dialog.py`

- Диалог выбора:
  - Spreadsheet (из списка или новый)
  - Что экспортировать (таблицы, матрицы, отчёты)
  - Фильтры (по типу, критичности, ответственным)
- Прогресс-бар для больших объёмов
- Кнопка "Открыть в браузере" после экспорта

#### 1.3. Меню в main.py
```
Файл → Экспорт → Google Sheets
  ├── Все таблицы БД
  ├── Матрица покрытия
  ├── RACI матрица
  ├── Тест-план (фильтры)
  └── Пользовательский экспорт
```

---

## 🎯 Приоритет 2: Интеграция Zoho Tasks (v0.4.1)

### Цель:
Получать таски текущего спринта из Zoho Projects и распределять их по QA согласно ответственности в VoluptAS.

### Референс:
`C:\ITS_QA\ITS_Scripts\services\ZOHO\` — простая реализация для анализа.

### Архитектура:

#### 2.1. Модель данных для тасок Zoho
**Файл:** `src/models/zoho_task.py`

```python
class ZohoTask(Base):
    """Таска из Zoho Projects (синхронизация)"""
    
    __tablename__ = 'zoho_tasks'
    
    id = Column(Integer, primary_key=True)
    zoho_task_id = Column(String, unique=True, index=True)  # ID из Zoho
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Связь с функционалом VoluptAS
    functional_item_id = Column(Integer, ForeignKey('functional_items.id'))
    functional_item = relationship('FunctionalItem', back_populates='zoho_tasks')
    
    # Zoho метаданные
    status_name = Column(String)  # "Open", "In Progress", "Testing", etc.
    status_id = Column(String)
    milestone_name = Column(String)  # Спринт
    tasklist_name = Column(String)  # Таск-лист
    
    # Ответственные
    owner_id = Column(String)  # Zoho user ID
    owner_name = Column(String)
    assigned_qa_id = Column(Integer, ForeignKey('users.id'))  # Назначенный QA в VoluptAS
    assigned_qa = relationship('User')
    
    # Даты
    created_time = Column(DateTime)
    updated_time = Column(DateTime)
    closed_time = Column(DateTime)
    due_date = Column(Date)
    
    # Метаданные синхронизации
    synced_at = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(String, default='synced')  # synced, conflict, outdated
```

#### 2.2. Сервис синхронизации Zoho Tasks
**Файл:** `src/services/ZohoTaskSync.py`

```python
class ZohoTaskSync:
    """Синхронизация тасок Zoho Projects с VoluptAS"""
    
    def __init__(self, zoho_client: ZohoAPI, session: Session):
        self.zoho = zoho_client
        self.session = session
    
    def sync_current_sprint(self, sprint_name: str):
        """
        Синхронизировать таски текущего спринта
        
        1. Получить milestone_id по названию спринта
        2. Получить все таски этого milestone из Zoho
        3. Для каждой таски:
           - Сохранить/обновить в zoho_tasks
           - Попытаться связать с функционалом VoluptAS (по тегам, названию)
           - Назначить QA согласно ответственности в VoluptAS
        """
        
    def sync_task(self, zoho_task_data: dict) -> ZohoTask:
        """Синхронизировать одну таску"""
        
    def auto_assign_qa(self, task: ZohoTask):
        """
        Автоматически назначить QA на таску по логике:
        
        1. Если есть связь с functional_item → берём responsible_qa оттуда
        2. Если нет связи → ищем по тегам/keywords в названии
        3. Если не нашли → назначаем по round-robin или по нагрузке QA
        4. Если owner в Zoho = QA → оставляем как есть
        """
        
    def reassign_tasks_by_coverage(self):
        """
        Перераспределить таски по покрытию функционала
        
        Логика:
        - Для каждой таски найти связанный функционал в VoluptAS
        - Если функционал назначен на QA1, а таска на QA2 → предложить reassign
        - Учитывать текущую нагрузку QA
        """
        
    def get_sprint_report(self, sprint_name: str) -> dict:
        """
        Отчёт по спринту:
        - Всего тасок
        - По статусам
        - По QA (нагрузка)
        - Покрытие функционала
        - Таски без связи с VoluptAS
        """
```

#### 2.3. UI для управления Zoho тасками
**Файл:** `src/ui/widgets/zoho_sprint_tab.py`

```python
class ZohoSprintTab(QWidget):
    """Вкладка для работы с тасками Zoho"""
    
    # Секция 1: Выбор спринта
    - Комбобокс с доступными milestone
    - Кнопка "Синхронизировать"
    - Дата последней синхронизации
    
    # Секция 2: Таблица тасок
    Колонки:
    - Zoho Task ID (гиперссылка)
    - Название таски
    - Статус
    - Owner (Zoho)
    - Assigned QA (VoluptAS) — редактируемое
    - Функционал VoluptAS — редактируемое (автокомплит)
    - Покрытие (есть TC/автотесты?)
    - Кнопка "Reassign"
    
    # Секция 3: Статистика
    - Всего тасок: 45
    - По QA: Сергей (12), Закhar (15), Anatol (18)
    - Без покрытия: 8
    - Без связи с VoluptAS: 3
    
    # Секция 4: Действия
    - Кнопка "Авто-назначить QA" (по покрытию)
    - Кнопка "Экспорт в Google Sheets" (тест-план)
    - Кнопка "Создать feature файлы для спринта"
```

#### 2.4. Интеграция в главное меню
```
Инструменты → Zoho Integration
  ├── Синхронизировать текущий спринт
  ├── Авто-назначить QA по покрытию
  ├── Отчёт по спринту
  └── Настройки синхронизации

Вид → Вкладки
  └── 🔧 Zoho Sprint Tasks (новая вкладка)
```

---

## 🎯 Приоритет 3: Шаблоны отчётов (v0.4.2)

### Цель:
Генерировать стандартные отчёты для команды и менеджмента.

### Шаблоны:

#### 3.1. Тест-план спринта
**Формат:** Google Sheets + PDF

**Секции:**
1. Заголовок (спринт, даты, ответственные)
2. Scope (что тестируем)
   - Функционал из VoluptAS (по критичности)
   - Связанные таски Zoho
3. Test Coverage
   - Функционал → TC → Автотесты
   - Gaps (что не покрыто)
4. Распределение по QA
   - QA → Функционал → Таски
5. Test Schedule (timeline)
6. Risks & Issues

**Генерация:**
```python
from src.services import TestPlanGenerator

generator = TestPlanGenerator(session)
plan = generator.generate_sprint_plan(
    sprint_name="Sprint 45",
    include_critical=True,
    include_focus=True,
    assigned_qa=["Anatol", "Sergey", "Zakhar"]
)
plan.export_to_google_sheets(spreadsheet_id)
plan.export_to_pdf("testplan_sprint45.pdf")
```

#### 3.2. Coverage Report
Еженедельный отчёт о покрытии функционала.

#### 3.3. QA Workload Report
Нагрузка QA по функционалу и тасками.

---

## 🎯 Приоритет 4: Улучшения UX (v0.4.3)

### 4.1. Dashboard (главный экран)
- Метрики покрытия в реальном времени
- Графики (coverage trends, QA workload)
- Критичные зоны без покрытия
- Быстрый доступ к спринту

### 4.2. Улучшение графа связей
- Клик по ноде → переход к элементу
- Подсветка связанных тасок Zoho
- Легенда и фильтры

### 4.3. Inline-редактирование в таблице
- Все поля редактируются на месте
- Автосохранение
- Validation

---

## 📋 План реализации (приоритеты)

### Спринт 1 (v0.4.0) — Google Sheets Export
**Сроки:** 1-2 недели  
**Задачи:**
1. ✅ Создать `GoogleSheetsExporter` service
2. ✅ Реализовать экспорт всех таблиц БД
3. ✅ Реализовать экспорт матрицы покрытия с форматированием
4. ✅ Создать UI диалог для экспорта
5. ✅ Интегрировать в меню "Файл → Экспорт → Google Sheets"
6. ✅ Тестирование на реальных данных
7. ✅ Документация

### Спринт 2 (v0.4.1) — Zoho Tasks Integration
**Сроки:** 2-3 недели  
**Задачи:**
1. ✅ Создать модель `ZohoTask` в БД
2. ✅ Миграция БД (добавить таблицу zoho_tasks)
3. ✅ Создать сервис `ZohoTaskSync`
4. ✅ Реализовать синхронизацию тасок по milestone
5. ✅ Реализовать автоназначение QA по покрытию
6. ✅ Создать UI вкладку "Zoho Sprint Tasks"
7. ✅ Интегрировать в главное меню
8. ✅ Тестирование синхронизации
9. ✅ Документация

### Спринт 3 (v0.4.2) — Reports & Templates
**Сроки:** 1-2 недели  
**Задачи:**
1. ✅ Расширить `TestPlanGenerator` для работы с Zoho тасками
2. ✅ Шаблон тест-плана спринта
3. ✅ Coverage Report
4. ✅ QA Workload Report
5. ✅ Экспорт в PDF (опционально)
6. ✅ UI для генерации отчётов
7. ✅ Документация

### Спринт 4 (v0.4.3) — UX Improvements
**Сроки:** 1 неделя  
**Задачи:**
1. ✅ Dashboard с метриками
2. ✅ Улучшение графа связей
3. ✅ Inline-редактирование
4. ✅ Hotkeys и ускорители
5. ✅ Полировка UI

---

## 🔧 Технические детали

### Зависимости для установки
```bash
# Уже есть:
- gspread (Google Sheets)
- requests (Zoho API)
- SQLAlchemy (БД)
- PyQt6 (UI)

# Нужно добавить (опционально):
- reportlab (PDF export)
- plotly (графики для Dashboard)
```

### Структура файлов (новые)
```
src/
├── models/
│   └── zoho_task.py          # NEW: модель Zoho тасок
├── services/
│   ├── GoogleSheetsExporter.py  # NEW: экспорт в Google Sheets
│   ├── ZohoTaskSync.py          # NEW: синхронизация Zoho
│   └── TestPlanGenerator.py     # UPDATE: расширение для Zoho
├── ui/
│   ├── dialogs/
│   │   └── google_export_dialog.py  # NEW: диалог экспорта
│   └── widgets/
│       └── zoho_sprint_tab.py       # NEW: вкладка Zoho тасок
└── utils/
    ├── zoho_matcher.py       # NEW: матчинг тасок с функционалом
    └── qa_assignment.py      # NEW: логика назначения QA
```

---

## 🧪 Тестирование

### Unit-тесты
- `tests/services/test_google_sheets_exporter.py`
- `tests/services/test_zoho_task_sync.py`
- `tests/utils/test_qa_assignment.py`

### Интеграционные тесты
- Экспорт реальных данных в Google Sheets (тестовый spreadsheet)
- Синхронизация с Zoho (тестовый проект)
- End-to-end: синхронизация → назначение → экспорт

---

## 📝 Документация

### Обновить:
- `README.md` — новые возможности
- `CHANGELOG.md` — версии 0.4.x
- `SETUP.md` — настройка Google Sheets и Zoho

### Создать:
- `docs/GOOGLE_SHEETS_INTEGRATION.md` — руководство по экспорту
- `docs/ZOHO_INTEGRATION.md` — руководство по синхронизации
- `docs/REPORTS.md` — шаблоны и генерация отчётов

---

## 🎯 Метрики успеха

### v0.4.0 (Google Sheets)
- ✅ Экспорт всех таблиц БД за < 30 сек
- ✅ Корректное форматирование (цвета, границы)
- ✅ Матрица покрытия актуализируется в 1 клик

### v0.4.1 (Zoho Tasks)
- ✅ Синхронизация спринта (50 тасок) за < 1 мин
- ✅ Автоназначение QA с точностью > 80%
- ✅ Таски связываются с функционалом автоматически > 70%

### v0.4.2 (Reports)
- ✅ Генерация тест-плана за < 1 мин
- ✅ Отчёты соответствуют стандартам команды
- ✅ Экономия времени QA на создание отчётов > 50%

---

## 💡 Идеи для будущего (v0.5.0+)

### Автоматизация
- Авто-синхронизация по расписанию (cron-like)
- Уведомления о новых тасках / изменениях
- Интеграция с Slack/Telegram (боты)

### Расширенная аналитика
- Velocity tracking (скорость покрытия)
- Predictive analytics (прогноз по срокам)
- Burn-down charts для покрытия

### Интеграция с другими системами
- Jira (альтернатива Zoho)
- TestRail (альтернатива Qase)
- Confluence (экспорт документации)

### AI-фичи
- GPT-генерация тест-кейсов по функционалу
- Автоматическое заполнение описаний
- Умный поиск и recommendations

---

## 🚀 Начать можно с:

1. **Проверка существующих интеграций**
   - Запустить экспорт в Google Sheets (есть клиент, нужен UI)
   - Протестировать Zoho API клиент (забрать таски)

2. **Референс из ITS_Scripts**
   - Изучить `portal_data.py` — как хранятся статусы и пользователи
   - Адаптировать логику для VoluptAS

3. **Первый прототип (MVP)**
   - Экспорт таблицы functional_items в Google Sheets
   - Синхронизация 1 спринта из Zoho
   - Простейшее назначение QA вручную через UI

**Выбирай с чего начнём!** 🎯
