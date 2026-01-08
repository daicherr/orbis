"""
DynamicLocation Model - Locais criados narrativamente pelo Mestre
Permite que a IA crie novos locais (casas, cabanas, lojas) baseados na narrativa
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Column, JSON


class DynamicLocation(SQLModel, table=True):
    """
    Locais dinâmicos criados pelo Mestre ou por ações do player.
    
    Exemplos:
    - "Casa do Wei Lin" (criada no Session Zero)
    - "Cabana Abandonada na Floresta" (criada durante narrativa)
    - "Loja do Alquimista Chen" (criada quando player pediu para comprar algo)
    """
    __tablename__ = "dynamic_locations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Identificação
    name: str = Field(index=True)  # "Casa do Wei Lin"
    location_type: str = Field(default="generic")  # residence, shop, dungeon, ruins, temple
    
    # Hierarquia Geográfica
    parent_location: str = Field(index=True)  # "Floresta Nublada" (localização macro)
    
    # Propriedade
    owner_player_id: Optional[int] = Field(default=None, index=True)  # Se for casa de um player
    owner_npc_id: Optional[int] = Field(default=None)  # Se pertencer a um NPC
    
    # Descrição Narrativa
    description: str  # Descrição rica gerada pela IA
    interior_description: Optional[str] = None  # Como é por dentro
    
    # Metadados
    created_by: str = Field(default="narrative")  # "session_zero" | "narrative" | "player_request"
    creation_context: Optional[str] = None  # "Player pediu para comprar casa"
    
    # Estado
    is_destroyed: bool = Field(default=False)
    destruction_event_id: Optional[int] = Field(default=None)  # Link para WorldEvent que destruiu
    is_public: bool = Field(default=True)  # Outros players podem encontrar?
    is_hidden: bool = Field(default=False)  # Precisa descobrir para visitar?
    
    # Conteúdo
    npcs_present: List[int] = Field(default=[], sa_column=Column(JSON))  # NPCs que ficam aqui
    items_available: List[dict] = Field(default=[], sa_column=Column(JSON))  # Se for loja
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_visited_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True


class LocationAlias(SQLModel, table=True):
    """
    Aliases para locais - permite "casa", "lar", "minha cabana" apontar para o mesmo lugar.
    """
    __tablename__ = "location_aliases"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    alias: str = Field(index=True)  # "casa", "lar", "minha cabana"
    location_id: Optional[int] = Field(default=None, foreign_key="dynamic_locations.id")
    player_id: int = Field(index=True)  # Alias é pessoal por player
    
    # Para locais estáticos (que não estão em dynamic_locations)
    static_location_name: Optional[str] = None  # "Floresta Nublada"
