# 🚀 COPILOT MASTER PLAN — Этапы 0-4

**Статус:** IN PROGRESS  
**Дата:** 2026-02-20  
**Исполнитель:** GitHub Copilot (в IDE)  
**Планировщик:** Qwen Code

---

## 📊 ОБЗОР

| Этап | Задача | SP | Статус | Файл плана |
|------|--------|----|--------|------------|
| **0** | Git Sync | 1 | ✅ DONE | `.ai/PLANS/PLAN_002_GIT_SYNC.md` |
| **1** | Code Quality | 3 | 🟡 IN PROGRESS | `.ai/PLANS/PLAN_003_CODE_QUALITY.md` |
| **2** | Graph N:M + Zoho | 5 | ⏸️ BACKLOG | `.ai/PLANS/PLAN_004_GRAPH_ZOHO.md` |
| **3** | Tests | 2 | ⏸️ BACKLOG | `.ai/PLANS/PLAN_005_TESTS.md` |
| **4** | Documentation | 1 | ⏸️ BACKLOG | `.ai/PLANS/PLAN_006_DOCS.md` |

**Всего:** 12 SP (~18 часов)

---

## 🔄 ЭТАП 0: GIT SYNC ✅

**Статус:** COMPLETED

**Команды:**
```bash
git pull --rebase origin main
git push origin main
```

**Результат:** Локальная и remote ветки синхронизированы

---

## 🧹 ЭТАП 1: CODE QUALITY 🟡

**Статус:** IN PROGRESS

**Команды:**
```bash
pip install flake8 black pylint
flake8 src/ --select=E9,F63,F7,F82 --show-source
black src/
pylint src/ --disable=all --enable=duplicate-code
tree /F /A > docs/PROJECT_TREE.txt
```

**Результат:**
- 0 критичных flake8 ошибок
- Все файлы отформатированы black
- < 10 дублей
- Структура проверена

**Коммит:** `style: Code quality fixes`

---

## 🌐 ЭТАП 2: GRAPH N:M + ZOHO ⏸️

**Статус:** BACKLOG

**Задачи:**
1. Graph: N:M связи из Relation table
2. Zoho: Синхронизация пользователей
3. Zoho: Синхронизация дефектов

**Файлы:**
- `src/utils/graph_builder.py` (update)
- `src/integrations/zoho.py` (update)
- `src/ui/dialogs/zoho_sync_dialog.py` (update)

**Коммиты:**
- `feat: Graph N:M relations`
- `feat: Zoho users sync`
- `feat: Zoho defects sync`

---

## 🧪 ЭТАП 3: TESTS ⏸️

**Статус:** BACKLOG

**Тесты:**
1. `tests/test_graph_builder.py`
2. `tests/test_qase_client.py`
3. `tests/test_zoho_sync.py`
4. `tests/test_project_deletion.py`

**Команда:**
```bash
pytest tests/ --cov=src --cov-report=html
```

**Требование:** Coverage > 80%

**Коммит:** `test: Comprehensive tests`

---

## 📝 ЭТАП 4: DOCUMENTATION ⏸️

**Статус:** BACKLOG

**Файлы:**
- `.github/copilot-instructions.md` (update)
- `docs/INTERFACE_GUIDE.md` (update)
- `README.md` (update)

**Коммит:** `docs: Update documentation`

---

## 🎯 WORKFLOW

**Copilot в IDE:**
1. Открывает этот файл
2. Читает план текущего этапа
3. Выполняет шаги
4. Делает коммит
5. Переходит к следующему этапу

**Qwen CLI:**
1. Наблюдает
2. Запускает тесты после Этапа 3
3. Проверяет линтер после Этапа 1
4. Делает push после всех этапов

---

## 📞 ЕСЛИ ВОПРОСЫ

**Открыть:**
- `.ai/PLANS/PLAN_XXX.md` — детали этапа
- `.ai/AI_SYNC.md` — текущий статус
- `.github/copilot-instructions.md` — контекст проекта

**Спросить Qwen:**
- Запустить тесты
- Проверить логи
- Сверить структуру

---

**Начинай с Этапа 1 (Этап 0 завершён)!** 🚀
