"""
Создание hierarchy связей из существующих module/epic/feature полей
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.functional_item import FunctionalItem
from src.models.relation import Relation

engine = create_engine('sqlite:///data/voluptas.db')
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# Загружаем все элементы
items = session.query(FunctionalItem).all()

print(f"Всего элементов: {len(items)}")

# Создаём словарь для быстрого поиска по functional_id
items_by_funcid = {item.functional_id: item for item in items}

created = 0
skipped = 0

for item in items:
    # Epic → Module
    if item.type == 'Epic' and item.module:
        # Ищем Module
        module_item = next((i for i in items if i.type == 'Module' and i.module == item.module), None)
        if module_item:
            # Проверяем, нет ли уже связи
            existing = session.query(Relation).filter_by(
                source_id=module_item.id,
                target_id=item.id,
                type='hierarchy'
            ).first()
            
            if not existing:
                rel = Relation(
                    source_id=module_item.id,
                    target_id=item.id,
                    type='hierarchy',
                    directed=True,
                    weight=1.0,
                    active=True
                )
                rel.set_metadata({"origin": "auto_generated", "from": "module→epic"})
                session.add(rel)
                created += 1
                print(f"✓ {module_item.functional_id} → {item.functional_id}")
            else:
                skipped += 1
    
    # Feature → Epic
    if item.type == 'Feature' and item.epic:
        # Ищем Epic
        epic_item = next((i for i in items if i.type == 'Epic' and i.epic == item.epic and i.module == item.module), None)
        if epic_item:
            existing = session.query(Relation).filter_by(
                source_id=epic_item.id,
                target_id=item.id,
                type='hierarchy'
            ).first()
            
            if not existing:
                rel = Relation(
                    source_id=epic_item.id,
                    target_id=item.id,
                    type='hierarchy',
                    directed=True,
                    weight=1.0,
                    active=True
                )
                rel.set_metadata({"origin": "auto_generated", "from": "epic→feature"})
                session.add(rel)
                created += 1
                print(f"✓ {epic_item.functional_id} → {item.functional_id}")
            else:
                skipped += 1
    
    # Story → Feature
    if item.type == 'Story' and item.feature:
        # Ищем Feature
        feature_item = next((i for i in items if i.type == 'Feature' and i.feature == item.feature and i.epic == item.epic), None)
        if feature_item:
            existing = session.query(Relation).filter_by(
                source_id=feature_item.id,
                target_id=item.id,
                type='hierarchy'
            ).first()
            
            if not existing:
                rel = Relation(
                    source_id=feature_item.id,
                    target_id=item.id,
                    type='hierarchy',
                    directed=True,
                    weight=1.0,
                    active=True
                )
                rel.set_metadata({"origin": "auto_generated", "from": "feature→story"})
                session.add(rel)
                created += 1
                print(f"✓ {feature_item.functional_id} → {item.functional_id}")
            else:
                skipped += 1

session.commit()
print(f"\n✅ Создано связей: {created}")
print(f"⚠️  Пропущено (уже существуют): {skipped}")

session.close()
