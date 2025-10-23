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
from pathlib import Path
from typing import List, Tuple


class PortabilityChecker:
    """Проверка портабельности проекта"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.warnings = []
        self.ok = []
        
    def check_all(self):
        """Запустить все проверки"""
        print("🔍 Проверка портабельности проекта...\n")
        
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
        print("📂 Проверка абсолютных путей...")
        
        # Паттерны абсолютных путей
        windows_path = re.compile(r'["\']([A-Z]:\\\\[^"\']+)["\']')
        unix_path = re.compile(r'["\'](/home/[^"\']+|/Users/[^"\']+)["\']')
        
        python_files = list(self.project_root.rglob('*.py'))
        found_paths = []
        
        for file in python_files:
            if '.venv' in str(file) or '__pycache__' in str(file):
                continue
                
            try:
                content = file.read_text(encoding='utf-8')
                
                for match in windows_path.finditer(content):
                    path = match.group(1)
                    # Игнорируем примеры в комментариях и docstrings
                    if 'example' not in path.lower() and 'C:\\\\Auto_Tests' not in path and 'C:\\\\ITS_QA' not in path:
                        found_paths.append((file, path))
                
                for match in unix_path.finditer(content):
                    path = match.group(1)
                    if 'example' not in path.lower():
                        found_paths.append((file, path))
                        
            except Exception as e:
                self.warnings.append(f"Не удалось прочитать {file}: {e}")
        
        if found_paths:
            self.issues.append("❌ Найдены абсолютные пути:")
            for file, path in found_paths[:5]:  # Показываем первые 5
                rel_path = file.relative_to(self.project_root)
                self.issues.append(f"   {rel_path}: {path}")
            if len(found_paths) > 5:
                self.issues.append(f"   ... и ещё {len(found_paths) - 5}")
        else:
            self.ok.append("✅ Абсолютные пути не найдены")
    
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
        """Проверка документации"""
        print("📚 Проверка документации...")
        
        required_docs = [
            ('README.md', 'основной README'),
            ('CHANGELOG.md', 'история изменений'),
            ('TODO.md', 'список задач'),
        ]
        
        missing = []
        for filename, desc in required_docs:
            if not (self.project_root / filename).exists():
                missing.append(f"{filename} ({desc})")
        
        if missing:
            self.warnings.append("⚠️  Отсутствует документация:")
            for item in missing:
                self.warnings.append(f"   {item}")
        else:
            self.ok.append("✅ Основная документация на месте")
    
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
        """Печать отчёта"""
        print("\n" + "="*60)
        print("📊 ОТЧЁТ О ПОРТАБЕЛЬНОСТИ")
        print("="*60 + "\n")
        
        if self.ok:
            print("✅ УСПЕШНО:")
            for item in self.ok:
                print(f"  {item}")
            print()
        
        if self.warnings:
            print("⚠️  ПРЕДУПРЕЖДЕНИЯ:")
            for item in self.warnings:
                print(f"  {item}")
            print()
        
        if self.issues:
            print("❌ ПРОБЛЕМЫ:")
            for item in self.issues:
                print(f"  {item}")
            print()
        
        print("="*60)
        if not self.issues:
            print("✅ Проект готов к переносу!")
        else:
            print("❌ Исправьте проблемы перед переносом")
        print("="*60)


def main():
    """Запуск проверки"""
    project_root = Path(__file__).parent.parent
    
    checker = PortabilityChecker(project_root)
    success = checker.check_all()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
