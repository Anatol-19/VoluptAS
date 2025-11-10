import os
import shutil
from pathlib import Path

def setup_credentials():
    # Базовые пути
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    creds_dir = base_dir / "data" / "credentials"

    print(f"📂 Настройка креденшелов в {creds_dir}")

    # Создаем структуру директорий
    for dir_name in ["examples", "default", "vrp"]:
        dir_path = creds_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Создана директория {dir_path}")

    # Копируем существующие креденшелы в default
    for cred_file in creds_dir.glob("*.env"):
        if not cred_file.name.endswith(".example"):
            target = creds_dir / "default" / cred_file.name
            shutil.copy2(cred_file, target)
            print(f"✓ Скопирован {cred_file.name} в default/")

    for cred_file in creds_dir.glob("*.json"):
        if not cred_file.name.endswith(".example"):
            target = creds_dir / "default" / cred_file.name
            shutil.copy2(cred_file, target)
            print(f"✓ Скопирован {cred_file.name} в default/")

    # Копируем примеры
    examples_dir = creds_dir / "examples"
    for example in creds_dir.glob("*.example"):
        target = examples_dir / example.name
        shutil.copy2(example, target)
        print(f"✓ Скопирован {example.name} в examples/")

    print("\n✅ Структура креденшелов обновлена")

if __name__ == "__main__":
    setup_credentials()
