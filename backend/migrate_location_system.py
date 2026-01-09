"""
Migração: Location System
Cria tabelas para o sistema de localizações estruturadas.

Novas tabelas:
- locations: Locais do mapa do mundo
- location_visits: Histórico de visitas

Alterações em tabelas existentes:
- dynamic_locations: Novos campos
- location_aliases: Novo campo static_location_id
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from app.config import settings


def get_sync_connection_params():
    """Extrai parâmetros de conexão da URL do banco."""
    url = settings.DATABASE_URL
    
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if url.startswith("postgresql://"):
        url = url[len("postgresql://"):]
    
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
    """Executa a migração criando/atualizando tabelas de localização."""
    
    params = get_sync_connection_params()
    print(f"Conectando ao banco: {params['host']}:{params['port']}/{params['dbname']}")
    
    conn = psycopg2.connect(**params)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        # ==================== CRIAR TABELA LOCATIONS ====================
        print("\n📍 Verificando tabela 'locations'...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'locations'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("  ➕ Criando tabela 'locations'...")
            cur.execute("""
                CREATE TABLE locations (
                    id SERIAL PRIMARY KEY,
                    
                    -- Identificação
                    name VARCHAR(150) NOT NULL UNIQUE,
                    display_name VARCHAR(200) DEFAULT '',
                    location_type VARCHAR(50) DEFAULT 'wilderness',
                    
                    -- Descrição
                    description TEXT DEFAULT '',
                    short_description VARCHAR(300) DEFAULT '',
                    atmosphere VARCHAR(50) DEFAULT 'neutral',
                    
                    -- Geografia
                    parent_region VARCHAR(150),
                    connections JSONB DEFAULT '{}'::jsonb,
                    sub_locations JSONB DEFAULT '[]'::jsonb,
                    x FLOAT,
                    y FLOAT,
                    
                    -- Bioma e Perigo
                    biome VARCHAR(50) DEFAULT 'temperate',
                    danger_level VARCHAR(50) DEFAULT 'safe',
                    recommended_tier INTEGER DEFAULT 1,
                    max_tier INTEGER DEFAULT 3,
                    
                    -- Recursos e Economia
                    resources JSONB DEFAULT '{}'::jsonb,
                    price_modifiers JSONB DEFAULT '{}'::jsonb,
                    
                    -- Facção e Controle
                    controlling_faction VARCHAR(100),
                    faction_influence FLOAT DEFAULT 0.0,
                    
                    -- Clima e Tempo
                    weather_pattern VARCHAR(50) DEFAULT 'normal',
                    current_weather VARCHAR(50) DEFAULT 'clear',
                    possible_events JSONB DEFAULT '[]'::jsonb,
                    
                    -- População
                    population INTEGER DEFAULT 0,
                    npc_spawn_types JSONB DEFAULT '[]'::jsonb,
                    max_npc_count INTEGER DEFAULT 10,
                    
                    -- Lore
                    history TEXT DEFAULT '',
                    secrets JSONB DEFAULT '[]'::jsonb,
                    legend TEXT,
                    
                    -- Flags
                    is_safe_zone BOOLEAN DEFAULT FALSE,
                    is_pvp_zone BOOLEAN DEFAULT FALSE,
                    is_hidden BOOLEAN DEFAULT FALSE,
                    is_locked BOOLEAN DEFAULT FALSE,
                    lock_requirement VARCHAR(200),
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            # Índices
            cur.execute("CREATE INDEX idx_locations_name ON locations(name)")
            cur.execute("CREATE INDEX idx_locations_type ON locations(location_type)")
            cur.execute("CREATE INDEX idx_locations_region ON locations(parent_region)")
            cur.execute("CREATE INDEX idx_locations_faction ON locations(controlling_faction)")
            cur.execute("CREATE INDEX idx_locations_danger ON locations(danger_level)")
            cur.execute("CREATE INDEX idx_locations_biome ON locations(biome)")
            
            print("  ✅ Tabela 'locations' criada com sucesso!")
        else:
            print("  ✓ Tabela 'locations' já existe")
        
        # ==================== CRIAR TABELA LOCATION_VISITS ====================
        print("\n📍 Verificando tabela 'location_visits'...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'location_visits'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("  ➕ Criando tabela 'location_visits'...")
            cur.execute("""
                CREATE TABLE location_visits (
                    id SERIAL PRIMARY KEY,
                    player_id INTEGER NOT NULL,
                    
                    location_name VARCHAR(150) NOT NULL,
                    location_id INTEGER REFERENCES locations(id),
                    dynamic_location_id INTEGER REFERENCES dynamic_locations(id),
                    
                    first_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    visit_count INTEGER DEFAULT 1,
                    
                    secrets_found JSONB DEFAULT '[]'::jsonb,
                    npcs_met JSONB DEFAULT '[]'::jsonb,
                    items_found JSONB DEFAULT '[]'::jsonb,
                    
                    UNIQUE(player_id, location_name)
                )
            """)
            
            cur.execute("CREATE INDEX idx_visits_player ON location_visits(player_id)")
            cur.execute("CREATE INDEX idx_visits_location ON location_visits(location_name)")
            
            print("  ✅ Tabela 'location_visits' criada com sucesso!")
        else:
            print("  ✓ Tabela 'location_visits' já existe")
        
        # ==================== ATUALIZAR DYNAMIC_LOCATIONS ====================
        print("\n📍 Verificando colunas de 'dynamic_locations'...")
        
        new_columns = [
            ("parent_location_id", "INTEGER REFERENCES locations(id)", "NULL"),
            ("owner_name", "VARCHAR(100)", "NULL"),
            ("atmosphere", "VARCHAR(50)", "'neutral'"),
            ("is_locked", "BOOLEAN", "FALSE"),
            ("stored_items", "JSONB", "'[]'::jsonb"),
            ("qi_density", "FLOAT", "1.0"),
            ("safety_level", "VARCHAR(50)", "'normal'"),
        ]
        
        for col_name, col_type, default_value in new_columns:
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'dynamic_locations' AND column_name = '{col_name}'
                )
            """)
            column_exists = cur.fetchone()[0]
            
            if not column_exists:
                sql = f"ALTER TABLE dynamic_locations ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
                print(f"  ➕ Adicionando coluna: {col_name}")
                cur.execute(sql)
            else:
                print(f"  ✓ Coluna já existe: {col_name}")
        
        # ==================== ATUALIZAR LOCATION_ALIASES ====================
        print("\n📍 Verificando colunas de 'location_aliases'...")
        
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'location_aliases' AND column_name = 'static_location_id'
            )
        """)
        column_exists = cur.fetchone()[0]
        
        if not column_exists:
            print("  ➕ Adicionando coluna: static_location_id")
            cur.execute("ALTER TABLE location_aliases ADD COLUMN static_location_id INTEGER REFERENCES locations(id)")
        else:
            print("  ✓ Coluna já existe: static_location_id")
        
        # ==================== POPULAR LOCALIZAÇÕES INICIAIS ====================
        print("\n📍 Verificando localizações iniciais...")
        
        cur.execute("SELECT COUNT(*) FROM locations")
        count = cur.fetchone()[0]
        
        if count == 0:
            print("  ➕ Populando localizações iniciais...")
            
            initial_locations = [
                # Vila Inicial
                ("Initial Village", "Vila das Nuvens Brancas", "village", "temperate", "safe", 1, 1,
                 "Uma pequena vila pacífica aos pés das montanhas, onde cultivadores iniciantes começam sua jornada.",
                 "Vila pequena e pacífica", "peaceful", 500, True, None),
                
                # Floresta Nublada
                ("Misty Forest", "Floresta Nublada", "forest", "temperate", "low", 1, 3,
                 "Uma floresta densa coberta por névoa mística, lar de bestas de baixo nível e ervas raras.",
                 "Floresta densa e misteriosa", "mysterious", 0, False, "Região Norte"),
                
                # Montanhas do Dragão
                ("Dragon Mountains", "Montanhas do Dragão Adormecido", "mountain", "arctic", "moderate", 3, 5,
                 "Picos gelados onde antigos dragões supostamente dormem. Rico em minérios espirituais.",
                 "Montanhas geladas e imponentes", "tense", 0, False, "Região Norte"),
                
                # Cidade Mercante
                ("Merchant City", "Cidade do Comércio Celestial", "city", "temperate", "safe", 1, 9,
                 "A maior cidade comercial da região, onde cultivadores de todos os níveis negociam.",
                 "Grande cidade comercial", "neutral", 50000, True, "Região Central"),
                
                # Seita da Espada
                ("Sword Sect", "Seita da Espada Trovejante", "sect", "spiritual", "safe", 3, 7,
                 "Uma seita renomada especializada em técnicas de espada. Aceita apenas discípulos talentosos.",
                 "Seita de artes marciais", "peaceful", 2000, True, "Região Central"),
                
                # Pântano Venenoso
                ("Poison Swamp", "Pântano das Mil Toxinas", "swamp", "tropical", "high", 5, 7,
                 "Um pântano mortal cheio de criaturas venenosas e plantas letais. Poucos retornam.",
                 "Pântano perigoso e venenoso", "dangerous", 0, False, "Região Sul"),
                
                # Ruínas Antigas
                ("Ancient Ruins", "Ruínas do Império Caído", "ruins", "corrupted", "extreme", 7, 9,
                 "Ruínas de um império antigo corrompido por energia demoníaca. Tesouros inestimáveis jazem aqui.",
                 "Ruínas corrompidas", "dangerous", 0, False, "Região Oeste"),
                
                # Lago Espiritual
                ("Spirit Lake", "Lago do Despertar Espiritual", "lake", "spiritual", "low", 2, 4,
                 "Um lago sagrado onde cultivadores meditam para alcançar insights espirituais.",
                 "Lago sagrado e tranquilo", "peaceful", 50, False, "Região Leste"),
            ]
            
            for loc in initial_locations:
                cur.execute("""
                    INSERT INTO locations (
                        name, display_name, location_type, biome, danger_level,
                        recommended_tier, max_tier, description, short_description,
                        atmosphere, population, is_safe_zone, parent_region
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, loc)
            
            # Adicionar conexões
            connections = [
                ("Initial Village", "Misty Forest", 1, "2 hours", "low"),
                ("Initial Village", "Merchant City", 3, "1 day", "safe"),
                ("Misty Forest", "Dragon Mountains", 2, "6 hours", "moderate"),
                ("Misty Forest", "Spirit Lake", 2, "4 hours", "low"),
                ("Merchant City", "Sword Sect", 2, "8 hours", "safe"),
                ("Merchant City", "Poison Swamp", 4, "2 days", "moderate"),
                ("Dragon Mountains", "Ancient Ruins", 3, "1 day", "high"),
            ]
            
            for from_loc, to_loc, dist, time, danger in connections:
                # A -> B
                cur.execute("""
                    UPDATE locations 
                    SET connections = connections || %s::jsonb
                    WHERE name = %s
                """, (
                    f'{{"{to_loc}": {{"distance": {dist}, "travel_time": "{time}", "danger": "{danger}"}}}}',
                    from_loc
                ))
                
                # B -> A
                cur.execute("""
                    UPDATE locations 
                    SET connections = connections || %s::jsonb
                    WHERE name = %s
                """, (
                    f'{{"{from_loc}": {{"distance": {dist}, "travel_time": "{time}", "danger": "{danger}"}}}}',
                    to_loc
                ))
            
            print("  ✅ Localizações iniciais criadas!")
        else:
            print(f"  ✓ Já existem {count} localizações")
        
        print("\n✅ Migração do Location System concluída com sucesso!")
        
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
        # Listar localizações
        cur.execute("""
            SELECT name, location_type, danger_level, recommended_tier, max_tier
            FROM locations
            ORDER BY recommended_tier, name
        """)
        
        print("\n📋 Localizações no sistema:")
        print("-" * 80)
        print(f"{'Nome':<30} {'Tipo':<15} {'Perigo':<12} {'Tier Range':<12}")
        print("-" * 80)
        
        for row in cur.fetchall():
            name, loc_type, danger, rec_tier, max_tier = row
            print(f"{name:<30} {loc_type:<15} {danger:<12} {rec_tier}-{max_tier}")
        
        print("-" * 80)
        
        # Contar tabelas
        cur.execute("SELECT COUNT(*) FROM locations")
        loc_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM dynamic_locations")
        dyn_count = cur.fetchone()[0]
        
        print(f"\nTotal: {loc_count} localizações estáticas, {dyn_count} localizações dinâmicas")
        
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migração Location System")
    parser.add_argument("--verify", action="store_true", help="Apenas verificar estrutura")
    args = parser.parse_args()
    
    if args.verify:
        verify_migration()
    else:
        run_migration()
        verify_migration()
