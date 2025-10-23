# VoluptAS TODO & Bug Tracker

**Last Updated**: 2025-10-23  
**Current Version**: 0.3.4+

---

## 🔥 Critical Bugs (P0)

### 1. ❗ Credentials Path Issues
**Status**: 🔴 In Progress  
**Priority**: P0 - Critical  
**Description**: Используются абсолютные пути к credential файлам вместо относительных  
**Impact**: Приложение не работает при переносе на другие машины  
**Steps to Reproduce**:
1. Скопировать проект на другой ПК
2. Попытаться открыть настройки Google/Zoho
3. Ошибка: путь не найден

**Solution**:
- Переписать все пути к `credentials/` как относительные от корня проекта
- Добавить helper функцию `get_credentials_path()` в config.py
- Обновить все интеграционные клиенты

**Files to Fix**:
- `src/ui/dialogs/settings_dialog.py`
- `src/integrations/google/google_sheets_client.py`
- `src/integrations/zoho/Zoho_api_client.py`
- `src/integrations/qase/qase_client.py`

---

### 2. ❗ Google Settings Save Error
**Status**: 🔴 Blocked  
**Priority**: P0 - Critical  
**Description**: При сохранении Google credentials выдаёт ошибку про отсутствие `zoho.env`  
**Error Message**:
```
[Errno 2] No such file or directory: 'C:\\Auto_Tests\\VoluptAS\\data\\credentials\\zoho.env'
```

**Root Cause**: Путаница между табами настроек - сохранение Google пытается записать в Zoho path

**Solution**:
- Исправить логику сохранения credentials по профилям
- Разделить пути для Google/Zoho/Qase
- Тестировать каждый таб отдельно

**Related**: Task #4

---

### 3. ❗ Project Creation Rollback Missing
**Status**: 🔴 New  
**Priority**: P0 - Critical  
**Description**: При ошибке создания проекта он всё равно создаётся в БД и блокирует повторное создание  
**Impact**: Нельзя пересоздать проект с тем же ID после ошибки  

**Steps to Reproduce**:
1. Создать новый проект
2. Во время создания происходит ошибка (например, с User model)
3. Проект остаётся в `projects.json` но не работает
4. Попытка создать заново - ошибка "уже существует"

**Solution**:
- Обернуть создание проекта в транзакцию
- При ошибке: откатить `projects.json`, удалить созданные папки/файлы
- Логировать детали ошибки

**Files to Fix**:
- `src/ui/dialogs/project_dialogs.py` (метод `create_project`)
- `src/services/project_manager.py`

---

### 4. ❗ Missing ZOHO_AUTHORIZATION_CODE in UI
**Status**: 🔴 New  
**Priority**: P1 - High  
**Description**: В UI настроек Zoho отсутствует поле для `ZOHO_AUTHORIZATION_CODE`  
**Impact**: Невозможно получить первичные токены через UI  

**Solution**:
- Добавить поле `ZOHO_AUTHORIZATION_CODE` в `settings_dialog.py` (Zoho tab)
- Добавить кнопку "Получить токены" для автоматического обмена code на tokens
- Инструкции по получению кода из Zoho OAuth

**Files to Fix**:
- `src/ui/dialogs/settings_dialog.py`
- `src/integrations/zoho/Zoho_api_client.py`

---

## 🐛 High Priority Bugs (P1)

### 5. No Project Deletion Functionality
**Status**: 🟡 Planned  
**Priority**: P1  
**Description**: Нет возможности удалить созданный проект через UI  
**Solution**: Добавить пункт меню "Удалить проект" с подтверждением

---

### 6. Settings Require Project Restart
**Status**: 🟡 Planned  
**Priority**: P1  
**Description**: Требуется переоткрытие проекта для применения настроек  
**Solution**: Автоматически перезагружать credentials и config после сохранения

---

## 📋 Feature Requests

### 7. Improve Import/Export UX
**Status**: 🟡 Planned  
**Priority**: P2  
**Description**: Добавить предлоги "ИЗ" и "В" к пунктам меню импорта/экспорта  
**Solution**:
- "Импорт" → "Импорт ИЗ..."
  - "Импорт ИЗ CSV"
  - "Импорт ИЗ Google Sheets"
- "Экспорт" → "Экспорт В..."
  - "Экспорт В CSV"
  - "Экспорт В Google Sheets"

---

### 8. Rename "Файл" Menu to "Проект"
**Status**: 🟡 Planned  
**Priority**: P2  
**Description**: Меню "Файл" не соответствует содержимому (там управление проектами)  
**Solution**: Переименовать в "Проект"

---

### 9. Remove Redundant "Save" Buttons
**Status**: 🟢 Review Needed  
**Priority**: P3  
**Description**: Проверить где есть избыточные кнопки "Сохранить" если изменения применяются сразу  
**Solution**: Реализовать auto-save или убрать лишние кнопки

---

### 10. Centralize Integration Settings
**Status**: 🟡 Planned  
**Priority**: P2  
**Description**: Все настройки API (Google, Zoho, Qase) и адреса таблиц синхронизации должны быть в одном месте  
**Current State**: Разбросаны по разным меню  
**Solution**: Единое окно "Настройки" с tabs для каждой интеграции

---

## 📦 Technical Debt

### 11. Cleanup Credentials Folder
**Status**: ✅ Done (2025-10-23)  
~~Удалить `.backup` файлы, унифицировать именование~~

---

### 12. Add Portability Check Script
**Status**: 🟡 Planned  
**Priority**: P2  
**Description**: Скрипт проверки готовности проекта к переносу на другие машины  
**Checks**:
- ✅ Нет абсолютных путей в коде
- ✅ `.gitignore` корректен
- ✅ Все credentials в `.gitignore`
- ✅ Документация актуальна
- ✅ Нет дублей/рудиментов

**Solution**: Создать `scripts/check_portability.py`

---

### 13. AI Development Context
**Status**: ✅ Done (2025-10-23)  
~~Создать `.cursorrules` для AI-ассистентов~~

---

## 📚 Documentation Tasks

### 14. Update ROADMAP.md
**Status**: 🟡 In Progress  
**Priority**: P2  
**Description**: Актуализировать план развития на следующие версии  

---

### 15. Write Architecture Doc
**Status**: 🟡 Planned  
**Priority**: P3  
**Description**: Документировать архитектурные решения и паттерны  
**File**: `docs/ARCHITECTURE.md`

---

## 🎯 Next Sprint (v0.3.5)

**Goal**: Стабилизация multi-project support и исправление критических багов

**Tasks**:
1. ✅ Cleanup credentials folder
2. ✅ Add `.cursorrules` for AI
3. 🔄 Fix credentials path issues (P0)
4. 🔄 Fix Google settings save error (P0)
5. 🔄 Add project rollback on error (P0)
6. 🔄 Add project deletion feature (P1)
7. 📝 Update ROADMAP.md
8. 📝 Create portability check script

**Target Date**: 2025-10-25

---

## Legend

**Status**:
- 🔴 Blocked / Critical
- 🟡 Planned / In Progress
- 🟢 Review / Testing
- ✅ Done

**Priority**:
- P0 - Critical (blocker)
- P1 - High (must have)
- P2 - Medium (should have)
- P3 - Low (nice to have)
