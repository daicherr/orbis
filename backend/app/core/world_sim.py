from typing import List, Dict, Any
from app.core.chronos import world_clock
from app.database.models.npc import NPC
from app.database.models.player import Player
from app.agents.villains.strategist import Strategist
from app.agents.social.diplomat import Diplomat
from app.agents.social.gossip_monger import GossipMonger

class WorldSimulator:
    def __init__(
        self, 
        npc_list: List[NPC], 
        player: Player,
        # Factions e world_map seriam carregados do DB
        factions: List[Dict],
        world_map: Dict
    ):
        self.npc_list = npc_list
        self.player = player
        self.factions = factions
        self.world_events: List[Dict] = []
        
        # Inicializa os agentes de IA
        self.strategist = Strategist(world_map=world_map)
        self.diplomat = Diplomat()
        self.gossip_monger = GossipMonger()

    def _make_npc_decision(self, npc: NPC):
        """Usa os agentes de IA para tomar decisões pelos NPCs."""
        if npc.emotional_state == "hostile" and npc.vendetta_target == self.player.id:
            action = self.strategist.decide_next_action(npc, self.player)
            if action["type"] == "hunt" and action["destination"]:
                npc.current_location = action["destination"]
                print(f"SIM: {npc.name} se move para {npc.current_location} caçando {self.player.name}.")
        else:
            # Placeholder para NPCs não-hostis
            pass

    def _process_world_events(self):
        """Usa agentes sociais para processar eventos e gerar narrativa."""
        # Exemplo de evento (seria gerado por ações do jogador ou da simulação)
        if len(self.world_events) > 0:
            event = self.world_events.pop(0)
            rumor = self.gossip_monger.generate_rumor(event)
            self.gossip_monger.spread_rumor(rumor, self.npc_list)
        
        # Avalia a diplomacia entre facções
        if len(self.factions) >= 2:
            self.diplomat.evaluate_faction_relations(self.factions[0], self.factions[1], self.world_events)

    def run_simulation_tick(self):
        """Executa um único passo (tick) da simulação do mundo."""
        world_clock.advance_turn()
        print(f"--- Tick de Simulação: {world_clock.get_current_time_str()} ---")

        for npc in self.npc_list:
            self._make_npc_decision(npc)

        self._process_world_events()

        print("--- Fim do Tick ---")

    def add_event(self, event: Dict):
        self.world_events.append(event)
