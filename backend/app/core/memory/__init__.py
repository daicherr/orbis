"""
Memory System 2.0 - Sistema de Memória Hierárquico
GEM RPG ORBIS - Arquitetura Cognitiva

Este pacote implementa um sistema de memória de três camadas:
1. Episodic Memory - Eventos específicos com contexto temporal
2. Semantic Memory - Fatos extraídos e conhecimento geral
3. Procedural Memory - Padrões de comportamento detectados

A HierarchicalMemory orquestra as três stores e fornece
interface unificada para remember/recall.
"""

from app.core.memory.episodic import EpisodicMemory, EpisodicStore, TimeRange
from app.core.memory.semantic import SemanticFact, SemanticStore, FactType
from app.core.memory.procedural import BehaviorPattern, ProceduralStore, PatternType
from app.core.memory.memory_manager import HierarchicalMemory, MemoryBundle, GameEvent

__all__ = [
    # Episodic
    "EpisodicMemory",
    "EpisodicStore", 
    "TimeRange",
    # Semantic
    "SemanticFact",
    "SemanticStore",
    "FactType",
    # Procedural
    "BehaviorPattern",
    "ProceduralStore",
    "PatternType",
    # Manager
    "HierarchicalMemory",
    "MemoryBundle",
    "GameEvent",
]
