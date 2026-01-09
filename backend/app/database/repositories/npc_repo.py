"""
NPC Repository - Acesso a dados de NPCs
GEM RPG ORBIS - Arquitetura Cognitiva

Repositório completo para operações com NPCs incluindo:
- CRUD básico
- Busca por localização, facção, espécie
- Busca por relacionamentos
- Atualização de estado emocional e combate
- Gerenciamento de rotina diária
"""

from typing import Optional, List, Dict, Any
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models.npc import NPC


class NpcRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== CRUD BÁSICO ====================
    
    async def create(self, npc: NPC) -> NPC:
        """Cria um novo NPC."""
        self.session.add(npc)
        await self.session.commit()
        await self.session.refresh(npc)
        return npc
    
    async def create_many(self, npcs: List[NPC]) -> List[NPC]:
        """Cria múltiplos NPCs de uma vez."""
        for npc in npcs:
            self.session.add(npc)
        await self.session.commit()
        for npc in npcs:
            await self.session.refresh(npc)
        return npcs

    async def get_by_id(self, npc_id: int) -> Optional[NPC]:
        """Busca um NPC pelo seu ID."""
        result = await self.session.exec(select(NPC).where(NPC.id == npc_id))
        return result.one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[NPC]:
        """Busca um NPC pelo nome exato."""
        result = await self.session.exec(select(NPC).where(NPC.name == name))
        return result.one_or_none()
    
    async def search_by_name(self, name_partial: str) -> List[NPC]:
        """Busca NPCs cujo nome contém a string."""
        result = await self.session.exec(
            select(NPC).where(NPC.name.ilike(f"%{name_partial}%"))
        )
        return list(result.all())
        
    async def get_all(self) -> List[NPC]:
        """Busca todos os NPCs do banco de dados."""
        result = await self.session.exec(select(NPC))
        return list(result.all())
    
    async def get_all_active(self) -> List[NPC]:
        """Busca todos os NPCs ativos."""
        result = await self.session.exec(
            select(NPC).where(NPC.is_active == True, NPC.is_alive == True)
        )
        return list(result.all())

    async def update(self, npc: NPC) -> NPC:
        """Atualiza os dados de um NPC no banco."""
        self.session.add(npc)
        await self.session.commit()
        await self.session.refresh(npc)
        return npc
    
    async def delete(self, npc_id: int) -> bool:
        """Deleta um NPC (soft delete - marca como inativo)."""
        npc = await self.get_by_id(npc_id)
        if npc:
            npc.is_active = False
            await self.update(npc)
            return True
        return False
    
    async def kill(self, npc_id: int) -> Optional[NPC]:
        """Marca um NPC como morto."""
        npc = await self.get_by_id(npc_id)
        if npc:
            npc.is_alive = False
            npc.current_hp = 0
            return await self.update(npc)
        return None

    # ==================== BUSCA POR LOCALIZAÇÃO ====================
    
    async def get_by_location(self, location: str) -> List[NPC]:
        """Busca NPCs em uma localização específica."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.current_location == location,
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def get_by_location_and_role(self, location: str, role: str) -> List[NPC]:
        """Busca NPCs em uma localização com papel específico."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.current_location == location,
                NPC.role == role,
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def get_enemies_at_location(self, location: str) -> List[NPC]:
        """Busca NPCs hostis em uma localização."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.current_location == location,
                NPC.role == "enemy",
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def get_merchants_at_location(self, location: str) -> List[NPC]:
        """Busca merchants em uma localização."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.current_location == location,
                NPC.role == "merchant",
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def get_speaking_npcs_at_location(self, location: str) -> List[NPC]:
        """Busca NPCs que podem falar em uma localização."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.current_location == location,
                NPC.can_speak == True,
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def move_npc(self, npc_id: int, new_location: str) -> Optional[NPC]:
        """Move um NPC para uma nova localização."""
        npc = await self.get_by_id(npc_id)
        if npc:
            npc.current_location = new_location
            return await self.update(npc)
        return None

    # ==================== BUSCA POR ESPÉCIE/TIPO ====================
    
    async def get_by_species(self, species: str) -> List[NPC]:
        """Busca NPCs de uma espécie específica."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.species == species,
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def get_beasts_at_location(self, location: str) -> List[NPC]:
        """Busca bestas em uma localização."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.current_location == location,
                NPC.species == "beast",
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def get_demons_at_location(self, location: str) -> List[NPC]:
        """Busca demônios em uma localização."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.current_location == location,
                NPC.species == "demon",
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())

    # ==================== BUSCA POR FACÇÃO ====================
    
    async def get_by_faction(self, faction_id: str) -> List[NPC]:
        """Busca NPCs de uma facção específica."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.faction_id == faction_id,
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def get_faction_leaders(self, faction_id: str) -> List[NPC]:
        """Busca líderes de uma facção."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.faction_id == faction_id,
                NPC.faction_role == "leader",
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def set_faction(self, npc_id: int, faction_id: str, role: str = "member") -> Optional[NPC]:
        """Define a facção de um NPC."""
        npc = await self.get_by_id(npc_id)
        if npc:
            npc.faction_id = faction_id
            npc.faction_role = role
            return await self.update(npc)
        return None

    # ==================== ESTADO EMOCIONAL E COMBATE ====================
    
    async def set_emotional_state(self, npc_id: int, state: str) -> Optional[NPC]:
        """Define o estado emocional de um NPC."""
        npc = await self.get_by_id(npc_id)
        if npc:
            npc.emotional_state = state
            return await self.update(npc)
        return None
    
    async def set_vendetta(self, npc_id: int, target_player_id: int) -> Optional[NPC]:
        """Define um alvo de vingança para o NPC."""
        npc = await self.get_by_id(npc_id)
        if npc:
            npc.vendetta_target = target_player_id
            npc.emotional_state = "hostile"
            return await self.update(npc)
        return None
    
    async def get_vendettas_against_player(self, player_id: int) -> List[NPC]:
        """Busca NPCs que têm vingança contra um jogador."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.vendetta_target == player_id,
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def update_hp(self, npc_id: int, new_hp: float) -> Optional[NPC]:
        """Atualiza HP de um NPC."""
        npc = await self.get_by_id(npc_id)
        if npc:
            npc.current_hp = max(0, min(new_hp, npc.max_hp))
            if npc.current_hp <= 0:
                npc.is_alive = False
            return await self.update(npc)
        return None
    
    async def apply_damage(self, npc_id: int, damage: float) -> Optional[NPC]:
        """Aplica dano a um NPC."""
        npc = await self.get_by_id(npc_id)
        if npc and npc.is_alive:
            npc.current_hp = max(0, npc.current_hp - damage)
            if npc.current_hp <= 0:
                npc.is_alive = False
            return await self.update(npc)
        return None
    
    async def heal(self, npc_id: int, amount: float) -> Optional[NPC]:
        """Cura um NPC."""
        npc = await self.get_by_id(npc_id)
        if npc and npc.is_alive:
            npc.current_hp = min(npc.max_hp, npc.current_hp + amount)
            return await self.update(npc)
        return None

    # ==================== RELACIONAMENTOS ====================
    
    async def add_relationship(
        self, 
        npc_id: int, 
        target_name: str, 
        stance: str, 
        history: str = ""
    ) -> Optional[NPC]:
        """Adiciona ou atualiza um relacionamento."""
        npc = await self.get_by_id(npc_id)
        if npc:
            if npc.relationships is None:
                npc.relationships = {}
            npc.relationships[target_name] = {
                "stance": stance,  # friendly, neutral, hostile, fearful, respectful
                "history": history
            }
            return await self.update(npc)
        return None
    
    async def get_relationship(self, npc_id: int, target_name: str) -> Optional[Dict[str, Any]]:
        """Obtém o relacionamento de um NPC com outro."""
        npc = await self.get_by_id(npc_id)
        if npc and npc.relationships:
            return npc.relationships.get(target_name)
        return None
    
    async def get_npcs_with_relationship_to(self, target_name: str) -> List[NPC]:
        """Busca NPCs que têm relacionamento com um alvo."""
        all_npcs = await self.get_all_active()
        return [
            npc for npc in all_npcs 
            if npc.relationships and target_name in npc.relationships
        ]

    # ==================== ROTINA DIÁRIA ====================
    
    async def set_schedule(self, npc_id: int, schedule: Dict[str, str]) -> Optional[NPC]:
        """Define a rotina diária de um NPC."""
        npc = await self.get_by_id(npc_id)
        if npc:
            npc.daily_schedule = schedule
            return await self.update(npc)
        return None
    
    async def update_activity(self, npc_id: int, activity: str) -> Optional[NPC]:
        """Atualiza a atividade atual de um NPC."""
        npc = await self.get_by_id(npc_id)
        if npc:
            npc.current_activity = activity
            return await self.update(npc)
        return None
    
    async def process_time_tick(self, time_of_day: str) -> List[NPC]:
        """
        Processa mudança de horário para todos os NPCs com rotina.
        Move NPCs para localizações de acordo com seu schedule.
        Retorna lista de NPCs que se moveram.
        """
        all_npcs = await self.get_all_active()
        moved_npcs = []
        
        for npc in all_npcs:
            if npc.daily_schedule and time_of_day in npc.daily_schedule:
                scheduled_location = npc.daily_schedule[time_of_day]
                if scheduled_location and scheduled_location != npc.current_location:
                    npc.current_location = scheduled_location
                    npc.current_activity = f"chegando ao {scheduled_location}"
                    await self.update(npc)
                    moved_npcs.append(npc)
        
        return moved_npcs

    # ==================== INVENTÁRIO E QUESTS ====================
    
    async def get_quest_givers(self) -> List[NPC]:
        """Busca NPCs que têm quests disponíveis."""
        result = await self.session.exec(
            select(NPC).where(
                NPC.role == "quest_giver",
                NPC.is_active == True,
                NPC.is_alive == True
            )
        )
        return list(result.all())
    
    async def add_quest(self, npc_id: int, quest_id: int) -> Optional[NPC]:
        """Adiciona uma quest disponível a um NPC."""
        npc = await self.get_by_id(npc_id)
        if npc:
            if quest_id not in npc.available_quest_ids:
                npc.available_quest_ids.append(quest_id)
                return await self.update(npc)
        return npc
    
    async def remove_quest(self, npc_id: int, quest_id: int) -> Optional[NPC]:
        """Remove uma quest de um NPC."""
        npc = await self.get_by_id(npc_id)
        if npc and quest_id in npc.available_quest_ids:
            npc.available_quest_ids.remove(quest_id)
            return await self.update(npc)
        return npc
    
    async def add_item_to_inventory(self, npc_id: int, item: Dict[str, Any]) -> Optional[NPC]:
        """Adiciona um item ao inventário de um merchant."""
        npc = await self.get_by_id(npc_id)
        if npc:
            if npc.inventory is None:
                npc.inventory = []
            npc.inventory.append(item)
            return await self.update(npc)
        return None
    
    async def remove_item_from_inventory(self, npc_id: int, item_name: str) -> Optional[NPC]:
        """Remove um item do inventário de um merchant."""
        npc = await self.get_by_id(npc_id)
        if npc and npc.inventory:
            npc.inventory = [i for i in npc.inventory if i.get("name") != item_name]
            return await self.update(npc)
        return None

    # ==================== UTILITÁRIOS ====================
    
    async def get_context_for_location(self, location: str) -> Dict[str, Any]:
        """
        Obtém contexto completo de NPCs para uma localização.
        Usado pelo Narrator para descrever cenas.
        """
        npcs = await self.get_by_location(location)
        
        context = {
            "total_npcs": len(npcs),
            "enemies": [],
            "friendlies": [],
            "merchants": [],
            "quest_givers": [],
            "beasts": [],
            "can_speak": [],
        }
        
        for npc in npcs:
            npc_data = {
                "id": npc.id,
                "name": npc.name,
                "species": npc.species,
                "gender": npc.gender,
                "role": npc.role,
                "rank": npc.rank,
                "emotional_state": npc.emotional_state,
                "context_string": npc.to_context_string() if hasattr(npc, 'to_context_string') else None
            }
            
            if npc.role == "enemy" or npc.is_hostile():
                context["enemies"].append(npc_data)
            elif npc.is_friendly():
                context["friendlies"].append(npc_data)
            
            if npc.role == "merchant":
                context["merchants"].append(npc_data)
            
            if npc.available_quest_ids:
                context["quest_givers"].append(npc_data)
            
            if npc.species == "beast":
                context["beasts"].append(npc_data)
            
            if npc.can_speak:
                context["can_speak"].append(npc_data)
        
        return context
    
    async def count_by_faction(self, faction_id: str) -> int:
        """Conta membros de uma facção."""
        members = await self.get_by_faction(faction_id)
        return len(members)
    
    async def count_alive_at_location(self, location: str) -> int:
        """Conta NPCs vivos em uma localização."""
        npcs = await self.get_by_location(location)
        return len(npcs)
