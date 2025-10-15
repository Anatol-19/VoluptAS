from sqlalchemy import create_engine, inspect

engine = create_engine('sqlite:///data/voluptas.db')
inspector = inspect(engine)
cols = inspector.get_columns('functional_items')

for col in cols:
    print(f"{col['name']}: {col['type']}")
