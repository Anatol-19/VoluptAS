"""
Migration utility - Миграция старой структуры БД в новую мультипроектную

Обрабатывает автоматическую миграцию при первом запуске
"""

import shutil
import logging
from pathlib import Path
from typing import Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MigrationManager:
    """Менеджер миграции старой структуры"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.data_dir = project_root / 'data'
        self.old_db_path = self.data_dir / 'voluptas.db'
        self.config_dir = self.data_dir / 'config'
        self.projects_dir = self.data_dir / 'projects'
    
    def needs_migration(self) -> bool:
        """
        Проверка необходимости миграции
        
        Returns:
            True если найдена старая структура и нет новой
        """
        # Есть старая БД и нет новой структуры
        has_old_db = self.old_db_path.exists()
        has_new_config = self.config_dir.exists() and (self.config_dir / 'projects.json').exists()
        
        return has_old_db and not has_new_config
    
    def perform_migration(self) -> Tuple[bool, str]:
        """
        Выполнить миграцию
        
        Returns:
            Tuple[success, message]
        """
        try:
            logger.info("🔄 Начало миграции старой структуры...")
            
            # Создаём директории
            self.config_dir.mkdir(exist_ok=True, parents=True)
            default_project_dir = self.projects_dir / 'default'
            default_project_dir.mkdir(exist_ok=True, parents=True)
            
            # Создаём поддиректории проекта
            (default_project_dir / 'bdd_features').mkdir(exist_ok=True)
            (default_project_dir / 'reports').mkdir(exist_ok=True)
            
            # Копируем старую БД в новую структуру
            new_db_path = default_project_dir / 'voluptas.db'
            
            if new_db_path.exists():
                # Создаём бэкап
                backup_path = default_project_dir / f'voluptas_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
                shutil.copy2(new_db_path, backup_path)
                logger.info(f"Создан бэкап: {backup_path}")
            
            shutil.copy2(self.old_db_path, new_db_path)
            logger.info(f"✅ БД скопирована: {self.old_db_path} → {new_db_path}")
            
            # Создаём default проект в ProjectManager
            from src.models.project_config import ProjectManager, ProjectConfig
            
            pm = ProjectManager(self.config_dir)
            
            # Проверяем, не создан ли уже default проект
            if 'default' not in pm.projects:
                default_project = ProjectConfig(
                    id='default',
                    name='Default Project',
                    description='Мигрированный проект из старой структуры',
                    database_path=new_db_path,
                    bdd_features_dir=default_project_dir / 'bdd_features',
                    reports_dir=default_project_dir / 'reports',
                    settings_profile='production',
                    created_at=datetime.now().isoformat(),
                    is_active=True,
                    tags=['migrated']
                )
                
                pm.projects['default'] = default_project
                pm.current_project_id = 'default'
                pm.save()
                
                logger.info("✅ Создан default проект")
            
            # Переименовываем старую БД в .old
            old_db_backup = self.old_db_path.with_suffix('.db.old')
            self.old_db_path.rename(old_db_backup)
            logger.info(f"✅ Старая БД переименована: {old_db_backup}")
            
            success_msg = (
                f"✅ Миграция завершена успешно!\n\n"
                f"Ваша БД перемещена в:\n{new_db_path}\n\n"
                f"Старая БД сохранена как:\n{old_db_backup}\n\n"
                f"Теперь вы можете создавать новые проекты через меню 'Файл → Новый проект'"
            )
            
            logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"❌ Ошибка миграции: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def rollback_migration(self):
        """Откат миграции (восстановление из .old)"""
        try:
            old_db_backup = self.old_db_path.with_suffix('.db.old')
            if old_db_backup.exists():
                shutil.copy2(old_db_backup, self.old_db_path)
                logger.info(f"✅ Откат миграции: восстановлена {self.old_db_path}")
                return True
            else:
                logger.warning("Файл для отката не найден")
                return False
        except Exception as e:
            logger.error(f"Ошибка отката: {e}")
            return False


def check_and_migrate(project_root: Path, show_dialog_func=None) -> Tuple[bool, str]:
    """
    Проверка и выполнение миграции с опциональным диалогом подтверждения
    
    Args:
        project_root: Корень проекта
        show_dialog_func: Функция показа диалога подтверждения (опционально)
                         Сигнатура: func(message: str) -> bool
    
    Returns:
        Tuple[migration_performed, message]
    """
    mm = MigrationManager(project_root)
    
    if not mm.needs_migration():
        return False, "Миграция не требуется"
    
    logger.info("⚠️ Обнаружена старая структура БД")
    
    # Если передана функция диалога, спрашиваем пользователя
    if show_dialog_func:
        message = (
            "Обнаружена старая структура базы данных.\n\n"
            "Для работы с несколькими проектами необходимо выполнить миграцию.\n\n"
            "Ваши данные будут сохранены в проекте 'Default Project'.\n"
            "Старая БД будет переименована в .old\n\n"
            "Выполнить миграцию?"
        )
        
        if not show_dialog_func(message):
            logger.info("Миграция отменена пользователем")
            return False, "Миграция отменена"
    
    # Выполняем миграцию
    return mm.perform_migration()
