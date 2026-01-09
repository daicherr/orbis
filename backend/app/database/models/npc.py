"""
NPC Model - Entidades do Mundo
GEM RPG ORBIS - Arquitetura Cognitiva

Modelo completo de NPC com suporte a:
- Espécie e gênero (para narração consistente)
- Capacidade de fala (animais não falam)
- Rotina diária (schedule)
- Afiliação a facções
- Relacionamentos com outros NPCs
"""

from typing import Optional, List, Dict, Any
from sqlmodel import Field, SQLModel, JSON, Column


class NPC(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    rank: int = Field(default=1)
    
    # ==================== IDENTIDADE ====================
    # Espécie: human, beast, spirit, demon, undead, construct
    species: str = Field(default="human", index=True)
    
    # Gênero: male, female, unknown, none (para constructs/spirits)
    gender: str = Field(default="unknown")
    
    # Pode falar? (Bestas comuns não falam, bestas espirituais podem)
    can_speak: bool = Field(default=True)
    
    # Descrição física (para narração)
    description: Optional[str] = Field(default=None)
    
    # ==================== ATRIBUTOS DE COMBATE ====================
    current_hp: float = Field(default=100.0)
    max_hp: float = Field(default=100.0)
    defense: float = Field(default=10.0)
    attack_power: float = Field(default=10.0)
    speed: float = Field(default=10.0)
    
    # ==================== PERSONALIDADE E IA ====================
    personality_traits: List[str] = Field(sa_column=Column(JSON))
    emotional_state: str = Field(default="neutral")  # neutral, hostile, friendly, fearful, respectful
    vendetta_target: Optional[int] = Field(default=None, foreign_key="player.id")
    
    # Nível de agressividade (0=pacífico, 100=ataca à vista)
    aggression: int = Field(default=50)
    
    # Nível de coragem (0=covarde, 100=nunca foge)
    courage: int = Field(default=50)
    
    # ==================== LOCALIZAÇÃO E ROTINA ====================
    current_location: str = Field(default="Initial Village")
    home_location: Optional[str] = Field(default=None)  # Onde "mora"
    
    # Rotina diária: {"dawn": "home", "morning": "market", "noon": "tavern", ...}
    daily_schedule: Dict[str, str] = Field(default={}, sa_column=Column(JSON))
    
    # Atividade atual
    current_activity: Optional[str] = Field(default=None)
    
    # ==================== SOCIAL ====================
    # ID da facção (se pertencer a uma)
    faction_id: Optional[str] = Field(default=None, index=True)
    
    # Papel na facção: leader, member, recruit, ally
    faction_role: Optional[str] = Field(default=None)
    
    # Relacionamentos com outros NPCs: {"npc_name": {"stance": "friendly", "history": "..."}}
    relationships: Dict[str, Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))
    
    # ==================== FUNCIONALIDADE ====================
    # Papel do NPC: enemy, merchant, quest_giver, elder, healer, trainer, informant, guard, civilian
    role: str = Field(default="civilian")
    
    # IDs de quests disponíveis
    available_quest_ids: List[int] = Field(default=[], sa_column=Column(JSON))
    
    # Inventário para merchants
    inventory: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    
    # Diálogos disponíveis (IDs ou textos)
    dialogue_options: List[str] = Field(default=[], sa_column=Column(JSON))
    
    # ==================== STATUS ====================
    status_effects: List[dict] = Field(default=[], sa_column=Column(JSON))
    
    # Está vivo?
    is_alive: bool = Field(default=True)
    
    # Está ativo no mundo? (NPCs inativos não aparecem)
    is_active: bool = Field(default=True)
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def get_pronoun(self, case: str = "subject") -> str:
        """
        Retorna pronome correto baseado no gênero.
        case: subject (ele/ela), object (o/a), possessive (seu/sua)
        """
        if self.gender == "male":
            return {"subject": "ele", "object": "o", "possessive": "seu"}.get(case, "ele")
        elif self.gender == "female":
            return {"subject": "ela", "object": "a", "possessive": "sua"}.get(case, "ela")
        else:
            return {"subject": "ele", "object": "o", "possessive": "seu"}.get(case, "ele")
    
    def get_species_description(self) -> str:
        """Retorna descrição da espécie para narração."""
        descriptions = {
            "human": "humano",
            "beast": "besta",
            "spirit": "espírito",
            "demon": "demônio",
            "undead": "morto-vivo",
            "construct": "constructo",
        }
        return descriptions.get(self.species, "criatura")
    
    def can_dialogue(self) -> bool:
        """Verifica se o NPC pode participar de diálogo."""
        return self.can_speak and self.is_alive and self.is_active
    
    def is_hostile(self) -> bool:
        """Verifica se o NPC é hostil."""
        return self.emotional_state == "hostile" or self.aggression >= 80
    
    def is_friendly(self) -> bool:
        """Verifica se o NPC é amigável."""
        return self.emotional_state == "friendly" or self.aggression <= 20
    
    def get_current_schedule_location(self, time_of_day: str) -> Optional[str]:
        """Retorna onde o NPC deveria estar baseado na rotina."""
        return self.daily_schedule.get(time_of_day, self.home_location)
    
    def should_flee(self, hp_percent: float) -> bool:
        """Verifica se o NPC deveria fugir baseado em coragem e HP."""
        if self.courage >= 90:
            return False  # Nunca foge
        
        flee_threshold = (100 - self.courage) / 100  # Ex: courage=30 -> foge com 70% HP
        return hp_percent <= flee_threshold
    
    def to_context_string(self) -> str:
        """Retorna string de contexto para prompts de IA."""
        parts = [
            f"Nome: {self.name}",
            f"Espécie: {self.get_species_description()} ({self.species})",
            f"Gênero: {self.gender}",
            f"Pode falar: {'sim' if self.can_speak else 'não'}",
            f"Rank: {self.rank}",
            f"Estado: {self.emotional_state}",
            f"Papel: {self.role}",
        ]
        
        if self.description:
            parts.append(f"Descrição: {self.description}")
        
        if self.personality_traits:
            parts.append(f"Personalidade: {', '.join(self.personality_traits[:3])}")
        
        if self.faction_id:
            parts.append(f"Facção: {self.faction_id} ({self.faction_role or 'membro'})")
        
        hp_percent = self.current_hp / self.max_hp if self.max_hp > 0 else 1.0
        hp_status = "saudável" if hp_percent > 0.7 else ("ferido" if hp_percent > 0.3 else "gravemente ferido")
        parts.append(f"Condição: {hp_status}")
        
        return " | ".join(parts)
