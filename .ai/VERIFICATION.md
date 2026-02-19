# VERIFICATION LOOP

> Проверка изменений в проекте VoluptAS

---

## Полный цикл (основной режим)

Любое изменение должно пройти:

| № | Шаг | Команда |
|---|-----|---------|
| 1 | **Линтер** | `flake8 src/ --count --show-source --statistics` |
| 2 | **Проверка типов** | `mypy src/ --ignore-missing-imports` |
| 3 | **Тесты** | `pytest --cov=src` |
| 4 | **Сборка** | `python -m py_compile main.py` |

**Быстрый запуск:**
```bash
scripts/verify.bat       # Windows
scripts/verify.sh        # Linux/Mac
```

### Если любой шаг падает:

1. **Остановись**, проанализируй причину
2. **Исправь** код (или вернись к плану)
3. **Запусти цикл заново**

> **Принцип:** доверяй инструментам, а не модели.

---

## Quick-fix режим

**Применяется, если изменение <5 строк кода и не меняет логику:**
- Опечатка
- Форматирование
- Комментарии
- Исправление пути

**Можно пропустить полный цикл, но:**
- ✅ Обязательно примени правило **MAKE NO MISTAKES**
- ✅ Убедись, что изменение тривиально
- ✅ Рекомендуется прогнать линтер и сборку

```bash
# Минимальная проверка для quick-fix
flake8 src/
python -m py_compile main.py
```

---

## Специфичные проверки для VoluptAS

### Database
```bash
python -c "from src.db import DatabaseManager; print('Database OK')"
```

### Integrations (если credentials доступны)
```bash
python -c "from src.integrations.zoho.Zoho_api_client import ZohoClient; print('Zoho OK')"
python -c "from src.integrations.google.google_sheets_client import GoogleSheetsClient; print('Google OK')"
python -c "from src.integrations.qase.qase_client import QaseClient; print('Qase OK')"
```

### UI Smoke Test
```bash
python main.py
# Проверить: главное окно открывается, нет ошибок в консоли
```
