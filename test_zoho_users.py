"""
Тестовый скрипт для проверки импорта юзеров из Zoho

Запуск: python test_zoho_users.py
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.integrations.zoho.Zoho_api_client import ZohoAPI
import json


def test_zoho_users():
    """Тестирование получения пользователей из Zoho"""
    print("=" * 80)
    print("🧪 ТЕСТ: Получение пользователей из Zoho")
    print("=" * 80)
    
    try:
        # Инициализация клиента
        print("\n1️⃣ Инициализация Zoho API клиента...")
        client = ZohoAPI()
        print(f"   ✅ Клиент создан")
        print(f"   Portal: {client.portal_name}")
        print(f"   Project ID: {client.project_id}")
        print(f"   Base URL: {client.base_url}")
        
        # Получение пользователей
        print("\n2️⃣ Запрос пользователей через API...")
        users_data = client.get_users()
        
        if not users_data:
            print("   ❌ Не удалось получить пользователей")
            print("   Возможные причины:")
            print("      - Неверные токены")
            print("      - Нет прав доступа к проекту")
            print("      - Неверный project_id")
            return False
        
        print(f"   ✅ Получено пользователей: {len(users_data)}")
        
        # Анализ структуры данных
        print("\n3️⃣ Анализ структуры данных...")
        if users_data:
            first_user = users_data[0]
            print(f"   Пример пользователя (первый в списке):")
            print(f"   {json.dumps(first_user, indent=4, ensure_ascii=False)}")
            
            # Проверка обязательных полей
            required_fields = ['id', 'name', 'email']
            print(f"\n   Проверка обязательных полей: {required_fields}")
            for field in required_fields:
                exists = field in first_user
                status = "✅" if exists else "❌"
                value = first_user.get(field, 'N/A')
                print(f"      {status} {field}: {value}")
            
            # Проверка опциональных полей
            optional_fields = ['role', 'position', 'profile']
            print(f"\n   Проверка опциональных полей: {optional_fields}")
            for field in optional_fields:
                exists = field in first_user
                status = "✅" if exists else "⚠️"
                value = first_user.get(field, 'N/A')
                print(f"      {status} {field}: {value}")
        
        # Список всех пользователей
        print(f"\n4️⃣ Список всех пользователей ({len(users_data)}):")
        for idx, user in enumerate(users_data, 1):
            user_id = user.get('id', 'N/A')
            name = user.get('name', 'Unknown')
            email = user.get('email', 'N/A')
            role = user.get('role', user.get('profile', {}).get('role', 'N/A'))
            print(f"   {idx:2d}. ID: {user_id:12s} | {name:30s} | {email:35s} | {role}")
        
        print("\n" + "=" * 80)
        print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 80)
        print("❌ ТЕСТ ПРОВАЛЕН")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = test_zoho_users()
    sys.exit(0 if success else 1)
