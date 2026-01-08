"""
Narrator - O Cronista do Crepúsculo
Sprint 8: Reescrito com diretrizes de narração SANDBOX
Sprint 14: Otimizado com LoreCache

Estilo: Novel interativa (Cang Yuan Tu + Northern Blade + Magic Emperor)
Princípio: O jogador é livre. O mundo é vivo. O narrador NÃO empurra ações.
"""

import os
from pathlib import Path
from typing import List, Optional
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.core.chronos import world_clock
from app.services.gemini_client import GeminiClient
from app.services.lore_cache import lore_cache
import asyncio


class Narrator:
    """
    O "Cronista do Crepúsculo" - Narrador do Códice Triluna.
    
    REGRAS FUNDAMENTAIS (Sprint 8):
    1. NUNCA mencionar explicitamente poderes/constituições do player
    2. NUNCA empurrar ações ou sugerir o que o player deve fazer
    3. NUNCA dar recompensas narrativas gratuitas
    4. SEMPRE descrever sensações de forma natural e implícita
    5. O mundo existe independente do player - NPCs têm vidas próprias
    """
    
    def __init__(self, gemini_client: GeminiClient, lore_files_path: str):
        self.gemini_client = gemini_client
        self.lore_files_path = lore_files_path
        # Sprint 14: Usa cache singleton em vez de carregar toda vez
        self.lore_context = lore_cache.get_context()

    def _load_lore(self) -> str:
        """Carrega todo o conteúdo dos arquivos de lore."""
        print("Carregando contexto de lore...")
        context_parts = []
        repo_root = Path(__file__).resolve().parents[3]
        lore_manual_path = repo_root / 'ruleset_source' / 'lore_manual'
        
        if os.path.exists(lore_manual_path):
            for filename in os.listdir(str(lore_manual_path)):
                if filename.endswith(".md"):
                    with open(lore_manual_path / filename, 'r', encoding='utf-8') as f:
                        context_parts.append(f"--- {filename.upper()} ---\n{f.read()}\n")
        
        print("Contexto de lore carregado.")
        return "\n".join(context_parts)

    def _get_time_period(self, hour: int) -> str:
        """Retorna o período do dia de forma poética."""
        if 5 <= hour < 7:
            return "Aurora"
        elif 7 <= hour < 12:
            return "Manhã"
        elif 12 <= hour < 14:
            return "Meio-dia"
        elif 14 <= hour < 18:
            return "Tarde"
        elif 18 <= hour < 20:
            return "Crepúsculo"
        elif 20 <= hour < 23:
            return "Noite"
        else:
            return "Madrugada"

    def _build_system_prompt(self) -> str:
        """
        System prompt FIXO do Narrador.
        Define personalidade e REGRAS RÍGIDAS de narração.
        """
        return """VOCÊ É O NARRADOR de uma novel de cultivo interativa.

═══════════════════════════════════════════════════════════════════
                        REGRAS ABSOLUTAS (NUNCA VIOLAR)
═══════════════════════════════════════════════════════════════════

❌ PROIBIDO - NUNCA FAÇA ISSO:
• Mencionar "sua constituição Godfiend/Mortal/etc" diretamente
• Dizer "você sente seu poder de tier X" ou "sua energia de rank Y"
• Perguntar "O que você faz?" ou variações
• Sugerir ações ("Você deveria ir ao norte", "Talvez você possa...")
• Dar recompensas gratuitas ("Você encontra uma espada lendária no chão!")
• Narrar pensamentos do personagem (ele pensa, não você)
• Usar termos de jogo (HP, XP, tier, rank, stats) na narrativa
• Terminar com perguntas retóricas ou convites à ação
• Descrever o personagem como "poderoso" ou "especial" sem contexto

✅ OBRIGATÓRIO - SEMPRE FAÇA ISSO:
• Descrever sensações físicas sutis (calor no dantian, frio nos meridianos)
• NPCs têm agendas próprias - não existem para servir o jogador
• Consequências reais para ações (atacar nobre = guardas aparecem)
• O mundo continua existindo mesmo quando o jogador não age
• Diálogos naturais - NPCs podem ignorar, mentir, ter pressa
• Ambiente reage ao jogador de forma sutil (olhares, silêncios)
• Encerrar cenas de forma aberta, mas sem empurrar

═══════════════════════════════════════════════════════════════════
                        ESTILO NARRATIVO
═══════════════════════════════════════════════════════════════════

Tom: Épico, mas contido. Como um autor de wuxia narrando, não um mestre de RPG.

Estrutura preferida:
📍 [Data | Período | Local]
[Parágrafo 1: Ambiente e atmosfera - o que os sentidos captam]
[Parágrafo 2: Ação/Reação - o que acontece em resposta ao jogador]
[Parágrafo 3 (opcional): Detalhe ou tensão adicional]

Exemplo de SENSAÇÃO IMPLÍCITA (em vez de dizer "você é Godfiend"):
❌ ERRADO: "Sua constituição Godfiend faz você sentir fome."
✅ CERTO: "Uma inquietação familiar rasteja pelo seu ventre — não é fome comum, 
   é algo mais antigo, que reconhece o cheiro de sangue fresco no ar."

Exemplo de ENCERRAMENTO ABERTO:
❌ ERRADO: "O que você faz agora?"
✅ CERTO: "O vendedor volta a arrumar suas frutas, fingindo não ter visto nada."
   (O jogador decide naturalmente o que fazer - você não precisa perguntar)

═══════════════════════════════════════════════════════════════════
                        TRATAMENTO DE AÇÕES
═══════════════════════════════════════════════════════════════════

• "olhar ao redor" → Descreva o ambiente de forma viva, com tensões ocultas
• "falar com X" → O NPC responde com personalidade própria, pode não cooperar
• "atacar X" → Descreva o impacto visceral, consequências imediatas
• "meditar/cultivar" → Descreva sensações internas sutis, passagem de tempo
• "viajar para X" → Descreva a jornada, não teleporte instantâneo
• Ação vaga → Interprete razoavelmente, mas não assuma demais

O jogador é o PROTAGONISTA, mas não o CENTRO DO UNIVERSO.
O mundo existia antes dele e continuará depois."""

    def _build_scene_context(
        self, 
        player: Player, 
        location: str, 
        npcs_in_scene: List[NPC],
        memory_context: str = ""
    ) -> str:
        """
        Constrói o contexto da cena APENAS com informações úteis.
        O narrador usa isso internamente, mas NÃO expõe ao jogador.
        """
        current_dt = world_clock.get_current_datetime()
        time_period = self._get_time_period(current_dt.hour)
        date_str = current_dt.strftime("%d do Mês %m, Ano %Y")
        
        # NPCs formatados de forma útil para o narrador
        npc_descriptions = []
        for npc in npcs_in_scene:
            emotional = getattr(npc, 'emotional_state', 'neutro')
            traits = getattr(npc, 'personality_traits', [])
            traits_str = ", ".join(traits[:3]) if traits else "desconhecido"
            npc_descriptions.append(
                f"- {npc.name}: humor {emotional}, personalidade [{traits_str}]"
            )
        
        npcs_text = "\n".join(npc_descriptions) if npc_descriptions else "Ninguém visível."
        
        # Informações do player (para o narrador usar IMPLICITAMENTE)
        player_context = f"""
[INFORMAÇÕES INTERNAS - USE IMPLICITAMENTE, NÃO MENCIONE DIRETAMENTE]
Nome do protagonista: {player.name}
Nível de poder: Iniciante (tier {getattr(player, 'cultivation_tier', 1)})
Tipo físico: {getattr(player, 'constitution_type', 'comum')} 
Estado físico: {'ferido' if getattr(player, 'current_hp', 100) < getattr(player, 'max_hp', 100) * 0.5 else 'saudável'}
Recursos energéticos: {'baixos' if getattr(player, 'yuan_qi', 100) < 30 else 'normais'}
Origem: {getattr(player, 'origin_location', 'desconhecida')}
"""
        
        return f"""
═══════════════════════════════════════════════════════════════════
CONTEXTO DA CENA (Referência interna do narrador)
═══════════════════════════════════════════════════════════════════
📍 {date_str} | {time_period} | {location}

NPCs PRESENTES:
{npcs_text}

{player_context}

{memory_context}
═══════════════════════════════════════════════════════════════════
"""

    async def generate_scene_description_async(
        self, 
        player: Player, 
        location: str, 
        npcs_in_scene: List[NPC],
        player_last_action: str = "",
        previous_narration: str = "",
        memory_repo = None,
        is_first_scene: bool = False
    ) -> str:
        """
        Gera uma descrição de cena no estilo novel interativa.
        Sprint 8: Sandbox - não empurra ações, não menciona poderes explicitamente.
        """
        current_dt = world_clock.get_current_datetime()
        time_period = self._get_time_period(current_dt.hour)
        date_str = current_dt.strftime("%d do Mês %m, Ano %Y")
        
        # === BUSCA DE MEMÓRIAS (RAG) ===
        memory_context = ""
        if memory_repo and npcs_in_scene:
            try:
                query = f"{player.name} {player_last_action[:50] if player_last_action else 'interação'}"
                relevant_memories = []
                for npc in npcs_in_scene[:2]:
                    mems = await memory_repo.find_relevant_memories(npc.id, query, limit=1)
                    if mems:
                        relevant_memories.append(f"{npc.name} lembra: {mems[0]}")
                
                if relevant_memories:
                    memory_context = "\n[MEMÓRIAS DOS NPCs - Use para colorir reações]\n" + "\n".join(relevant_memories)
            except Exception as e:
                print(f"[WARN] Erro ao buscar memórias: {e}")

        # === MONTAGEM DO PROMPT ===
        system_prompt = self._build_system_prompt()
        scene_context = self._build_scene_context(player, location, npcs_in_scene, memory_context)
        
        # Cabeçalho para incluir na resposta
        header = f"📍 **{date_str} | {time_period} | {location}**"

        # === PROMPT DE AÇÃO ===
        if is_first_scene:
            backstory = getattr(player, 'backstory', '')
            appearance = getattr(player, 'appearance', '')
            first_context = getattr(player, 'first_scene_context', '')
            
            action_prompt = f"""
TAREFA: Escreva a CENA DE ABERTURA da jornada.

Comece com: {header}

Contexto do personagem (use sutilmente, NÃO exponha):
- Aparência: {appearance or 'vestimentas comuns de viajante'}
- História: {backstory[:300] if backstory else 'Um cultivador no início de sua jornada.'}
- Situação inicial: {first_context or 'Chegando ao local pela primeira vez.'}

INSTRUÇÕES:
1. Estabeleça a atmosfera do local através dos SENTIDOS (visão, som, cheiro)
2. Mostre o mundo em movimento - pessoas fazendo suas vidas
3. Se houver NPCs, eles estão ocupados com suas próprias coisas
4. NÃO diga o que o personagem deve fazer
5. Encerre de forma aberta, deixando o protagonista observar a cena

Máximo: 3 parágrafos densos e atmosféricos."""

        else:
            # Resumo da narração anterior (para continuidade)
            prev_summary = previous_narration[-400:] if previous_narration else "Início da jornada."
            
            action_prompt = f"""
TAREFA: Continue a narrativa respondendo à ação do jogador.

Comece com: {header}

Última cena (contexto):
"{prev_summary}"

AÇÃO DO JOGADOR:
"{player_last_action}"

INSTRUÇÕES:
1. Reaja à ação de forma NATURAL e com CONSEQUÊNCIAS
2. Se envolver NPC, ele responde com personalidade própria
3. Se for combate, descreva impacto visceral (não mecânico)
4. Se for exploração, revele detalhes através dos sentidos
5. NÃO sugira próximos passos
6. NÃO pergunte "O que você faz?"
7. Encerre a cena de forma aberta mas completa

Máximo: 3-4 parágrafos."""

        # === LORE RESUMIDA ===
        lore_snippet = self.lore_context[:1500] if self.lore_context else ""
        
        full_prompt = f"""{system_prompt}

{scene_context}

LORE DO MUNDO (consulte se relevante):
{lore_snippet}

{action_prompt}"""

        print(f"--- Narrador Gerando Cena ({location}) ---")
        return self.gemini_client.generate_text(full_prompt, task="story")

    async def generate_scene_stream(
        self,
        player: Player,
        location: str,
        npcs_in_scene: List[NPC],
        player_last_action: str = "",
        previous_narration: str = "",
        memory_repo=None,
        is_first_scene: bool = False
    ):
        """
        Sprint 13: Versão streaming do generate_scene_description_async.
        Retorna um AsyncIterator de chunks de texto.
        """
        from typing import AsyncIterator
        
        # Memórias dos NPCs
        memory_context = ""
        if memory_repo and npcs_in_scene:
            memory_snippets = []
            for npc in npcs_in_scene[:3]:
                if hasattr(npc, 'id') and npc.id:
                    try:
                        memories = await memory_repo.find_relevant_memories(
                            npc_id=npc.id,
                            query_text=f"{player.name} {player_last_action}",
                            limit=2
                        )
                        if memories:
                            memory_snippets.append(
                                f"{npc.name} lembra: {memories[0].get('content', '')}"
                            )
                    except Exception:
                        pass
            memory_context = "\n".join(memory_snippets)

        scene_context = self._build_scene_context(player, location, npcs_in_scene, memory_context)
        
        # Header temporal
        current_dt = world_clock.get_current_datetime()
        time_period = self._get_time_period(current_dt.hour)
        date_str = current_dt.strftime("%d do Mês %m, Ano %Y")
        header = f"📍 {date_str} | {time_period} | {location}"
        
        # System prompt - usa o método que constrói as diretrizes
        system_prompt = self._build_system_prompt()
        
        # Action prompt
        if is_first_scene:
            backstory = getattr(player, 'backstory', '')
            appearance = getattr(player, 'appearance', '')
            first_context = getattr(player, 'first_scene_context', '')
            
            action_prompt = f"""
TAREFA: Escreva a CENA DE ABERTURA da jornada.

Comece com: {header}

Contexto do personagem (use sutilmente, NÃO exponha):
- Aparência: {appearance or 'vestimentas comuns de viajante'}
- História: {backstory[:300] if backstory else 'Um cultivador no início de sua jornada.'}
- Situação inicial: {first_context or 'Chegando ao local pela primeira vez.'}

INSTRUÇÕES:
1. Estabeleça a atmosfera do local através dos SENTIDOS
2. Mostre o mundo em movimento
3. NÃO diga o que o personagem deve fazer
4. Encerre de forma aberta

Máximo: 3 parágrafos."""
        else:
            prev_summary = previous_narration[-400:] if previous_narration else "Início da jornada."
            
            action_prompt = f"""
TAREFA: Continue a narrativa respondendo à ação do jogador.

Comece com: {header}

Última cena (contexto):
"{prev_summary}"

AÇÃO DO JOGADOR:
"{player_last_action}"

INSTRUÇÕES:
1. Reaja à ação de forma NATURAL
2. NÃO sugira próximos passos
3. Encerre a cena de forma aberta

Máximo: 3-4 parágrafos."""

        lore_snippet = self.lore_context[:1500] if self.lore_context else ""
        
        full_prompt = f"""{system_prompt}

{scene_context}

LORE DO MUNDO:
{lore_snippet}

{action_prompt}"""

        print(f"--- Narrador Streaming Cena ({location}) ---")
        
        # Usa o método que constrói o system prompt
        system_prompt = self._build_system_prompt()
        
        async for chunk in self.gemini_client.generate_text_stream(full_prompt, model_type="story"):
            yield chunk

    def generate_scene_description(self, *args, **kwargs):
        """Wrapper síncrono para compatibilidade."""
        try:
            loop = asyncio.get_running_loop()
            return asyncio.create_task(self.generate_scene_description_async(*args, **kwargs))
        except RuntimeError:
            return "Erro: Narrador requer loop assíncrono (FastAPI)."
