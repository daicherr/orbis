"""
Cognitive Referee - Interpretador Avançado de Ações
GEM RPG ORBIS - Arquitetura Cognitiva

O Referee Cognitivo usa o framework ReAct para:
1. Interpretar input do jogador (texto livre)
2. Identificar intenção, alvos, recursos usados
3. Validar se a ação é possível no contexto atual
4. Resolver mecânicas de jogo (combate, economia, etc)
5. Retornar ação estruturada para o sistema

Este é o "Juiz" do jogo - garante que as regras sejam seguidas.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.agents.react_agent import ReActAgent, Tool
from app.database.models.player import Player
from app.database.models.npc import NPC


class ActionIntent(str, Enum):
    """Possíveis intenções de ação do jogador."""
    # Combate
    ATTACK = "attack"
    DEFEND = "defend"
    FLEE = "flee"
    USE_SKILL = "use_skill"
    
    # Social
    TALK = "talk"
    PERSUADE = "persuade"
    INTIMIDATE = "intimidate"
    TRADE = "trade"
    
    # Exploração
    MOVE = "move"
    EXPLORE = "explore"
    SEARCH = "search"
    OBSERVE = "observe"
    REST = "rest"
    
    # Cultivo
    MEDITATE = "meditate"
    CULTIVATE = "cultivate"
    TRAIN = "train"
    ABSORB = "absorb"
    
    # Itens
    USE_ITEM = "use_item"
    EQUIP = "equip"
    DROP = "drop"
    PICK_UP = "pick_up"
    
    # Meta
    WAIT = "wait"
    UNKNOWN = "unknown"


@dataclass
class ParsedAction:
    """Ação parseada do input do jogador."""
    intent: ActionIntent
    raw_input: str
    
    # Alvos
    target_name: Optional[str] = None
    target_type: Optional[str] = None  # npc, location, item, self
    secondary_target: Optional[str] = None
    
    # Skill/Item usado
    skill_name: Optional[str] = None
    item_name: Optional[str] = None
    
    # Movimento
    destination: Optional[str] = None
    
    # Diálogo
    spoken_words: Optional[str] = None
    tone: Optional[str] = None  # friendly, hostile, neutral, sarcastic
    
    # Mecânicas resolvidas
    damage_dealt: float = 0.0
    resource_cost: Dict[str, float] = field(default_factory=dict)
    roll_result: Optional[Dict[str, Any]] = None
    
    # Validação
    is_valid: bool = True
    validation_error: Optional[str] = None
    
    # Contexto
    confidence: float = 1.0
    reasoning: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "intent": self.intent.value if isinstance(self.intent, ActionIntent) else self.intent,
            "raw_input": self.raw_input,
            "target_name": self.target_name,
            "target_type": self.target_type,
            "secondary_target": self.secondary_target,
            "skill_name": self.skill_name,
            "item_name": self.item_name,
            "destination": self.destination,
            "spoken_words": self.spoken_words,
            "tone": self.tone,
            "damage_dealt": self.damage_dealt,
            "resource_cost": self.resource_cost,
            "roll_result": self.roll_result,
            "is_valid": self.is_valid,
            "validation_error": self.validation_error,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


class CognitiveReferee(ReActAgent):
    """
    Referee que usa ReAct para interpretar ações de forma inteligente.
    
    Pode consultar o contexto do jogo, verificar regras e resolver mecânicas
    antes de retornar a ação estruturada.
    """
    
    def __init__(
        self,
        gemini_client: Any,
        max_iterations: int = 5,
        verbose: bool = False
    ):
        super().__init__(
            name="CognitiveReferee",
            gemini_client=gemini_client,
            max_iterations=max_iterations,
            verbose=verbose
        )
        
        # Contexto atual (será preenchido em cada chamada)
        self._current_player: Optional[Player] = None
        self._current_targets: List[NPC] = []
        self._current_location: str = ""
        self._available_skills: List[str] = []
        self._inventory_items: List[str] = []
    
    def _build_system_prompt(self) -> str:
        """Constrói o prompt de sistema do Referee."""
        return """Você é o REFEREE (Juiz) de um RPG de Cultivo no estilo Wuxia/Xianxia.

Seu trabalho é INTERPRETAR o que o jogador quer fazer baseado no texto que ele digitou,
e TRADUZIR isso para uma ação mecânica estruturada.

REGRAS DE INTERPRETAÇÃO:

