from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from contextlib import asynccontextmanager

from app.database.db_connection import engine
from app.database.init_db import seed_initial_npcs, ensure_pgvector_extension
from sqlmodel import SQLModel
from app.core.combat_engine import CombatEngine
from app.database.models.player import Player
from app.database.models.memory import Memory
from app.database.repositories.player_repo import PlayerRepository
from app.database.repositories.npc_repo import NpcRepository
from app.database.repositories.hybrid_search import HybridSearchRepository
from app.services.gemini_client import GeminiClient
from app.agents.narrator import Narrator
from app.agents.referee import Referee
from app.agents.director import Director
from app.agents.stylizer import Stylizer
from app.agents.scribe import Scribe
from app.agents.architect import Architect
from sqlalchemy import text
from app.core.simulation.daily_tick import DailyTickSimulator

# Armazenamento simples para as instâncias dos nossos serviços
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup na inicialização
    print("Iniciando a aplicação e os serviços...")
    
    # Garante pgvector e cria tabelas (se não existirem) com retry
    for attempt in range(10):
        try:
            await ensure_pgvector_extension()
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            break
        except Exception as e:
            print(f"DB init tentativa {attempt+1}/10 falhou: {e}")
            await asyncio.sleep(1.5)
    
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

# --- CORS (permitir frontend local) ---
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

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

def get_hybrid_repo(session: AsyncSession) -> HybridSearchRepository:
    return HybridSearchRepository(session)

# --- Endpoints da API ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Gem RPG Orbis API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/db")
async def health_db():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}

@app.post("/player/create")
async def create_player(name: str, session: AsyncSession = Depends(get_session)) -> Player:
    player_repo = PlayerRepository(session)
    player = await player_repo.create(name=name)
    return player

@app.post("/game/turn")
async def game_turn(player_id: int, player_input: str, director: Director = Depends(get_director)):
    # `Director` é injetado por dependência e construído on-demand.
    # Se serviços base não estiverem prontos, a dependência levantará erro.
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

@app.post("/npc/{npc_id}/memory")
async def add_npc_memory(
    npc_id: int,
    content: str,
    session: AsyncSession = Depends(get_session),
):
    repo = HybridSearchRepository(session)
    mem = await repo.add_memory(npc_id=npc_id, content=content, embedding_dim=128)
    return {"id": mem.id, "npc_id": mem.npc_id, "content": mem.content}

@app.get("/npc/{npc_id}/memories")
async def search_npc_memories(
    npc_id: int,
    q: str,
    limit: int = 5,
    session: AsyncSession = Depends(get_session),
):
    repo = HybridSearchRepository(session)
    results = await repo.find_relevant_memories(npc_id=npc_id, query_text=q, limit=limit)
    return {"npc_id": npc_id, "query": q, "results": results}

@app.post("/simulation/tick")
async def simulation_tick():
    simulator = DailyTickSimulator()
    await simulator.run_daily_simulation()
    return {"status": "ok", "message": "Daily simulation executed"}
