"""
Инициализация справочников (seed data)

Заполняет таблицу dictionaries дефолтными значениями при первом запуске
"""

from src.db import SessionLocal
from src.models import Dictionary


def seed_dictionaries():
    """Заполнить таблицу справочников дефолтными значениями"""
    
    session = SessionLocal()
    
    # Проверяем, есть ли уже данные
    existing_count = session.query(Dictionary).count()
    if existing_count > 0:
        print(f"⚠️ Справочники уже существуют ({existing_count} записей). Пропускаем seed.")
        session.close()
        return
    
    print("🌱 Инициализация справочников...")
    
    # === TYPES (типы элементов) ===
    types = [
        ("Module", 1, "Модуль системы"),
        ("Epic", 2, "Эпик"),
        ("Feature", 3, "Фича/функциональность"),
        ("Story", 4, "Пользовательская история"),
        ("Page", 5, "Страница UI"),
        ("Element", 6, "Элемент UI (для POM)"),
        ("Service", 7, "Сервис/микросервис"),
    ]
    
    for value, order, desc in types:
        d = Dictionary(
            dict_type='type',
            value=value,
            display_order=order,
            is_active=True,
            description=desc
        )
        session.add(d)
    
    # === SEGMENTS (сегменты) ===
    segments = [
        ("UI", 1, "Пользовательский интерфейс"),
        ("UX/CX", 2, "Пользовательский опыт"),
        ("API", 3, "Программный интерфейс"),
        ("Backend", 4, "Серверная логика"),
        ("Database", 5, "База данных"),
        ("Integration", 6, "Интеграции с внешними системами"),
        ("Security", 7, "Безопасность"),
        ("Performance", 8, "Производительность"),
    ]
    
    for value, order, desc in segments:
        d = Dictionary(
            dict_type='segment',
            value=value,
            display_order=order,
            is_active=True,
            description=desc
        )
        session.add(d)
    
    # === AUTOMATION_STATUSES ===
    automation_statuses = [
        ("Not Started", 1, "Автоматизация не начата"),
        ("In Progress", 2, "Автоматизация в процессе"),
        ("Automated", 3, "Полностью автоматизировано"),
        ("Partially Automated", 4, "Частично автоматизировано"),
        ("Not Applicable", 5, "Автоматизация не применима"),
    ]
    
    for value, order, desc in automation_statuses:
        d = Dictionary(
            dict_type='automation_status',
            value=value,
            display_order=order,
            is_active=True,
            description=desc
        )
        session.add(d)
    
    # === MATURITY_LEVELS ===
    maturity_levels = [
        ("Draft", 1, "Черновик"),
        ("In Review", 2, "На ревью"),
        ("Approved", 3, "Утверждено"),
        ("Deprecated", 4, "Устаревшее"),
    ]
    
    for value, order, desc in maturity_levels:
        d = Dictionary(
            dict_type='maturity',
            value=value,
            display_order=order,
            is_active=True,
            description=desc
        )
        session.add(d)
    
    # === POSITIONS (должности) ===
    positions = [
        # QA
        ("QA Engineer", 1, "QA роль"),
        ("QA Team Lead", 2, "QA роль"),
        ("QA Tech Lead", 3, "QA роль"),
        ("QA Lead", 4, "QA роль"),
        ("QA", 5, "QA роль"),
        
        # Dev
        ("Frontend Developer", 10, "Dev роль"),
        ("Frontend Lead", 11, "Dev роль"),
        ("Backend Developer", 12, "Dev роль"),
        ("Backend Tech Developer", 13, "Dev роль"),
        ("Backend Tech Lead", 14, "Dev роль"),
        ("DevOps Engineer", 15, "Dev роль"),
        
        # Management
        ("Project Manager", 20, "Менеджмент"),
        ("Product Owner", 21, "Менеджмент"),
        
        # Other
        ("Business Analyst", 30, "Другое"),
        ("Designer", 31, "Другое"),
        ("Content Manager", 32, "Другое"),
        ("Other", 99, "Другое"),
    ]
    
    for value, order, desc in positions:
        d = Dictionary(
            dict_type='position',
            value=value,
            display_order=order,
            is_active=True,
            description=desc
        )
        session.add(d)
    
    try:
        session.commit()
        count = session.query(Dictionary).count()
        print(f"✅ Справочники инициализированы: {count} записей")
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при инициализации справочников: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_dictionaries()
