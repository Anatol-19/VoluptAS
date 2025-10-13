# Создание репозитория на GitHub для VoluptAS

## Шаг 1: Создать репозиторий на GitHub

1. Перейти на: https://github.com/new
2. Заполнить:
   - **Repository name:** `VoluptAS`
   - **Description:** `Universal QA Functional Coverage and Traceability Tool`
   - **Visibility:** Public (или Private на ваш выбор)
   - **⚠️ НЕ СОЗДАВАТЬ:** README, .gitignore, license (уже есть в проекте)
3. Нажать **Create repository**

## Шаг 2: Подключить remote и запушить

После создания репозитория выполнить команды:

```powershell
cd C:\ITS_QA\VoluptAS
git remote add origin git@github.com:Anatol-19/VoluptAS.git
git branch -M main
git push -u origin main
```

**Примечание:** Используется SSH (личный ключ `id_ed25519_github_personal`)

## Проверка

После пуша проверить:
```powershell
git remote -v
git log --oneline
```

Репозиторий должен быть доступен на: https://github.com/Anatol-19/VoluptAS
