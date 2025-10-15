"""
Скрипт для проверки functional_id на соответствие структуре и правилам
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.functional_item import FunctionalItem

engine = create_engine('sqlite:///data/voluptas.db')
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

items = session.query(FunctionalItem).all()

print(f"Всего записей: {len(items)}\n")
print("Проверка functional_id на корректность структуры:\n")
print("="*80)

issues = []

for item in items:
    funcid = item.functional_id
    parts = funcid.split('.')
    item_type = item.type
    
    # Правила структуры functional_id
    problems = []
    
    # Module: должен быть вида "Module_Name"
    if item_type == 'Module':
        if len(parts) != 1:
            problems.append(f"Module должен быть одним словом, найдено {len(parts)} частей")
    
    # Epic: должен быть вида "Module.Epic_Name"
    elif item_type == 'Epic':
        if len(parts) != 2:
            problems.append(f"Epic должен быть Module.Epic, найдено {len(parts)} частей")
        if not item.module:
            problems.append("У Epic должен быть указан Module")
    
    # Feature: должен быть вида "Module.Epic.Feature_Name"
    elif item_type == 'Feature':
        if len(parts) < 3:
            problems.append(f"Feature должен быть Module.Epic.Feature, найдено {len(parts)} частей")
        if not item.module:
            problems.append("У Feature должен быть указан Module")
        if not item.epic:
            problems.append("У Feature должен быть указан Epic")
    
    # Story: должен быть вида "Module.Epic.Feature.Story_Name"
    elif item_type == 'Story':
        if len(parts) < 4:
            problems.append(f"Story должен быть Module.Epic.Feature.Story, найдено {len(parts)} частей")
        if not item.module:
            problems.append("У Story должен быть указан Module")
        if not item.epic:
            problems.append("У Story должен быть указан Epic")
        if not item.feature:
            problems.append("У Story должен быть указан Feature")
    
    # Page: должен быть вида "Module.Epic.Page_Name" или "Module.Epic.Feature.Page_Name"
    elif item_type == 'Page':
        if len(parts) < 3:
            problems.append(f"Page должен быть Module.Epic.Page или Module.Epic.Feature.Page, найдено {len(parts)} частей")
        if not item.module:
            problems.append("У Page должен быть указан Module")
        if not item.epic:
            problems.append("У Page должен быть указан Epic")
    
    # Element: может быть вида "Element_Name" или привязан к странице
    elif item_type == 'Element':
        # Элементы могут быть как самостоятельными, так и привязанными к страницам
        pass
    
    # Service: должен быть вида "Module.Service_Name"
    elif item_type == 'Service':
        if len(parts) < 2:
            problems.append(f"Service должен быть Module.Service, найдено {len(parts)} частей")
        if not item.module:
            problems.append("У Service должен быть указан Module")
    
    # Проверка segment для типов
    if item.segment:
        if item_type in ['Module', 'Epic']:
            problems.append(f"{item_type} не должен иметь segment, но указан: {item.segment}")
    
    if problems:
        issues.append({
            'id': item.id,
            'funcid': funcid,
            'type': item_type,
            'problems': problems
        })
        print(f"❌ ID: {item.id}")
        print(f"   FuncID: {funcid}")
        print(f"   Type: {item_type}")
        print(f"   Module: {item.module or 'не указан'}")
        print(f"   Epic: {item.epic or 'не указан'}")
        print(f"   Feature: {item.feature or 'не указан'}")
        print(f"   Segment: {item.segment or 'не указан'}")
        for prob in problems:
            print(f"   ⚠️  {prob}")
        print()

print("="*80)
print(f"\n📊 Итого найдено проблем: {len(issues)}")

if not issues:
    print("✅ Все functional_id соответствуют требованиям!")

session.close()
