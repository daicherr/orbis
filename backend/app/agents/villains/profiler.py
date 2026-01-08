"""
Villain Profiler - Emotional AI System
Tracks relationships, vendetta, and emotional states (Sprint 6)
"""

from app.database.models.npc import NPC
from app.database.models.player import Player
from typing import Dict, Optional

class Profiler:
    """
    Sistema emocional de NPCs antagonistas.
    Gerencia ódio, respeito, vingança e alianças.
    [SPRINT 6] Expanded para Nemesis System.
    """
    
    def __init__(self):
        # Cache de relações (NPC_ID -> Player_ID -> relationship_data)
        self.relationships: Dict[int, Dict[int, Dict[str, any]]] = {}

    async def process_event(
        self, 
        event_type: str, 
        actor: Player, 
        target: NPC,
        npc_repo=None
    ):
        """
        Processa um evento de jogo e atualiza o perfil emocional do NPC.
        
        [SPRINT 6] Expandido com:
        - Tracking de kills (contador de mortes)
        - Sistema de reputação
        - Triggers de vendetta
        - Notificação para Strategist
        """
        
        if event_type == "player_attacked_npc":
            self._increase_hostility(target, actor, amount=20)
            print(f"Profiler: Hostilidade de {target.name} para com {actor.name} aumentou (+20).")
            
        elif event_type == "player_killed_npc":
            # [SPRINT 6] Registrar morte para rumores
            self._record_kill(actor, target)
            print(f"Profiler: {actor.name} matou {target.name}. Família pode buscar vingança.")
            
            # [SPRINT 6] Criar NPCs vingativos (parentes)
            if npc_repo:
                await self._spawn_avenger(actor, target, npc_repo)
            
        elif event_type == "player_killed_npc_friend":
            self._increase_hostility(target, actor, amount=50)
            self._assign_vendetta(target, actor)
            print(f"Profiler: {target.name} agora busca vingança contra {actor.name}.")
            
        elif event_type == "player_helped_npc":
            self._increase_friendship(target, actor, amount=15)
            print(f"Profiler: Amizade de {target.name} com {actor.name} aumentou (+15).")
            
        elif event_type == "player_spared_enemy":
            # [SPRINT 6] Poupar inimigo gera respeito
            self._increase_respect(target, actor, amount=30)
            target.emotional_state = "respectful"
            print(f"Profiler: {target.name} agora respeita {actor.name} por tê-lo poupado.")

    def _increase_hostility(self, npc: NPC, player: Player, amount: int):
        """Aumenta a hostilidade do NPC em relação ao jogador."""
        
        # Inicializar relação se não existir
        if npc.id not in self.relationships:
            self.relationships[npc.id] = {}
        if player.id not in self.relationships[npc.id]:
            self.relationships[npc.id][player.id] = {
                "hostility": 0,
                "friendship": 0,
                "respect": 0,
                "kills_witnessed": 0
            }
        
        self.relationships[npc.id][player.id]["hostility"] += amount
        
        # Atualizar estado emocional se hostilidade passar de threshold
        if self.relationships[npc.id][player.id]["hostility"] >= 50:
            npc.emotional_state = "hostile"

    def _increase_friendship(self, npc: NPC, player: Player, amount: int):
        """Aumenta a amizade do NPC com o jogador."""
        
        if npc.id not in self.relationships:
            self.relationships[npc.id] = {}
        if player.id not in self.relationships[npc.id]:
            self.relationships[npc.id][player.id] = {
                "hostility": 0,
                "friendship": 0,
                "respect": 0,
                "kills_witnessed": 0
            }
        
        self.relationships[npc.id][player.id]["friendship"] += amount
        
        if self.relationships[npc.id][player.id]["friendship"] >= 40:
            npc.emotional_state = "friendly"

    def _increase_respect(self, npc: NPC, player: Player, amount: int):
        """[SPRINT 6] Aumenta o respeito do NPC pelo jogador."""
        
        if npc.id not in self.relationships:
            self.relationships[npc.id] = {}
        if player.id not in self.relationships[npc.id]:
            self.relationships[npc.id][player.id] = {
                "hostility": 0,
                "friendship": 0,
                "respect": 0,
                "kills_witnessed": 0
            }
        
        self.relationships[npc.id][player.id]["respect"] += amount

    def _assign_vendetta(self, npc: NPC, player: Player):
        """Atribui um alvo de vingança ao NPC."""
        npc.vendetta_target = player.id
        npc.emotional_state = "vengeful"

    def _record_kill(self, player: Player, victim: NPC):
        """[SPRINT 6] Registra uma morte para estatísticas e rumores."""
        
        # Inicializar kill tracker se não existir
        if not hasattr(player, 'kill_count'):
            player.kill_count = 0
        
        player.kill_count += 1
        
        # Adicionar ao histórico de kills (para rumores)
        if not hasattr(player, 'kill_history'):
            player.kill_history = []
        
        player.kill_history.append({
            "victim_name": victim.name,
            "victim_rank": victim.rank,
            "location": victim.current_location
        })

    async def _spawn_avenger(self, player: Player, victim: NPC, npc_repo):
        """
        [SPRINT 6] Cria um NPC vingativo quando player mata alguém importante.
        Chance de 30% de spawnar um parente/discípulo.
        """
        
        import random
        
        # Apenas spawnar avenger se vítima for Rank 3+ (importante)
        if victim.rank < 3:
            return
        
        # 30% de chance
        if random.random() > 0.3:
            return
        
        # Escolher tipo de avenger baseado na vítima
        avenger_types = {
            "Scheming Elder": "Discípulo vingativo",
            "Demonic Shadow": "Irmão de sangue",
            "Young Master": "Pai poderoso",
            "Cultivador": "Membro da seita"
        }
        
        avenger_title = "Vingador desconhecido"
        for key in avenger_types:
            if key.lower() in victim.name.lower():
                avenger_title = avenger_types[key]
                break
        
        # Criar NPC vingativo
        avenger_name = f"{avenger_title} de {victim.name}"
        avenger_rank = victim.rank + 1  # Sempre mais forte
        
        avenger = await npc_repo.create(
            name=avenger_name,
            rank=avenger_rank,
            personality_traits=["vengeful", "ruthless", "calculating"],
            emotional_state="vengeful",
            vendetta_target=player.id,
            current_location=victim.current_location  # Aparece no mesmo local
        )
        
        print(f"[NEMESIS] SPAWNED: {avenger_name} (Rank {avenger_rank}) busca vinganca por {victim.name}!")
        
        return avenger

    def get_relationship(self, npc_id: int, player_id: int) -> Optional[Dict[str, any]]:
        """[SPRINT 6] Retorna dados de relacionamento entre NPC e jogador."""
        
        if npc_id in self.relationships and player_id in self.relationships[npc_id]:
            return self.relationships[npc_id][player_id]
        
        return None

    def get_hostile_npcs(self, player_id: int) -> list[int]:
        """[SPRINT 6] Retorna lista de NPCs hostis ao jogador."""
        
        hostile_npcs = []
        
        for npc_id, player_relations in self.relationships.items():
            if player_id in player_relations:
                if player_relations[player_id]["hostility"] >= 50:
                    hostile_npcs.append(npc_id)
        
        return hostile_npcs

