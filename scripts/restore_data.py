#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт восстановления данных из backup на новом ПК

Использование:
    python scripts/restore_data.py [путь_к_csv_файлу]
    
Если путь не указан, ищет последний backup в data/export/
"""

import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.db.database import SessionLocal, init_db, DATABASE_PATH
from scripts.import_csv_full import import_from_csv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def find_latest_backup():
    """Найти последний backup CSV в data/export/"""
    export_dir = project_root / 'data' / 'export'
    if not export_dir.exists():
        return None
    
    csv_files = list(export_dir.glob('*.csv'))
    if not csv_files:
        return None
    
    # Сортируем по дате изменения
    csv_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return csv_files[0]


def restore_from_backup(csv_path=None):
    """
    Восстановить данные из backup
    
    Args:
        csv_path: путь к CSV файлу, если None - ищем последний backup
    """
    logger.info("="*60)
    logger.info("🔄 ВОССТАНОВЛЕНИЕ ДАННЫХ ИЗ BACKUP")
    logger.info("="*60)
    
    # Проверяем БД
    if not DATABASE_PATH.exists():
        logger.warning("⚠️  БД не найдена, инициализирую...")
        init_db()
    else:
        logger.info(f"✅ БД найдена: {DATABASE_PATH}")
    
    # Определяем файл для импорта
    if csv_path is None:
        logger.info("📂 Поиск последнего backup в data/export/...")
        csv_path = find_latest_backup()
        if csv_path is None:
            logger.error("❌ Backup файлы не найдены в data/export/")
            return False
        logger.info(f"✅ Найден backup: {csv_path.name}")
    else:
        csv_path = Path(csv_path)
        if not csv_path.exists():
            logger.error(f"❌ Файл не найден: {csv_path}")
            return False
    
    # Импортируем данные
    logger.info(f"📥 Импорт данных из {csv_path}...")
    try:
        session = SessionLocal()
        count = import_from_csv(str(csv_path), session)
        session.close()
        
        logger.info("="*60)
        logger.info(f"✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО")
        logger.info(f"   Импортировано: {count} элементов")
        logger.info(f"   База данных: {DATABASE_PATH}")
        logger.info("="*60)
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        return False


if __name__ == '__main__':
    # Получаем путь из аргументов или None
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = restore_from_backup(csv_file)
    sys.exit(0 if success else 1)
