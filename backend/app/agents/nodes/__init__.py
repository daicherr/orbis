"""
GEM RPG ORBIS - LangGraph Nodes
Nós do grafo de agentes

Cada nó é uma função Python pura que:
1. Recebe o AgentState
2. Processa
3. Retorna atualizações parciais do estado

Princípio: Sem mágica, sem black boxes.
"""

from app.agents.nodes.state import AgentState, PlayerContext, WorldContext, ActionResult
from app.agents.nodes.planner import planner_node
from app.agents.nodes.executor import executor_node
from app.agents.nodes.validator import validator_node
from app.agents.nodes.narrator import narrator_node

__all__ = [
    # State
    "AgentState",
    "PlayerContext",
    "WorldContext",
    "ActionResult",
    
    # Nodes
    "planner_node",
    "executor_node",
    "validator_node",
    "narrator_node",
]
