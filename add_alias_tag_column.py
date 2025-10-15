from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/voluptas.db')

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE functional_items ADD COLUMN alias_tag VARCHAR(100);"))
    conn.commit()
    print("✅ Колонка alias_tag добавлена успешно!")
