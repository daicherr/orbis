"""
Narrator Node - Gera narrativa final
GEM RPG ORBIS - LangGraph Architecture

O Narrator é o "poeta" que transforma os resultados mecânicos
em prosa literária no estilo Wuxia/Xianxia.

Responsabilidades:
1. Receber o ActionResult validado
2. Consultar contexto (mundo, NPCs, memórias)
3. Gerar narrativa imersiva
4. NÃO empurrar ações, NÃO fazer perguntas

Princípio: SANDBOX - o mundo existe, o jogador decide.
"""

from typing import Dict, Any, List
from datetime import datetime

from app.agents.nodes.state import (
    AgentState,
    ActionIntent,
    ActionResult,
    ValidationStatus
)


# ==================== PROMPTS ====================

NARRATOR_SYSTEM_PROMPT = """Você é o NARRADOR de uma novel de cultivo interativa estilo Wuxia/Xianxia.

═══════════════════════════════════════════════════════════════════
                        REGRAS ABSOLUTAS (NUNCA VIOLAR)
═══════════════════════════════════════════════════════════════════

❌ PROIBIDO - NUNCA FAÇA ISSO:
• Mencionar stats, tiers, HP, XP ou mecânicas de jogo
• Dizer "sua constituição Godfiend/Mortal/etc" diretamente
• Perguntar "O que você faz?" ou sugerir próximas ações
• Dar recompensas narrativas gratuitas
• Terminar com perguntas retóricas ou convites à ação
• Usar termos de jogo na narrativa (HP, dano, turno)

✅ OBRIGATÓRIO - SEMPRE FAÇA:
• Descrever sensações físicas sutis (calor, frio, arrepios)
• NPCs reagem com personalidade própria
• Consequências reais e viscerais
• Encerrar de forma aberta mas COMPLETA
• Usar economia de texto (150-250 palavras)

═══════════════════════════════════════════════════════════════════
                        ESTILO NARRATIVO
═══════════════════════════════════════════════════════════════════

Tom: Épico mas contido. Como autor de wuxia narrando.

Estrutura preferida:
📍 [Data | Período | Local]
[Parágrafo 1: Ambiente/Atmosfera]
[Parágrafo 2: Ação/Reação]
[Parágrafo 3 (opcional): Consequência/Tensão]

EXEMPLOS DE TRANSFORMAÇÃO:

Resultado mecânico: "Você causou 45 de dano. HP do inimigo: 55"
Narrativa: "O golpe conecta com o abdômen da criatura, arrancando um urro gutural. 
Ela cambaleia para trás, icor negro escorrendo pelo ferimento. Ainda de pé, 
mas visivelmente abalada."

Resultado mecânico: "Movimento para Floresta Nublada realizado"
Narrativa: "O caminho se afunila entre árvores antigas cujos galhos bloqueiam 
o sol. Uma névoa rasteira abraça seus tornozelos. O ar carrega o cheiro de 
folhas em decomposição e algo mais... metálico."
"""


