"""
Скрипт для исправления functional_id и segment по новым правилам
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.functional_item import FunctionalItem

engine = create_engine('sqlite:///data/voluptas.db')
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

items = session.query(FunctionalItem).all()

print("Исправление segment для Module и Epic...")
print("="*80)

fixed_segments = 0
fixed_funcids = 0

for item in items:
    changed = False
    
    # Убираем segment у Module и Epic
    if item.type in ['Module', 'Epic'] and item.segment:
        print(f"✓ Убираем segment '{item.segment}' у {item.type}: {item.functional_id}")
        item.segment = None
        changed = True
        fixed_segments += 1
    
    # Исправляем functional_id для структуры
    parts = item.functional_id.split('.')
    
    # Epic: должен быть Module.Epic
    if item.type == 'Epic' and len(parts) != 2:
        if item.module and item.epic:
            new_funcid = f"{item.module}.{item.epic.replace(' ', '_')}"
            print(f"✓ Исправляем FuncID для Epic: {item.functional_id} → {new_funcid}")
            item.functional_id = new_funcid
            changed = True
            fixed_funcids += 1
    
    # Feature: должен быть Module.Epic.Feature
    if item.type == 'Feature' and len(parts) < 3:
        if item.module and item.epic and item.feature:
            new_funcid = f"{item.module}.{item.epic.replace(' ', '_')}.{item.feature.replace(' ', '_')}"
            print(f"✓ Исправляем FuncID для Feature: {item.functional_id} → {new_funcid}")
            item.functional_id = new_funcid
            changed = True
            fixed_funcids += 1
    
    # Module: должен быть одним словом
    if item.type == 'Module' and len(parts) > 1:
        if item.module:
            new_funcid = item.module.replace(' ', '_')
            print(f"✓ Исправляем FuncID для Module: {item.functional_id} → {new_funcid}")
            item.functional_id = new_funcid
            changed = True
            fixed_funcids += 1
    
    # Service: должен быть Module.Service
    if item.type == 'Service' and len(parts) == 1:
        if item.module:
            service_name = item.functional_id.replace(' ', '_')
            new_funcid = f"{item.module}.{service_name}"
            print(f"✓ Исправляем FuncID для Service: {item.functional_id} → {new_funcid}")
            item.functional_id = new_funcid
            changed = True
            fixed_funcids += 1

print("="*80)
print(f"\n📊 Итого исправлено:")
print(f"  - Убрано segment: {fixed_segments}")
print(f"  - Исправлено functional_id: {fixed_funcids}")

if fixed_segments > 0 or fixed_funcids > 0:
    response = input("\n💾 Сохранить изменения в БД? (y/n): ")
    if response.lower() == 'y':
        session.commit()
        print("✅ Изменения сохранены!")
    else:
        session.rollback()
        print("❌ Изменения отменены.")
else:
    print("\n✅ Исправлений не требуется!")

session.close()
