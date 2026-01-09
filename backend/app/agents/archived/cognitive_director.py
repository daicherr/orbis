"""
Cognitive Director - Coordenador Inteligente do Mundo
GEM RPG ORBIS - Arquitetura Cognitiva

O Director Cognitivo é o "maestro" que orquestra todos os sistemas:
1. Coordena NPCs e suas ações autônomas
2. Gerencia eventos do mundo
3. Processa turnos do jogador de forma inteligente
4. Mantém consistência narrativa
5. Usa ReAct para decisões complexas

Este é o "Game Master" - controla o fluxo do jogo.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

from app.agents.react_agent import ReActAgent, Tool
from app.agents.cognitive_referee import CognitiveReferee, ParsedAction, ActionIntent
from app.agents.cognitive_narrator import CognitiveNarrator, NarrativeStyle, NarrativeContext
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.core.chronos import world_clock


class EventType(str, Enum):
    """Tipos de eventos no mundo."""
    PLAYER_ACTION = "player_action"
    NPC_ACTION = "npc_action"
    WORLD_EVENT = "world_event"
    COMBAT = "combat"
    DIALOGUE = "dialogue"
    DISCOVERY = "discovery"
    TIME_PASSAGE = "time_passage"


class TurnPhase(str, Enum):
    """Fases de um turno."""
    PRE_TURN = "pre_turn"           # Verificar efeitos contínuos
    INPUT_PARSING = "input_parsing"  # Interpretar ação do jogador
    VALIDATION = "validation"        # Validar se a ação é possível
    EXECUTION = "execution"          # Executar a ação
    NPC_REACTION = "npc_reaction"    # NPCs reagem
    NARRATION = "narration"          # Narrar o resultado
    POST_TURN = "post_turn"          # Atualizar estado do mundo


@dataclass
class TurnResult:
    """Resultado completo de um turno processado."""
    turn_number: int
    player_input: str
    parsed_action: Optional[ParsedAction]
    
    # Narrativa
    scene_description: str
    action_result: str
    
    # Estado
    player_state: Dict[str, Any]
    npcs_in_scene: List[Dict[str, Any]]
    location: str
    world_time: str
    
    # Eventos
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Meta
    success: bool = True
    error: Optional[str] = None
    processing_time_ms: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "turn_number": self.turn_number,
            "player_input": self.player_input,
            "parsed_action": self.parsed_action.to_dict() if self.parsed_action else None,
            "scene_description": self.scene_description,
            "action_result": self.action_result,
            "player_state": self.player_state,
            "npcs_in_scene": self.npcs_in_scene,
            "location": self.location,
            "world_time": self.world_time,
            "events": self.events,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class WorldState:
    """Estado atual do mundo para consultas."""
    current_time: datetime
    time_period: str
    weather: str
    active_events: List[Dict[str, Any]]
    faction_states: Dict[str, Dict[str, Any]]
    economy_state: Dict[str, float]
    
    @classmethod
    def create_default(cls) -> "WorldState":
        """Cria estado padrão."""
        now = world_clock.get_current_datetime()
        hour = now.hour
        
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "afternoon"
        elif 18 <= hour < 21:
            period = "evening"
        else:
            period = "night"
        
        return cls(
            current_time=now,
            time_period=period,
            weather="clear",
            active_events=[],
            faction_states={},
            economy_state={}
        )


class CognitiveDirector(ReActAgent):
    """
    Director que usa ReAct para coordenar o mundo de forma inteligente.
    
    Responsabilidades:
    - Orquestrar Referee e Narrator cognitivos
    - Gerenciar NPCs e suas ações
    - Manter consistência do mundo
    - Processar eventos complexos
    """
    
    def __init__(
        self,
        gemini_client: Any,
        cognitive_referee: Optional[CognitiveReferee] = None,
        cognitive_narrator: Optional[CognitiveNarrator] = None,
        max_iterations: int = 6,
        verbose: bool = False
    ):
        super().__init__(
            name="CognitiveDirector",
            gemini_client=gemini_client,
            max_iterations=max_iterations,
            verbose=verbose
        )
        
        # Agentes subordinados
        self._referee = cognitive_referee or CognitiveReferee(gemini_client)
        self._narrator = cognitive_narrator or CognitiveNarrator(gemini_client)
        
        # Repositórios (injetados externamente)
        self._player_repo = None
        self._npc_repo = None
        self._gamelog_repo = None
        self._memory_repo = None
        self._location_repo = None
        
        # Estado do mundo
        self._world_state = WorldState.create_default()
        
        # Contexto atual do turno
        self._current_player: Optional[Player] = None
        self._current_location: str = ""
        self._npcs_in_scene: List[NPC] = []
        self._turn_events: List[Dict[str, Any]] = []
    
    def set_repositories(
        self,
        player_repo=None,
        npc_repo=None,
        gamelog_repo=None,
        memory_repo=None,
        location_repo=None
    ):
        """Injeta repositórios necessários."""
        self._player_repo = player_repo
        self._npc_repo = npc_repo
        self._gamelog_repo = gamelog_repo
        self._memory_repo = memory_repo
        self._location_repo = location_repo
        
        # Propagar para agentes subordinados
        if self._narrator:
            self._narrator.set_repositories(
                memory_repo=memory_repo,
                location_repo=location_repo
            )
    
    def _build_system_prompt(self) -> str:
        """System prompt do Director Cognitivo."""
        return """Você é o DIRECTOR (Mestre do Jogo) de um RPG de Cultivo.

