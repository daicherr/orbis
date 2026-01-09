"""
Validator Node - Valida resultado e decide retry/continuar
GEM RPG ORBIS - LangGraph Architecture

O Validator é o "juiz" que verifica se a ação foi válida.
Se não for, manda de volta pro Planner com o motivo.

Responsabilidades:
1. Verificar se a ação teve sucesso
2. Validar regras de jogo (ex: não pode atacar fantasma com espada)
3. Decidir: RETRY (volta pro Planner) ou CONTINUE (vai pro Narrator)
4. Controlar limite de tentativas

Este é o NÓ CRÍTICO que implementa o LOOP do grafo.
"""

from typing import Dict, Any
from datetime import datetime

from app.agents.nodes.state import (
    AgentState,
    ActionIntent,
    ActionResult,
    ValidationStatus,
    ValidationResult
)


# ==================== REGRAS DE VALIDAÇÃO ====================

def _validate_attack(action_result: Dict[str, Any], planned_action: Dict[str, Any], world: Dict[str, Any]) -> ValidationResult:
    """Valida uma ação de ataque."""
    
    # Se já falhou no executor, validar o motivo
    if not action_result.get("success"):
        target_name = planned_action.get("target_name")
        npcs = world.get("npcs_in_scene", [])
        
        # Verificar se alvo existe
        target = None
        for npc in npcs:
            if npc.get("name") == target_name:
                target = npc
                break
        
        if not target:
            # Alvo não existe - sugerir alvos válidos
            hostile_npcs = [n.get("name") for n in npcs if n.get("is_hostile")]
            if hostile_npcs:
                suggestion = f"Tente atacar: {', '.join(hostile_npcs)}"
            else:
                suggestion = "Não há alvos hostis na cena. Tente observar ou mover-se."
            
            return ValidationResult(
                status=ValidationStatus.NEEDS_RETRY,
                is_valid=False,
                error_message=f"Alvo '{target_name}' não encontrado.",
                retry_reason="Alvo inválido",
                suggested_alternative=suggestion
            )
        
        # Verificar regras especiais (exemplo: fantasmas)
        species = target.get("species", "human")
        if species == "ghost" or species == "spirit":
            skill = planned_action.get("skill_name", "basic_attack")
            # Ataques físicos não funcionam em fantasmas
            physical_skills = ["basic_attack", "heavy_strike", "power_slash"]
            if skill in physical_skills:
                return ValidationResult(
                    status=ValidationStatus.NEEDS_RETRY,
                    is_valid=False,
                    error_message=f"Ataques físicos não afetam {target_name} (espírito)!",
                    retry_reason="Imunidade a dano físico",
                    suggested_alternative="Use uma técnica de Qi ou magia."
                )
    
    # Se o jogador morreu, é válido mas com consequência
    if action_result.get("player_died"):
        return ValidationResult(
            status=ValidationStatus.VALID,
            is_valid=True,
            error_message="Você foi derrotado!"
        )
    
    return ValidationResult(
        status=ValidationStatus.VALID,
        is_valid=True
    )


def _validate_move(action_result: Dict[str, Any], planned_action: Dict[str, Any], world: Dict[str, Any]) -> ValidationResult:
    """Valida uma ação de movimento."""
    
    if not action_result.get("success"):
        destination = planned_action.get("destination")
        exits = world.get("available_exits", [])
        
        return ValidationResult(
            status=ValidationStatus.NEEDS_RETRY,
            is_valid=False,
            error_message=f"Não é possível ir para '{destination}'.",
            retry_reason="Destino inválido",
            suggested_alternative=f"Destinos disponíveis: {', '.join(exits) if exits else 'explore para descobrir'}"
        )
    
    return ValidationResult(
        status=ValidationStatus.VALID,
        is_valid=True
    )


def _validate_talk(action_result: Dict[str, Any], planned_action: Dict[str, Any], world: Dict[str, Any]) -> ValidationResult:
    """Valida uma ação de diálogo."""
    
    if not action_result.get("success"):
        target_name = planned_action.get("target_name")
        npcs = world.get("npcs_in_scene", [])
        
        # Verificar se há NPCs que podem falar
        talkable = [n.get("name") for n in npcs if n.get("can_speak", True)]
        
        if talkable:
            suggestion = f"Você pode conversar com: {', '.join(talkable)}"
        else:
            suggestion = "Não há ninguém para conversar aqui."
        
        return ValidationResult(
            status=ValidationStatus.NEEDS_RETRY,
            is_valid=False,
            error_message=action_result.get("message", "Falha na comunicação."),
            retry_reason="Alvo não pode falar",
            suggested_alternative=suggestion
        )
    
    return ValidationResult(
        status=ValidationStatus.VALID,
        is_valid=True
    )


