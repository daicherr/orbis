from app.database.models.npc import NPC
from app.database.models.player import Player

class Profiler:

    def process_event(self, event_type: str, actor: Player, target: NPC):
        """
        Processa um evento de jogo (ex: ataque, ajuda) e atualiza o perfil emocional do NPC.
        """
        
        if event_type == "player_attacked_npc":
            self._increase_hostility(target, amount=20)
            print(f"Profiler: Hostilidade de {target.name} para com {actor.name} aumentou.")
            
        elif event_type == "player_killed_npc_friend":
            self._increase_hostility(target, amount=50)
            self._assign_vendetta(target, actor)
            print(f"Profiler: {target.name} agora busca vingança contra {actor.name}.")
            
        elif event_type == "player_helped_npc":
            self._increase_friendship(target, amount=15)
            print(f"Profiler: Amizade de {target.name} com {actor.name} aumentou.")

    def _increase_hostility(self, npc: NPC, amount: int):
        """Aumenta a hostilidade do NPC."""
        # Esta lógica precisaria de um campo 'relations' no modelo NPC
        # npc.relations[player.id]['hostility'] += amount
        npc.emotional_state = "hostile" # Simplificação

    def _increase_friendship(self, npc: NPC, amount: int):
        """Aumenta a amizade do NPC."""
        # npc.relations[player.id]['friendship'] += amount
        npc.emotional_state = "friendly" # Simplificação

    def _assign_vendetta(self, npc: NPC, player: Player):
        """Atribui um alvo de vingança ao NPC."""
        npc.vendetta_target = player.id