Seu papel é COORDENAR todos os sistemas do jogo para criar uma experiência coerente.

═══════════════════════════════════════════════════════════════════
                        RESPONSABILIDADES
═══════════════════════════════════════════════════════════════════

1. INTERPRETAR a ação do jogador (via Referee)
2. VALIDAR se a ação é possível no contexto
3. EXECUTAR a mecânica da ação
4. GERAR reações dos NPCs
5. NARRAR o resultado (via Narrator)
6. ATUALIZAR o estado do mundo

═══════════════════════════════════════════════════════════════════
                        PRINCÍPIOS
═══════════════════════════════════════════════════════════════════

• O mundo é VIVO - NPCs têm vidas próprias
• Ações têm CONSEQUÊNCIAS reais
• O tempo PASSA mesmo quando o jogador não age
• Decisões do jogador IMPORTAM para a história
• Nunca force narrativas - deixe o jogador liderar

Use as ferramentas para coordenar os sistemas e produzir um turno completo."""
    
    def _get_tools(self) -> List[Tool]:
        """Ferramentas do Director."""
        return [
            Tool(
                name="get_player_state",
                description="Retorna o estado atual do jogador (HP, Qi, localização, etc)",
                parameters={},
                handler=self._tool_get_player_state
            ),
            Tool(
                name="get_npcs_in_scene",
                description="Retorna NPCs presentes na localização atual",
                parameters={},
                handler=self._tool_get_npcs_in_scene
            ),
            Tool(
                name="parse_player_action",
                description="Usa o Referee para interpretar a ação do jogador",
                parameters={
                    "player_input": {"type": "string", "description": "Texto digitado pelo jogador"}
                },
                handler=self._tool_parse_player_action
            ),
            Tool(
                name="execute_combat",
                description="Executa uma ação de combate",
                parameters={
                    "attacker_is_player": {"type": "boolean", "description": "Se true, jogador ataca NPC"},
                    "target_name": {"type": "string", "description": "Nome do alvo"},
                    "skill_name": {"type": "string", "description": "Skill usada (ou basic_attack)"}
                },
                handler=self._tool_execute_combat
            ),
            Tool(
                name="execute_dialogue",
                description="Executa uma interação de diálogo",
                parameters={
                    "npc_name": {"type": "string", "description": "Nome do NPC"},
                    "player_words": {"type": "string", "description": "O que o jogador disse"},
                    "tone": {"type": "string", "description": "Tom: friendly, hostile, neutral"}
                },
                handler=self._tool_execute_dialogue
            ),
            Tool(
                name="execute_movement",
                description="Executa movimento para outro local",
                parameters={
                    "destination": {"type": "string", "description": "Destino do movimento"}
                },
                handler=self._tool_execute_movement
            ),
            Tool(
                name="generate_npc_reactions",
                description="Gera reações dos NPCs à ação do jogador",
                parameters={
                    "action_type": {"type": "string", "description": "Tipo da ação: combat, dialogue, movement"},
                    "action_result": {"type": "string", "description": "Resultado da ação"}
                },
                handler=self._tool_generate_npc_reactions
            ),
            Tool(
                name="generate_narration",
                description="Usa o Narrator para gerar a descrição da cena",
                parameters={
                    "action_result": {"type": "string", "description": "Resultado da ação para narrar"},
                    "style": {"type": "string", "description": "Estilo: exploration, combat, dialogue"}
                },
                handler=self._tool_generate_narration
            ),
            Tool(
                name="finalize_turn",
                description="Finaliza o turno e retorna o resultado completo",
                parameters={
                    "scene_description": {"type": "string", "description": "Narrativa da cena"},
                    "action_result": {"type": "string", "description": "Resultado da ação"},
                    "events": {"type": "string", "description": "Lista de eventos (JSON)"}
                },
                handler=self._tool_finalize_turn
            ),
        ]
    
    # ==================== FERRAMENTAS INTERNAS ====================
    
    async def _tool_get_player_state(self) -> Dict[str, Any]:
        """Retorna estado do jogador."""
        if not self._current_player:
            return {"error": "Jogador não carregado"}
        
        p = self._current_player
        return {
            "name": p.name,
            "cultivation_rank": p.cultivation_rank,
            "hp": f"{p.current_hp}/{p.max_hp}",
            "yuan_qi": getattr(p, 'yuan_qi', 100),
            "gold": p.gold,
            "location": p.current_location,
            "learned_skills": p.learned_skills[:5] if p.learned_skills else [],
            "constitution": getattr(p, 'constitution_type', None),
            "inventory_count": len(p.inventory) if p.inventory else 0
        }
    
    async def _tool_get_npcs_in_scene(self) -> Dict[str, Any]:
        """Retorna NPCs na cena."""
        if not self._npcs_in_scene:
            return {"npcs": [], "note": "Nenhum NPC na cena"}
        
        npcs_data = []
        for npc in self._npcs_in_scene[:5]:
            npcs_data.append({
                "name": npc.name,
                "emotional_state": getattr(npc, 'emotional_state', 'neutral'),
                "species": getattr(npc, 'species', 'human'),
                "can_speak": getattr(npc, 'can_speak', True),
                "hp": f"{npc.current_hp}/{npc.max_hp}",
                "rank": npc.rank
            })
        
        return {"npcs": npcs_data, "count": len(self._npcs_in_scene)}
    
    async def _tool_parse_player_action(self, player_input: str) -> Dict[str, Any]:
        """Parseia a ação do jogador usando o Referee."""
        if not self._current_player:
            return {"error": "Jogador não carregado"}
        
        try:
            parsed = await self._referee.parse_action(
                player_input=player_input,
                player=self._current_player,
                possible_targets=self._npcs_in_scene,
                current_location=self._current_location
            )
            
            return {
                "intent": parsed.intent.value if hasattr(parsed.intent, 'value') else str(parsed.intent),
                "target_name": parsed.target_name,
                "skill_name": parsed.skill_name,
                "destination": parsed.destination,
                "spoken_words": parsed.spoken_words,
                "is_valid": parsed.is_valid,
                "confidence": parsed.confidence
            }
        except Exception as e:
            return {"error": str(e), "intent": "unknown"}
    
    async def _tool_execute_combat(
        self,
        attacker_is_player: bool,
        target_name: str,
        skill_name: str = "basic_attack"
    ) -> Dict[str, Any]:
        """Executa ação de combate."""
        if not self._current_player:
            return {"error": "Jogador não carregado"}
        
        # Encontrar alvo
        target = None
        for npc in self._npcs_in_scene:
            if npc.name.lower() == target_name.lower() or target_name.lower() in npc.name.lower():
                target = npc
                break
        
        if not target:
            return {"success": False, "message": f"Alvo '{target_name}' não encontrado"}
        
        # Calcular dano (simplificado - deveria usar combat_engine real)
        if attacker_is_player:
            base_damage = 10 + (self._current_player.rank * 5)
            damage = max(1, base_damage - target.defense)
            target.current_hp -= damage
            
            result = {
                "attacker": self._current_player.name,
                "target": target.name,
                "skill": skill_name,
                "damage": damage,
                "target_hp_remaining": target.current_hp,
                "target_defeated": target.current_hp <= 0
            }
            
            # Registrar evento
            self._turn_events.append({
                "type": "combat",
                "actor": self._current_player.name,
                "target": target.name,
                "damage": damage
            })
            
            if target.current_hp <= 0:
                result["message"] = f"Você derrotou {target.name}!"
                self._turn_events.append({
                    "type": "npc_defeated",
                    "npc_name": target.name
                })
            else:
                result["message"] = f"Você causou {damage} de dano a {target.name}. HP restante: {target.current_hp}"
            
            return result
        else:
            # NPC ataca jogador
            base_damage = 5 + (target.rank * 3)
            damage = max(1, base_damage - self._current_player.defense)
            self._current_player.current_hp -= damage
            
            return {
                "attacker": target.name,
                "target": self._current_player.name,
                "damage": damage,
                "player_hp_remaining": self._current_player.current_hp,
                "player_defeated": self._current_player.current_hp <= 0,
                "message": f"{target.name} causou {damage} de dano a você!"
            }
    
    async def _tool_execute_dialogue(
        self,
        npc_name: str,
        player_words: str,
        tone: str = "neutral"
    ) -> Dict[str, Any]:
        """Executa interação de diálogo."""
        # Encontrar NPC
        target_npc = None
        for npc in self._npcs_in_scene:
            if npc.name.lower() == npc_name.lower() or npc_name.lower() in npc.name.lower():
                target_npc = npc
                break
        
        if not target_npc:
            return {"success": False, "message": f"NPC '{npc_name}' não encontrado"}
        
        # Verificar se pode falar
        can_speak = getattr(target_npc, 'can_speak', True)
        if not can_speak:
            species = getattr(target_npc, 'species', 'criatura')
            return {
                "success": True,
                "response": f"O {species} não parece entender suas palavras, mas observa você com atenção.",
                "npc_emotion": "curious"
            }
        
        # Gerar resposta baseada em estado emocional
        emotional = getattr(target_npc, 'emotional_state', 'neutral')
        
        if emotional == 'hostile':
            response = f"{target_npc.name} rosna: 'Não perca meu tempo, cultivador!'"
        elif emotional == 'friendly':
            response = f"{target_npc.name} sorri: 'É bom ver você, amigo.'"
        elif emotional == 'scared':
            response = f"{target_npc.name} recua nervosamente: 'O-o que você quer?'"
        else:
            response = f"{target_npc.name} considera suas palavras antes de responder."
        
        # Registrar evento
        self._turn_events.append({
            "type": "dialogue",
            "player_said": player_words,
            "npc": target_npc.name,
            "tone": tone
        })
        
        return {
            "success": True,
            "npc": target_npc.name,
            "player_said": player_words,
            "response": response,
            "npc_emotion": emotional
        }
    
    async def _tool_execute_movement(self, destination: str) -> Dict[str, Any]:
        """Executa movimento para outro local."""
        if not self._current_player:
            return {"error": "Jogador não carregado"}
        
        old_location = self._current_player.current_location
        
        # Destinos válidos (simplificado - deveria consultar location_repo)
        valid_destinations = {
            "Initial Village": ["Misty Forest", "Merchant City"],
            "Misty Forest": ["Initial Village", "Dragon Mountains", "Spirit Lake"],
            "Dragon Mountains": ["Misty Forest", "Ancient Ruins"],
            "Merchant City": ["Initial Village", "Sword Sect"],
        }
        
        destinations = valid_destinations.get(old_location, ["Initial Village"])
        
        # Verificar se destino é válido
        matched_destination = None
        for d in destinations:
            if destination.lower() in d.lower() or d.lower() in destination.lower():
                matched_destination = d
                break
        
        if matched_destination:
            self._current_player.current_location = matched_destination
            self._current_location = matched_destination
            
            # Registrar evento
            self._turn_events.append({
                "type": "movement",
                "from": old_location,
                "to": matched_destination
            })
            
            return {
                "success": True,
                "from_location": old_location,
                "to_location": matched_destination,
                "message": f"Você viaja de {old_location} para {matched_destination}."
            }
        else:
            return {
                "success": False,
                "message": f"Você não conhece o caminho para '{destination}'.",
                "valid_destinations": destinations
            }
    
    async def _tool_generate_npc_reactions(
        self,
        action_type: str,
        action_result: str
    ) -> Dict[str, Any]:
        """Gera reações dos NPCs à ação do jogador."""
        reactions = []
        
        for npc in self._npcs_in_scene[:3]:
            emotional = getattr(npc, 'emotional_state', 'neutral')
            
            if action_type == "combat":
                if emotional == 'hostile':
                    reactions.append(f"{npc.name} se prepara para lutar!")
                elif emotional == 'scared':
                    reactions.append(f"{npc.name} recua em pânico!")
                else:
                    reactions.append(f"{npc.name} observa o combate com cautela.")
            
            elif action_type == "dialogue":
                if emotional == 'friendly':
                    reactions.append(f"{npc.name} escuta com interesse.")
                else:
                    reactions.append(f"{npc.name} mantém distância.")
            
            elif action_type == "movement":
                reactions.append(f"{npc.name} observa você partir.")
        
        return {"reactions": reactions}
    
    async def _tool_generate_narration(
        self,
        action_result: str,
        style: str = "exploration"
    ) -> Dict[str, Any]:
        """Gera narrativa usando o Narrator cognitivo."""
        if not self._current_player:
            return {"error": "Jogador não carregado"}
        
        style_map = {
            "exploration": NarrativeStyle.EXPLORATION,
            "combat": NarrativeStyle.COMBAT,
            "dialogue": NarrativeStyle.DIALOGUE,
            "opening": NarrativeStyle.OPENING,
            "rest": NarrativeStyle.REST,
        }
        
        narrative_style = style_map.get(style, NarrativeStyle.EXPLORATION)
        
        try:
            narration = await self._narrator.narrate(
                player=self._current_player,
                location=self._current_location,
                npcs_in_scene=self._npcs_in_scene,
                player_action=action_result,
                style=narrative_style
            )
            
            return {
                "success": True,
                "narration": narration,
                "style": style
            }
        except Exception as e:
            # Fallback simples
            return {
                "success": True,
                "narration": f"Em {self._current_location}, {action_result}",
                "style": style,
                "note": f"Fallback usado: {str(e)}"
            }
    
    async def _tool_finalize_turn(
        self,
        scene_description: str,
        action_result: str,
        events: str = "[]"
    ) -> Dict[str, Any]:
        """Finaliza o turno."""
        try:
            events_list = json.loads(events) if events else []
        except:
            events_list = []
        
        # Combinar com eventos registrados durante o turno
        all_events = self._turn_events + events_list
        
        return {
            "finalized": True,
            "scene_description": scene_description,
            "action_result": action_result,
            "events": all_events,
            "player_location": self._current_location,
            "world_time": world_clock.get_current_datetime().isoformat()
        }
    
    # ==================== MÉTODOS PRINCIPAIS ====================
    
    async def process_turn(
        self,
        player: Player,
        player_input: str,
        npcs_in_scene: List[NPC],
        previous_narration: str = "",
        is_first_scene: bool = False
    ) -> TurnResult:
        """
        Processa um turno completo do jogador.
        
        Este é o método principal que orquestra todo o fluxo.
        """
        import time
        start_time = time.time()
        
        # Configurar contexto
        self._current_player = player
        self._current_location = player.current_location or "Initial Village"
        self._npcs_in_scene = npcs_in_scene
        self._turn_events = []
        
        # Avançar tempo
        time_result = world_clock.advance_turn()
        current_time = world_clock.get_current_datetime()
        
        # Se for primeira cena, usar fluxo simplificado
        if is_first_scene:
            return await self._process_first_scene(player, current_time, start_time)
        
        # Construir task para o agente
        npc_names = [npc.name for npc in npcs_in_scene[:5]]
        
        task = f"""Processe o turno do jogador.

