from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.functional_item import FunctionalItem

engine = create_engine('sqlite:///data/voluptas.db')
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

items = session.query(FunctionalItem).all()

print(f"Всего записей: {len(items)}\n")
print("Записи с полными адресами в alias_tag (нужно исправить):\n")

needs_fix = []
for item in items:
    if item.alias_tag and '.' in item.alias_tag:
        needs_fix.append(item)
        print(f"ID: {item.id}")
        print(f"  functional_id: {item.functional_id}")
        print(f"  alias_tag: {item.alias_tag}")
        print(f"  Предложение: {item.functional_id.split('.')[-1]}")
        print()

print(f"\nНайдено записей, требующих исправления: {len(needs_fix)}")

if needs_fix:
    response = input("\nИсправить автоматически? (y/n): ")
    if response.lower() == 'y':
        for item in needs_fix:
            old_tag = item.alias_tag
            item.alias_tag = item.functional_id.split('.')[-1]
            print(f"✓ {old_tag} → {item.alias_tag}")
        
        session.commit()
        print(f"\n✅ Исправлено записей: {len(needs_fix)}")
    else:
        print("Отменено.")

session.close()
