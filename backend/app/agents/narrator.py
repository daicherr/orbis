import os
from pathlib import Path
from typing import List
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.core.chronos import world_clock
from app.services.gemini_client import GeminiClient
import asyncio

class Narrator:
    def __init__(self, gemini_client: GeminiClient, lore_files_path: str):
        self.gemini_client = gemini_client
        self.lore_files_path = lore_files_path
        self.lore_context = self._load_lore()

    def _load_lore(self) -> str:
        """Carrega todo o conteúdo dos arquivos de lore em uma única string."""
        print("Carregando contexto de lore...")
        context_parts = []
        
        # Caminhos para as pastas de lore (independente do cwd)
        repo_root = Path(__file__).resolve().parents[3]
        lore_manual_path = repo_root / 'ruleset_source' / 'lore_manual'
        
        # Ler arquivos de lore_manual
        for filename in os.listdir(str(lore_manual_path)):
            if filename.endswith(".md"):
                with open(lore_manual_path / filename, 'r', encoding='utf-8') as f:
                    context_parts.append(f"--- Início de {filename} ---\n{f.read()}\n--- Fim de {filename} ---\n")
        
        print("Contexto de lore carregado.")
        return "\n".join(context_parts)

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
        Versão async da geração de cena (usa await para memórias)
        """
        time_of_day = "dia" if 6 <= world_clock.get_current_datetime().hour < 18 else "noite"
        npc_names = ", ".join([npc.name for npc in npcs_in_scene])
        if not npc_names:
            npc_names = "ninguém por perto"

        # Construir contexto do personagem (Sprint 4 integration)
        character_context = f"\nJogador: {player.name}, um cultivador no Tier {player.cultivation_tier or 1}.\n"
        
        # Adicionar informações do Character Creation se existirem
        if hasattr(player, 'constitution_type') and player.constitution_type:
            character_context += f"Constituição: {player.constitution_type}.\n"
        if hasattr(player, 'origin_location') and player.origin_location:
            character_context += f"Origem: {player.origin_location}.\n"
        if hasattr(player, 'appearance') and player.appearance:
            character_context += f"Aparência: {player.appearance}.\n"
        
        # Se for a primeira cena, incluir backstory
        backstory_context = ""
        if is_first_scene and hasattr(player, 'backstory') and player.backstory:
            backstory_context = f"\n--- Backstory do Personagem (Use para contextualizar a cena inicial) ---\n{player.backstory}\n"

        # Construir contexto com histórico
        history_context = ""
        if previous_narration:
            history_context = f"\n--- Narração Anterior (NÃO REPITA ISTO) ---\n{previous_narration[:300]}...\n"
        if player_last_action:
            history_context += f"--- Última Ação do Jogador ---\n{player_last_action}\n"
        
        # ===== BUSCAR MEMÓRIAS DOS NPCs =====
        npc_memories_context = ""
        if memory_repo and npcs_in_scene:
            npc_memories_context = "\n--- Memórias dos NPCs (Use para reações contextuais) ---\n"
            for npc in npcs_in_scene[:3]:  # Limita a 3 NPCs para não sobrecarregar
                try:
                    # Busca memórias relevantes baseadas no jogador e localização
                    query = f"{player.name} {location}"
                    memories = await memory_repo.find_relevant_memories(
                        npc_id=npc.id,
                        query_text=query,
                        limit=2
                    )
                    if memories:
                        memory_summary = " | ".join(memories[:2])
                        npc_memories_context += f"- {npc.name} lembra: {memory_summary}\n"
                except Exception as e:
                    print(f"⚠️ Erro ao buscar memórias de {npc.name}: {e}")

        # Prompt diferente para primeira cena vs cenas subsequentes
        if is_first_scene:
            prompt = (
                f"Você é um mestre de RPG narrando a PRIMEIRA CENA de uma jornada épica em português. "
                f"Seu estilo é literário, evocativo e alinhado com o gênero de cultivo (wuxia/xianxia). "
                f"Use o lore do mundo como base:\n{self.lore_context[:800]}...\n"
                f"{backstory_context}\n"
                f"{character_context}\n"
                f"Localização: {location}.\n"
                f"Hora: É {time_of_day}.\n"
                f"NPCs Próximos: {npc_names}.\n\n"
                f"--- TAREFA: Escreva a cena de ABERTURA (3 parágrafos) ---\n"
                f"1. Descreva o local atual ({location}) com detalhes sensoriais\n"
                f"2. Mencione a constituição ({getattr(player, 'constitution_type', 'Mortal')}) e origem\n"
                f"3. Cite um elemento do backstory do personagem\n"
                f"4. Termine com um gancho narrativo (um evento ou escolha iminente)\n"
            )
        else:
            prompt = (
                f"Você é um mestre de RPG narrando uma cena em português. "
                f"Seu estilo é literário, evocativo e alinhado com o gênero de cultivo (wuxia/xianxia). "
                f"IMPORTANTE: Avance a história. NÃO repita a descrição anterior. Mostre o RESULTADO da ação do jogador.\n"
                f"Use o seguinte lore como base para o tom e os detalhes do mundo:\n{self.lore_context[:500]}...\n"
                f"{history_context}\n"
                f"{npc_memories_context}\n"
                f"--- Descreva a Cena ATUAL (2 parágrafos curtos) ---\n"
                f"{character_context}"
                f"Localização: {location}.\n"
                f"Hora: É {time_of_day}.\n"
                f"NPCs Próximos: {npc_names}.\n"
                f"O que acontece AGORA? (Seja diferente da narração anterior)\n"
            )

        print(f"--- Gerando descrição NOVA para {location} (após ação: {player_last_action[:50]}...) via Gemini ---")
        literary_description = self.gemini_client.generate_text(prompt, task="story")
        
        return literary_description
    
    def generate_scene_description(
        self, 
        player: Player, 
        location: str, 
        npcs_in_scene: List[NPC],
        player_last_action: str = "",
        previous_narration: str = "",
        memory_repo = None
    ) -> str:
        """
        Gera uma descrição literária de uma cena usando o Gemini.
        Versão sync que chama a versão async (para compatibilidade)
        """
        # Se estamos em contexto async, use a versão async
        try:
            loop = asyncio.get_running_loop()
            # Estamos em contexto async, retornar coroutine
            return asyncio.create_task(
                self.generate_scene_description_async(
                    player, location, npcs_in_scene, 
                    player_last_action, previous_narration, memory_repo
                )
            )
        except RuntimeError:
            # Não estamos em contexto async, usar versão sync simplificada
            time_of_day = "dia" if 6 <= world_clock.get_current_datetime().hour < 18 else "noite"
            npc_names = ", ".join([npc.name for npc in npcs_in_scene])
            if not npc_names:
                npc_names = "ninguém por perto"

            history_context = ""
            if previous_narration:
                history_context = f"\n--- Narração Anterior (NÃO REPITA ISTO) ---\n{previous_narration[:300]}...\n"
            if player_last_action:
                history_context += f"--- Última Ação do Jogador ---\n{player_last_action}\n"

            prompt = (
                f"Você é um mestre de RPG narrando uma cena em português. "
                f"Seu estilo é literário, evocativo e alinhado com o gênero de cultivo (wuxia/xianxia). "
                f"IMPORTANTE: Avance a história. NÃO repita a descrição anterior. Mostre o RESULTADO da ação do jogador.\n"
                f"Use o seguinte lore como base para o tom e os detalhes do mundo:\n{self.lore_context[:500]}...\n"
                f"{history_context}\n"
                f"--- Descreva a Cena ATUAL (2 parágrafos curtos) ---\n"
                f"Jogador: {player.name}, um cultivador no Tier {player.cultivation_tier or 1} ({player.rank or 1}).\n"
                f"Localização: {location}.\n"
                f"Hora: É {time_of_day}.\n"
                f"NPCs Próximos: {npc_names}.\n"
                f"O que acontece AGORA? (Seja diferente da narração anterior)\n"
            )

            literary_description = self.gemini_client.generate_text(prompt, task="story")
            return literary_description
