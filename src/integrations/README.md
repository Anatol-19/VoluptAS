# Integrations - MATURE CODE ⚠️

Этот модуль содержит **проверенный и стабильный код** из продакшена `ITS_Scripts`.

## 📁 Содержимое

- **`google/`** - Google Sheets API клиент (экспорт данных)
- **`zoho/`** - Zoho Projects API клиент (задачи, баги, мейлстоуны)

## 🚨 ВАЖНО

⚠️ **MATURE CODE** - изменения вносить с осторожностью!

- Код работает стабильно в продакшене
- Используется в реальных релизных процессах
- Любые изменения тестировать тщательно

## 📚 Документация

Подробная документация: [`docs/INTEGRATIONS.md`](../../docs/INTEGRATIONS.md)

## 🔐 Секреты

**НЕ КОММИТИТЬ:**
- `*.env` файлы
- `service_account*.json`
- `config_*.env`

Эти файлы уже добавлены в `.gitignore`

## 🛠️ Быстрый старт

```python
# Google Sheets
from src.integrations.google import GoogleSheetsClient

# Zoho Projects
from src.integrations.zoho import ZohoAPI, user_manager

# Test Plan Generator
from src.services import TestPlanGenerator
```

---

**Источник**: `C:\ITS_QA\ITS_Scripts\services`
**Портировано**: 2025-10-13
