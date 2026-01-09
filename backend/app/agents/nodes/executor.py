"""
Executor Node - Executa a ação planejada
GEM RPG ORBIS - LangGraph Architecture

O Executor é o "braço" que executa a ação decidida pelo Planner.
Usa as ferramentas de game_tools.py e o CombatEngine.

Responsabilidades:
1. Receber a PlannedAction do estado
2. Executar a ação apropriada
3. Calcular resultados mecânicos (dano, recursos, etc)
4. Retornar ActionResult

Princípio: Função PURA - sem side effects no banco.
Os side effects (save) são feitos DEPOIS da validação.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from app.agents.nodes.state import (
    AgentState,
    ActionIntent,
    ActionResult,
    PlannedAction
)


# ==================== EXECUTORS POR INTENT ====================

def _execute_attack(
    action: PlannedAction,
    player: Dict[str, Any],
    world: Dict[str, Any]
) -> ActionResult:
    """Executa um ataque."""
    target_name = action.target_name
    skill_name = action.skill_name or "basic_attack"
    
    # Encontrar alvo
    npcs = world.get("npcs_in_scene", [])
    target = None
    for npc in npcs:
        if npc.get("name") == target_name:
            target = npc
            break
    
    if not target:
        return ActionResult(
            success=False,
            message=f"Alvo '{target_name}' não encontrado na cena."
        )
    
    # Calcular dano (simplificado - o CombatEngine real será usado no Director)
    player_rank = player.get("cultivation_rank", 1)
    base_damage = 10 + (player_rank * 5)
    
    # Skill multiplier
    skill_multipliers = {
        "basic_attack": 1.0,
        "heavy_strike": 1.5,
        "power_slash": 1.8,
        "qi_blast": 2.0,
    }
    multiplier = skill_multipliers.get(skill_name, 1.0)
    
    # Roll de dano (d20 + base)
    roll = random.randint(1, 20)
    final_damage = int((base_damage + roll) * multiplier)
    
    # Verificar se matou
    target_hp = target.get("current_hp", 100)
    new_hp = target_hp - final_damage
    killed = new_hp <= 0
    
    # Contra-ataque (se não morreu e é hostil)
    damage_received = 0
    if not killed and target.get("is_hostile"):
        enemy_rank = target.get("rank", 1)
        counter_damage = 5 + (enemy_rank * 3) + random.randint(1, 10)
        damage_received = counter_damage
    
    # Construir mensagem
    if killed:
        message = f"Você usa {skill_name} em {target_name}, causando {final_damage} de dano! {target_name} foi derrotado!"
    else:
        message = f"Você usa {skill_name} em {target_name}, causando {final_damage} de dano! HP restante: {new_hp}"
        if damage_received > 0:
            message += f"\n{target_name} contra-atacou: -{damage_received} HP"
    
    # XP e loot se matou
    xp_gained = 0
    gold_changed = 0
    items_gained = []
    if killed:
        xp_gained = target.get("rank", 1) * 50
        gold_changed = random.randint(10, 50) * target.get("rank", 1)
        # Chance de drop
        if random.random() < 0.3:
            items_gained.append({
                "item_id": "healing_pill",
                "quantity": 1,
                "name": "Pílula de Cura"
            })
    
    return ActionResult(
        success=True,
        message=message,
        damage_dealt=final_damage,
        damage_received=damage_received,
        xp_gained=xp_gained,
        gold_changed=gold_changed,
        items_gained=items_gained,
        npc_killed=target_name if killed else None,
        player_died=player.get("current_hp", 100) - damage_received <= 0
    )


def _execute_talk(
    action: PlannedAction,
    player: Dict[str, Any],
    world: Dict[str, Any]
) -> ActionResult:
    """Executa uma interação social."""
    target_name = action.target_name
    spoken_words = action.spoken_words or "..."
    
    # Encontrar alvo
    npcs = world.get("npcs_in_scene", [])
    target = None
    for npc in npcs:
        if npc.get("name") == target_name:
            target = npc
            break
    
    if not target:
        if not target_name:
            return ActionResult(
                success=True,
                message=f"Você diz em voz alta: \"{spoken_words}\""
            )
        return ActionResult(
            success=False,
            message=f"Não há ninguém chamado '{target_name}' aqui."
        )
    
    if not target.get("can_speak", True):
        species = target.get("species", "criatura")
        return ActionResult(
            success=False,
            message=f"{target_name} é um(a) {species} e não pode falar."
        )
    
    # Resposta baseada no estado emocional
    emotional = target.get("emotional_state", "neutral")
    
    if emotional == "hostile":
        response = f"{target_name} rosna: 'Não tenho nada a dizer a você, verme!'"
    elif emotional == "friendly":
        response = f"{target_name} sorri: 'É bom ver você, amigo. O que posso fazer por você?'"
    elif emotional == "afraid":
        response = f"{target_name} recua nervosamente: 'P-por favor, não me machuque...'"
    else:
        response = f"{target_name} observa você com cautela antes de responder: 'O que você quer?'"
    
    return ActionResult(
        success=True,
        message=f"Você diz: \"{spoken_words}\"\n\n{response}"
    )


def _execute_move(
    action: PlannedAction,
    player: Dict[str, Any],
    world: Dict[str, Any]
) -> ActionResult:
    """Executa movimento para outro local."""
    destination = action.destination
    
    if not destination:
        return ActionResult(
            success=False,
            message="Você precisa especificar um destino."
        )
    
    # Verificar se destino é válido
    available_exits = world.get("available_exits", [])
    current_location = world.get("current_location", "Unknown")
    
    # Busca flexível
    matched_exit = None
    for exit in available_exits:
        if exit.lower() == destination.lower() or destination.lower() in exit.lower():
            matched_exit = exit
            break
    
    if matched_exit:
        return ActionResult(
            success=True,
            message=f"Você viaja de {current_location} para {matched_exit}.",
            location_changed=True,
            new_location=matched_exit
        )
    
    # Destino não encontrado - pode ser criado pelo sistema
    return ActionResult(
        success=False,
        message=f"Você não conhece o caminho para '{destination}'. Saídas conhecidas: {', '.join(available_exits) if available_exits else 'nenhuma'}."
    )


def _execute_meditate(
    action: PlannedAction,
    player: Dict[str, Any],
    world: Dict[str, Any]
) -> ActionResult:
    """Executa meditação/cultivo."""
    player_rank = player.get("cultivation_rank", 1)
    qi_density = world.get("qi_density", 1.0)
    
    # Cálculo de ganho
    base_qi = 10 * player_rank
    qi_gained = int(base_qi * qi_density)
    
    current_qi = player.get("yuan_qi", 0)
    max_qi = player.get("max_yuan_qi", 100)
    
    # Também recupera um pouco de chi
    chi_gained = int(qi_gained * 0.5)
    
    return ActionResult(
        success=True,
        message=f"Você entra em meditação profunda. O Qi do mundo flui através de seus meridianos. (+{qi_gained} Yuan Qi, +{chi_gained} Shadow Chi)",
        resources_changed={
            "yuan_qi": qi_gained,
            "shadow_chi": chi_gained
        }
    )


def _execute_observe(
    action: PlannedAction,
    player: Dict[str, Any],
    world: Dict[str, Any]
) -> ActionResult:
    """Executa observação do ambiente."""
    location = world.get("current_location", "Unknown")
    npcs = world.get("npcs_in_scene", [])
    exits = world.get("available_exits", [])
    weather = world.get("weather", "clear")
    
    # Descrição dos NPCs
    npc_desc = []
    for npc in npcs:
        species = npc.get("species", "humano")
        emotional = npc.get("emotional_state", "neutral")
        npc_desc.append(f"- {npc.get('name')}: {species}, parece {emotional}")
    
    npcs_text = "\n".join(npc_desc) if npc_desc else "O local parece vazio."
    exits_text = ", ".join(exits) if exits else "Nenhuma saída visível."
    
    message = f"""Você observa atentamente {location}.

