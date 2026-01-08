from typing import List, Dict, Any
from app.core.chronos import world_clock
from app.database.models.npc import NPC
from app.database.models.player import Player
from app.agents.villains.strategist import Strategist
from app.agents.social.diplomat import Diplomat
from app.agents.social.gossip_monger import GossipMonger

class WorldSimulator:
    """
    Coordena os sistemas de IA do mundo (Strategist, Diplomat, GossipMonger).
    Agora aceita GeminiClient na inicialização e recebe repositórios dinamicamente.
    """
    def __init__(self, gemini_client):
        # Inicializa os agentes de IA
        self.strategist = Strategist(world_map={})  # world_map pode vir do DB
        self.diplomat = Diplomat()
        self.gossip_monger = GossipMonger()
        self.gemini_client = gemini_client
        self.world_events: List[Dict] = []

    async def run_simulation_tick(self, npc_repo, player_repo):
        """Executa um único passo (tick) da simulação do mundo."""
        world_clock.advance_turn()
        print(f"--- Tick de Simulação: {world_clock.get_current_time_str()} ---")
        
        # Busca NPCs hostis do banco
        npcs = await npc_repo.get_all()
        hostile_npcs = [npc for npc in npcs if npc.emotional_state == "hostile" and npc.vendetta_target]
        
        # Busca todos os jogadores (se houver múltiplos)
        # Para single-player, busca o único player
        all_players = await player_repo.get_all()
        if not all_players:
            print("Nenhum jogador encontrado para simulação.")
            return
        
        player = all_players[0]  # Assume single-player por enquanto
        
        # Strategist: Move vilões hostis
        for npc in hostile_npcs:
            if npc.vendetta_target == player.id:
                action = self.strategist.decide_next_action(npc, player)
                if action["type"] == "hunt" and action["destination"]:
                    npc.current_location = action["destination"]
                    await npc_repo.update(npc)
                    print(f"SIM: {npc.name} se move para {npc.current_location} caçando {player.name}.")
        
        # GossipMonger: Processa eventos e gera rumores
        if len(self.world_events) > 0:
            event = self.world_events.pop(0)
            rumor = self.gossip_monger.generate_rumor(event)
            self.gossip_monger.spread_rumor(rumor, npcs)
            print(f"SIM: Rumor espalhado - {rumor}")
        
        # Diplomat: Avalia relações de facções (placeholder por enquanto)
        # factions = await load_factions_from_db()
        # if len(factions) >= 2:
        #     self.diplomat.evaluate_faction_relations(factions[0], factions[1], self.world_events)

        print("--- Fim do Tick de Simulação ---")

    def add_event(self, event: Dict):
        """Adiciona evento ao log para ser processado no próximo tick."""
        self.world_events.append(event)
