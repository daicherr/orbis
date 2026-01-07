import os
import sys
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

    print("\n" + "="*50)
    print("🏁 ESTRUTURA CRIADA COM SUCESSO!")
    print("="*50)
    print("Próximos Passos:")
    print("1. Instale o PostgreSQL na sua máquina.")
    print("2. Instale as dependências: pip install -r backend/requirements.txt")
    print("3. Use o DeepSearch com o prompt fornecido e preencha a pasta '/ruleset_source'.")

if __name__ == "__main__":
    main()