def _build_narrator_prompt(state: AgentState) -> str:
    """Constrói o prompt para o Narrator."""
    player = state.get("player", {})
    world = state.get("world", {})
    action_result = state.get("action_result", {})
    planned_action = state.get("planned_action", {})
    validation = state.get("validation", {})
    user_input = state.get("user_input", "")
    
    # Informações temporais
    time_of_day = world.get("time_of_day", "day")
    date_str = world.get("date_string", "Dia desconhecido")
    location = world.get("current_location", "Unknown")
    weather = world.get("weather", "clear")
    
    # Header temporal
    period_map = {
        "morning": "Manhã",
        "afternoon": "Tarde",
        "evening": "Crepúsculo",
        "night": "Noite",
        "dawn": "Aurora",
        "day": "Dia"
    }
    period = period_map.get(time_of_day, "Dia")
    header = f"📍 **{date_str} | {period} | {location}**"
    
    # NPCs na cena
    npcs = world.get("npcs_in_scene", [])
    npcs_desc = []
    for npc in npcs:
        state_desc = npc.get("emotional_state", "neutro")
        npcs_desc.append(f"- {npc.get('name')}: {state_desc}")
    npcs_text = "\n".join(npcs_desc) if npcs_desc else "Ninguém por perto."
    
    # Resultado da ação
    intent = planned_action.get("intent", "unknown")
    success = action_result.get("success", False)
    result_message = action_result.get("message", "")
    
    # Detalhes mecânicos (para o narrador usar implicitamente)
    damage_dealt = action_result.get("damage_dealt", 0)
    damage_received = action_result.get("damage_received", 0)
    npc_killed = action_result.get("npc_killed")
    player_died = action_result.get("player_died", False)
    location_changed = action_result.get("location_changed", False)
    new_location = action_result.get("new_location")
    items_gained = action_result.get("items_gained", [])
    
    # Contexto de validação (se houve retry)
    validation_context = ""
    if validation.get("status") == ValidationStatus.INVALID.value:
        validation_context = f"\n⚠️ A ação falhou: {validation.get('error_message', 'razão desconhecida')}"
    
    # Construir contexto mecânico
    mechanics_context = []
    if damage_dealt > 0:
        mechanics_context.append(f"Dano causado: {damage_dealt}")
    if damage_received > 0:
        mechanics_context.append(f"Dano recebido: {damage_received}")
    if npc_killed:
        mechanics_context.append(f"Derrotou: {npc_killed}")
    if player_died:
        mechanics_context.append("JOGADOR FOI DERROTADO")
    if location_changed:
        mechanics_context.append(f"Mudou para: {new_location}")
    if items_gained:
        items_str = ", ".join([i.get("name", i.get("item_id", "?")) for i in items_gained])
        mechanics_context.append(f"Itens obtidos: {items_str}")
    
    mechanics_text = "\n".join(mechanics_context) if mechanics_context else "Ação simples."
    
    prompt = f"""{NARRATOR_SYSTEM_PROMPT}

═══════════════════════════════════════════════════════════════════
CONTEXTO DA CENA
═══════════════════════════════════════════════════════════════════

JOGADOR: {player.get('name', 'Desconhecido')}
LOCAL: {location}
CLIMA: {weather}

NPCs PRESENTES:
{npcs_text}

═══════════════════════════════════════════════════════════════════
AÇÃO DO JOGADOR
═══════════════════════════════════════════════════════════════════

Input original: "{user_input}"
Intenção interpretada: {intent}
Sucesso: {"Sim" if success else "Não"}

RESULTADO MECÂNICO (use implicitamente, NÃO mencione números):
{mechanics_text}
{result_message}
{validation_context}

═══════════════════════════════════════════════════════════════════
TAREFA
═══════════════════════════════════════════════════════════════════

Comece com: {header}

Escreva 2-3 parágrafos (150-250 palavras) narrando o resultado dessa ação.
Transforme os resultados mecânicos em prosa literária.
NÃO pergunte o que o jogador faz em seguida.
Encerre de forma aberta mas completa."""

    return prompt


def _generate_fallback_narration(state: AgentState) -> str:
    """Gera narração de fallback se o LLM falhar."""
    world = state.get("world", {})
    action_result = state.get("action_result", {})
    player = state.get("player", {})
    
    location = world.get("current_location", "algum lugar")
    success = action_result.get("success", False)
    message = action_result.get("message", "")
    
    time_of_day = world.get("time_of_day", "day")
    period_map = {
        "morning": "Manhã",
        "afternoon": "Tarde", 
        "evening": "Crepúsculo",
        "night": "Noite"
    }
    period = period_map.get(time_of_day, "Dia")
    
    header = f"📍 **{world.get('date_string', 'Hoje')} | {period} | {location}**"
    
    if success:
        body = f"""{player.get('name', 'Você')} executa sua ação com determinação.

{message}

O mundo ao redor continua em movimento, indiferente aos eventos que acabaram de se desenrolar."""
    else:
        body = f"""Algo não sai como planejado.

{message}

{player.get('name', 'Você')} precisa reconsiderar sua abordagem."""
    
    return f"{header}\n\n{body}"


# ==================== MAIN NARRATOR ====================

async def narrator_node(state: AgentState, gemini_client) -> Dict[str, Any]:
    """
    Node do Narrator - gera narrativa literária.
    
    Este é o último nó do fluxo principal.
    Transforma resultados mecânicos em prosa.
    
    Args:
        state: Estado atual do agente
        gemini_client: Cliente Gemini para LLM
        
    Returns:
        Atualizações parciais do estado incluindo narração
    """
    print(f"[NARRATOR] Gerando narrativa...")
    
    # Construir prompt
    prompt = _build_narrator_prompt(state)
    
    # Chamar LLM
    try:
        narration = gemini_client.generate_text(prompt, task="story")
        
        if not narration or len(narration) < 50:
            narration = _generate_fallback_narration(state)
            
    except Exception as e:
        print(f"[NARRATOR] Erro ao chamar LLM: {e}")
        narration = _generate_fallback_narration(state)
    
    # Extrair resumo da ação para o log
    action_result = state.get("action_result", {})
    action_summary = action_result.get("message", "Ação executada.")
    
    print(f"[NARRATOR] Narrativa gerada ({len(narration)} chars)")
    
    # Adicionar mensagem ao histórico
    new_message = {
        "role": "assistant",
        "content": narration,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "turn": state.get("turn_number", 1),
            "action_summary": action_summary[:100]
        }
    }
    
    return {
        "narration": narration,
        "action_summary": action_summary,
        "messages": [new_message],  # Será concatenado pelo operator.add
        "current_node": "narrator",
        "next_node": "end",
        "timestamp": datetime.utcnow().isoformat()
    }
