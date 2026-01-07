from typing import Dict, Any, List

class GossipMonger:

    def generate_rumor(self, event: Dict[str, Any]) -> str:
        """
        Gera uma frase de boato com base em um evento de jogo.
        Ex de evento: {"type": "kill", "actor": "PlayerName", "target": "Goblin King", "location": "Dark Forest"}
        """
        
        event_type = event.get("type")
        actor = event.get("actor")
        target = event.get("target")
        location = event.get("location")

        rumor = ""
        if event_type == "kill":
            rumor = f"Ouvi dizer que um cultivador chamado {actor} derrotou {target} na {location}! Dizem que foi uma batalha feroz."
        elif event_type == "theft":
            rumor = f"Fique de olhos abertos! Parece que {actor} foi visto roubando um item valioso de {target} em {location}."
        elif event_type == "faction_war_start":
            rumor = f"As nuvens da guerra se formam... A facção {actor} declarou guerra à facção {target}!"
        else:
            rumor = "As folhas sussurram segredos que ainda não consigo decifrar."
            
        print(f"GossipMonger gerou o boato: '{rumor}'")
        return rumor

    def spread_rumor(self, rumor: str, npcs: List[Any]):
        """
        Espalha um boato para uma lista de NPCs (placeholder).
        """
        print(f"Espalhando o boato para {len(npcs)} NPCs...")
        # Lógica para adicionar o boato à memória de cada NPC
        pass
