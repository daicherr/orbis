from typing import Dict, Any
# Supondo a existência de um modelo Faction
# from app.database.models.world_state import Faction

class Diplomat:

    def evaluate_faction_relations(self, faction_a: Dict, faction_b: Dict, world_events: list) -> str:
        """
        Avalia a relação entre duas facções e decide se o status deve mudar.
        Retorna o novo status: 'allied', 'neutral', 'hostile', 'war'.
        """
        
        current_relation = faction_a.get("relations", {}).get(faction_b["name"], "neutral")
        
        # Lógica de decisão placeholder
        # Exemplo: Se uma facção ataca um membro da outra, a relação piora.
        for event in world_events:
            if (event.get("type") == "faction_attack" and 
                event.get("attacker") == faction_a["name"] and 
                event.get("defender") == faction_b["name"]):
                
                print(f"Diplomat: {faction_a['name']} atacou {faction_b['name']}. A relação piorou!")
                return "hostile"

        # Exemplo: Se os recursos de uma facção estão baixos, ela pode declarar guerra
        # a uma facção mais fraca para roubar recursos.
        if (faction_a.get("resources") < 200 and 
            faction_b.get("power_level") < faction_a.get("power_level")):
            
            print(f"Diplomat: {faction_a['name']} está desesperada por recursos. Declarando guerra a {faction_b['name']}!")
            return "war"
            
        return current_relation
