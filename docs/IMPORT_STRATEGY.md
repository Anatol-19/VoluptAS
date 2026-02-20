# Стратегия импорта — VoluptAS

**Версия:** 1.0  
**Дата:** 2026-02-19

---

## 📋 Обзор

Этот документ описывает стратегию импорта данных в VoluptAS.

---

## 1. Уровни импорта

### MVP (Инкремент 1)

**CSV с фиксированной схемой:**
- Названия колонок строго определены
- Без UI маппинга
- Ошибки логгируются, строки пропускаются

**Формат:**
```csv
FuncID,Title,Type,Module,Epic,Feature,Segment,ResponsibleQA,ResponsibleDev,IsCrit,IsFocus,Status,Maturity,TestCases,DocsLinks
```

### v0.5 (Инкремент 2)

**Мастер маппинга:**
- UI для сопоставления колонок
- Сохранение пресетов
- Предпросмотр данных
- Валидация перед импортом

**Формат:**
- CSV (любая схема)
- Excel (XLSX)
- Google Sheets (импорт из таблицы)

---

## 2. Схема CSV (MVP)

### Обязательные колонки

| Колонка | Тип | Описание | Пример |
|---------|-----|----------|--------|
| `FuncID` | string | Уникальный ID | `MOD:FRONT` |
| `Title` | string | Название | `Frontend Module` |
| `Type` | enum | Тип элемента | `Module` |

### Опциональные колонки

| Колонка | Тип | Описание | Пример |
|---------|-----|----------|--------|
| `Module` | string | Родитель Module | `FRONT` |
| `Epic` | string | Родитель Epic | `AUTH` |
| `Feature` | string | Родитель Feature | `LOGIN` |
| `Segment` | enum | Сегмент | `UI` |
| `ResponsibleQA` | string | Ответственный QA | `Ivanov` |
| `ResponsibleDev` | string | Ответственный Dev | `Petrov` |
| `IsCrit` | boolean | Критичный | `1` или `TRUE` |
| `IsFocus` | boolean | Фокусный | `0` или `FALSE` |
| `Status` | enum | Статус | `Approved` |
| `Maturity` | enum | Зрелость | `Stable` |
| `TestCases` | string | Тест-кейсы | `TC-001, TC-002` |
| `DocsLinks` | string | Документация | `https://docs/auth` |

---

## 3. Обработка ошибок

### Уровни ошибок

| Уровень | Описание | Действие |
|---------|----------|----------|
| **Критичная** | FuncID дубликат, неверный Type | Пропуск строки, лог ERROR |
| **Предупреждение** | Ответственный не найден | Создать пользователя, лог WARN |
| **Информация** | Пустая опциональная колонка | Пропуск, лог INFO |

### Логирование

```
[INFO] Импорт CSV: файл data/import/VoluptaS_VRS_reference.xlsx
[INFO] Всего строк: 111
[WARN] Строка 5: ResponsibleQA "Smirnov" не найден → создан пользователь
[ERROR] Строка 12: FuncID "MOD:FRONT" дубликат → пропущено
[ERROR] Строка 18: Type "Modulee" неверный → пропущено
[INFO] Импортировано: 108
[INFO] Создано пользователей: 3
[INFO] Пропущено (ошибки): 2
```

---

## 4. Алгоритм импорта

### Шаг 1: Чтение файла

```python
def read_csv(file_path: Path) -> List[Dict]:
    """Чтение CSV файла в список словарей"""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)
```

### Шаг 2: Валидация схемы

```python
def validate_schema(rows: List[Dict]) -> ValidationResult:
    """Проверка наличия обязательных колонок"""
    required = {'FuncID', 'Title', 'Type'}
    columns = set(rows[0].keys()) if rows else set()
    
    missing = required - columns
    if missing:
        return ValidationResult(
            valid=False,
            errors=[f"Missing columns: {missing}"]
        )
    
    return ValidationResult(valid=True)
```

### Шаг 3: Импорт строк

```python
def import_row(row: Dict, session: Session) -> ImportResult:
    """Импорт одной строки"""
    # 1. Проверка дубликата FuncID
    existing = session.query(FunctionalItem).filter_by(
        functional_id=row['FuncID']
    ).first()
    
    if existing:
        return ImportResult(
            success=False,
            error=f"Duplicate FuncID: {row['FuncID']}"
        )
    
    # 2. Валидация Type
    valid_types = ['Module', 'Epic', 'Feature', 'Story', 'Page', 'Element', 'Service']
    if row['Type'] not in valid_types:
        return ImportResult(
            success=False,
            error=f"Invalid Type: {row['Type']}"
        )
    
    # 3. Создание элемента
    item = FunctionalItem(
        functional_id=row['FuncID'],
        title=row['Title'],
        type=row['Type'],
        status=row.get('Status', 'Draft'),
        maturity=row.get('Maturity', 'Idea'),
        # ... остальные поля
    )
    
    session.add(item)
    session.commit()
    
    return ImportResult(success=True)
```

---

## 5. Создание пользователей

### Автоматическое создание

Если пользователь не найден в справочнике:

```python
def get_or_create_user(name: str, session: Session) -> User:
    """Найти или создать пользователя"""
    user = session.query(User).filter_by(name=name).first()
    
    if not user:
        user = User(
            name=name,
            position='Unknown',
            role='Unknown',
            is_active=True,
            imported_from_csv=True  # метка для последующей модерации
        )
        session.add(user)
        session.commit()
    
    return user
```

### Пост-обработка

После импорта:
- Показать список созданных пользователей
- Предложить заполнить данные (position, role, email)
- Отметить флажком `imported_from_csv=True`

---

## 6. Примеры

### Успешный импорт

**CSV:**
```csv
FuncID,Title,Type,Module,Epic,Feature,Segment,ResponsibleQA,ResponsibleDev,IsCrit,IsFocus,Status,Maturity
MOD:FRONT,Frontend Module,Module,,,,,,Ivanov,Petrov,0,1,Approved,Stable
EPIC:AUTH,Authentication,Epic,FRONT,,,,,Ivanov,Petrov,1,1,Approved,Beta
```

**Результат:**
```
✅ Импортировано: 2
✅ Создано пользователей: 0 (Ivanov и Petrov уже есть)
```

### Импорт с ошибками

**CSV:**
```csv
FuncID,Title,Type
MOD:FRONT,Frontend,Module
MOD:FRONT,Frontend Duplicate,Module  ← дубликат
EPIC:AUTH,Auth,Epicpe  ← опечатка в Type
```

**Результат:**
```
✅ Импортировано: 1
❌ Пропущено: 2
  - Строка 2: Duplicate FuncID: MOD:FRONT
  - Строка 3: Invalid Type: Epicpe
```

---

## 7. Roadmap

| Версия | Функция | Статус |
|--------|---------|--------|
| **MVP** | CSV с фиксированной схемой | ✅ В работе |
| **v0.5** | Мастер маппинга | ⏸️ Planned |
| **v0.5** | Excel (XLSX) импорт | ⏸️ Planned |
| **v0.6** | Google Sheets импорт (двусторонний) | ⏸️ Planned |

---

**См. также:**
- `docs/TZ.md` — Техническое задание
- `docs/TECH_DECISIONS.md` — Технические решения
- `src/import/csv_importer.py` — Реализация
