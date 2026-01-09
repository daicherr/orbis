"""
Cognitive Narrator - Narrador com Capacidades Cognitivas
GEM RPG ORBIS - Arquitetura Cognitiva

O Narrador Cognitivo usa o framework ReAct para:
1. Consultar memórias dos NPCs antes de narrar
2. Buscar lore relevante para a cena
3. Verificar estado do mundo e clima
4. Gerar narrativas contextualizadas e consistentes

Este é o "Cronista do Crepúsculo" - conta a história do mundo.
"""

from typing import Dict, List, Any, Optional, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

from app.agents.react_agent import ReActAgent, Tool
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.core.chronos import world_clock
from app.services.lore_cache import lore_cache


class NarrativeStyle(str, Enum):
    """Estilos narrativos disponíveis."""
    OPENING = "opening"       # Cena de abertura
    EXPLORATION = "exploration"  # Exploração de ambiente
    DIALOGUE = "dialogue"     # Conversa com NPC
    COMBAT = "combat"         # Cena de combate
    CULTIVATION = "cultivation"  # Meditação/cultivo
    TRAVEL = "travel"         # Viagem entre locais
    REST = "rest"             # Descanso/recuperação
    DISCOVERY = "discovery"   # Descoberta de algo novo


@dataclass
class NarrativeContext:
    """Contexto completo para geração de narrativa."""
    player: Player
    location: str
    npcs_in_scene: List[NPC]
    player_action: str
    previous_narration: str
    style: NarrativeStyle
    
    # Contexto enriquecido (preenchido pelo agente)
    time_info: Optional[Dict[str, str]] = None
    weather_info: Optional[Dict[str, Any]] = None
    location_details: Optional[Dict[str, Any]] = None
    npc_memories: List[Dict[str, str]] = field(default_factory=list)
    relevant_lore: str = ""
    recent_events: List[str] = field(default_factory=list)
    
    # Configurações de geração
    max_words: int = 250
    include_sensory: bool = True
    show_npc_reactions: bool = True


