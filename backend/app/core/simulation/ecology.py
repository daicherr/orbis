from typing import List, Dict

class EcologySimulator:

    def __init__(self, world_map: Dict):
        self.world_map = world_map
        # O estado da ecologia (ex: população de monstros por região) seria carregado do DB
        self.monster_populations = {"Floresta Sombria": 100, "Montanhas do Norte": 50}

    async def process_migrations(self):
        """
        Simula a migração de monstros entre regiões.
        """
        
        # Lógica placeholder
        if self.monster_populations["Floresta Sombria"] > 80:
            migrating_monsters = 20
            self.monster_populations["Floresta Sombria"] -= migrating_monsters
            self.monster_populations["Montanhas do Norte"] += migrating_monsters
            print(f"ECOLOGIA: Uma horda de {migrating_monsters} monstros migrou da Floresta Sombria para as Montanhas do Norte.")
