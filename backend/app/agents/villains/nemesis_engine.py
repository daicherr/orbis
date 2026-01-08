"""
Nemesis Engine - Coordenador do Sistema de Vilões
Integra Profiler (emoções) + Strategist (movimento) (Sprint 6)
"""

from typing import List, Dict, Any
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.agents.villains.profiler import Profiler
from app.agents.villains.strategist import Strategist
from app.database.repositories.npc_repo import NpcRepository

class NemesisEngine:
    """
    Sistema de nemesis que gerencia vilões dinâmicos.
    
    Funcionalidades:
    - Move vilões off-screen baseado em vendetta
    - Cria NPCs vingativos quando player mata alguém
    - Prepara emboscadas estratégicas
    - Gerencia relacionamentos (ódio, respeito, vingança)
    
    [SPRINT 6] Core do sistema de antagonistas vivos.
    """
    
    def __init__(self, profiler: Profiler = None, strategist: Strategist = None):
        self.profiler = profiler or Profiler()
        self.strategist = strategist or Strategist()
        
        # Tracking de vilões ativos
        self.active_villains: List[int] = []  # NPC IDs
    
    async def process_turn(self, player: Player, npc_repo: NpcRepository):
        """
        Processa um turno do sistema de nemesis.
        
        Deve ser chamado pelo Director a cada turno do jogador.
        Move vilões, verifica emboscadas, atualiza relações.
        """
        
        # 1. Buscar vilões hostis
        hostile_npc_ids = self.profiler.get_hostile_npcs(player.id)
        
        # 2. Mover vilões vingativos
        for npc_id in hostile_npc_ids:
            villain = await npc_repo.get(npc_id)
            
            if not villain:
                continue
            
            # Decidir ação do vilão
            action = self.strategist.decide_next_action(villain, player)
            
            # Executar ação
            if action["type"] == "hunt" and action["destination"]:
                # Mover vilão
                villain.current_location = action["destination"]
                await npc_repo.update(villain)
                
            elif action["type"] == "retreat" and action["destination"]:
                # Vilão foge
                villain.current_location = action["destination"]
                await npc_repo.update(villain)
        
        # 3. Atualizar timers de emboscada
        self.strategist.update_ambush_timers()
    
    async def check_for_ambush(
        self, 
        location: str, 
        player: Player, 
        npc_repo: NpcRepository
    ) -> List[NPC]:
        """
        Verifica se há emboscadas preparadas na localização atual.
        
        Returns:
            Lista de NPCs que emboscam o jogador
        """
        
        ambusher_ids = self.strategist.check_for_ambush(location, player.id)
        
        ambushers = []
        for npc_id in ambusher_ids:
            villain = await npc_repo.get(npc_id)
            if villain:
                ambushers.append(villain)
        
        return ambushers
    
    async def register_kill(
        self, 
        player: Player, 
        victim: NPC, 
        npc_repo: NpcRepository
    ):
        """
        Registra morte de NPC.
        
        - Atualiza estatísticas do player
        - 30% de chance de spawnar vingador
        - Notifica sistema de rumores
        """
        
        await self.profiler.process_event(
            event_type="player_killed_npc",
            actor=player,
            target=victim,
            npc_repo=npc_repo
        )
    
    def get_relationship(self, npc_id: int, player_id: int) -> Dict[str, any]:
        """Retorna dados de relacionamento entre NPC e jogador."""
        return self.profiler.get_relationship(npc_id, player_id) or {
            "hostility": 0,
            "friendship": 0,
            "respect": 0,
            "kills_witnessed": 0
        }
    
    def format_relationship_message(self, npc: NPC, player: Player) -> str:
        """
        Formata mensagem literária do relacionamento.
        
        Returns:
            String descrevendo como NPC vê o player
        """
        
        relationship = self.get_relationship(npc.id, player.id)
        
        hostility = relationship["hostility"]
        friendship = relationship["friendship"]
        respect = relationship["respect"]
        
        # Determinar emoção dominante
        if hostility >= 50:
            if npc.vendetta_target == player.id:
                return f"💀 {npc.name} busca sua vingança com ódio mortal! (Hostilidade: {hostility})"
            return f"⚔️ {npc.name} te encara com hostilidade intensa. (Hostilidade: {hostility})"
        
        elif friendship >= 40:
            return f"🤝 {npc.name} te considera um aliado. (Amizade: {friendship})"
        
        elif respect >= 30:
            return f"🎖️ {npc.name} te respeita como guerreiro. (Respeito: {respect})"
        
        else:
            return f"😐 {npc.name} não tem opinião forte sobre você."


# Instância global (Singleton)
nemesis_engine = NemesisEngine()