PRESENÇAS:
{npcs_text}

SAÍDAS: {exits_text}

O clima está {weather}."""
    
    return ActionResult(
        success=True,
        message=message
    )


def _execute_rest(
    action: PlannedAction,
    player: Dict[str, Any],
    world: Dict[str, Any]
) -> ActionResult:
    """Executa descanso."""
    current_hp = player.get("current_hp", 100)
    max_hp = player.get("max_hp", 100)
    
    if current_hp >= max_hp:
        return ActionResult(
            success=True,
            message="Você já está completamente recuperado."
        )
    
    # Recupera 20% do HP máximo
    heal_amount = int(max_hp * 0.2)
    new_hp = min(max_hp, current_hp + heal_amount)
    actual_heal = new_hp - current_hp
    
    return ActionResult(
        success=True,
        message=f"Você descansa por um momento, recuperando suas forças. (+{actual_heal} HP)",
        resources_changed={
            "hp": actual_heal
        }
    )


def _execute_use_item(
    action: PlannedAction,
    player: Dict[str, Any],
    world: Dict[str, Any]
) -> ActionResult:
    """Executa uso de item."""
    item_name = action.item_name
    
    if not item_name:
        return ActionResult(
            success=False,
            message="Você precisa especificar qual item usar."
        )
    
    # Verificar inventário
    inventory = player.get("inventory", [])
    found_item = None
    for item in inventory:
        item_id = item.get("item_id", item.get("name", ""))
        if item_id.lower() == item_name.lower() or item_name.lower() in item_id.lower():
            found_item = item
            break
    
    if not found_item:
        return ActionResult(
            success=False,
            message=f"Você não possui '{item_name}' no inventário."
        )
    
    # Efeitos por tipo de item
    item_id = found_item.get("item_id", found_item.get("name", ""))
    
    if "healing" in item_id.lower() or "cura" in item_id.lower():
        heal = 50
        return ActionResult(
            success=True,
            message=f"Você usa {item_id}. (+{heal} HP)",
            resources_changed={"hp": heal},
            items_lost=[item_id]
        )
    
    if "qi" in item_id.lower():
        qi_restore = 50
        return ActionResult(
            success=True,
            message=f"Você usa {item_id}. (+{qi_restore} Yuan Qi)",
            resources_changed={"yuan_qi": qi_restore},
            items_lost=[item_id]
        )
    
    return ActionResult(
        success=True,
        message=f"Você usa {item_id}.",
        items_lost=[item_id]
    )


def _execute_flee(
    action: PlannedAction,
    player: Dict[str, Any],
    world: Dict[str, Any]
) -> ActionResult:
    """Tenta fugir do local atual."""
    current_location = world.get("location", "Desconhecido")
    exits = world.get("exits", [])
    
    # Verificar se há saídas
    if not exits:
        # Tentar criar uma rota de fuga padrão
        possible_escapes = ["trilha", "caminho", "estrada", "floresta"]
        escape_route = random.choice(possible_escapes)
        new_location = f"{escape_route.title()} próximo a {current_location}"
    else:
        escape_route = random.choice(exits)
        new_location = escape_route
    
    # Chance de fuga baseada em velocidade
    player_speed = player.get("speed", 10)
    npcs = world.get("npcs_in_scene", [])
    
    # Verificar se há inimigos hostis
    hostile_npcs = [npc for npc in npcs if npc.get("is_hostile") or npc.get("aggression", 0) > 5]
    
    if hostile_npcs:
        # Rolar fuga
        escape_roll = random.randint(1, 20) + (player_speed // 5)
        enemy_pursuit = max([npc.get("speed", 10) for npc in hostile_npcs])
        
        if escape_roll >= 10 + (enemy_pursuit // 5):
            return ActionResult(
                success=True,
                message=f"Você conseguiu escapar para {new_location}!",
                location_changed=True,
                new_location=new_location
            )
        else:
            # Falhou na fuga, leva dano ao fugir
            damage = random.randint(5, 15)
            return ActionResult(
                success=False,
                message=f"Você tentou fugir, mas foi bloqueado! Recebeu {damage} de dano ao tentar escapar.",
                damage_received=damage
            )
    else:
        # Sem inimigos, fuga automática
        return ActionResult(
            success=True,
            message=f"Você se afasta calmamente para {new_location}.",
            location_changed=True,
            new_location=new_location
        )


def _execute_trade(
    action: PlannedAction,
    player: Dict[str, Any],
    world: Dict[str, Any]
) -> ActionResult:
    """Executa interação de comércio."""
    target_name = action.target_name
    
    npcs = world.get("npcs_in_scene", [])
    target = None
    for npc in npcs:
        if npc.get("name") == target_name:
            target = npc
            break
    
    if not target:
        return ActionResult(
            success=False,
            message="Não há comerciantes aqui."
        )
    
    # Verificar se é comerciante
    traits = target.get("personality_traits", [])
    is_merchant = "merchant" in traits or "comerciante" in traits
    
    if not is_merchant and not target.get("can_speak"):
        return ActionResult(
            success=False,
            message=f"{target_name} não parece interessado em negociar."
        )
    
    return ActionResult(
        success=True,
        message=f"{target_name} mostra suas mercadorias. 'O que você deseja comprar ou vender?'"
    )


# ==================== MAIN EXECUTOR ====================

async def executor_node(state: AgentState, **dependencies) -> Dict[str, Any]:
    """
    Node do Executor - executa a ação planejada.
    
    Args:
        state: Estado atual do agente
        **dependencies: Dependências (combat_engine, etc)
        
    Returns:
        Atualizações parciais do estado
    """
    planned_action_dict = state.get("planned_action", {})
    player = state.get("player", {})
    world = state.get("world", {})
    
    if not planned_action_dict:
        return {
            "action_result": ActionResult(
                success=False,
                message="Nenhuma ação planejada."
            ).to_dict(),
            "current_node": "executor",
            "next_node": "validator",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Reconstruir PlannedAction
    intent_str = planned_action_dict.get("intent", "unknown")
    try:
        intent = ActionIntent(intent_str)
    except ValueError:
        intent = ActionIntent.UNKNOWN
    
    action = PlannedAction(
        intent=intent,
        target_name=planned_action_dict.get("target_name"),
        skill_name=planned_action_dict.get("skill_name"),
        destination=planned_action_dict.get("destination"),
        spoken_words=planned_action_dict.get("spoken_words"),
        item_name=planned_action_dict.get("item_name"),
        reasoning=planned_action_dict.get("reasoning", ""),
        confidence=planned_action_dict.get("confidence", 0.7)
    )
    
    print(f"[EXECUTOR] Executando: {action.intent.value}")
    
    # Dispatch por intent
    executors = {
        ActionIntent.ATTACK: _execute_attack,
        ActionIntent.USE_SKILL: _execute_attack,  # Usa mesmo executor
        ActionIntent.TALK: _execute_talk,
        ActionIntent.PERSUADE: _execute_talk,
        ActionIntent.INTIMIDATE: _execute_talk,
        ActionIntent.MOVE: _execute_move,
        ActionIntent.EXPLORE: _execute_move,
        ActionIntent.FLEE: _execute_flee,
        ActionIntent.MEDITATE: _execute_meditate,
        ActionIntent.CULTIVATE: _execute_meditate,
        ActionIntent.TRAIN: _execute_meditate,
        ActionIntent.OBSERVE: _execute_observe,
        ActionIntent.SEARCH: _execute_observe,
        ActionIntent.REST: _execute_rest,
        ActionIntent.WAIT: _execute_rest,
        ActionIntent.USE_ITEM: _execute_use_item,
        ActionIntent.TRADE: _execute_trade,
    }
    
    executor_fn = executors.get(action.intent)
    
    if executor_fn:
        result = executor_fn(action, player, world)
    else:
        result = ActionResult(
            success=False,
            message=f"Ação '{action.intent.value}' não reconhecida."
        )
    
    status_icon = "[OK]" if result.success else "[FAIL]"
    print(f"[EXECUTOR] Resultado: {status_icon} - {result.message[:50]}...")
    
    return {
        "action_result": result.to_dict(),
        "current_node": "executor",
        "next_node": "validator",
        "timestamp": datetime.utcnow().isoformat()
    }
