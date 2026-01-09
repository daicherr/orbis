"""
GEM RPG ORBIS - Agents Module
Arquitetura LangGraph de Agentes IA

Este módulo contém o sistema de agentes baseado em LangGraph:

CORE:
- GameGraph: Grafo principal com checkpointer PostgreSQL
- SimpleGameGraph: Versão sem persistência para testes

NODES:
- planner_node: Interpreta input e decide ação
- executor_node: Executa a ação via tools
- validator_node: Valida resultado e decide retry
- narrator_node: Gera narrativa literária

STATE:
- AgentState: Estado central do grafo (TypedDict)
- PlayerContext, WorldContext: Contextos estruturados
- ActionResult, PlannedAction: Resultados e ações

LEGACY (em archived/):
- react_agent.py: ReAct manual (arquivado)
- cognitive_*.py: Agentes cognitivos (arquivados)

FERRAMENTAS:
- game_tools.py: Ferramentas do jogo (mantido)
"""

# ============================================================
# LangGraph v2 Architecture
# ============================================================

# Graph Core
from app.agents.graph_core import GameGraph, SimpleGameGraph

# Nodes (Pure Functions)
from app.agents.nodes.planner import planner_node
from app.agents.nodes.executor import executor_node
from app.agents.nodes.validator import validator_node, should_retry
from app.agents.nodes.narrator import narrator_node

# State
from app.agents.nodes.state import (
    AgentState,
    PlayerContext,
    WorldContext,
    NPCContext,
    PlannedAction,
    ActionResult,
    ValidationResult,
    ActionIntent,
    ValidationStatus,
    create_initial_state,
    player_from_db,
    npc_from_db,
    world_from_context
)

# ============================================================
# Game Tools (Shared between LangGraph and Legacy)
# ============================================================
from app.agents.game_tools import (
    Tool,
    search_lore,
    get_cultivation_ranks,
    roll_dice,
    calculate_damage,
    get_market_prices,
    get_travel_options,
    get_knowledge_tools,
    get_mechanics_tools,
    get_economy_tools,
    get_navigation_tools,
    get_all_game_tools
)

# ============================================================
# Legacy Agents (compatibilidade - ainda em uso por endpoints antigos)
# ============================================================
from app.agents.narrator import Narrator
from app.agents.director import Director
from app.agents.architect import Architect
from app.agents.scribe import Scribe
from app.agents.quest_generator import QuestGenerator

# Villain Agents
from app.agents.villains.profiler import Profiler


__all__ = [
    # === LangGraph Core (v2) ===
    "GameGraph",
    "SimpleGameGraph",
    
    # === State Types ===
    "AgentState",
    "PlayerContext",
    "WorldContext",
    "NPCContext",
    "PlannedAction",
    "ActionResult",
    "ValidationResult",
    "ActionIntent",
    "ValidationStatus",
    "create_initial_state",
    "player_from_db",
    "npc_from_db",
    "world_from_context",
    
    # === Graph Nodes ===
    "planner_node",
    "executor_node",
    "validator_node",
    "should_retry",
    "narrator_node",
    
    # === Game Tools ===
    "Tool",
    "search_lore",
    "get_cultivation_ranks",
    "roll_dice",
    "calculate_damage",
    "get_market_prices",
    "get_travel_options",
    "get_knowledge_tools",
    "get_mechanics_tools",
    "get_economy_tools",
    "get_navigation_tools",
    "get_all_game_tools",
    
    # === Legacy (compatibilidade) ===
    "Narrator",
    "Director",
    "Architect",
    "Scribe",
    "QuestGenerator",
    
    # === Villains ===
    "Profiler",
]
