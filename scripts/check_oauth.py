"""
Проверка и настройка OAuth credentials

Запуск:
    python scripts/check_oauth.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

print("="*60)
print("  VoluptAS — Проверка OAuth Credentials")
print("="*60)
print()

# Проверка Google credentials
print("[1/2] Google Sheets credentials...")
google_file = project_root / "credentials" / "google_credentials.json"

if not google_file.exists():
    print("  ❌ Файл не найден: credentials/google_credentials.json")
    print()
    print("  Как получить:")
    print("  1. https://console.cloud.google.com/")
    print("  2. Создать Service Account")
    print("  3. Скачать JSON ключ")
    print("  4. Сохранить как credentials/google_credentials.json")
else:
    import json
    try:
        with open(google_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'client_email' in data and 'private_key' in data:
            print(f"  ✅ Файл найден и корректен")
            print(f"     Client Email: {data['client_email']}")
        else:
            print(f"  ⚠️  Файл найден, но не содержит нужных полей")
    except json.JSONDecodeError:
        print(f"  ❌ Файл повреждён (неверный JSON)")

print()

# Проверка Zoho credentials
print("[2/2] Zoho Projects credentials...")
zoho_file = project_root / "credentials" / "zoho.env"

if not zoho_file.exists():
    print("  ❌ Файл не найден: credentials/zoho.env")
else:
    from dotenv import dotenv_values
    creds = dotenv_values(zoho_file)
    
    required = ['ZOHO_CLIENT_ID', 'ZOHO_CLIENT_SECRET', 'ZOHO_REFRESH_TOKEN']
    missing = [k for k in required if k not in creds or not creds[k]]
    
    if missing:
        print(f"  ⚠️  Отсутствуют обязательные поля:")
        for k in missing:
            print(f"     - {k}")
    else:
        print(f"  ✅ Файл найден, все поля заполнены")
        print(f"     Portal: {creds.get('ZOHO_PORTAL_NAME', 'unknown')}")
        print(f"     Project ID: {creds.get('ZOHO_PROJECT_ID', 'unknown')}")
        print(f"     Region: {creds.get('ZOHO_REGION', 'com')}")
    
    print()
    print("  Для обновления токенов:")
    print("  1. Запустить приложение")
    print("  2. Файл → Настройки → Zoho")
    print("  3. Нажать '🧙 Запустить OAuth Wizard'")

print()
print("="*60)
print("  Проверка завершена")
print("="*60)