class CognitiveNarrator(ReActAgent):
    """
    Narrador que usa ReAct para gerar narrativas contextualizadas.
    
    Diferente do Narrator simples, este pode:
    - Consultar memórias de NPCs antes de descrever reações
    - Buscar lore específica para o contexto
    - Verificar eventos recentes que afetam a cena
    - Adaptar o estilo baseado no tipo de ação
    """
    
    def __init__(
        self,
        gemini_client: Any,
        max_iterations: int = 4,
        verbose: bool = False
    ):
        super().__init__(
            name="CognitiveNarrator",
            gemini_client=gemini_client,
            max_iterations=max_iterations,
            verbose=verbose
        )
        
        # Contexto atual (preenchido em cada chamada)
        self._context: Optional[NarrativeContext] = None
        self._lore_cache = lore_cache
        
        # Repositórios (injetados quando disponíveis)
        self._memory_repo = None
        self._location_repo = None
        self._event_repo = None
    
    def set_repositories(
        self,
        memory_repo=None,
        location_repo=None,
        event_repo=None
    ):
        """Injeta repositórios para acesso a dados."""
        self._memory_repo = memory_repo
        self._location_repo = location_repo
        self._event_repo = event_repo
    
    def _build_system_prompt(self) -> str:
        """System prompt do Narrador Cognitivo."""
        return """Você é o NARRADOR COGNITIVO de um RPG de Cultivo estilo Wuxia/Xianxia.

Seu papel é GERAR NARRATIVAS ricas e imersivas, consultando o contexto do mundo
antes de escrever.

═══════════════════════════════════════════════════════════════════
                        REGRAS ABSOLUTAS (NUNCA VIOLAR)
═══════════════════════════════════════════════════════════════════

❌ PROIBIDO - NUNCA FAÇA ISSO:
• Mencionar stats, tiers, HP, XP ou mecânicas de jogo
• Dizer "sua constituição Godfiend/Mortal/etc" diretamente
• Perguntar "O que você faz?" ou sugerir ações
• Dar recompensas narrativas gratuitas
• Terminar com perguntas retóricas

✅ OBRIGATÓRIO - SEMPRE FAÇA:
• Use as FERRAMENTAS para buscar contexto ANTES de narrar
• Descreva sensações físicas sutis (calor, frio, arrepios)
• NPCs reagem com base em suas MEMÓRIAS do jogador
• O mundo tem consequências reais
• Encerre de forma aberta, mas sem empurrar

═══════════════════════════════════════════════════════════════════
                        PROCESSO DE NARRAÇÃO
═══════════════════════════════════════════════════════════════════

1. ANALISE a ação do jogador
2. USE FERRAMENTAS para buscar:
   - Memórias dos NPCs presentes
   - Lore relevante para a cena
   - Estado do tempo e clima
   - Eventos recentes no local
3. CONSTRUA a narrativa integrando todo o contexto
4. Use a ferramenta final_narration para entregar o texto

ESTILO:
• Tom: Épico mas contido, como autor de wuxia
• Extensão: 150-250 palavras (máximo 300 em combate)
• Estrutura: Header temporal → Ambiente → Ação → Consequência"""
    
    def _get_tools(self) -> List[Tool]:
        """Ferramentas disponíveis para o Narrador."""
        return [
            Tool(
                name="get_npc_memories",
                description="Busca memórias de um NPC específico sobre o jogador ou evento",
                parameters={
                    "npc_name": {"type": "string", "description": "Nome do NPC"},
                    "query": {"type": "string", "description": "O que buscar nas memórias"}
                },
                handler=self._tool_get_npc_memories
            ),
            Tool(
                name="search_lore",
                description="Busca informações de lore relevantes para um tópico",
                parameters={
                    "topic": {"type": "string", "description": "Tópico a buscar (ex: 'Floresta Nublada', 'cultivo', 'dragões')"}
                },
                handler=self._tool_search_lore
            ),
            Tool(
                name="get_time_and_weather",
                description="Retorna informações sobre hora, período do dia e clima",
                parameters={},
                handler=self._tool_get_time_and_weather
            ),
            Tool(
                name="get_location_details",
                description="Retorna detalhes sobre a localização atual",
                parameters={
                    "location_name": {"type": "string", "description": "Nome do local"}
                },
                handler=self._tool_get_location_details
            ),
            Tool(
                name="get_recent_events",
                description="Retorna eventos recentes no local atual",
                parameters={
                    "location": {"type": "string", "description": "Nome do local"},
                    "hours_ago": {"type": "number", "description": "Quantas horas atrás buscar (default: 24)"}
                },
                handler=self._tool_get_recent_events
            ),
            Tool(
                name="analyze_npc_state",
                description="Analisa o estado emocional e físico de um NPC na cena",
                parameters={
                    "npc_name": {"type": "string", "description": "Nome do NPC"}
                },
                handler=self._tool_analyze_npc_state
            ),
            Tool(
                name="generate_narration",
                description="Gera a narrativa final. Use DEPOIS de coletar contexto.",
                parameters={
                    "header": {"type": "string", "description": "Cabeçalho temporal (📍 Data | Período | Local)"},
                    "scene_description": {"type": "string", "description": "Descrição da cena (1-3 parágrafos)"},
                    "reasoning": {"type": "string", "description": "Seu raciocínio sobre como integrou o contexto"}
                },
                handler=self._tool_generate_narration
            ),
        ]
    
    # ==================== FERRAMENTAS INTERNAS ====================
    
    async def _tool_get_npc_memories(self, npc_name: str, query: str) -> Dict[str, Any]:
        """Busca memórias de um NPC."""
        if not self._context:
            return {"error": "Contexto não inicializado"}
        
        # Encontrar o NPC pelo nome
        target_npc = None
        for npc in self._context.npcs_in_scene:
            if npc.name.lower() == npc_name.lower() or npc_name.lower() in npc.name.lower():
                target_npc = npc
                break
        
        if not target_npc:
            return {"memories": [], "note": f"NPC '{npc_name}' não encontrado na cena"}
        
        # Se temos memory_repo, buscar memórias reais
        if self._memory_repo and hasattr(target_npc, 'id') and target_npc.id:
            try:
                memories = await self._memory_repo.find_relevant_memories(
                    npc_id=target_npc.id,
                    query_text=query,
                    limit=3
                )
                if memories:
                    return {
                        "npc_name": target_npc.name,
                        "memories": [
                            m.get("content", str(m)) if isinstance(m, dict) else str(m)
                            for m in memories
                        ]
                    }
            except Exception as e:
                pass
        
        # Fallback: gerar memórias baseadas no estado do NPC
        emotional_state = getattr(target_npc, 'emotional_state', 'neutro')
        relationship = getattr(target_npc, 'relationships', {}).get(self._context.player.name, 0)
        
        memories = []
        if relationship > 0:
            memories.append(f"Lembrança positiva de interação anterior com {self._context.player.name}")
        elif relationship < 0:
            memories.append(f"Lembrança negativa de conflito anterior com {self._context.player.name}")
        
        return {
            "npc_name": target_npc.name,
            "emotional_state": emotional_state,
            "relationship_value": relationship,
            "memories": memories if memories else ["Nenhuma memória específica"]
        }
    
    async def _tool_search_lore(self, topic: str) -> Dict[str, Any]:
        """Busca lore relevante."""
        lore_text = self._lore_cache.get_context() or ""
        
        if not lore_text:
            return {"lore": "", "note": "Lore não carregada"}
        
        # Buscar seções relevantes
        topic_lower = topic.lower()
        relevant_sections = []
        
        # Dividir lore em seções
        sections = lore_text.split("---")
        for section in sections:
            if topic_lower in section.lower():
                # Pegar um trecho relevante (max 500 chars)
                relevant_sections.append(section[:500].strip())
        
        if relevant_sections:
            return {
                "topic": topic,
                "lore": relevant_sections[0],
                "additional_sections": len(relevant_sections) - 1
            }
        
        # Fallback: retornar resumo geral
        return {
            "topic": topic,
            "lore": f"Mundo de cultivo onde {topic} pode existir. Use sua imaginação baseada no contexto.",
            "note": "Lore específica não encontrada, use contexto geral"
        }
    
    async def _tool_get_time_and_weather(self) -> Dict[str, Any]:
        """Retorna informações de tempo e clima."""
        current_dt = world_clock.get_current_datetime()
        hour = current_dt.hour
        
        # Período do dia
        if 5 <= hour < 7:
            period = "Aurora"
            light = "Luz dourada nascente"
            atmosphere = "O mundo desperta"
        elif 7 <= hour < 12:
            period = "Manhã"
            light = "Sol claro"
            atmosphere = "Atividade crescente"
        elif 12 <= hour < 14:
            period = "Meio-dia"
            light = "Sol a pino"
            atmosphere = "Calor intenso"
        elif 14 <= hour < 18:
            period = "Tarde"
            light = "Sol inclinado"
            atmosphere = "Sombras alongadas"
        elif 18 <= hour < 20:
            period = "Crepúsculo"
            light = "Céu alaranjado"
            atmosphere = "Transição para a noite"
        elif 20 <= hour < 23:
            period = "Noite"
            light = "Lua e estrelas"
            atmosphere = "Silêncio noturno"
        else:
            period = "Madrugada"
            light = "Escuridão profunda"
            atmosphere = "O mundo dorme"
        
        # Clima (placeholder - pode ser conectado a sistema real)
        weather = "céu limpo"  # TODO: integrar com sistema de clima
        
        return {
            "date": current_dt.strftime("%d do Mês %m, Ano %Y"),
            "hour": hour,
            "period": period,
            "light_description": light,
            "atmosphere": atmosphere,
            "weather": weather,
            "header": f"📍 {current_dt.strftime('%d do Mês %m, Ano %Y')} | {period} | {self._context.location if self._context else 'Desconhecido'}"
        }
    
    async def _tool_get_location_details(self, location_name: str) -> Dict[str, Any]:
        """Retorna detalhes do local."""
        # Descrições de locais conhecidos
        location_data = {
            "Initial Village": {
                "type": "Vila",
                "description": "Uma pequena vila agrícola cercada por campos de arroz",
                "ambiance": "Pacata, com ruídos de animais e trabalhadores",
                "smells": "Terra molhada, fumaça de cozinha, grama",
                "population": "Cerca de 200 habitantes"
            },
            "Misty Forest": {
                "type": "Floresta",
                "description": "Floresta densa envolta em névoa perpétua",
                "ambiance": "Misteriosa, sons abafados, sensação de ser observado",
                "smells": "Musgo, folhas em decomposição, umidade",
                "danger": "Criaturas selvagens e bestas espirituais"
            },
            "Dragon Mountains": {
                "type": "Montanhas",
                "description": "Picos nevados onde lendas dizem que dragões habitam",
                "ambiance": "Majestoso, vento cortante, solidão",
                "smells": "Ar rarefeito, neve, rocha antiga",
                "danger": "Clima extremo e bestas poderosas"
            },
            "Merchant City": {
                "type": "Cidade",
                "description": "Metrópole comercial com mercados imensos",
                "ambiance": "Caótica, vozes de mercadores, música de rua",
                "smells": "Especiarias, incenso, comida de rua",
                "population": "Dezenas de milhares"
            },
        }
        
        data = location_data.get(location_name, {
            "type": "Desconhecido",
            "description": f"Uma região chamada {location_name}",
            "ambiance": "Atmosfera indefinida",
            "smells": "Ar fresco"
        })
        
        return {
            "location": location_name,
            **data
        }
    
    async def _tool_get_recent_events(self, location: str, hours_ago: int = 24) -> Dict[str, Any]:
        """Retorna eventos recentes no local."""
        # Por enquanto, retorna eventos placeholder
        # TODO: integrar com sistema real de eventos
        events = []
        
        # Eventos genéricos baseados no contexto
        if self._context and self._context.npcs_in_scene:
            for npc in self._context.npcs_in_scene[:2]:
                emotional = getattr(npc, 'emotional_state', 'neutro')
                if emotional == 'irritado':
                    events.append(f"{npc.name} teve uma discussão recente")
                elif emotional == 'animado':
                    events.append(f"{npc.name} parece ter recebido boas notícias")
        
        return {
            "location": location,
            "hours_checked": hours_ago,
            "events": events if events else ["Nenhum evento significativo recente"]
        }
    
    async def _tool_analyze_npc_state(self, npc_name: str) -> Dict[str, Any]:
        """Analisa estado de um NPC."""
        if not self._context:
            return {"error": "Contexto não inicializado"}
        
        # Encontrar NPC
        target_npc = None
        for npc in self._context.npcs_in_scene:
            if npc.name.lower() == npc_name.lower() or npc_name.lower() in npc.name.lower():
                target_npc = npc
                break
        
        if not target_npc:
            return {"error": f"NPC '{npc_name}' não encontrado"}
        
        # Extrair informações
        species = getattr(target_npc, 'species', 'human')
        can_speak = getattr(target_npc, 'can_speak', True)
        emotional = getattr(target_npc, 'emotional_state', 'neutro')
        traits = getattr(target_npc, 'personality_traits', [])
        current_activity = getattr(target_npc, 'current_activity', 'idle')
        
        # Descrição comportamental
        behavior = "comportamento normal"
        if emotional == 'irritado':
            behavior = "tenso e impaciente"
        elif emotional == 'feliz':
            behavior = "relaxado e receptivo"
        elif emotional == 'triste':
            behavior = "cabisbaixo e silencioso"
        elif emotional == 'assustado':
            behavior = "nervoso e vigilante"
        
        return {
            "name": target_npc.name,
            "species": species,
            "can_speak": can_speak,
            "emotional_state": emotional,
            "behavior": behavior,
            "personality_traits": traits[:3] if traits else ["desconhecido"],
            "current_activity": current_activity,
            "description_suggestion": f"{target_npc.name} parece {behavior}"
        }
    
    async def _tool_generate_narration(
        self,
        header: str,
        scene_description: str,
        reasoning: str
    ) -> Dict[str, Any]:
        """Gera a narrativa final."""
        # Combinar header com descrição
        full_narration = f"{header}\n\n{scene_description}"
        
        return {
            "narration_ready": True,
            "full_text": full_narration,
            "word_count": len(scene_description.split()),
            "reasoning": reasoning
        }
    
    # ==================== MÉTODO PRINCIPAL ====================
    
    async def narrate(
        self,
        player: Player,
        location: str,
        npcs_in_scene: List[NPC],
        player_action: str = "",
        previous_narration: str = "",
        style: NarrativeStyle = NarrativeStyle.EXPLORATION,
        max_words: int = 250
    ) -> str:
        """
        Gera uma narrativa completa usando o processo ReAct.
        
        Args:
            player: Objeto Player
            location: Localização atual
            npcs_in_scene: NPCs na cena
            player_action: Última ação do jogador
            previous_narration: Narração anterior (para continuidade)
            style: Estilo narrativo
            max_words: Limite de palavras
            
        Returns:
            Texto narrativo gerado
        """
        # Criar contexto
        self._context = NarrativeContext(
            player=player,
            location=location,
            npcs_in_scene=npcs_in_scene,
            player_action=player_action,
            previous_narration=previous_narration,
            style=style,
            max_words=max_words
        )
        
        # Construir task description
        npc_names = [npc.name for npc in npcs_in_scene]
        
        if style == NarrativeStyle.OPENING:
            task = f"""Gere a CENA DE ABERTURA para {player.name} chegando em {location}.
NPCs presentes: {npc_names}.
Limite: {max_words} palavras.
Use as ferramentas para buscar contexto antes de narrar."""
        
        elif style == NarrativeStyle.COMBAT:
            task = f"""Narre o resultado de combate.
Ação do jogador: "{player_action}"
Local: {location}
Alvos possíveis: {npc_names}
Limite: {max_words} palavras.
Foque em impacto visceral e consequências."""
        
        elif style == NarrativeStyle.DIALOGUE:
            task = f"""Narre uma interação social.
Jogador disse/fez: "{player_action}"
NPCs presentes: {npc_names}
Local: {location}
Limite: {max_words} palavras.
Consulte memórias dos NPCs para colorir reações."""
        
        else:
            task = f"""Continue a narrativa respondendo à ação do jogador.
Ação: "{player_action}"
Local: {location}
NPCs: {npc_names}
Contexto anterior: "{previous_narration[-200:]}"
Limite: {max_words} palavras."""
        
        # Contexto adicional
        context = {
            "player_name": player.name,
            "player_tier": player.cultivation_rank,
            "location": location,
            "npcs": [
                {
                    "name": npc.name,
                    "emotional_state": getattr(npc, 'emotional_state', 'neutro'),
                    "can_speak": getattr(npc, 'can_speak', True)
                }
                for npc in npcs_in_scene[:5]
            ],
            "style": style.value,
            "max_words": max_words
        }
        
        # Executar agente
        trace = await self.run(task=task, context=context)
        
        # Extrair narrativa do resultado
        if trace.final_answer:
            return self._extract_narration(trace)
        else:
            # Fallback se algo falhou
            return self._generate_fallback_narration()
    
    def _extract_narration(self, trace) -> str:
        """Extrai a narrativa do trace do agente."""
        # Procurar pelo resultado de generate_narration
        for step in reversed(trace.steps):
            if step.observation and "narration_ready" in step.observation:
                try:
                    # Extrair o texto da observação
                    obs = step.observation
                    if "full_text" in obs:
                        # Parse JSON
                        import json
                        if "✓" in obs:
                            obs = obs.split(":", 1)[1].strip()
                        data = json.loads(obs)
                        return data.get("full_text", trace.final_answer or "")
                except:
                    pass
        
        # Fallback para final_answer
        return trace.final_answer or self._generate_fallback_narration()
    
    def _generate_fallback_narration(self) -> str:
        """Gera narrativa de fallback se o agente falhar."""
        if not self._context:
            return "O mundo aguarda sua ação..."
        
        # Gerar narrativa mínima
        current_dt = world_clock.get_current_datetime()
        hour = current_dt.hour
        
        if 5 <= hour < 12:
            period = "Manhã"
        elif 12 <= hour < 18:
            period = "Tarde"
        elif 18 <= hour < 21:
            period = "Crepúsculo"
        else:
            period = "Noite"
        
        date_str = current_dt.strftime("%d do Mês %m, Ano %Y")
        
        npc_text = ""
        if self._context.npcs_in_scene:
            npc_names = [npc.name for npc in self._context.npcs_in_scene[:3]]
            npc_text = f" {', '.join(npc_names)} {'estão' if len(npc_names) > 1 else 'está'} por perto."
        
        return f"""📍 **{date_str} | {period} | {self._context.location}**

O ar carrega a tensão do mundo em transformação. {self._context.player.name} observa o ambiente ao redor.{npc_text}

A atmosfera de {self._context.location} envolve tudo em um silêncio expectante."""


