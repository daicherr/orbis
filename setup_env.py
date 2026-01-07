import os
import sys
import subprocess
from pathlib import Path

# --- DEFINIÇÃO DA ESTRUTURA ---
PROJECT_STRUCTURE = {
    "backend": {
        "app": {
            "agents": {
                "villains": ["strategist.py", "profiler.py", "__init__.py"],
                "social": ["gossip_monger.py", "diplomat.py", "__init__.py"],
                "__init__.py": None,
                "narrator.py": None,
                "referee.py": None,
                "stylizer.py": None,
                "scribe.py": None,
                "director.py": None
            },
            "core": {
                "simulation": ["daily_tick.py", "economy.py", "lineage.py", "ecology.py", "__init__.py"],
                "__init__.py": None,
                "combat_engine.py": None,
                "chronos.py": None,
                "skill_manager.py": None,
                "dice_roller.py": None,
                "world_sim.py": None
            },
            "database": {
                "models": ["player.py", "npc.py", "memory.py", "world_state.py", "logs.py", "quest.py", "__init__.py"],
                "repositories": ["player_repo.py", "npc_repo.py", "hybrid_search.py", "__init__.py"],
                "__init__.py": None,
                "db_connection.py": None,
                "init_db.py": None
            },
            "services": {
                "__init__.py": None,
                "gemini_client.py": None,
                "embedding_service.py": None
            },
            "main.py": None,
            "config.py": None
        },
        "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\nsqlmodel\nasyncpg\npgvector\ngoogle-generativeai\npython-dotenv\n"
    },
    "frontend": {
        "src": {
            "components": ["GameWindow.js", "DialogueInput.js", "CombatInterface.js", "PlayerHUD.js", "WorldClock.js", "InventoryGrid.js", "NpcInspector.js", "LoadingScreen.js"],
            "pages": ["index.js", "game.js"]
        },
        "package.json": "{\n  \"name\": \"gem-rpg-frontend\",\n  \"version\": \"1.0.0\"\n}",
        "tailwind.config.js": ""
    },
    "ruleset_source": {
        "mechanics": ["cultivation_ranks.json", "techniques.json", "items.json", "loot_tables.json", "godfiend_transformations.json"],
        "lore_manual": ["cultivation_rules.md", "world_physics.md", "locations_desc.md", "bestiary_lore.md"]
    },
    "lore_library": ["world_history.txt", "bestiary.txt", "villain_templates.txt", "initial_economy.json"]
}

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = base_path / name
        
        if isinstance(content, dict):
            # É uma pasta
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        elif isinstance(content, list):
            # É uma pasta com lista de arquivos
            os.makedirs(path, exist_ok=True)
            for file_name in content:
                file_path = path / file_name
                if not file_path.exists():
                    file_path.touch()
                    print(f"✅ Criado: {file_path}")
        else:
            # É um arquivo
            if content is not None:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                path.touch()
            print(f"✅ Criado: {path}")

def main():
    print("🚀 Iniciando Setup do GEM RPG ORBIS (God Mode)...")
    
    # 1. Verifica Python
    if sys.version_info < (3, 10):
        print("❌ Erro: Precisa de Python 3.10 ou superior.")
        return

    base_path = Path.cwd()
    create_structure(base_path, PROJECT_STRUCTURE)

    # 2. Criar .env apontando para o Postgres do Docker
    env_path = base_path / ".env"
    if not env_path.exists():
        env_content = (
            "# GEM RPG Orbis environment\n"
            "DATABASE_URL=postgresql+asyncpg://postgres:admin@localhost:5432/rpg_cultivo\n"
            "GEMINI_API_KEY=YOUR_GEMINI_API_KEY\n"
        )
        env_path.write_text(env_content, encoding="utf-8")
        print(f"✅ Criado: {env_path}")
    else:
        print(f"ℹ️ .env já existe em: {env_path}")

    # 3. Subir o banco com Docker (se Docker estiver instalado)
    compose_file = base_path / "docker-compose.yml"
    if compose_file.exists():
        print("➡️ Tentando subir o PostgreSQL com pgvector via Docker...")
        # Tenta 'docker compose', se falhar tenta 'docker-compose'
        cmd_variants = [
            ["docker", "compose", "up", "-d"],
            ["docker-compose", "up", "-d"],
        ]
        started = False
        for cmd in cmd_variants:
            try:
                subprocess.run(cmd, cwd=str(base_path), check=True)
                started = True
                break
            except Exception as e:
                continue
        if started:
            print("✅ Docker: serviço 'rpg_database' solicitado. Verifique com 'docker ps'.")
        else:
            print("⚠️ Não foi possível executar 'docker compose up -d'.\n   Execute manualmente no terminal dentro da pasta do projeto.")
    else:
        print("⚠️ docker-compose.yml não encontrado na raiz do projeto.")

    print("\n" + "="*50)
    print("🏁 SETUP CONCLUÍDO!")
    print("="*50)
    print("Próximos Passos:")
    print("1. Verifique o Docker: docker ps (deve aparecer 'rpg_database').")
    print("2. Instale dependências do backend: pip install -r backend/requirements.txt")
    print("3. Inicie o backend (FastAPI) e o frontend (Next.js).")
    print("4. Opcional: habilitar extensão pgvector via Docker:\n   docker exec -it rpg_database psql -U postgres -d rpg_cultivo -c 'CREATE EXTENSION IF NOT EXISTS vector;'")

if __name__ == "__main__":
    main()