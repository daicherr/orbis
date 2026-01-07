from typing import Dict, Any
from app.database.models.npc import NPC
from app.database.models.player import Player

class Strategist:
    
    def __init__(self, world_map: Dict[str, Any]):
        """
        Inicializa o estrategista com um mapa do mundo para tomar decisões de movimento.
        O world_map poderia definir localizações e suas conexões.
        """
        self.world_map = world_map

    def decide_next_action(self, villain: NPC, player: Player) -> Dict[str, Any]:
        """
        Determina a próxima ação estratégica para um vilão (movimento, emboscada, etc.).
        Esta é uma IA de alto nível, operando no mapa-múndi.
        """
        
        action = {"type": "idle", "target": None, "destination": None}
        
        # Lógica de decisão placeholder
        # Exemplo: Se o vilão tem uma vendeta contra o jogador, ele o caça.
        if villain.vendetta_target == player.id:
            action["type"] = "hunt"
            action["target"] = player.name
            
            # Lógica simples para mover em direção ao jogador
            # (supondo que a localização do jogador seja conhecida)
            player_location = "Vila Inicial" # Placeholder
            if villain.current_location != player_location:
                action["destination"] = player_location
            else:
                action["type"] = "ambush" # Se já estiver no mesmo local
        
        print(f"Estrategista decidiu: Vilão {villain.name} irá {action['type']}.")
        return action
