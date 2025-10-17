"""
Синхронизация parent_id с таблицей functional_item_relations

Создаёт записи типа 'hierarchy' для всех элементов, у которых parent_id != None
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.database import SessionLocal
from src.models.functional_item import FunctionalItem
from src.models.relation import Relation


def sync_hierarchy():
    """Синхронизировать иерархические связи"""
    
    session = SessionLocal()
    
    try:
        print("=" * 60)
        print("СИНХРОНИЗАЦИЯ: parent_id → functional_item_relations")
        print("=" * 60)
        
        # Получить все элементы с parent_id
        items_with_parent = session.query(FunctionalItem).filter(
            FunctionalItem.parent_id.isnot(None)
        ).all()
        
        print(f"\n📊 Найдено элементов с parent_id: {len(items_with_parent)}")
        
        created = 0
        skipped = 0
        
        for item in items_with_parent:
            # Проверить, существует ли уже такая связь
            existing = session.query(Relation).filter_by(
                source_id=item.parent_id,
                target_id=item.id,
                type='hierarchy'
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Создать новую связь
            relation = Relation(
                source_id=item.parent_id,
                target_id=item.id,
                type='hierarchy',
                directed=True,
                weight=1.0,
                active=True
            )
            
            session.add(relation)
            created += 1
            
            # Получить названия для красивого вывода
            parent = session.query(FunctionalItem).get(item.parent_id)
            if parent:
                print(f"   ✅ {parent.functional_id} → {item.functional_id}")
        
        session.commit()
        
        print(f"\n{'=' * 60}")
        print(f"✅ Синхронизация завершена:")
        print(f"   Создано связей: {created}")
        print(f"   Пропущено (уже существуют): {skipped}")
        print(f"{'=' * 60}")
        
        # Статистика по типам
        print(f"\n📊 Статистика связей типа 'hierarchy':")
        hierarchy_relations = session.query(Relation).filter_by(
            type='hierarchy', active=True
        ).all()
        
        by_level = {}
        for rel in hierarchy_relations:
            source = session.query(FunctionalItem).get(rel.source_id)
            target = session.query(FunctionalItem).get(rel.target_id)
            
            if source and target:
                key = f"{source.type} → {target.type}"
                by_level[key] = by_level.get(key, 0) + 1
        
        for key, count in sorted(by_level.items()):
            print(f"   {key}: {count}")
        
        print(f"\n   Всего hierarchy-связей: {len(hierarchy_relations)}")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sync_hierarchy()
