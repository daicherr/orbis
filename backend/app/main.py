from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from contextlib import asynccontextmanager

from app.database.db_connection import engine
from app.database.init_db import seed_initial_npcs, ensure_pgvector_extension
from sqlmodel import SQLModel
from app.core.combat_engine import CombatEngine
from app.core.constitution_effects import ConstitutionEffects
from app.database.models.player import Player
from app.database.models.memory import Memory
from app.database.repositories.player_repo import PlayerRepository
from app.database.repositories.npc_repo import NpcRepository
from app.database.repositories.hybrid_search import HybridSearchRepository
from app.database.repositories.gamelog_repo import GameLogRepository
from app.services.gemini_client import GeminiClient
from app.services.embedding_service import EmbeddingService
from app.agents.narrator import Narrator
from app.agents.referee import Referee
from app.agents.director import Director
from app.agents.stylizer import Stylizer
from app.agents.scribe import Scribe
from app.agents.architect import Architect
from app.agents.villains.profiler import Profiler
from app.core.world_sim import WorldSimulator
from sqlalchemy import text
from app.core.simulation.daily_tick import DailyTickSimulator
from app.services.quest_service import quest_service
from app.core.chronos import world_clock

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
        app_state["profiler"] = Profiler()
        
        # Inicializar WorldSimulator (coordena Strategist, Diplomat, GossipMonger)
        # Precisaremos passar os repositórios mais tarde nas chamadas
        app_state["world_simulator"] = WorldSimulator(gemini_client=gemini_client)
        print("Serviços de IA inicializados (incluindo WorldSimulator).")
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

async def get_session():
    async with AsyncSession(engine) as session:
        yield session

# Alias para compatibilidade com Sprint 6
get_async_session = get_session

