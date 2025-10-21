# VoluptAS - Быстрый запуск

## Предварительные требования

- **Python 3.11+** установлен и добавлен в PATH
- Операционная система: Windows 10/11

Проверьте Python:
```cmd
python --version
```

## Первый запуск (One-Click Setup)

### Вариант 1: Простой запуск (рекомендуется)

Просто запустите:
```cmd
setup.bat
```

Этот скрипт автоматически:
1. Проверит наличие Python
2. Создаст виртуальное окружение (.venv)
3. Установит все зависимости из requirements.txt
4. Проверит корректность установки
5. Запустит приложение

### Вариант 2: Пошаговая настройка

Если нужен больший контроль:

```cmd
# 1. Создать виртуальное окружение
python -m venv .venv

# 2. Активировать окружение
.venv\Scripts\activate.bat

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить приложение
python main.py
```

## Последующие запуски

После первоначальной настройки используйте:

```cmd
start_voluptas.bat
```

Или с активированным окружением:
```cmd
python main.py
```

## Решение проблем

### Python не найден
```
ERROR: Python not found in PATH
```
**Решение:** Установите Python 3.11+ с python.org и добавьте в PATH при установке

### Не удается создать виртуальное окружение
```
ERROR: Failed to create virtual environment
```
**Решение:** 
```cmd
# Удалите старое окружение
rd /s /q .venv

# Попробуйте снова
setup.bat
```

### ModuleNotFoundError: No module named 'PyQt6'
**Решение:** Переустановите зависимости
```cmd
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Ошибки кодировки в консоли
**Решение:** Используйте setup.bat или start_voluptas.bat (они автоматически устанавливают UTF-8)

## Структура проекта

```
VoluptAS/
├── setup.bat              # Полная установка и запуск
├── start_voluptas.bat     # Быстрый запуск
├── requirements.txt       # Зависимости Python
├── main.py               # Точка входа
├── .venv/                # Виртуальное окружение (создается автоматически)
└── scripts/
    └── bootstrap.ps1     # PowerShell скрипт настройки
```

## Дополнительная информация

- Полная документация: [README.md](README.md)
- Import/Export: [docs/IMPORT_EXPORT.md](docs/IMPORT_EXPORT.md)
- Changelog: [docs/CHANGELOG_2025-01-20.md](docs/CHANGELOG_2025-01-20.md)

## Поддержка

При возникновении проблем:
1. Проверьте, что Python 3.11+ установлен корректно
2. Удалите папку `.venv` и запустите `setup.bat` заново
3. Проверьте логи в папке `logs/`
