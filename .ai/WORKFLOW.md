# WORKFLOW — стандартный процесс

---

## Процесс

```
1. PLAN       → составь план и получи подтверждение (.ai/PLAN_MODE.md)
2. EXECUTE    → реализуй, соблюдая .ai/MEMORY_BANK.md и MAKE NO MISTAKES
3. VERIFY     → прогоняй .ai/VERIFICATION.md. При ошибках фиксируй и повторяй
4. UPDATE     → если задача длинная, обнови CONTINUITY.md
5. COMMIT/PR  → оформляй результат
```

---

## Слэш-команды

| Команда | Описание |
|---------|----------|
| `/commit-push-pr` | Закоммитить, запушить и создать PR |
| `/explain` | Объяснить фрагмент кода |
| `/simplify` | Предложить упрощение |
| `/plan` | Создать план задачи |
| `/verify` | Запустить verification loop |
| `/snapshot` | Обновить CONTINUITY.md (snapshot) |

---

## Сценарии

### Новая фича

```
1. /plan → создать развёрнутый план (3–7 шагов)
2. EXECUTE → по шагам
3. VERIFY → полный цикл
4. UPDATE CONTINUITY → после каждого шага
5. COMMIT → с подробным сообщением
```

### Багфикс

```
1. /plan → краткий план (1–2 шага)
2. EXECUTE → исправление
3. VERIFY → quick-fix режим
4. COMMIT → type: fix
```

### Исследование / Spike

```
1. /plan → цель исследования
2. EXECUTE → сбор информации
3. UPDATE CONTINUITY → фиксация находок
4. COMMIT → опционально, type: chore
```

---

## Длинные задачи

**Если задача не укладывается в 1 сессию:**

- ✅ Обязательно использовать `CONTINUITY.md`
- ✅ Фиксировать прогресс после каждого шага
- ✅ Обновлять статус при изменении контекста
- ✅ Делать коммиты после завершения логических этапов
- ✅ Snapshot при >15 шагов / >40k токенов

---

## Git Workflow

```bash
# Создать ветку
git checkout -b feature/<name>
# или
git checkout -b fix/<name>

# Коммит
git add <файлы>
git commit -m "type: description"

# Типы коммитов:
# feat     — новая фича
# fix      — багфикс
# refactor — рефакторинг
# docs     — документация
# test     — тесты
# chore    — инфраструктура

# Пуш (только с явного разрешения!)
git push origin <branch>
```

---

## Чек-лист завершения задачи

```bash
# 1. Verification пройден
scripts/verify.bat

# 2. CONTINUITY обновлён
cat CONTINUITY.md

# 3. Изменения проверены
git status
git diff --staged

# 4. Тесты проходят
pytest --cov=src

# 5. Линтер чист
flake8 src/

# 6. Типы проходят
mypy src/
```

---

> **См. также:**
> - `.ai/PLAN_MODE.md` — планирование
> - `.ai/VERIFICATION.md` — проверка
> - `.ai/MEMORY_BANK.md` — конвенции проекта
> - `CONTINUITY.md` — память сессии
