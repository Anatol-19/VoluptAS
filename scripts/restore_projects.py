"""
Восстановление projects.json из существующих данных

Скрипт создаёт запись о проекте в data/config/projects.json
на основе существующих данных в data/projects/default/
"""

import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).resolve().parent.parent
config_dir = project_root / 'data' / 'config'
projects_dir = project_root / 'data' / 'projects'

# Проверка существования директорий
if not projects_dir.exists():
    print(f"❌ Папка проектов не найдена: {projects_dir}")
    exit(1)

# Создание директории конфигов
config_dir.mkdir(exist_ok=True, parents=True)

# Поиск существующих проектов
projects = {}

for project_dir in projects_dir.iterdir():
    if project_dir.is_dir():
        project_id = project_dir.name
        db_path = project_dir / "project.db"
        
        if db_path.exists():
            print(f"✅ Найден проект: {project_id}")
            
            projects[project_id] = {
                "id": project_id,
                "name": project_id.replace("_", " ").title(),
                "description": f"Проект из папки {project_id}",
                "database_path": str(db_path),
                "bdd_features_dir": str(project_dir / "bdd_features"),
                "reports_dir": str(project_dir / "reports"),
                "settings_profile": "production",
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "is_active": True,
                "tags": ["restored"],
                "custom_fields": {}
            }
        else:
            print(f"⚠️  Проект {project_id} не имеет БД")

if not projects:
    print("❌ Проекты не найдены!")
    exit(1)

# Сохранение projects.json
projects_file = config_dir / "projects.json"
with open(projects_file, "w", encoding="utf-8") as f:
    json.dump(projects, f, indent=2, ensure_ascii=False)

print(f"\n✅ projects.json создан: {projects_file}")
print(f"📊 Найдено проектов: {len(projects)}")

# Установка текущего проекта
current_project_file = config_dir / "current_project.txt"
current_project = list(projects.keys())[0]  # Первый проект как текущий
current_project_file.write_text(current_project, encoding="utf-8")

print(f"🎯 Текущий проект: {current_project}")
print(f"   Файл: {current_project_file}")

# Проверка profiles.json
profiles_file = config_dir / "profiles.json"
if not profiles_file.exists():
    print("\n📝 Создание profiles.json...")
    profiles = {
        "production": {
            "id": "production",
            "name": "Production",
            "description": "Основной профиль для рабочих проектов",
            "zoho_env_path": str(project_root / "credentials" / "zoho.env"),
            "google_json_path": str(project_root / "credentials" / "google_credentials.json"),
            "qase_env_path": str(project_root / "credentials" / "qase.env"),
            "created_at": datetime.now().isoformat(),
            "is_default": True
        },
        "sandbox": {
            "id": "sandbox",
            "name": "Sandbox",
            "description": "Тестовый профиль для экспериментов",
            "zoho_env_path": str(project_root / "credentials" / "sandbox" / "zoho.env"),
            "google_json_path": str(project_root / "credentials" / "sandbox" / "google_credentials.json"),
            "qase_env_path": str(project_root / "credentials" / "sandbox" / "qase.env"),
            "created_at": datetime.now().isoformat(),
            "is_default": False
        }
    }
    
    with open(profiles_file, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    
    print(f"✅ profiles.json создан: {profiles_file}")
else:
    print(f"✅ profiles.json уже существует")

print("\n" + "="*60)
print("✅ Восстановление завершено!")
print("="*60)
print(f"\nТеперь запустите приложение:")
print(f"  python main.py")
