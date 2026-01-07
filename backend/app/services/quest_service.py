from typing import Optional
from app.database.models.quest import Quest
# from app.database.repositories.quest_repo import QuestRepository
# from app.database.repositories.npc_repo import NpcRepository
# from app.agents.narrator import Narrator # Para gerar descrições

class QuestService:

    def __init__(self, quest_repo, npc_repo, narrator):
        self.quest_repo = quest_repo
        self.npc_repo = npc_repo
        self.narrator = narrator

    async def generate_kill_quest(self, player_id: int) -> Optional[Quest]:
        """
        Gera uma missão de matar monstros simples para o jogador.
        """
        # 1. Encontrar um NPC para dar a missão
        # quest_giver = await self.npc_repo.get_random_npc()
        quest_giver_id = 1 # Placeholder

        if not quest_giver_id:
            return None

        # 2. Definir o objetivo
        target_monster = "Monstro de Nível Baixo"
        quantity = 3

        # 3. Gerar a descrição usando IA (placeholder)
        title = f"Exterminar {target_monster}s"
        description = f"Criaturas nefastas têm sido vistas nos arredores. Por favor, elimine {quantity} delas."
        
        # 4. Criar e salvar a missão
        new_quest = Quest(
            title=title,
            description=description,
            quest_giver_id=quest_giver_id,
            player_id=player_id,
            objective_type="kill",
            objective_target=target_monster,
            objective_quantity=quantity,
            reward_xp=100,
            reward_gold=50
        )
        
        # created_quest = await self.quest_repo.create(new_quest)
        print(f"MISSÃO GERADA: '{title}' para o jogador {player_id}.")
        
        # return created_quest
        return new_quest # Retornando o objeto mockado