# ==================== INTEGRAÇÃO COM NARRATOR ORIGINAL ====================

class EnhancedNarrator:
    """
    Wrapper que combina o Narrator original com capacidades cognitivas.
    Pode usar o CognitiveNarrator quando mais contexto é necessário,
    ou o método direto quando velocidade é prioridade.
    """
    
    def __init__(self, gemini_client, lore_files_path: str = ""):
        self.gemini_client = gemini_client
        self._cognitive_narrator: Optional[CognitiveNarrator] = None
        self._lore_files_path = lore_files_path
        
        # Import do narrator original (lazy)
        self._original_narrator = None
    
    def _get_cognitive_narrator(self) -> CognitiveNarrator:
        """Lazy load do CognitiveNarrator."""
        if self._cognitive_narrator is None:
            self._cognitive_narrator = CognitiveNarrator(
                gemini_client=self.gemini_client,
                max_iterations=4,
                verbose=False
            )
        return self._cognitive_narrator
    
    def _get_original_narrator(self):
        """Lazy load do Narrator original."""
        if self._original_narrator is None:
            from app.agents.narrator import Narrator
            self._original_narrator = Narrator(
                gemini_client=self.gemini_client,
                lore_files_path=self._lore_files_path
            )
        return self._original_narrator
    
    async def narrate_cognitive(
        self,
        player: Player,
        location: str,
        npcs_in_scene: List[NPC],
        player_action: str = "",
        previous_narration: str = "",
        style: NarrativeStyle = NarrativeStyle.EXPLORATION
    ) -> str:
        """
        Usa o CognitiveNarrator para narrativas ricas em contexto.
        Ideal para momentos importantes da história.
        """
        narrator = self._get_cognitive_narrator()
        return await narrator.narrate(
            player=player,
            location=location,
            npcs_in_scene=npcs_in_scene,
            player_action=player_action,
            previous_narration=previous_narration,
            style=style
        )
    
    async def narrate_fast(
        self,
        player: Player,
        location: str,
        npcs_in_scene: List[NPC],
        player_action: str = "",
        previous_narration: str = ""
    ) -> str:
        """
        Usa o Narrator original para respostas rápidas.
        Ideal para ações simples onde velocidade é prioridade.
        """
        narrator = self._get_original_narrator()
        return await narrator.generate_scene_description_async(
            player=player,
            location=location,
            npcs_in_scene=npcs_in_scene,
            player_last_action=player_action,
            previous_narration=previous_narration
        )
    
    async def auto_narrate(
        self,
        player: Player,
        location: str,
        npcs_in_scene: List[NPC],
        player_action: str = "",
        previous_narration: str = "",
        is_important_moment: bool = False
    ) -> str:
        """
        Escolhe automaticamente entre cognitivo e rápido.
        
        Usa cognitivo quando:
        - É um momento importante marcado
        - Há NPCs com histórico com o jogador
        - A ação é complexa (combate, diálogo importante)
        
        Usa rápido quando:
        - Ações simples (olhar, andar)
        - Sem NPCs significativos
        - Velocidade é prioridade
        """
        # Determinar se precisa de abordagem cognitiva
        needs_cognitive = is_important_moment
        
        if not needs_cognitive and npcs_in_scene:
            # Verificar se há NPCs com relacionamento estabelecido
            for npc in npcs_in_scene:
                relationships = getattr(npc, 'relationships', {})
                if player.name in relationships:
                    needs_cognitive = True
                    break
        
        if not needs_cognitive:
            # Verificar se a ação é complexa
            complex_keywords = ['atacar', 'attack', 'lutar', 'negociar', 'trade', 'comprar', 'vender']
            action_lower = player_action.lower()
            if any(kw in action_lower for kw in complex_keywords):
                needs_cognitive = True
        
        if needs_cognitive:
            return await self.narrate_cognitive(
                player=player,
                location=location,
                npcs_in_scene=npcs_in_scene,
                player_action=player_action,
                previous_narration=previous_narration
            )
        else:
            return await self.narrate_fast(
                player=player,
                location=location,
                npcs_in_scene=npcs_in_scene,
                player_action=player_action,
                previous_narration=previous_narration
            )