def _validate_use_item(action_result: Dict[str, Any], planned_action: Dict[str, Any], player: Dict[str, Any]) -> ValidationResult:
    """Valida uso de item."""
    
    if not action_result.get("success"):
        item_name = planned_action.get("item_name")
        inventory = player.get("inventory", [])
        
        # Listar itens disponíveis
        item_names = [i.get("item_id", i.get("name", "?")) for i in inventory[:5]]
        
        if item_names:
            suggestion = f"Itens no inventário: {', '.join(item_names)}"
        else:
            suggestion = "Seu inventário está vazio."
        
        return ValidationResult(
            status=ValidationStatus.NEEDS_RETRY,
            is_valid=False,
            error_message=f"Item '{item_name}' não encontrado.",
            retry_reason="Item não existe",
            suggested_alternative=suggestion
        )
    
    return ValidationResult(
        status=ValidationStatus.VALID,
        is_valid=True
    )


def _validate_generic(action_result: Dict[str, Any]) -> ValidationResult:
    """Validação genérica para ações sem regras especiais."""
    
    if action_result.get("success"):
        return ValidationResult(
            status=ValidationStatus.VALID,
            is_valid=True
        )
    
    return ValidationResult(
        status=ValidationStatus.INVALID,
        is_valid=False,
        error_message=action_result.get("message", "Ação falhou.")
    )


# ==================== MAIN VALIDATOR ====================

async def validator_node(state: AgentState) -> Dict[str, Any]:
    """
    Node do Validator - valida resultado e decide próximo passo.
    
    Este é o nó que implementa o LOOP condicional:
    - Se válido → vai para narrator
    - Se inválido e tentativas < max → volta para planner
    - Se inválido e tentativas >= max → vai para narrator com erro
    
    Args:
        state: Estado atual do agente
        
    Returns:
        Atualizações parciais do estado incluindo next_node
    """
    action_result = state.get("action_result", {})
    planned_action = state.get("planned_action", {})
    player = state.get("player", {})
    world = state.get("world", {})
    
    current_attempts = state.get("validation_attempts", 0)
    max_attempts = state.get("max_validation_attempts", 3)
    
    print(f"[VALIDATOR] Validando ação (tentativa {current_attempts + 1}/{max_attempts})")
    
    # Dispatch por intent
    intent_str = planned_action.get("intent", "unknown")
    
    if intent_str in ["attack", "use_skill"]:
        validation = _validate_attack(action_result, planned_action, world)
    elif intent_str in ["move", "explore"]:
        validation = _validate_move(action_result, planned_action, world)
    elif intent_str in ["talk", "persuade", "intimidate"]:
        validation = _validate_talk(action_result, planned_action, world)
    elif intent_str == "use_item":
        validation = _validate_use_item(action_result, planned_action, player)
    else:
        validation = _validate_generic(action_result)
    
    print(f"[VALIDATOR] Status: {validation.status.value}")
    
    # Decidir próximo nó
    if validation.is_valid:
        next_node = "narrator"
        new_attempts = current_attempts
    elif validation.status == ValidationStatus.NEEDS_RETRY and current_attempts < max_attempts - 1:
        # Pode tentar de novo
        next_node = "planner"
        new_attempts = current_attempts + 1
        print(f"[VALIDATOR] Retry! Motivo: {validation.retry_reason}")
    else:
        # Máximo de tentativas ou erro não-recuperável
        next_node = "narrator"
        new_attempts = current_attempts
        # Marcar como inválido para o narrator saber
        if not validation.is_valid:
            validation.error_message = validation.error_message or "Ação não pôde ser completada."
        print(f"[VALIDATOR] Máximo de tentativas atingido ou erro fatal.")
    
    return {
        "validation": validation.to_dict(),
        "validation_attempts": new_attempts,
        "current_node": "validator",
        "next_node": next_node,
        "timestamp": datetime.utcnow().isoformat()
    }


def should_retry(state: AgentState) -> str:
    """
    Função de roteamento condicional para LangGraph.
    Retorna o nome do próximo nó baseado no estado.
    
    Uso no grafo:
        graph.add_conditional_edges(
            "validator",
            should_retry,
            {"planner": "planner", "narrator": "narrator"}
        )
    """
    next_node = state.get("next_node", "narrator")
    
    # Garantir que é um dos valores válidos
    if next_node == "planner":
        return "planner"
    return "narrator"
