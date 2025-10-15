"""
Миграция таблицы functional_item_relations
Добавление полей для типизированных связей
"""
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/voluptas.db')

with engine.connect() as conn:
    # Проверяем структуру текущей таблицы
    result = conn.execute(text("PRAGMA table_info(functional_item_relations)"))
    columns = [row[1] for row in result.fetchall()]
    
    print(f"Текущие колонки: {columns}")
    
    # Если старая структура - пересоздаём таблицу
    if 'type' not in columns:
        print("Пересоздаём таблицу functional_item_relations...")
        
        # Создаём временную таблицу
        conn.execute(text("""
            CREATE TABLE functional_item_relations_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                type VARCHAR(50) NOT NULL DEFAULT 'functional',
                directed BOOLEAN DEFAULT 1,
                weight REAL DEFAULT 1.0,
                metadata TEXT,
                active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES functional_items(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES functional_items(id) ON DELETE CASCADE,
                UNIQUE(source_id, target_id, type)
            )
        """))
        conn.commit()
        
        # Копируем старые данные
        try:
            conn.execute(text("""
                INSERT INTO functional_item_relations_new (source_id, target_id, type, directed, active)
                SELECT item_id, related_item_id, 'functional', 1, 1
                FROM functional_item_relations
            """))
            conn.commit()
            print("✓ Данные скопированы")
        except Exception as e:
            print(f"⚠️  Старая таблица пуста или ошибка: {e}")
        
        # Удаляем старую таблицу
        conn.execute(text("DROP TABLE IF EXISTS functional_item_relations"))
        conn.commit()
        
        # Переименовываем новую
        conn.execute(text("ALTER TABLE functional_item_relations_new RENAME TO functional_item_relations"))
        conn.commit()
        
        # Создаём индексы
        conn.execute(text("CREATE INDEX idx_relations_source ON functional_item_relations(source_id)"))
        conn.execute(text("CREATE INDEX idx_relations_target ON functional_item_relations(target_id)"))
        conn.execute(text("CREATE INDEX idx_relations_type ON functional_item_relations(type)"))
        conn.execute(text("CREATE INDEX idx_relations_active ON functional_item_relations(active)"))
        conn.commit()
        
        print("✓ Индексы созданы")
    
    # Мигрируем parent_id → hierarchy relations
    print("\nМиграция parent_id → hierarchy relations...")
    result = conn.execute(text("""
        SELECT id, parent_id, functional_id 
        FROM functional_items 
        WHERE parent_id IS NOT NULL
    """))
    
    parent_relations = result.fetchall()
    
    if parent_relations:
        print(f"Найдено {len(parent_relations)} записей с parent_id")
        
        for item_id, parent_id, funcid in parent_relations:
            # Проверяем, нет ли уже такой связи
            existing = conn.execute(text("""
                SELECT id FROM functional_item_relations 
                WHERE source_id = :parent_id 
                AND target_id = :item_id 
                AND type = 'hierarchy'
            """), {"parent_id": parent_id, "item_id": item_id}).fetchone()
            
            if not existing:
                conn.execute(text("""
                    INSERT INTO functional_item_relations 
                    (source_id, target_id, type, directed, weight, active, metadata)
                    VALUES (:parent_id, :item_id, 'hierarchy', 1, 1.0, 1, '{"origin": "migration", "migrated_from": "parent_id"}')
                """), {"parent_id": parent_id, "item_id": item_id})
                print(f"  ✓ Создана hierarchy связь: parent {parent_id} → child {item_id} ({funcid})")
        
        conn.commit()
        print(f"✓ Мигрировано {len(parent_relations)} parent→child связей")
    else:
        print("⚠️  Нет записей с parent_id для миграции")

print("\n✅ Миграция завершена!")
