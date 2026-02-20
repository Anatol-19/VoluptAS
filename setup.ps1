<#
.SYNOPSIS
    Автоматическая настройка окружения VoluptAS

.DESCRIPTION
    Выполняет полную настройку проекта на новом ПК:
    - Проверяет Python
    - Создает виртуальное окружение
    - Устанавливает зависимости
    - Восстанавливает credentials из .backup
    - Инициализирует БД

.EXAMPLE
    .\setup.ps1
#>

param(
    [switch]$Force,  # Принудительная перезапись
    [switch]$SkipCredentials  # Пропустить восстановление credentials
)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   VoluptAS Setup Script" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Определяем корень проекта
$PROJECT_ROOT = $PSScriptRoot
Set-Location $PROJECT_ROOT

Write-Host "[1/6] Проверка Python..." -ForegroundColor Yellow

# Ищем Python
$python = $null
foreach ($cmd in @("py -3.12", "py -3.11", "py -3", "python")) {
    try {
        $version = & $cmd.Split() --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $python = $cmd
            Write-Host "  ✅ Найден: $version" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $python) {
    Write-Host "  ❌ Python 3.11+ не найден!" -ForegroundColor Red
    Write-Host "  Установите Python: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[2/6] Виртуальное окружение..." -ForegroundColor Yellow

if (Test-Path ".venv") {
    if ($Force) {
        Write-Host "  ⚠️  Удаляю старое окружение..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force ".venv"
    } else {
        Write-Host "  ℹ️  Окружение уже существует (используйте -Force для пересоздания)" -ForegroundColor Cyan
    }
}

if (-not (Test-Path ".venv")) {
    Write-Host "  🔧 Создаю .venv..." -ForegroundColor Cyan
    & $python.Split() -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Не удалось создать окружение!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✅ Окружение создано" -ForegroundColor Green
}

# Активируем окружение
$venvPip = ".\.venv\Scripts\pip.exe"

Write-Host "`n[3/6] Установка зависимостей..." -ForegroundColor Yellow
Write-Host "  Обновляю pip, setuptools, wheel..." -ForegroundColor Cyan
& $venvPip install --upgrade pip setuptools wheel --quiet

Write-Host "  🔧 Устанавливаю зависимости из requirements.txt..." -ForegroundColor Cyan
& $venvPip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Ошибка установки зависимостей!" -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ Зависимости установлены" -ForegroundColor Green

Write-Host "`n[4/6] Создание директорий..." -ForegroundColor Yellow
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "  ✅ data/ создана" -ForegroundColor Green
}
if (-not (Test-Path "credentials")) {
    New-Item -ItemType Directory -Path "credentials" | Out-Null
    Write-Host "  ✅ credentials/ создана" -ForegroundColor Green
}

Write-Host "`n[5/6] Восстановление credentials..." -ForegroundColor Yellow

# Восстановление credentials
if ($SkipCredentials) {
    Write-Host "  Пропущено (флаг -SkipCredentials)" -ForegroundColor Cyan
} else {
    $restored = 0
    if (Test-Path "credentials\zoho.env.backup") {
        if (-not (Test-Path "credentials\zoho.env") -or $Force) {
            Copy-Item "credentials\zoho.env.backup" "credentials\zoho.env" -Force
            Write-Host "  zoho.env восстановлен" -ForegroundColor Green
            $restored++
        } else {
            Write-Host "  zoho.env уже существует (пропущено)" -ForegroundColor Yellow
        }
    }
    if (Test-Path "credentials\google_credentials.json.backup") {
        if (-not (Test-Path "credentials\google_credentials.json") -or $Force) {
            Copy-Item "credentials\google_credentials.json.backup" "credentials\google_credentials.json" -Force
            Write-Host "  google_credentials.json восстановлен" -ForegroundColor Green
            $restored++
        } else {
            Write-Host "  google_credentials.json уже существует (пропущено)" -ForegroundColor Yellow
        }
    }
    if (-not (Test-Path "credentials\qase.env")) {
        Write-Host "  qase.env отсутствует (настройте через UI)" -ForegroundColor Yellow
    } else {
        Write-Host "  qase.env существует" -ForegroundColor Green
    }
    if ($restored -eq 0 -and -not (Test-Path "credentials\*.backup")) {
        Write-Host "  Нет .backup файлов для восстановления" -ForegroundColor Cyan
        Write-Host "  Настройте credentials через: Файл → Настройки" -ForegroundColor Yellow
    }
}
Write-Host "`n[6/6] Проверка портабельности..." -ForegroundColor Yellow
try {
    & python scripts/check_portability.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Portability check failed. Исправьте проблемы перед запуском." -ForegroundColor Red
        exit 1
    } else {
        Write-Host "  Portability check passed." -ForegroundColor Green
    }
} catch {
    Write-Host "  Не удалось запустить portability check." -ForegroundColor Red
}
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "   Настройка завершена!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green
Write-Host "Следующие шаги:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Запуск приложения:" -ForegroundColor Cyan
Write-Host "     .\start_voluptas.bat" -ForegroundColor White
Write-Host ""
Write-Host "  2. Настройка интеграций:" -ForegroundColor Cyan
Write-Host "     Файл → Настройки → Zoho/Google/Qase" -ForegroundColor White
Write-Host ""
Write-Host "  3. Импорт данных:" -ForegroundColor Cyan
Write-Host "     Файл → Импорт → CSV/Excel" -ForegroundColor White
Write-Host ""
if (-not $SkipCredentials -and (Test-Path "credentials\*.backup")) {
    Write-Host "  Проверьте токены в credentials/*.env" -ForegroundColor Yellow
    Write-Host "   Некоторые токены могут быть устаревшими" -ForegroundColor Gray
    Write-Host ""
}
Write-Host "Документация: README.md" -ForegroundColor Cyan
Write-Host "Известные проблемы: см. раздел 'Что реализовано' в README.md" -ForegroundColor Cyan
Write-Host ""
