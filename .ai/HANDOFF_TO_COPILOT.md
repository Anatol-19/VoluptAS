# 🚀 HANDOFF TO GITHUB COPILOT

**Plan:** PLAN_001: Qase Integration  
**Status:** ✅ APPROVED — READY TO EXECUTE  
**Date:** 2026-02-20

---

## 👋 ПРИВЕТ, GITHUB COPILOT!

**Твоя задача:** Реализовать интеграцию с Qase.io для импорта/экспорта тест-кейсов.

**План:** `.ai/PLANS/PLAN_001_QASE_INTEGRATION.md`

**Промт:** См. ниже 👇

---

## 🤖 ПРОМТ ДЛЯ ТЕБЯ

```
Задача: Реализовать интеграцию с Qase.io

Контекст:
- VoluptAS — система управления функционалом (PyQt6, SQLAlchemy, SQLite)
- Qase.io — TMS для тест-кейсов (API: https://api.qase.io/v1)
- Требуется: импорт/экспорт тест-кейсов

Требования:
1. Создать src/integrations/qase.py — QaseClient класс
2. Создать src/ui/dialogs/qase_sync_dialog.py — диалог синхронизации
3. Обновить src/ui/dialogs/settings_dialog.py — вкладка Qase settings
4. Обновить main.py — меню синхронизации

API Qase:
- Авторизация: Token Auth (заголовок: Token {api_token})
- Получить проекты: GET /project
- Получить кейсы: GET /case/{project_code}?suite_id={id}
- Создать кейс: POST /case/{project_code}

Хранение токена:
- credentials/qase.env: QASE_API_TOKEN=xxx
- Не коммитить в git!

Начни с:
1. Создать qase.py — базовый клиент
2. Протестировать через python -c "from src.integrations.qase import QaseClient"
3. Создать UI диалог
4. Интегрировать в main.py

Важно:
- Обработка rate limits (100 req/min)
- Логирование всех запросов
- Кэширование ответов
```

---

## 📁 ФАЙЛЫ ДЛЯ РАБОТЫ

**Создать:**
- `src/integrations/qase.py`
- `src/ui/dialogs/qase_sync_dialog.py`
- `credentials/qase.env`

**Обновить:**
- `src/ui/dialogs/settings_dialog.py`
- `main.py`
- `requirements.txt` (если нужно)

---

## 🔄 ШАГИ

### Шаг 1: QaseClient класс

```python
# src/integrations/qase.py
import requests
from typing import List, Dict, Optional

class QaseClient:
    def __init__(self, api_token: str, project_code: str):
        self.api_token = api_token
        self.project_code = project_code
        self.base_url = "https://api.qase.io/v1"
        self.headers = {"Token": self.api_token}
    
    def get_projects(self) -> List[Dict]:
        """Получить список проектов"""
        response = requests.get(f"{self.base_url}/project", headers=self.headers)
        response.raise_for_status()
        return response.json().get("result", [])
    
    def get_suites(self, project_code: str) -> List[Dict]:
        """Получить список тест-сюит"""
        response = requests.get(
            f"{self.base_url}/suite/{project_code}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json().get("result", [])
    
    def get_cases(self, project_code: str, suite_id: Optional[int] = None) -> List[Dict]:
        """Получить тест-кейсы"""
        params = {}
        if suite_id:
            params["suite_id"] = suite_id
        response = requests.get(
            f"{self.base_url}/case/{project_code}",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json().get("result", [])
    
    def create_case(self, title: str, suite_id: Optional[int] = None, **kwargs) -> Dict:
        """Создать тест-кейс"""
        data = {"title": title}
        if suite_id:
            data["suite_id"] = suite_id
        data.update(kwargs)
        response = requests.post(
            f"{self.base_url}/case/{self.project_code}",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json().get("result", {})
```

### Шаг 2: Settings Dialog

Добавить вкладку Qase в `settings_dialog.py` (аналогично Zoho):
- API Token (password field)
- Project Code (textfield)
- Кнопка "Check Connection"

### Шаг 3: Sync Dialog

Создать `qase_sync_dialog.py`:
- Вкладка "Import" — выбор suite → импорт кейсов
- Вкладка "Export" — выбор FuncID → экспорт в Qase
- Вкладка "Mapping" — маппинг FuncID ↔ Qase Case ID

### Шаг 4: Интеграция в UI

Обновить `main.py`:
```python
# Меню:
🔧 Инструменты → 🔄 Синхронизация → 🧪 Qase.io
```

---

## ✅ КРИТЕРИИ ГОТОВНОСТИ

**Проверь перед завершением:**

- [ ] QaseClient создан и работает
- [ ] `python -c "from src.integrations.qase import QaseClient"` — без ошибок
- [ ] Settings dialog — вкладка Qase есть
- [ ] Sync dialog — импорт/экспорт работают
- [ ] main.py — меню есть
- [ ] credentials/qase.env — токен хранится
- [ ] Логирование работает

---

## 📞 ЕСЛИ ЗАСТРЯЛ

**Вопросы?** Открой `.ai/PLANS/PLAN_001_QASE_INTEGRATION.md` — там детали.

**Нужна помощь?** Qwen Code на подхвате — запустит тесты, проверит логи.

---

## 🎯 СЛЕДУЮЩИЙ ШАГ

**Начни с:** `src/integrations/qase.py` — создай базовый клиент.

**Удачи! 🚀**
