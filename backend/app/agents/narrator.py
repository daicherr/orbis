import os
from pathlib import Path
from typing import List
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.core.chronos import world_clock
from app.services.gemini_client import GeminiClient

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

    def generate_scene_description(
        self, 
        player: Player, 
        location: str, 
        npcs_in_scene: List[NPC]
    ) -> str:
        """
        Gera uma descrição literária de uma cena usando o Gemini.
        """
        time_of_day = "dia" if 6 <= world_clock.get_current_datetime().hour < 18 else "noite"
        npc_names = ", ".join([npc.name for npc in npcs_in_scene])
        if not npc_names:
            npc_names = "ninguém por perto"

        prompt = (
            f"Você é um mestre de RPG narrando uma cena em português. "
            f"Seu estilo é literário, evocativo e alinhado com o gênero de cultivo (wuxia/xianxia). "
            f"Use o seguinte lore como base para o tom e os detalhes do mundo:\n{self.lore_context}\n\n"
            f"Descreva a cena atual em 2-3 parágrafos curtos. Seja conciso, mas imersivo.\n"
            f"--- Detalhes da Cena ---\n"
            f"Jogador: {player.name}, um cultivador no rank {player.rank}.\n"
            f"Localização: {location}.\n"
            f"Hora: É {time_of_day}.\n"
            f"NPCs Próximos: {npc_names}.\n\n"
            f"--- Narração ---\n"
        )

        print(f"--- Gerando descrição para a cena em {location} via Gemini ---")
        literary_description = self.gemini_client.generate_text(prompt, task="story")
        
        return literary_description