Jogador: {player.name} (Rank {player.cultivation_rank})
Localização: {self._current_location}
NPCs na cena: {npc_names}

Ação do jogador: "{player_input}"

Contexto anterior: "{previous_narration[-300:]}"

Siga este fluxo:
1. Use parse_player_action para interpretar a ação
2. Execute a ação apropriada (execute_combat, execute_dialogue, ou execute_movement)
3. Gere reações dos NPCs se necessário
4. Use generate_narration para criar a descrição da cena
5. Use finalize_turn para completar o processamento

Retorne um turno completo e coerente."""
        
        context = {
            "player_name": player.name,
            "player_input": player_input,
            "location": self._current_location,
            "npcs": npc_names,
            "time": current_time.isoformat()
        }
        
        # Executar agente
        trace = await self.run(task=task, context=context)
        
        # Extrair resultado
        result = self._extract_turn_result(
            trace=trace,
            player=player,
            player_input=player_input,
            current_time=current_time,
            start_time=start_time
        )
        
        return result
    
    async def _process_first_scene(
        self,
        player: Player,
        current_time: datetime,
        start_time: float
    ) -> TurnResult:
        """Processa a primeira cena (abertura)."""
        import time
        
        try:
            narration = await self._narrator.narrate(
                player=player,
                location=self._current_location,
                npcs_in_scene=self._npcs_in_scene,
                style=NarrativeStyle.OPENING
            )
        except Exception as e:
            # Fallback
            date_str = current_time.strftime("%d do Mês %m, Ano %Y")
            narration = f"""📍 **{date_str} | Aurora | {self._current_location}**

