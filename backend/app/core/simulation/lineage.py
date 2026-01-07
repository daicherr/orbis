from typing import List
# from app.database.models.npc import NPC
# from app.database.repositories.npc_repo import NpcRepository

class LineageSimulator:

    def __init__(self, npc_repo): # npc_repo: NpcRepository
        self.npc_repo = npc_repo

    async def check_for_vendetta(self, killed_npc: dict, killer_id: int):
        """
        Verifica se o NPC morto tem parentes e atribui uma vendeta a um deles.
        """
        
        # O modelo NPC precisaria de um campo 'family_id' ou 'relatives'
        # killed_npc_family_id = killed_npc.get("family_id")
        # all_npcs = await self.npc_repo.get_all()
        
        # parent = next((npc for npc in all_npcs if npc.family_id == killed_npc_family_id and npc.is_parent), None)
        
        # Placeholder para encontrar o pai do NPC morto
        parent = {"id": 10, "name": "Pai Furioso", "vendetta_target": None} # Mock

        if parent and parent["vendetta_target"] is None:
            # parent.vendetta_target = killer_id
            # await self.npc_repo.update(parent)
            print(f"LINHAGEM: {parent['name']} jura vingança contra o assassino de seu filho!")
            return True
            
        return False
