"""
Portability Check Script

Проверяет готовность проекта к переносу на другие машины:
- Отсутствие абсолютных путей в коде
- Корректность .gitignore
- Credentials не в репозитории
- Наличие документации
- Отсутствие дублей и рудиментов
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


class PortabilityChecker:
    """Проверка портабельности проекта"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.warnings = []
        self.ok = []
        
    def check_all(self):
        """Запустить все проверки"""
        print("Проверка портабельности проекта...\n")

        self.check_absolute_paths()
        self.check_gitignore()
        self.check_credentials_in_git()
        self.check_documentation()
        self.check_duplicates()
        self.check_required_files()
        
        self.print_report()
        
        return len(self.issues) == 0
    
    def check_absolute_paths(self):
        """Проверка на абсолютные пути в коде"""
        print("Проверка абсолютных путей...")
        windows_path = re.compile(r'"([A-Z]:\\[^\"]+)"')
        unix_path = re.compile(r'"(/home/[^\"]+|/Users/[^\"]+)"')
        python_files = [f for f in self.project_root.rglob('*.py') if '.venv' not in str(f.resolve()) and 'site-packages' not in str(f.resolve())]
        for file in python_files:
            with open(file, encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if windows_path.search(line) or unix_path.search(line):
                        if 'example' in line or 'test' in line:
                            continue
                        self.issues.append(f"{file.relative_to(self.project_root)}:{i+1}: {line.strip()}")
        if not self.issues:
            self.ok.append("Нет абсолютных путей в коде")

    def check_gitignore(self):
        """Проверка .gitignore"""
        print("📝 Проверка .gitignore...")
        
        gitignore = self.project_root / '.gitignore'
        
        if not gitignore.exists():
            self.issues.append("❌ Отсутствует .gitignore")
            return
        
        content = gitignore.read_text(encoding='utf-8')
        
        required_patterns = [
            ('*.db', 'база данных'),
            ('*.env', 'env файлы'),
            ('.venv', 'виртуальное окружение'),
            ('__pycache__', 'кеш Python'),
            ('credentials/', 'папка credentials'),
        ]
        
        missing = []
        for pattern, desc in required_patterns:
            if pattern not in content:
                missing.append(f"{pattern} ({desc})")
        
        if missing:
            self.warnings.append(f"⚠️  В .gitignore отсутствуют паттерны:")
            for item in missing:
                self.warnings.append(f"   {item}")
        else:
            self.ok.append("✅ .gitignore корректен")
    
    def check_credentials_in_git(self):
        """Проверка что credentials не в git"""
        print("🔐 Проверка credentials...")
        
        # Проверяем tracked files
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'ls-files'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            tracked = result.stdout.split('\n')
            credential_files = [
                f for f in tracked 
                if any(x in f.lower() for x in ['.env', 'credentials', 'secret', 'token'])
                and 'example' not in f.lower()
                and 'readme' not in f.lower()
            ]
            
            if credential_files:
                self.issues.append("❌ Файлы credentials в git:")
                for f in credential_files:
                    self.issues.append(f"   {f}")
            else:
                self.ok.append("✅ Credentials не в репозитории")
                
        except Exception as e:
            self.warnings.append(f"⚠️  Не удалось проверить git: {e}")
    
    def check_documentation(self):
        """Проверка наличия документации (теперь только README.md)"""
        print("📚 Проверка документации...")
        readme = self.project_root / "README.md"
        if readme.exists():
            self.ok.append("README.md найден и актуален")
        else:
            self.warnings.append("Отсутствует README.md (основная документация)")

    def check_duplicates(self):
        """Проверка дублей и рудиментов"""
        print("🗑️  Проверка дублей...")
        
        # Проверяем backup файлы
        backup_files = list(self.project_root.rglob('*.backup'))
        backup_files += list(self.project_root.rglob('*.bak'))
        backup_files += list(self.project_root.rglob('*.old'))
        
        if backup_files:
            self.warnings.append("⚠️  Найдены backup файлы:")
            for f in backup_files[:5]:
                rel = f.relative_to(self.project_root)
                self.warnings.append(f"   {rel}")
        else:
            self.ok.append("✅ Backup файлы отсутствуют")
    
    def check_required_files(self):
        """Проверка обязательных файлов"""
        print("📦 Проверка структуры проекта...")
        
        required = [
            'requirements.txt',
            'main.py',
            'setup.bat',
            'start_voluptas.bat',
            '.cursorrules',
        ]
        
        missing = [f for f in required if not (self.project_root / f).exists()]
        
        if missing:
            self.issues.append("❌ Отсутствуют файлы:")
            for f in missing:
                self.issues.append(f"   {f}")
        else:
            self.ok.append("✅ Все обязательные файлы на месте")
    
    def print_report(self):
        print("\n" + "="*60)
        print("ОТЧЁТ О ПОРТАБЕЛЬНОСТИ")
        print("="*60 + "\n")
        if self.ok:
            print("УСПЕШНО:")
            for item in self.ok:
                print(f"  {item}")
            print()
        if self.warnings:
            print("ПРЕДУПРЕЖДЕНИЯ:")
            for item in self.warnings:
                print(f"  {item}")
            print()
        if self.issues:
            print("ПРОБЛЕМЫ:")
            for item in self.issues:
                print(f"  {item}")
            print()
        print("="*60)
        if not self.issues:
            print("Проект готов к переносу!")
        else:
            print("Исправьте проблемы перед переносом")
            exit(1)
        print("="*60)


def main():
    """Запуск проверки"""
    project_root = Path(__file__).parent.parent
    
    checker = PortabilityChecker(project_root)
    success = checker.check_all()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
