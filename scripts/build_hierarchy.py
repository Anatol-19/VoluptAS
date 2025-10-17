"""
Скрипт для построения parent-child иерархии из существующих данных

Проблема: все parent_id = None
Решение: построить иерархию из полей module/epic/feature

Логика:
1. Module → parent_id = None (корневой уровень)
2. Epic → parent_id = ID модуля с таким же module
3. Feature → parent_id = ID эпика с таким же epic
4. Story → parent_id = ID фичи с таким же feature
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.db import SessionLocal
from src.models import FunctionalItem


def build_hierarchy():
    """Построить parent-child иерархию"""
    session = SessionLocal()
    
    try:
        print("🔄 Построение иерархии parent-child...")
        
        # Получаем все элементы
        all_items = session.query(FunctionalItem).all()
        print(f"   Всего элементов: {len(all_items)}")
        
        # Создаём индексы для быстрого поиска
        by_type = {}
        by_functional_id = {}
        
        for item in all_items:
            if item.type not in by_type:
                by_type[item.type] = []
            by_type[item.type].append(item)
            by_functional_id[item.functional_id] = item
        
        updated = 0
        
        # 1. Module → parent_id = None (уже так)
        modules = by_type.get('Module', [])
        print(f"   Модулей: {len(modules)} (parent_id = None)")
        
        # 2. Epic → parent_id = ID модуля
        epics = by_type.get('Epic', [])
        for epic in epics:
            if not epic.module:
                continue
            
            # Ищем родительский модуль
            parent_module = None
            for mod in modules:
                # Сравниваем по названию модуля (может быть разный регистр)
                if mod.module and mod.module.strip().upper() == epic.module.strip().upper():
                    parent_module = mod
                    break
            
            if parent_module and epic.parent_id != parent_module.id:
                epic.parent_id = parent_module.id
                updated += 1
                print(f"   Epic '{epic.functional_id}' → parent = Module '{parent_module.functional_id}'")
        
        # 3. Feature → parent_id = ID эпика
        features = by_type.get('Feature', [])
        for feature in features:
            if not feature.epic:
                continue
            
            # Ищем родительский эпик
            parent_epic = None
            for ep in epics:
                # Сравниваем по названию эпика
                if ep.epic and ep.epic.strip().upper() == feature.epic.strip().upper():
                    # Проверяем также совпадение модуля (если есть)
                    if feature.module and ep.module:
                        if ep.module.strip().upper() == feature.module.strip().upper():
                            parent_epic = ep
                            break
                    else:
                        parent_epic = ep
                        break
            
            if parent_epic and feature.parent_id != parent_epic.id:
                feature.parent_id = parent_epic.id
                updated += 1
                print(f"   Feature '{feature.functional_id}' → parent = Epic '{parent_epic.functional_id}'")
        
        # 4. Story → parent_id = ID фичи
        stories = by_type.get('Story', [])
        for story in stories:
            if not story.feature:
                continue
            
            # Ищем родительскую фичу
            parent_feature = None
            for feat in features:
                # Сравниваем по названию фичи
                if feat.feature and feat.feature.strip().upper() == story.feature.strip().upper():
                    # Проверяем также совпадение эпика и модуля (если есть)
                    match = True
                    if story.epic and feat.epic:
                        if feat.epic.strip().upper() != story.epic.strip().upper():
                            match = False
                    if story.module and feat.module:
                        if feat.module.strip().upper() != story.module.strip().upper():
                            match = False
                    
                    if match:
                        parent_feature = feat
                        break
            
            if parent_feature and story.parent_id != parent_feature.id:
                story.parent_id = parent_feature.id
                updated += 1
                print(f"   Story '{story.functional_id}' → parent = Feature '{parent_feature.functional_id}'")
        
        # 5. Page/Element/Service → пока без parent (специальные типы)
        # Можно будет добавить позже через N:M связи
        
        # Сохраняем изменения
        session.commit()
        
        print(f"\n✅ Готово! Обновлено связей: {updated}")
        print(f"   Epic → Module: {sum(1 for e in epics if e.parent_id)}")
        print(f"   Feature → Epic: {sum(1 for f in features if f.parent_id)}")
        print(f"   Story → Feature: {sum(1 for s in stories if s.parent_id)}")
        
        # Статистика
        print(f"\n📊 Статистика:")
        print(f"   Modules: {len(modules)}")
        print(f"   Epics: {len(epics)}")
        print(f"   Features: {len(features)}")
        print(f"   Stories: {len(stories)}")
        print(f"   Pages: {len(by_type.get('Page', []))}")
        print(f"   Elements: {len(by_type.get('Element', []))}")
        print(f"   Services: {len(by_type.get('Service', []))}")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    build_hierarchy()
