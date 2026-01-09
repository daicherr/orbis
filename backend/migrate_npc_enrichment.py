"""
Migração: NPC Entity Enrichment
Adiciona novos campos ao modelo NPC para suportar arquitetura cognitiva.

Novos campos:
- species, gender, can_speak: Identidade
- description, attack_power, speed: Atributos
- aggression, courage: Comportamento de IA
- home_location, daily_schedule, current_activity: Rotina
- faction_id, faction_role, relationships: Social
- role, inventory, dialogue_options: Funcionalidade
- is_alive, is_active: Status
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from app.config import settings


def get_sync_connection_params():
    """Extrai parâmetros de conexão da URL do banco."""
    # URL format: postgresql+asyncpg://user:pass@host:port/dbname
    url = settings.DATABASE_URL
    
    # Remove o prefixo postgresql+asyncpg://
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if url.startswith("postgresql://"):
        url = url[len("postgresql://"):]
    
    # Parse user:pass@host:port/dbname
    if "@" in url:
        auth, rest = url.split("@", 1)
        user, password = auth.split(":", 1)
    else:
        user, password = "postgres", "postgres"
        rest = url
    
    if "/" in rest:
        host_port, dbname = rest.split("/", 1)
    else:
        host_port = rest
        dbname = "orbis_db"
    
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"
    
    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "dbname": dbname
    }


def run_migration():
    """Executa a migração adicionando novos campos à tabela NPC."""
    
    params = get_sync_connection_params()
    print(f"Conectando ao banco: {params['host']}:{params['port']}/{params['dbname']}")
    
    conn = psycopg2.connect(**params)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Lista de colunas a adicionar com seus tipos e defaults
    new_columns = [
        # Identidade
        ("species", "VARCHAR(50)", "'human'"),
        ("gender", "VARCHAR(20)", "'unknown'"),
        ("can_speak", "BOOLEAN", "TRUE"),
        ("description", "TEXT", "NULL"),
        
        # Atributos de combate
        ("attack_power", "FLOAT", "10.0"),
        ("speed", "FLOAT", "10.0"),
        
        # Comportamento de IA
        ("aggression", "INTEGER", "50"),
        ("courage", "INTEGER", "50"),
        
        # Localização e rotina
        ("home_location", "VARCHAR(100)", "NULL"),
        ("daily_schedule", "JSONB", "'{}'::jsonb"),
        ("current_activity", "VARCHAR(100)", "NULL"),
        
        # Social
        ("faction_id", "VARCHAR(50)", "NULL"),
        ("faction_role", "VARCHAR(50)", "NULL"),
        ("relationships", "JSONB", "'{}'::jsonb"),
        
        # Funcionalidade
        ("role", "VARCHAR(50)", "'civilian'"),
        ("inventory", "JSONB", "'[]'::jsonb"),
        ("dialogue_options", "JSONB", "'[]'::jsonb"),
        
        # Status
        ("is_alive", "BOOLEAN", "TRUE"),
        ("is_active", "BOOLEAN", "TRUE"),
    ]
    
    try:
        # Verificar se a tabela existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'npc'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("⚠️ Tabela 'npc' não existe. Criando tabela completa...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS npc (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    rank INTEGER DEFAULT 1,
                    
                    -- Identidade
                    species VARCHAR(50) DEFAULT 'human',
                    gender VARCHAR(20) DEFAULT 'unknown',
                    can_speak BOOLEAN DEFAULT TRUE,
                    description TEXT,
                    
                    -- Atributos de combate
                    current_hp FLOAT DEFAULT 100.0,
                    max_hp FLOAT DEFAULT 100.0,
                    defense FLOAT DEFAULT 10.0,
                    attack_power FLOAT DEFAULT 10.0,
                    speed FLOAT DEFAULT 10.0,
                    
                    -- Personalidade e IA
                    personality_traits JSONB DEFAULT '[]'::jsonb,
                    emotional_state VARCHAR(50) DEFAULT 'neutral',
                    vendetta_target INTEGER,
                    aggression INTEGER DEFAULT 50,
                    courage INTEGER DEFAULT 50,
                    
                    -- Localização e rotina
                    current_location VARCHAR(100) DEFAULT 'Initial Village',
                    home_location VARCHAR(100),
                    daily_schedule JSONB DEFAULT '{}'::jsonb,
                    current_activity VARCHAR(100),
                    
                    -- Social
                    faction_id VARCHAR(50),
                    faction_role VARCHAR(50),
                    relationships JSONB DEFAULT '{}'::jsonb,
                    
                    -- Funcionalidade
                    role VARCHAR(50) DEFAULT 'civilian',
                    available_quest_ids JSONB DEFAULT '[]'::jsonb,
                    inventory JSONB DEFAULT '[]'::jsonb,
                    dialogue_options JSONB DEFAULT '[]'::jsonb,
                    
                    -- Status
                    status_effects JSONB DEFAULT '[]'::jsonb,
                    is_alive BOOLEAN DEFAULT TRUE,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Criar índices
            cur.execute("CREATE INDEX IF NOT EXISTS idx_npc_name ON npc(name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_npc_species ON npc(species)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_npc_faction ON npc(faction_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_npc_location ON npc(current_location)")
            
            print("✅ Tabela 'npc' criada com sucesso!")
        else:
            # Se a tabela existe, adicionar colunas que faltam
            print("📊 Tabela 'npc' existe. Verificando colunas faltantes...")
            
            for col_name, col_type, default_value in new_columns:
                # Verificar se a coluna já existe
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'npc' AND column_name = '{col_name}'
                    )
                """)
                column_exists = cur.fetchone()[0]
                
                if not column_exists:
                    sql = f"ALTER TABLE npc ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
                    print(f"  ➕ Adicionando coluna: {col_name} ({col_type})")
                    cur.execute(sql)
                else:
                    print(f"  ✓ Coluna já existe: {col_name}")
            
            # Criar índices se não existirem
            print("\n📇 Verificando índices...")
            indexes = [
                ("idx_npc_species", "species"),
                ("idx_npc_faction", "faction_id"),
                ("idx_npc_location", "current_location"),
            ]
            
            for idx_name, col_name in indexes:
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes 
                        WHERE tablename = 'npc' AND indexname = '{idx_name}'
                    )
                """)
                index_exists = cur.fetchone()[0]
                
                if not index_exists:
                    print(f"  ➕ Criando índice: {idx_name}")
                    cur.execute(f"CREATE INDEX {idx_name} ON npc({col_name})")
                else:
                    print(f"  ✓ Índice já existe: {idx_name}")
        
        print("\n✅ Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def verify_migration():
    """Verifica se a migração foi aplicada corretamente."""
    
    params = get_sync_connection_params()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    
    try:
        # Listar todas as colunas da tabela NPC
        cur.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'npc'
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Estrutura da tabela NPC:")
        print("-" * 60)
        for row in cur.fetchall():
            col_name, data_type, default = row
            default_str = f" (default: {str(default)[:30]}...)" if default and len(str(default)) > 30 else (f" (default: {default})" if default else "")
            print(f"  {col_name:<25} {data_type:<15}{default_str}")
        print("-" * 60)
        
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migração NPC Entity Enrichment")
    parser.add_argument("--verify", action="store_true", help="Apenas verificar estrutura")
    args = parser.parse_args()
    
    if args.verify:
        verify_migration()
    else:
        run_migration()
        verify_migration()