A jornada de {player.name} começa em {self._current_location}. O ar carrega promessas de aventuras por vir.

O mundo de Orbis aguarda suas decisões."""
        
        return TurnResult(
            turn_number=1,
            player_input="",
            parsed_action=None,
            scene_description=narration,
            action_result="Início da jornada.",
            player_state=self._player_to_dict(player),
            npcs_in_scene=[self._npc_to_dict(npc) for npc in self._npcs_in_scene],
            location=self._current_location,
            world_time=current_time.isoformat(),
            events=[{"type": "game_start", "player": player.name}],
            success=True,
            processing_time_ms=(time.time() - start_time) * 1000
        )
    
    def _extract_turn_result(
        self,
        trace,
        player: Player,
        player_input: str,
        current_time: datetime,
        start_time: float
    ) -> TurnResult:
        """Extrai TurnResult do trace do agente."""
        import time
        
        scene_description = ""
        action_result = ""
        parsed_action = None
        events = []
        
        # Procurar resultados nas observações
        for step in trace.steps:
            if step.observation:
                obs = step.observation
                
                # Extrair narração
                if "narration" in obs and "success" in obs:
                    try:
                        if "✓" in obs:
                            obs = obs.split(":", 1)[1].strip()
                        data = json.loads(obs)
                        scene_description = data.get("narration", "")
                    except:
                        pass
                
                # Extrair resultado finalizado
                if "finalized" in obs:
                    try:
                        if "✓" in obs:
                            obs = obs.split(":", 1)[1].strip()
                        data = json.loads(obs)
                        if not scene_description:
                            scene_description = data.get("scene_description", "")
                        action_result = data.get("action_result", "")
                        events = data.get("events", [])
                    except:
                        pass
                
                # Extrair ação parseada
                if "intent" in obs and "confidence" in obs:
                    try:
                        if "✓" in obs:
                            obs = obs.split(":", 1)[1].strip()
                        data = json.loads(obs)
                        intent_str = data.get("intent", "unknown")
                        parsed_action = ParsedAction(
                            intent=ActionIntent(intent_str) if intent_str in [e.value for e in ActionIntent] else ActionIntent.UNKNOWN,
                            raw_input=player_input,
                            target_name=data.get("target_name"),
                            skill_name=data.get("skill_name"),
                            destination=data.get("destination"),
                            spoken_words=data.get("spoken_words"),
                            confidence=data.get("confidence", 0.5)
                        )
                    except:
                        pass
        
        # Fallback se não encontrou narrativa
        if not scene_description:
            scene_description = trace.final_answer or f"Em {self._current_location}, {player.name} continua sua jornada."
        
        if not action_result:
            action_result = f"Você executou: {player_input}"
        
        # Combinar eventos do turno
        all_events = self._turn_events + events
        
        return TurnResult(
            turn_number=0,  # Será atualizado externamente
            player_input=player_input,
            parsed_action=parsed_action,
            scene_description=scene_description,
            action_result=action_result,
            player_state=self._player_to_dict(player),
            npcs_in_scene=[self._npc_to_dict(npc) for npc in self._npcs_in_scene],
            location=self._current_location,
            world_time=current_time.isoformat(),
            events=all_events,
            success=True,
            processing_time_ms=(time.time() - start_time) * 1000
        )
    
    def _player_to_dict(self, player: Player) -> Dict[str, Any]:
        """Converte Player para dicionário."""
        return {
            "id": player.id,
            "name": player.name,
            "cultivation_rank": player.cultivation_rank,
            "current_hp": player.current_hp,
            "max_hp": player.max_hp,
            "yuan_qi": getattr(player, 'yuan_qi', 100),
            "gold": player.gold,
            "current_location": player.current_location,
            "learned_skills": player.learned_skills[:5] if player.learned_skills else []
        }
    
    def _npc_to_dict(self, npc: NPC) -> Dict[str, Any]:
        """Converte NPC para dicionário."""
        return {
            "id": npc.id,
            "name": npc.name,
            "rank": npc.rank,
            "current_hp": npc.current_hp,
            "max_hp": npc.max_hp,
            "emotional_state": getattr(npc, 'emotional_state', 'neutral'),
            "species": getattr(npc, 'species', 'human'),
            "can_speak": getattr(npc, 'can_speak', True)
        }
    
    async def quick_process(
        self,
        player: Player,
        player_input: str,
        npcs_in_scene: List[NPC]
    ) -> Dict[str, Any]:
        """
        Processamento rápido sem usar agente ReAct completo.
        Para ações simples onde velocidade é prioridade.
        """
        # Configurar contexto
        self._current_player = player
        self._current_location = player.current_location or "Initial Village"
        self._npcs_in_scene = npcs_in_scene
        
        # Parsear ação
        parsed = await self._referee.parse_action(
            player_input=player_input,
            player=player,
            possible_targets=npcs_in_scene,
            current_location=self._current_location
        )
        
        # Executar ação baseada na intenção
        action_result = ""
        
        if parsed.intent == ActionIntent.ATTACK:
            combat_result = await self._tool_execute_combat(
                attacker_is_player=True,
                target_name=parsed.target_name or "",
                skill_name=parsed.skill_name or "basic_attack"
            )
            action_result = combat_result.get("message", "Ação de combate executada.")
        
        elif parsed.intent in [ActionIntent.TALK, ActionIntent.PERSUADE, ActionIntent.INTIMIDATE]:
            dialogue_result = await self._tool_execute_dialogue(
                npc_name=parsed.target_name or "",
                player_words=parsed.spoken_words or player_input,
                tone=parsed.tone or "neutral"
            )
            action_result = dialogue_result.get("response", "Interação concluída.")
        
        elif parsed.intent == ActionIntent.MOVE:
            move_result = await self._tool_execute_movement(
                destination=parsed.destination or ""
            )
            action_result = move_result.get("message", "Movimento executado.")
        
        elif parsed.intent in [ActionIntent.MEDITATE, ActionIntent.CULTIVATE]:
            qi_gain = 10 * player.rank
            player.yuan_qi = min(getattr(player, 'max_yuan_qi', 200), getattr(player, 'yuan_qi', 100) + qi_gain)
            action_result = f"Você medita e recupera {qi_gain} Yuan Qi."
        
        elif parsed.intent == ActionIntent.OBSERVE:
            if npcs_in_scene:
                npc_names = [npc.name for npc in npcs_in_scene[:5]]
                action_result = f"Você observa: {', '.join(npc_names)}."
            else:
                action_result = "O local parece vazio."
        
        else:
            action_result = f"Você {player_input}."
        
        return {
            "parsed_action": parsed.to_dict(),
            "action_result": action_result,
            "location": self._current_location,
            "player_hp": f"{player.current_hp}/{player.max_hp}"
        }
