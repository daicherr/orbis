"""
Migration: Adiciona sistema de locais dinâmicos e eventos globais melhorados
- Novas tabelas: dynamic_locations, location_aliases
- Novos campos em players: home_location, home_location_id, first_scene_context, important_npc_name
- Novos campos em world_events: event_type, location_affected, caused_by_player_id, etc.
"""
import asyncio
from sqlalchemy import text
from app.database.db_connection import engine as async_engine

async def run_migration():
    async with async_engine.begin() as conn:
        print("🔄 Iniciando migração: Locais Dinâmicos e Eventos Globais...")
        
        # ===== 1. ADICIONAR COLUNAS EM PLAYERS =====
        player_columns = [
            ("home_location", "VARCHAR(255)"),
            ("home_location_id", "INTEGER"),
            ("first_scene_context", "TEXT"),
            ("important_npc_name", "VARCHAR(100)")
        ]
        
        for col_name, col_type in player_columns:
            try:
                await conn.execute(text(f"ALTER TABLE player ADD COLUMN {col_name} {col_type}"))
                print(f"  ✅ Coluna 'player.{col_name}' adicionada")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  ⏭️ Coluna 'player.{col_name}' já existe")
                else:
                    print(f"  ⚠️ Erro ao adicionar 'player.{col_name}': {e}")
        
        # ===== 2. ATUALIZAR TABELA WORLD_EVENTS =====
        event_columns = [
            ("event_type", "VARCHAR(50) DEFAULT 'generic'"),
            ("location_affected", "VARCHAR(255)"),
            ("caused_by_player_id", "INTEGER"),
            ("caused_by_npc_id", "INTEGER"),
            ("author_alias", "VARCHAR(100)"),
            ("public_description", "TEXT DEFAULT ''"),
            ("secret_description", "TEXT DEFAULT ''"),
            ("investigation_difficulty", "INTEGER DEFAULT 5"),
            ("clues", "JSONB DEFAULT '[]'"),
            ("is_active", "BOOLEAN DEFAULT TRUE")
        ]
        
        for col_name, col_type in event_columns:
            try:
                await conn.execute(text(f"ALTER TABLE worldevent ADD COLUMN {col_name} {col_type}"))
                print(f"  ✅ Coluna 'worldevent.{col_name}' adicionada")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  ⏭️ Coluna 'worldevent.{col_name}' já existe")
                else:
                    print(f"  ⚠️ Erro ao adicionar 'worldevent.{col_name}': {e}")
        
        # ===== 3. CRIAR TABELA DYNAMIC_LOCATIONS =====
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dynamic_locations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    location_type VARCHAR(50) DEFAULT 'generic',
                    parent_location VARCHAR(255) NOT NULL,
                    owner_player_id INTEGER,
                    owner_npc_id INTEGER,
                    description TEXT NOT NULL,
                    interior_description TEXT,
                    created_by VARCHAR(50) DEFAULT 'narrative',
                    creation_context TEXT,
                    is_destroyed BOOLEAN DEFAULT FALSE,
                    destruction_event_id INTEGER,
                    is_public BOOLEAN DEFAULT TRUE,
                    is_hidden BOOLEAN DEFAULT FALSE,
                    npcs_present JSONB DEFAULT '[]',
                    items_available JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_visited_at TIMESTAMP
                )
            """))
            print("  ✅ Tabela 'dynamic_locations' criada")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  ⏭️ Tabela 'dynamic_locations' já existe")
            else:
                print(f"  ⚠️ Erro ao criar 'dynamic_locations': {e}")
        
        # Criar índices
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dynamic_locations_name ON dynamic_locations(name)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dynamic_locations_parent ON dynamic_locations(parent_location)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dynamic_locations_owner ON dynamic_locations(owner_player_id)"))
            print("  ✅ Índices em 'dynamic_locations' criados")
        except Exception as e:
            print(f"  ⏭️ Índices já existem ou erro: {e}")
        
        # ===== 4. CRIAR TABELA LOCATION_ALIASES =====
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS location_aliases (
                    id SERIAL PRIMARY KEY,
                    alias VARCHAR(100) NOT NULL,
                    location_id INTEGER REFERENCES dynamic_locations(id),
                    player_id INTEGER NOT NULL,
                    static_location_name VARCHAR(255)
                )
            """))
            print("  ✅ Tabela 'location_aliases' criada")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  ⏭️ Tabela 'location_aliases' já existe")
            else:
                print(f"  ⚠️ Erro ao criar 'location_aliases': {e}")
        
        # Criar índices
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_location_aliases_alias ON location_aliases(alias)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_location_aliases_player ON location_aliases(player_id)"))
            print("  ✅ Índices em 'location_aliases' criados")
        except Exception as e:
            print(f"  ⏭️ Índices já existem ou erro: {e}")
        
        # ===== 5. CRIAR ÍNDICES EM WORLD_EVENTS =====
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_worldevent_location ON worldevent(location_affected)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_worldevent_player ON worldevent(caused_by_player_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_worldevent_active ON worldevent(is_active)"))
            print("  ✅ Índices em 'worldevent' criados")
        except Exception as e:
            print(f"  ⏭️ Índices já existem ou erro: {e}")
        
        # ===== 6. ATUALIZAR PLAYERS EXISTENTES =====
        try:
            # Setar home_location = origin_location para players que não têm
            await conn.execute(text("""
                UPDATE player 
                SET home_location = origin_location 
                WHERE home_location IS NULL AND origin_location IS NOT NULL
            """))
            print("  ✅ Players atualizados: home_location = origin_location")
        except Exception as e:
            print(f"  ⚠️ Erro ao atualizar players: {e}")
        
        print("\n✅ Migração concluída com sucesso!")
        print("""
📝 Novas funcionalidades adicionadas:
   - Players agora têm 'home_location' (para "ir para casa")
   - Players têm 'first_scene_context' (contexto inicial da jornada)
   - Eventos globais rastreiam autor (player ou NPC)
   - Locais podem ser criados dinamicamente pelo Mestre
   - Aliases permitem "casa", "lar" → local real
   - Investigação de eventos para descobrir autores
        """)

if __name__ == "__main__":
    asyncio.run(run_migration())