1. **COMBATE**: Se o jogador menciona atacar, lutar, bater, golpear, usar técnica ofensiva:
   - Intent = "attack" ou "use_skill"
   - Identifique o alvo (NPC presente na cena)
   - Identifique a skill usada (ou basic_attack se não especificou)

2. **SOCIAL**: Se o jogador menciona falar, perguntar, negociar, ameaçar:
   - Intent = "talk", "persuade", "intimidate" ou "trade"
   - Identifique com quem está falando
   - Extraia as palavras ditas (spoken_words)
   - Identifique o tom (friendly, hostile, neutral)

3. **MOVIMENTO**: Se o jogador menciona ir, andar, viajar, explorar:
   - Intent = "move" ou "explore"
   - Identifique o destino

4. **CULTIVO**: Se o jogador menciona meditar, cultivar, treinar, absorver:
   - Intent = "meditate", "cultivate", "train" ou "absorb"
   - Verifique se o ambiente permite

5. **ITENS**: Se o jogador menciona usar, equipar, pegar, largar:
   - Intent = "use_item", "equip", "pick_up" ou "drop"
   - Identifique o item

PROCESSO:
1. Leia o input do jogador
2. Use ferramentas para verificar contexto se necessário
3. Determine a intenção principal
4. Valide se a ação é possível
5. Retorne a ação estruturada

