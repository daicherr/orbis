"""
Planner Node - Decide a próxima ação
GEM RPG ORBIS - LangGraph Architecture

O Planner é o "cérebro" que interpreta o input do jogador
e decide qual ação executar.

Responsabilidades:
1. Analisar o input do usuário
2. Considerar o contexto (player, world, histórico)
3. Decidir a intenção (attack, talk, move, etc)
4. Identificar alvos e parâmetros
5. Retornar PlannedAction

Princípio: Função PURA - recebe estado, retorna atualizações.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.agents.nodes.state import (
    AgentState,
    ActionIntent,
    PlannedAction,
    ValidationStatus
)


# ==================== PROMPTS ====================

PLANNER_SYSTEM_PROMPT = """Você é o PLANNER de um RPG de Cultivo estilo Wuxia/Xianxia.

Seu trabalho é INTERPRETAR o que o jogador quer fazer e retornar uma ação estruturada.

REGRAS DE INTERPRETAÇÃO:

1. **COMBATE** (attack, use_skill):
   - Palavras-chave: atacar, lutar, golpear, bater, usar técnica
   - Requer: target_name (NPC hostil na cena)
   - Opcional: skill_name (ou usa basic_attack)

2. **SOCIAL** (talk, persuade, intimidate, trade):
   - Palavras-chave: falar, perguntar, negociar, ameaçar, comprar, vender
   - Requer: target_name (NPC que pode falar)
   - Opcional: spoken_words (o que dizer)

3. **MOVIMENTO** (move, explore):
   - Palavras-chave: ir, andar, viajar, explorar, entrar, sair
   - Requer: destination (local válido ou direção)

4. **CULTIVO** (meditate, cultivate, train):
   - Palavras-chave: meditar, cultivar, treinar, absorver
   - Não requer alvo

5. **ITENS** (use_item, equip, pick_up, drop):
   - Palavras-chave: usar, equipar, pegar, largar, dropar
   - Requer: item_name

6. **OBSERVAÇÃO** (observe, search, rest, wait):
   - Palavras-chave: olhar, observar, examinar, descansar, esperar

RETORNE JSON com:
{
    "intent": "attack|talk|move|meditate|observe|use_item|...",
    "target_name": "Nome do NPC ou null",
    "skill_name": "Nome da skill ou null",
    "destination": "Nome do local ou null",
    "spoken_words": "O que o jogador disse ou null",
    "item_name": "Nome do item ou null",
    "reasoning": "Seu raciocínio curto",
    "confidence": 0.0-1.0
}

REGRAS:
- Se não encontrar alvo válido na cena, use null e confidence baixa
- Se ação for ambígua, escolha a mais provável
- NUNCA invente NPCs que não estão na cena
- basic_attack é sempre válido se nenhuma skill for especificada"""


def _build_planner_prompt(state: AgentState) -> str:
    """Constrói o prompt completo para o Planner."""
    user_input = state.get("user_input", "")
    player = state.get("player", {})
    world = state.get("world", {})
    validation = state.get("validation", {})
    
    # NPCs na cena
    npcs = world.get("npcs_in_scene", [])
    npc_list = []
    for npc in npcs:
        hostile = "hostil" if npc.get("is_hostile") else "amigável" if npc.get("can_speak") else "neutro"
        npc_list.append(f"- {npc.get('name')}: {npc.get('species', 'human')}, {hostile}")
    
    npcs_text = "\n".join(npc_list) if npc_list else "Nenhum NPC na cena."
    
    # Skills do jogador
    skills = player.get("learned_skills", [])
    skills_text = ", ".join(skills) if skills else "Nenhuma"
    
    # Se é retry, incluir motivo da falha
    retry_context = ""
    if validation and validation.get("status") == ValidationStatus.NEEDS_RETRY.value:
        retry_context = f"""
⚠️ ATENÇÃO: A ação anterior FALHOU. Motivo: {validation.get('retry_reason', 'desconhecido')}
Sugestão: {validation.get('suggested_alternative', 'tente outra abordagem')}

Você DEVE escolher uma ação DIFERENTE que seja válida.
"""
    
    prompt = f"""{PLANNER_SYSTEM_PROMPT}

═══════════════════════════════════════════════════════════════════
CONTEXTO ATUAL
═══════════════════════════════════════════════════════════════════

JOGADOR: {player.get('name', 'Desconhecido')}
- Tier: {player.get('cultivation_rank', 1)}
- HP: {player.get('current_hp', 100)}/{player.get('max_hp', 100)}
- Localização: {world.get('current_location', 'Desconhecido')}
- Skills: {skills_text}, basic_attack

NPCs NA CENA:
{npcs_text}

SAÍDAS DISPONÍVEIS: {', '.join(world.get('available_exits', ['nenhuma conhecida']))}

{retry_context}

═══════════════════════════════════════════════════════════════════
INPUT DO JOGADOR
═══════════════════════════════════════════════════════════════════

"{user_input}"