async def get_director(session: AsyncSession = Depends(get_session)) -> Director:
    player_repo = PlayerRepository(session)
    npc_repo = NpcRepository(session)
    
    # Initialize GameLogRepository with EmbeddingService
    embedding_service = EmbeddingService(gemini_client=app_state["gemini_client"])
    gamelog_repo = GameLogRepository(session, embedding_service=embedding_service)
    
    # Initialize HybridSearchRepository (Memory)
    memory_repo = HybridSearchRepository(session)
    
    director = Director(
        narrator=app_state["narrator"],
        referee=app_state["referee"],
        combat_engine=CombatEngine(),
        player_repo=player_repo,
        npc_repo=npc_repo,
        scribe=app_state["scribe"],
        architect=app_state["architect"],
        profiler=app_state["profiler"],
        gamelog_repo=gamelog_repo,
        memory_repo=memory_repo
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

# [SPRINT 5.1] GET Player by ID (para CharacterSheet)
@app.get("/player/{player_id}", response_model=Player)
async def get_player(player_id: int, session: AsyncSession = Depends(get_session)):
    """
    Retorna os dados completos de um player (usado pelo CharacterSheet UI).
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    
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
async def simulation_tick(session: AsyncSession = Depends(get_session)):
    """
    Roda uma simulação completa do mundo:
    - Strategist move vilões hostis
    - Diplomat gerencia relações de facção
    - GossipMonger espalha rumores
    - DailyTickSimulator atualiza economia e clima
    """
    npc_repo = NpcRepository(session)
    player_repo = PlayerRepository(session)
    
    # WorldSimulator (Strategist, Diplomat, GossipMonger)
    world_sim = app_state.get("world_simulator")
    if world_sim:
        await world_sim.run_simulation_tick(npc_repo, player_repo)
    
    # DailyTickSimulator (Economia, Clima, Linhagem)
    daily_sim = DailyTickSimulator()
    await daily_sim.run_daily_simulation()
    
    return {"status": "ok", "message": "World simulation executed (villains, diplomacy, rumors, economy)"}

@app.get("/world/time")
async def get_world_time():
    """
    Retorna o tempo atual do mundo (Chronos)
    """
    from app.core.chronos import world_clock
    dt = world_clock.get_current_datetime()
    time_of_day = world_clock.get_time_of_day()
    season = world_clock.get_season()
    
    return {
        "day": dt.day,
        "month": dt.month,
        "year": dt.year,
        "hour": dt.hour,
        "minute": dt.minute,
        "time_of_day": time_of_day,
        "season": season,
        "timestamp": dt.isoformat()
    }

# --- Character Creation Endpoints (Session Zero) ---

from pydantic import BaseModel
from typing import List, Optional

class SessionZeroRequest(BaseModel):
    name: str
    constitution: str
    origin_location: str

class SessionZeroResponse(BaseModel):
    questions: List[str]

class CreateCharacterRequest(BaseModel):
    name: str
    appearance: Optional[str] = None
    constitution: str
    origin_location: str
    session_zero_answers: List[str]

@app.post("/character/session-zero", response_model=SessionZeroResponse)
async def generate_session_zero_questions(
    request: SessionZeroRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Gera 3-5 perguntas personalizadas baseadas no nome, constituição e origem do personagem.
    O Architect usa Gemini para criar perguntas contextuais.
    """
    architect = app_state.get("architect")
    if not architect:
        raise HTTPException(status_code=500, detail="Architect service not available")
    
    # Prompt para Gemini gerar perguntas
    prompt = f"""
Você é o Mestre de um RPG de cultivação chamado Códice Triluna.
Um novo jogador está criando seu personagem:
- Nome: {request.name}
- Constituição: {request.constitution}
- Local de Origem: {request.origin_location}

Gere EXATAMENTE 3 perguntas profundas e pessoais para entender a motivação e o passado desse personagem.
As perguntas devem ser específicas ao contexto (constituição e origem).

Formato: Retorne apenas as perguntas, uma por linha, sem numeração.
Exemplo:
Qual foi o momento que definiu seu destino na cultivação?
Que sacrifício você fez para obter seu poder atual?
Quem é a pessoa que você mais deseja proteger ou vingar?
"""
    
    try:
        # Usar Gemini para gerar perguntas (modelo flash para rapidez)
        response = await architect.gemini_client.generate_content_async(
            prompt=prompt,
            model_type="flash"
        )
        
        # Parse das perguntas
        questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
        
        # Garantir que temos exatamente 3 perguntas
        if len(questions) < 3:
            questions.extend([
                "Qual é o seu maior objetivo na cultivação?",
                "O que você mais teme perder?",
                "Como você enfrenta adversidades?"
            ])
        
        return SessionZeroResponse(questions=questions[:3])
    
    except Exception as e:
        # Fallback com perguntas genéricas
        return SessionZeroResponse(questions=[
            "Qual foi o momento que definiu seu destino na cultivação?",
            "Que sacrifício você fez para obter seu poder atual?",
            "Quem é a pessoa que você mais deseja proteger ou vingar?"
        ])

@app.post("/player/create-full", response_model=Player)
async def create_player_full(
    request: CreateCharacterRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Cria um player completo com todos os dados do Character Creation Wizard:
    - Nome, aparência, constituição, origem, e backstory gerada pelo Session Zero
    """
    architect = app_state.get("architect")
    if not architect:
        raise HTTPException(status_code=500, detail="Architect service not available")
    
    # Gerar backstory narrativa baseada nas respostas
    backstory_prompt = f"""
Você é o Mestre de um RPG de cultivação chamado Códice Triluna.
Um novo personagem foi criado com os seguintes detalhes:

Nome: {request.name}
Aparência: {request.appearance or 'Não especificada'}
Constituição: {request.constitution}
Local de Origem: {request.origin_location}

Respostas do Session Zero:
{chr(10).join(f'- {ans}' for ans in request.session_zero_answers)}

Crie um parágrafo narrativo (4-6 linhas) descrevendo a história de fundo desse personagem.
O texto deve ser literário, no estilo de xianxia/wuxia, e mencionar:
- Sua origem e constituição
- Motivações e conflitos internos
- Como ele chegou ao ponto atual da jornada

Escreva em português brasileiro, tom épico mas pessoal.
"""
    
    try:
        backstory = await architect.gemini_client.generate_content_async(
            prompt=backstory_prompt,
            model_type="flash"
        )
    except Exception as e:
        # Fallback com backstory genérica
        backstory = f"{request.name}, nascido em {request.origin_location}, carrega a marca de uma {request.constitution}. Sua jornada de cultivação está apenas começando, mas o destino já traçou seu caminho entre os mortais e imortais."
    
    # Criar player no banco de dados
    player_repo = PlayerRepository(session)
    player = await player_repo.create(
        name=request.name,
        appearance=request.appearance,
        constitution_type=request.constitution,
        origin_location=request.origin_location,
        backstory=backstory.strip(),
        constitution=request.constitution  # constitution é o nome da skill/body
    )
    
    # [SPRINT 5] Aplicar efeitos de constituição nos stats base
    ConstitutionEffects.apply_constitution_effects(player)
    await session.commit()
    await session.refresh(player)
    
    return player

# =====================================================
# [SPRINT 5] SHOP & ECONOMY ENDPOINTS
# =====================================================

from app.services.shop_manager import shop_manager
from pydantic import BaseModel

class GetPriceRequest(BaseModel):
    item_id: str
    item_category: str  # "pills", "materials", "services", etc.
    item_tier: int  # 1-9
    location: str = "neutral"
    modifiers: list[str] = []

class BuyItemRequest(BaseModel):
    player_id: int
    item_id: str
    item_category: str
    item_tier: int
    location: str = "neutral"
    modifiers: list[str] = []

class SellItemRequest(BaseModel):
    player_id: int
    item_id: str
    buy_price: float
    condition: float = 1.0  # 0.0 a 1.0

@app.post("/shop/price")
async def get_item_price(request: GetPriceRequest):
    """
    Retorna o preço de um item baseado em categoria, tier, localização e modificadores.
    """
    price_data = shop_manager.get_price(
        item_id=request.item_id,
        item_category=request.item_category,
        item_tier=request.item_tier,
        location=request.location,
        modifiers=request.modifiers
    )
    
    return {
        "success": True,
        "data": price_data,
        "formatted": shop_manager.format_price(price_data["final_price"])
    }

@app.post("/shop/buy")
async def buy_item(
    request: BuyItemRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Compra um item. Deduz ouro do jogador e adiciona item ao inventário.
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get(request.player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Calcular preço
    price_data = shop_manager.get_price(
        item_id=request.item_id,
        item_category=request.item_category,
        item_tier=request.item_tier,
        location=request.location,
        modifiers=request.modifiers
    )
    
    final_price = price_data["final_price"]
    
    # Verificar fundos
    if not shop_manager.can_afford(player.gold, final_price):
        raise HTTPException(
            status_code=400, 
            detail=f"Fundos insuficientes. Necessário: {final_price} gold, disponível: {player.gold} gold"
        )
    
    # Deduzir ouro
    player.gold -= final_price
    
    # Adicionar item ao inventário
    new_item = {
        "item_id": request.item_id,
        "category": request.item_category,
        "tier": request.item_tier,
        "quantity": 1,
        "buy_price": final_price
    }
    
    player.inventory.append(new_item)
    
    await session.commit()
    await session.refresh(player)
    
    return {
        "success": True,
        "message": f"Item '{request.item_id}' comprado por {shop_manager.format_price(final_price)}",
        "remaining_gold": player.gold,
        "item": new_item
    }

@app.post("/shop/sell")
async def sell_item(
    request: SellItemRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Vende um item do inventário. Adiciona ouro ao jogador e remove item.
    """
    player_repo = PlayerRepository(session)
    player = await player_repo.get(request.player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Buscar item no inventário
    item_index = None
    for i, inv_item in enumerate(player.inventory):
        if inv_item.get("item_id") == request.item_id:
            item_index = i
            break
    
    if item_index is None:
        raise HTTPException(status_code=404, detail=f"Item '{request.item_id}' not found in inventory")
    
    # Calcular preço de venda
    sell_price = shop_manager.calculate_sell_price(request.buy_price, request.condition)
    
    # Adicionar ouro
    player.gold += sell_price
    
    # Remover item do inventário
    removed_item = player.inventory.pop(item_index)
    
    await session.commit()
    await session.refresh(player)
    
    return {
        "success": True,
        "message": f"Item '{request.item_id}' vendido por {shop_manager.format_price(sell_price)}",
        "gold_earned": sell_price,
        "total_gold": player.gold,
        "removed_item": removed_item
    }

# ========== SPRINT 6: QUEST ENDPOINTS ==========

@app.post("/quest/generate")
async def generate_quest(player_id: int, session: AsyncSession = Depends(get_async_session)):
    """Gera uma nova quest para o player baseada em origin_location e tier."""
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player não encontrado")
    
    quest = quest_service.generate_quest(player)
    if not quest:
        raise HTTPException(status_code=400, detail="Não há quests disponíveis para seu tier/localização")
    
    quest_service.add_quest_to_player(player_id, quest)
    
    return {
        "success": True,
        "quest": quest,
        "message": f"🎯 Nova missão desbloqueada: {quest['title']}"
    }

@app.get("/quest/active/{player_id}")
async def get_active_quests(player_id: int):
    """Retorna todas as quests ativas de um player."""
    active_quests = quest_service.get_active_quests(player_id)
    
    # Verificar deadlines automaticamente
    quest_service.check_deadlines(player_id)
    
    return {
        "quests": active_quests,
        "count": len(active_quests)
    }

@app.post("/quest/complete")
async def complete_quest(
    player_id: int,
    quest_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Completa uma quest e aplica recompensas."""
    player_repo = PlayerRepository(session)
    player = await player_repo.get_by_id(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player não encontrado")
    
    active_quests = quest_service.get_active_quests(player_id)
    quest = next((q for q in active_quests if q["id"] == quest_id), None)
    
    if not quest:
        raise HTTPException(status_code=404, detail="Quest não encontrada")
    
    if quest["status"] != "completed":
        raise HTTPException(status_code=400, detail="Quest ainda não foi concluída")
    
    quest_service.complete_quest(player, quest)
    
    await session.commit()
    await session.refresh(player)
    
    return {
        "success": True,
        "message": f"✨ Quest '{quest['title']}' finalizada!",
        "rewards": {
            "xp": quest["reward_xp"],
            "gold": quest["reward_gold"],
            "items": quest.get("reward_items", [])
        },
        "player_xp": player.xp,
        "player_gold": player.gold
    }

@app.get("/game/current-turn")
async def get_current_turn():
    """Retorna o turno atual do mundo."""
    return {
        "current_turn": world_clock.get_current_turn(),
        "current_date": world_clock.get_current_date()
    }