NUNCA invente informações que não estão no contexto.
Se não tiver certeza, peça esclarecimento ou marque confidence baixa."""
    
    def _get_tools(self) -> List[Tool]:
        """Retorna ferramentas disponíveis para o Referee."""
        return [
            Tool(
                name="check_target_exists",
                description="Verifica se um alvo (NPC) existe na cena atual",
                parameters={
                    "target_name": {"type": "string", "description": "Nome do alvo a verificar"}
                },
                handler=self._tool_check_target_exists
            ),
            Tool(
                name="check_skill_available",
                description="Verifica se o jogador tem uma skill disponível",
                parameters={
                    "skill_name": {"type": "string", "description": "Nome da skill a verificar"}
                },
                handler=self._tool_check_skill_available
            ),
            Tool(
                name="check_item_in_inventory",
                description="Verifica se o jogador tem um item no inventário",
                parameters={
                    "item_name": {"type": "string", "description": "Nome do item a verificar"}
                },
                handler=self._tool_check_item_in_inventory
            ),
            Tool(
                name="get_player_stats",
                description="Retorna os stats atuais do jogador",
                parameters={},
                handler=self._tool_get_player_stats
            ),
            Tool(
                name="get_valid_destinations",
                description="Retorna destinos válidos a partir da localização atual",
                parameters={},
                handler=self._tool_get_valid_destinations
            ),
            Tool(
                name="resolve_action",
                description="Resolve a ação e retorna resultado estruturado. Use quando tiver todas as informações.",
                parameters={
                    "intent": {"type": "string", "description": "Intenção: attack, talk, move, etc"},
                    "target_name": {"type": "string", "description": "Nome do alvo (pode ser null)"},
                    "skill_name": {"type": "string", "description": "Skill usada (pode ser null)"},
                    "destination": {"type": "string", "description": "Destino se move (pode ser null)"},
                    "spoken_words": {"type": "string", "description": "Palavras ditas (pode ser null)"},
                    "tone": {"type": "string", "description": "Tom: friendly, hostile, neutral"},
                    "reasoning": {"type": "string", "description": "Seu raciocínio sobre a interpretação"}
                },
                handler=self._tool_resolve_action
            ),
        ]
    
    # ==================== FERRAMENTAS INTERNAS ====================
    
    async def _tool_check_target_exists(self, target_name: str) -> Dict[str, Any]:
        """Verifica se um alvo existe na cena."""
        target_names = [npc.name.lower() for npc in self._current_targets]
        
        # Busca exata
        if target_name.lower() in target_names:
            matching_npc = next(
                npc for npc in self._current_targets 
                if npc.name.lower() == target_name.lower()
            )
            return {
                "exists": True,
                "name": matching_npc.name,
                "type": "npc",
                "emotional_state": matching_npc.emotional_state,
                "species": getattr(matching_npc, 'species', 'unknown'),
                "can_speak": getattr(matching_npc, 'can_speak', True)
            }
        
        # Busca parcial
        for npc in self._current_targets:
            if target_name.lower() in npc.name.lower():
                return {
                    "exists": True,
                    "name": npc.name,
                    "type": "npc",
                    "partial_match": True,
                    "emotional_state": npc.emotional_state,
                    "species": getattr(npc, 'species', 'unknown'),
                    "can_speak": getattr(npc, 'can_speak', True)
                }
        
        return {
            "exists": False,
            "available_targets": [npc.name for npc in self._current_targets[:5]]
        }
    
    async def _tool_check_skill_available(self, skill_name: str) -> Dict[str, Any]:
        """Verifica se uma skill está disponível."""
        # basic_attack sempre disponível
        if skill_name.lower() == "basic_attack":
            return {"available": True, "skill": "basic_attack", "cost": {"qi": 0}}
        
        # Verificar em learned_skills
        for skill in self._available_skills:
            if skill.lower() == skill_name.lower() or skill_name.lower() in skill.lower():
                return {
                    "available": True,
                    "skill": skill,
                    "cost": {"qi": 10}  # TODO: buscar custo real
                }
        
        return {
            "available": False,
            "available_skills": self._available_skills[:5] + ["basic_attack"]
        }
    
    async def _tool_check_item_in_inventory(self, item_name: str) -> Dict[str, Any]:
        """Verifica se um item está no inventário."""
        for item in self._inventory_items:
            if item.lower() == item_name.lower() or item_name.lower() in item.lower():
                return {"has_item": True, "item": item}
        
        return {
            "has_item": False,
            "inventory_sample": self._inventory_items[:5] if self._inventory_items else []
        }
    
    async def _tool_get_player_stats(self) -> Dict[str, Any]:
        """Retorna stats do jogador atual."""
        if not self._current_player:
            return {"error": "Jogador não carregado"}
        
        p = self._current_player
        return {
            "name": p.name,
            "tier": p.cultivation_rank,
            "hp": f"{p.current_hp}/{p.max_hp}",
            "qi": getattr(p, 'current_qi', 100),
            "gold": p.gold,
            "location": p.current_location,
            "learned_skills": p.learned_skills[:5] if p.learned_skills else []
        }
    
    async def _tool_get_valid_destinations(self) -> Dict[str, Any]:
        """Retorna destinos válidos."""
        # Por enquanto, retorna destinos hardcoded baseados na localização
        destinations_map = {
            "Initial Village": ["Misty Forest", "Merchant City"],
            "Misty Forest": ["Initial Village", "Dragon Mountains", "Spirit Lake"],
            "Dragon Mountains": ["Misty Forest", "Ancient Ruins"],
            "Merchant City": ["Initial Village", "Sword Sect", "Poison Swamp"],
        }
        
        destinations = destinations_map.get(self._current_location, ["Initial Village"])
        
        return {
            "current_location": self._current_location,
            "valid_destinations": destinations
        }
    
    async def _tool_resolve_action(
        self,
        intent: str,
        target_name: Optional[str] = None,
        skill_name: Optional[str] = None,
        destination: Optional[str] = None,
        spoken_words: Optional[str] = None,
        tone: str = "neutral",
        reasoning: str = ""
    ) -> Dict[str, Any]:
        """Resolve e estrutura a ação final."""
        
        # Mapear intent string para enum
        intent_map = {
            "attack": ActionIntent.ATTACK,
            "defend": ActionIntent.DEFEND,
            "flee": ActionIntent.FLEE,
            "use_skill": ActionIntent.USE_SKILL,
            "talk": ActionIntent.TALK,
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
        
        parsed_intent = intent_map.get(intent.lower(), ActionIntent.UNKNOWN)
        
        return {
            "action_resolved": True,
            "intent": intent,
            "target_name": target_name,
            "skill_name": skill_name or ("basic_attack" if parsed_intent == ActionIntent.ATTACK else None),
            "destination": destination,
            "spoken_words": spoken_words,
            "tone": tone,
            "reasoning": reasoning,
            "is_valid": True
        }
    
    # ==================== MÉTODO PRINCIPAL ====================
    
    async def parse_action(
        self,
        player_input: str,
        player: Player,
        possible_targets: List[NPC],
        current_location: str = "",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ParsedAction:
        """
        Parseia o input do jogador e retorna uma ação estruturada.
        
        Args:
            player_input: Texto digitado pelo jogador
            player: Objeto Player
            possible_targets: NPCs na cena
            current_location: Localização atual
            additional_context: Contexto adicional (opcional)
            
        Returns:
            ParsedAction com a ação interpretada
        """
        # Configurar contexto para as ferramentas
        self._current_player = player
        self._current_targets = possible_targets
        self._current_location = current_location or player.current_location
        self._available_skills = player.learned_skills if player.learned_skills else []
        self._inventory_items = [
            item.get("name", str(item)) if isinstance(item, dict) else str(item)
            for item in (player.inventory if player.inventory else [])
        ]
        
        # Construir contexto para o agente
        context = {
            "player_name": player.name,
            "player_tier": player.cultivation_rank,
            "current_location": self._current_location,
            "targets_in_scene": [
                {
                    "name": npc.name,
                    "emotional_state": npc.emotional_state,
                    "species": getattr(npc, 'species', 'human'),
                    "can_speak": getattr(npc, 'can_speak', True)
                }
                for npc in possible_targets[:5]  # Limitar a 5 NPCs
            ],
            "available_skills": self._available_skills[:5] + ["basic_attack"],
            "inventory_sample": self._inventory_items[:5]
        }
        
        if additional_context:
            context.update(additional_context)
        
        # Executar agente ReAct
        trace = await self.run(
            task=f"Interprete a ação do jogador: \"{player_input}\"",
            context=context
        )
        
        # Processar resultado
        if trace.final_answer:
            # Tentar extrair JSON do final_answer
            return self._extract_action_from_trace(trace, player_input)
        else:
            # Falha na interpretação
            return ParsedAction(
                intent=ActionIntent.UNKNOWN,
                raw_input=player_input,
                is_valid=False,
                validation_error=trace.error or "Não foi possível interpretar a ação",
                confidence=0.0
            )
    
    def _extract_action_from_trace(self, trace, raw_input: str) -> ParsedAction:
        """Extrai ParsedAction do trace do agente."""
        # Buscar o resultado do resolve_action nas observações
        for step in reversed(trace.steps):
            if step.observation and "action_resolved" in step.observation:
                try:
                    import json
                    # Extrair JSON da observação
                    obs = step.observation
                    if "✓" in obs:
                        obs = obs.split(":", 1)[1].strip()
                    
                    data = json.loads(obs)
                    
                    intent_map = {
                        "attack": ActionIntent.ATTACK,
                        "talk": ActionIntent.TALK,
                        "move": ActionIntent.MOVE,
                        "use_skill": ActionIntent.USE_SKILL,
                        "meditate": ActionIntent.MEDITATE,
                        "cultivate": ActionIntent.CULTIVATE,
                        "trade": ActionIntent.TRADE,
                        "observe": ActionIntent.OBSERVE,
                        "rest": ActionIntent.REST,
                        "flee": ActionIntent.FLEE,
                        "use_item": ActionIntent.USE_ITEM,
                    }
                    
                    return ParsedAction(
                        intent=intent_map.get(data.get("intent", "unknown"), ActionIntent.UNKNOWN),
                        raw_input=raw_input,
                        target_name=data.get("target_name"),
                        skill_name=data.get("skill_name"),
                        destination=data.get("destination"),
                        spoken_words=data.get("spoken_words"),
                        tone=data.get("tone", "neutral"),
                        is_valid=data.get("is_valid", True),
                        reasoning=data.get("reasoning"),
                        confidence=0.9
                    )
                except:
                    pass
        
        # Fallback: tentar extrair do final_answer
        answer = trace.final_answer or ""
        
        # Heurística simples baseada em palavras-chave
        intent = ActionIntent.UNKNOWN
        target = None
        
        lower_input = raw_input.lower()
        
        if any(w in lower_input for w in ["atacar", "attack", "golpear", "bater", "lutar"]):
            intent = ActionIntent.ATTACK
        elif any(w in lower_input for w in ["falar", "talk", "perguntar", "dizer", "conversar"]):
            intent = ActionIntent.TALK
        elif any(w in lower_input for w in ["ir", "andar", "viajar", "move", "go"]):
            intent = ActionIntent.MOVE
        elif any(w in lower_input for w in ["meditar", "cultivar", "treinar"]):
            intent = ActionIntent.MEDITATE
        elif any(w in lower_input for w in ["observar", "olhar", "examinar"]):
            intent = ActionIntent.OBSERVE
        
        # Tentar identificar alvo
        for npc in self._current_targets:
            if npc.name.lower() in lower_input:
                target = npc.name
                break
        
        return ParsedAction(
            intent=intent,
            raw_input=raw_input,
            target_name=target,
            reasoning=answer,
            confidence=0.6
        )


# ==================== WRAPPER PARA COMPATIBILIDADE ====================

class Referee:
    """
    Wrapper de compatibilidade que mantém a interface antiga
    mas usa CognitiveReferee internamente quando possível.
    """
    
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self._cognitive_referee: Optional[CognitiveReferee] = None
    
    def _get_cognitive_referee(self) -> CognitiveReferee:
        """Lazy load do CognitiveReferee."""
        if self._cognitive_referee is None:
            self._cognitive_referee = CognitiveReferee(
                gemini_client=self.gemini_client,
                max_iterations=5,
                verbose=False
            )
        return self._cognitive_referee
    
    def parse_player_action(
        self,
        player_input: str,
        player: Player,
        possible_targets: List[NPC]
    ) -> Dict[str, Any]:
        """
        Interface de compatibilidade com o sistema antigo.
        Usa o método síncrono original para não quebrar código existente.
        """
        target_names = ", ".join([npc.name for npc in possible_targets]) if possible_targets else "Nenhum"
        player_skills = ", ".join(player.learned_skills) if player.learned_skills else "basic_attack"

        prompt = (
            f"Você é um juiz de RPG (referee) que analisa a ação de um jogador. "
            f"Seu trabalho é converter o texto do jogador em um objeto JSON estruturado. "
            f"Analise o texto e preencha o JSON com as seguintes chaves:\n"
            f"- 'intent': A intenção principal do jogador. Válidas são: 'attack', 'talk', 'move', 'use_item', 'observe', 'meditate', 'cultivate', 'speak', 'trade', 'rest', 'flee', 'unknown'.\n"
            f"- 'target_name': O nome exato do alvo da ação (NPC ou local). Deve ser um dos 'Alvos Possíveis' se for NPC. Para 'move', use o nome do destino. Se não houver alvo específico, use null.\n"
            f"- 'destination': O nome do local de destino se intent='move'. Ex: 'Floresta Nublada', 'Vila Crisântemos'.\n"
            f"- 'skill_name': O ID da habilidade usada. DEVE ser uma das 'Skills Disponíveis'. Se o jogador não especificou uma skill, use 'basic_attack'.\n"
            f"- 'spoken_words': Se o jogador disse algo em voz alta (texto entre aspas ou diálogo direto), coloque aqui o que foi dito.\n"
            f"- 'tone': O tom do diálogo se houver spoken_words. Valores: 'friendly', 'hostile', 'neutral', 'sarcastic'.\n\n"
            f"REGRA IMPORTANTE: Se a intenção é 'attack' e o jogador não especificou uma habilidade exata, use 'basic_attack' como skill_name.\n"
            f"REGRA IMPORTANTE: Se a intenção é 'move', extraia o destino mencionado e coloque em 'destination'.\n"
            f"REGRA IMPORTANTE: Se o texto começa com aspas ou o jogador está FALANDO algo (não atacando), use intent='speak' e coloque o diálogo em 'spoken_words'. O target_name deve ser o NPC a quem ele fala, se identificável.\n"
            f"REGRA IMPORTANTE: Se não há alvo claro, target_name deve ser null (não 'None' como string).\n\n"
            f"--- Contexto ---\n"
            f"Alvos Possíveis: {target_names}\n"
            f"Skills Disponíveis: {player_skills}, basic_attack\n"
            f"Texto do Jogador: \"{player_input}\"\n\n"
            f"--- JSON de Saída ---\n"
        )

        print(f"--- Analisando a ação do jogador via Gemini: '{player_input}' ---")
        
        action_data = self.gemini_client.generate_json(prompt, task="combat")

        if not isinstance(action_data, dict) or "intent" not in action_data:
            return {"intent": "unknown", "target_name": None, "skill_name": None, "error": "Invalid response from AI"}

        return action_data
    
    async def parse_player_action_async(
        self,
        player_input: str,
        player: Player,
        possible_targets: List[NPC],
        current_location: str = ""
    ) -> ParsedAction:
        """
        Versão assíncrona que usa o CognitiveReferee completo.
        Prefer esta versão para novos códigos.
        """
        referee = self._get_cognitive_referee()
        return await referee.parse_action(
            player_input=player_input,
            player=player,
            possible_targets=possible_targets,
            current_location=current_location
        )