═══════════════════════════════════════════════════════════════════
RETORNE O JSON DA AÇÃO
═══════════════════════════════════════════════════════════════════
"""
    return prompt


def _parse_planner_response(response: str) -> PlannedAction:
    """Parseia a resposta do LLM em PlannedAction."""
    import json
    import re
    
    # Tentar extrair JSON da resposta
    try:
        # Primeiro tenta parse direto
        data = json.loads(response)
    except json.JSONDecodeError:
        # Tenta encontrar JSON no texto
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
            except:
                data = {}
        else:
            data = {}
    
    # Mapear intent
    intent_str = data.get("intent", "unknown").lower()
    intent_map = {
        "attack": ActionIntent.ATTACK,
        "defend": ActionIntent.DEFEND,
        "flee": ActionIntent.FLEE,
        "use_skill": ActionIntent.USE_SKILL,
        "talk": ActionIntent.TALK,
        "speak": ActionIntent.TALK,
        "persuade": ActionIntent.PERSUADE,
        "intimidate": ActionIntent.INTIMIDATE,
        "trade": ActionIntent.TRADE,
        "move": ActionIntent.MOVE,
        "explore": ActionIntent.EXPLORE,
        "search": ActionIntent.SEARCH,
        "observe": ActionIntent.OBSERVE,
        "rest": ActionIntent.REST,
        "meditate": ActionIntent.MEDITATE,
        "cultivate": ActionIntent.CULTIVATE,
        "train": ActionIntent.TRAIN,
        "use_item": ActionIntent.USE_ITEM,
        "equip": ActionIntent.EQUIP,
        "pick_up": ActionIntent.PICK_UP,
        "drop": ActionIntent.DROP,
        "wait": ActionIntent.WAIT,
    }
    
    intent = intent_map.get(intent_str, ActionIntent.UNKNOWN)
    
    return PlannedAction(
        intent=intent,
        target_name=data.get("target_name"),
        skill_name=data.get("skill_name"),
        destination=data.get("destination"),
        spoken_words=data.get("spoken_words"),
        item_name=data.get("item_name"),
        reasoning=data.get("reasoning", ""),
        confidence=float(data.get("confidence", 0.7))
    )


# ==================== NODE FUNCTION ====================

async def planner_node(state: AgentState, gemini_client) -> Dict[str, Any]:
    """
    Node do Planner - interpreta input e planeja ação.
    
    Args:
        state: Estado atual do agente
        gemini_client: Cliente Gemini para LLM
        
    Returns:
        Atualizações parciais do estado
    """
    print(f"[PLANNER] Analisando input: '{state.get('user_input', '')[:50]}...'")
    
    # Construir prompt
    prompt = _build_planner_prompt(state)
    
    # Chamar LLM
    try:
        response = gemini_client.generate_json(prompt, task="combat")
        
        if isinstance(response, dict):
            # Resposta já é dict
            planned = PlannedAction(
                intent=ActionIntent(response.get("intent", "unknown")),
                target_name=response.get("target_name"),
                skill_name=response.get("skill_name"),
                destination=response.get("destination"),
                spoken_words=response.get("spoken_words"),
                item_name=response.get("item_name"),
                reasoning=response.get("reasoning", ""),
                confidence=float(response.get("confidence", 0.7))
            )
        else:
            # Resposta é string, parsear
            planned = _parse_planner_response(str(response))
            
    except Exception as e:
        print(f"[PLANNER] Erro ao chamar LLM: {e}")
        # Fallback: tentar heurística simples
        planned = _heuristic_plan(state)
    
    print(f"[PLANNER] Ação planejada: {planned.intent.value} -> {planned.target_name or planned.destination or 'self'}")
    
    return {
        "planned_action": planned.to_dict(),
        "current_node": "planner",
        "next_node": "executor",
        "timestamp": datetime.utcnow().isoformat()
    }


def _heuristic_plan(state: AgentState) -> PlannedAction:
    """Fallback: planeja ação usando heurísticas simples."""
    user_input = state.get("user_input", "").lower()
    world = state.get("world", {})
    npcs = world.get("npcs_in_scene", [])
    
    # Palavras-chave para cada intent
    attack_words = ["atacar", "attack", "bater", "golpear", "lutar", "matar"]
    talk_words = ["falar", "talk", "perguntar", "dizer", "conversar"]
    move_words = ["ir", "andar", "viajar", "mover", "go", "walk"]
    meditate_words = ["meditar", "cultivar", "treinar"]
    observe_words = ["olhar", "observar", "examinar", "ver"]
    
    # Determinar intent
    intent = ActionIntent.UNKNOWN
    target = None
    destination = None
    
    for word in attack_words:
        if word in user_input:
            intent = ActionIntent.ATTACK
            # Encontrar alvo
            for npc in npcs:
                if npc.get("name", "").lower() in user_input:
                    target = npc.get("name")
                    break
            if not target and npcs:
                # Usar primeiro NPC hostil
                hostile = [n for n in npcs if n.get("is_hostile")]
                if hostile:
                    target = hostile[0].get("name")
            break
    
    if intent == ActionIntent.UNKNOWN:
        for word in talk_words:
            if word in user_input:
                intent = ActionIntent.TALK
                for npc in npcs:
                    if npc.get("name", "").lower() in user_input and npc.get("can_speak"):
                        target = npc.get("name")
                        break
                break
    
    if intent == ActionIntent.UNKNOWN:
        for word in move_words:
            if word in user_input:
                intent = ActionIntent.MOVE
                # Tentar extrair destino
                exits = world.get("available_exits", [])
                for exit in exits:
                    if exit.lower() in user_input:
                        destination = exit
                        break
                break
    
    if intent == ActionIntent.UNKNOWN:
        for word in meditate_words:
            if word in user_input:
                intent = ActionIntent.MEDITATE
                break
    
    if intent == ActionIntent.UNKNOWN:
        for word in observe_words:
            if word in user_input:
                intent = ActionIntent.OBSERVE
                break
    
    return PlannedAction(
        intent=intent,
        target_name=target,
        destination=destination,
        reasoning="Fallback heurístico",
        confidence=0.5
    )
