from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/voluptas.db')

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE functional_item_relations RENAME COLUMN metadata TO meta_data"))
    conn.commit()
    print("✅ Колонка переименована: metadata → meta_data")
