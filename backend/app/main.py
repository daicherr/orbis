from fastapi import FastAPI, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from contextlib import asynccontextmanager

from app.database.db_connection import engine
from app.database.init_db import seed_initial_npcs, ensure_pgvector_extension
from sqlmodel import SQLModel
from app.core.combat_engine import CombatEngine
from app.database.models.player import Player
from app.database.repositories.player_repo import PlayerRepository
from app.database.repositories.npc_repo import NpcRepository
from app.services.gemini_client import GeminiClient
from app.agents.narrator import Narrator
from app.agents.referee import Referee
from app.agents.director import Director
from app.agents.stylizer import Stylizer
from app.agents.scribe import Scribe
from app.agents.architect import Architect

# Armazenamento simples para as instâncias dos nossos serviços
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup na inicialização
    print("Iniciando a aplicação e os serviços...")
    
    # Garante pgvector e cria tabelas (se não existirem)
    await ensure_pgvector_extension()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Popula o banco de dados com NPCs iniciais
    await seed_initial_npcs()

    # Inicializar serviços
    try:
        gemini_client = GeminiClient()
        app_state["gemini_client"] = gemini_client
        app_state["narrator"] = Narrator(gemini_client=gemini_client, lore_files_path="./lore_library")
        app_state["referee"] = Referee(gemini_client=gemini_client)
        app_state["stylizer"] = Stylizer(gemini_client=gemini_client)
        app_state["scribe"] = Scribe(gemini_client=gemini_client)
        app_state["architect"] = Architect(gemini_client=gemini_client)
        print("Serviços de IA inicializados.")
    except ValueError as e:
        print(f"ERRO CRÍTICO: Falha ao inicializar o GeminiClient. Verifique a GEMINI_API_KEY. Detalhes: {e}")
        # Em um app real, poderíamos decidir parar a inicialização aqui.
    
    yield
    
    # Cleanup no desligamento
    print("Encerrando a aplicação...")
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

# --- Gestão de Dependências ---

async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

async def get_director(session: AsyncSession = Depends(get_session)) -> Director:
    player_repo = PlayerRepository(session)
    npc_repo = NpcRepository(session)
    director = Director(
        narrator=app_state["narrator"],
        referee=app_state["referee"],
        combat_engine=CombatEngine(),
        player_repo=player_repo,
        npc_repo=npc_repo,
        scribe=app_state["scribe"],
        architect=app_state["architect"]
    )
    return director

async def get_stylizer() -> Stylizer:
    return app_state["stylizer"]

# --- Endpoints da API ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Gem RPG Orbis API"}

@app.post("/player/create")
async def create_player(name: str, session: AsyncSession = Depends(get_session)) -> Player:
    player_repo = PlayerRepository(session)
    player = await player_repo.create(name=name)
    return player

@app.post("/game/turn")
async def game_turn(player_id: int, player_input: str, director: Director = Depends(get_director)):
    if "director" not in app_state:
        raise HTTPException(status_code=500, detail="Director service not initialized.")
        
    result = await director.process_player_turn(player_id=player_id, player_input=player_input)
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result.get("error"))
        
    return result

@app.post("/npc/{npc_id}/observe")
async def observe_npc(
    npc_id: int, 
    session: AsyncSession = Depends(get_session),
    stylizer: Stylizer = Depends(get_stylizer)
):
    npc_repo = NpcRepository(session)
    npc = await npc_repo.get_by_id(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")
        
    description = stylizer.generate_npc_description(npc)
    return {"description": description}
