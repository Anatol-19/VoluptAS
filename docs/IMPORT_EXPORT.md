# Импорт и Экспорт данных

## 📤 Экспорт

### Google Sheets Export

**Меню:** Файл → Экспорт → Google Sheets

**Возможности:**
- Экспорт всех таблиц БД в отдельные листы
- Автоматическое создание/очистка листов
- Сохранение структуры данных

**Листы в таблице:**
1. **Функционал** - все functional_items (18 колонок)
2. **Сотрудники** - users (7 колонок) 
3. **Связи** - relations (11 колонок)

**Настройка:**
1. Настройки → Google API → вставить service_account.json
2. Расшарить таблицу на email из JSON (client_email)
3. Файл → Экспорт → Google Sheets → вставить URL

**⚠️ Важно:**
- Экспорт очищает существующие листы
- Если БД пустая - листы НЕ очищаются (safe mode)
- Credentials настраиваются ОДИН раз в Settings

---

### CSV Export

**Меню:** Файл → Экспорт → CSV

**Формат:**
```csv
FuncID,Alias,Title,Type,Module,Epic,QA,Dev,Segment,Crit,Focus
front,,,[Module]: FRONT,Module,,,,,,
```

**Колонки:**
- FuncID, Alias, Title, Type, Module, Epic
- QA, Dev (имена пользователей)
- Segment, Crit (1/0), Focus (1/0)

**Использование:**
- Быстрый backup
- Обмен данными между машинами
- Простой импорт

---

## 📥 Импорт

### Google Sheets Import

**Меню:** Файл → Импорт → Google Sheets

**Стратегия:** **Merge** (не destroy!)
- **Users**: ищет по `name`, обновляет если нашёл, создаёт если нет
- **FunctionalItems**: ищет по `functional_id`, обновляет/создаёт
- **Relations**: ищет по `source_id + target_id + type`, создаёт если нет

**Преимущества:**
- Безопасно - не удаляет существующие данные
- Обновляет изменённые поля
- Сохраняет локальные наработки

**Порядок импорта:**
1. Сначала Users (нужны для FK)
2. Затем FunctionalItems
3. В конце Relations

---

### CSV Import

**Меню:** Файл → Импорт → CSV

**Поддерживаемые форматы колонок:**
- `FuncID` или `Functional ID`
- `QA` или `Responsible (QA)`
- `Dev` или `Responsible (Dev)`
- `Crit` или `isCrit` (TRUE/1/Yes/Да)
- `Focus` или `isFocus` (TRUE/1/Yes/Да)

**Автосоздание пользователей:**
- Если пользователя нет в БД - создаётся автоматически
- Кэширование для производительности

**Статистика:**
```
📊 ИТОГИ ИМПОРТА:
  📁 Всего строк в CSV: 111
  ✅ Импортировано: 111
  👥 Создано пользователей: 13
  ⏭️  Пропущено (пустые): 0
  ⏭️  Пропущено (дубли): 0
  ❌ Ошибок: 0
```

---

## 🔄 Рабочий процесс

### Backup на другой компьютер
```
Машина 1:
1. Файл → Экспорт → Google Sheets
2. Скопировать URL таблицы

Машина 2:
1. Настройки → Google API → вставить тот же JSON
2. Файл → Импорт → Google Sheets → вставить URL
3. ✅ Все данные синхронизированы
```

### Быстрый backup через CSV
```
1. Файл → Экспорт → CSV → сохранить на Desktop
2. [При необходимости восстановить]
3. Файл → Импорт → CSV → выбрать файл с Desktop
```

---

## ⚙️ Настройка Google Sheets

### Создание Service Account

1. Перейти в [Google Cloud Console](https://console.cloud.google.com/)
2. Создать проект
3. Включить Google Sheets API
4. Создать Service Account
5. Скачать JSON ключ

### Настройка в VoluptAS

1. Настройки → Google API
2. Вставить весь JSON в текстовое поле
3. Сохранить

### Расшаривание таблицы

1. Открыть JSON файл
2. Найти `client_email`: `xxx@xxx.iam.gserviceaccount.com`
3. В Google Sheets: Настройки доступа → Добавить email → Редактор
4. ✅ Готово!

---

## 🐛 Troubleshooting

### Ошибка 403 Forbidden
**Причина:** Таблица не расшарена на service account  
**Решение:** Добавить `client_email` из JSON как редактора

### Ошибка 429 Quota Exceeded
**Причина:** Превышен лимит записей в минуту (60 requests/min)  
**Решение:** Подождать 1 минуту, экспорт продолжится

### CSV импорт - дубли
**Причина:** Элементы с таким functional_id уже есть  
**Решение:** Нормально, пропускаются автоматически

### Google импорт - нет данных
**Причина:** Листы пустые или неправильные имена  
**Решение:** Проверить имена листов: "Функционал", "Сотрудники", "Связи"

---

## 📊 Технические детали

### Google Sheets Client
- **Библиотека:** gspread + google-auth
- **Batch запись:** append_rows для производительности
- **Кэширование заголовков:** вставка 1 раз на лист
- **clear_on_open:** False для импорта, True для экспорта

### CSV Handler
- **Кодировка:** UTF-8
- **Delimiter:** `,`
- **Quoting:** MINIMAL
- **Автосоздание Users:** через get_or_create паттерн

### Merge стратегия
```python
# Пример для FunctionalItem
item = session.query(FunctionalItem).filter_by(functional_id=func_id).first()
if item:
    # UPDATE
    for key, value in data.items():
        setattr(item, key, value)
else:
    # INSERT
    item = FunctionalItem(**data)
    session.add(item)
```
