"""
LocationManager - Gerencia criação dinâmica de locais pelo Mestre
Permite que a IA crie locais baseados na narrativa ou pedidos do player
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.location import DynamicLocation, LocationAlias
from ..database.models.player import Player
from ..services.gemini_client import GeminiClient


class LocationManager:
    """
    Gerencia a criação e busca de locais dinâmicos.
    
    Responsabilidades:
    1. Criar locais baseados no Session Zero (casa do player)
    2. Criar locais durante a narrativa (quando fizer sentido)
    3. Resolver aliases ("casa" → "Cabana do Wei Lin")
    4. Verificar se local foi destruído por WorldEvent
    """
    
    # Sinônimos de "casa" em português
    HOME_ALIASES = ["casa", "lar", "meu lar", "minha casa", "residência", "moradia", "cabana", "refúgio"]
    
    def __init__(self, session: AsyncSession, gemini_client: Optional[GeminiClient] = None):
        self.session = session
        self.gemini_client = gemini_client
    
    async def resolve_location(self, location_name: str, player_id: int) -> Dict[str, Any]:
        """
        Resolve um nome de local para o local real.
        Retorna info sobre o local (nome real, descrição, se existe, etc.)
        """
        location_lower = location_name.lower().strip()
        
        # 1. Verificar se é um alias de casa
        if location_lower in self.HOME_ALIASES:
            return await self._resolve_home(player_id)
        
        # 2. Verificar aliases personalizados do player
        alias_result = await self._check_alias(location_lower, player_id)
        if alias_result:
            return alias_result
        
        # 3. Verificar locais dinâmicos
        dynamic = await self._find_dynamic_location(location_name, player_id)
        if dynamic:
            return {
                "found": True,
                "type": "dynamic",
                "location": dynamic,
                "name": dynamic.name,
                "description": dynamic.description,
                "is_destroyed": dynamic.is_destroyed
            }
        
        # 4. Verificar locais estáticos (do locations_desc.md)
        static = self._check_static_location(location_name)
        if static:
            return {
                "found": True,
                "type": "static",
                "name": static["name"],
                "description": static["description"]
            }
        
        # 5. Local não encontrado
        return {
            "found": False,
            "name": location_name,
            "reason": "unknown_location"
        }
    
    async def _resolve_home(self, player_id: int) -> Dict[str, Any]:
        """Resolve 'casa' para o home_location do player"""
        stmt = select(Player).where(Player.id == player_id)
        result = await self.session.execute(stmt)
        player = result.scalar_one_or_none()
        
        if not player:
            return {"found": False, "reason": "player_not_found"}
        
        if player.home_location:
            # Se tem home_location_id, buscar o DynamicLocation
            if player.home_location_id:
                stmt = select(DynamicLocation).where(DynamicLocation.id == player.home_location_id)
                result = await self.session.execute(stmt)
                home = result.scalar_one_or_none()
                if home:
                    return {
                        "found": True,
                        "type": "dynamic_home",
                        "location": home,
                        "name": home.name,
                        "description": home.description,
                        "is_destroyed": home.is_destroyed
                    }
            
            # Se não tem ID, home_location é um nome de local
            return {
                "found": True,
                "type": "static_home",
                "name": player.home_location,
                "description": f"Seu lar em {player.home_location}."
            }
        
        # Player não tem casa definida
        # Usar origin_location como fallback
        if player.origin_location:
            return {
                "found": True,
                "type": "origin_fallback",
                "name": player.origin_location,
                "description": f"Sua terra natal: {player.origin_location}."
            }
        
        return {
            "found": False,
            "reason": "no_home_defined",
            "message": "Você ainda não tem um lar definido neste mundo."
        }
    
    async def _check_alias(self, alias: str, player_id: int) -> Optional[Dict]:
        """Verifica aliases personalizados do player"""
        stmt = select(LocationAlias).where(
            LocationAlias.alias == alias,
            LocationAlias.player_id == player_id
        )
        result = await self.session.execute(stmt)
        location_alias = result.scalar_one_or_none()
        
        if location_alias:
            if location_alias.location_id:
                # Buscar o DynamicLocation
                stmt = select(DynamicLocation).where(DynamicLocation.id == location_alias.location_id)
                result = await self.session.execute(stmt)
                loc = result.scalar_one_or_none()
                if loc:
                    return {
                        "found": True,
                        "type": "aliased_dynamic",
                        "location": loc,
                        "name": loc.name,
                        "description": loc.description
                    }
            elif location_alias.static_location_name:
                return {
                    "found": True,
                    "type": "aliased_static",
                    "name": location_alias.static_location_name
                }
        
        return None
    
    async def _find_dynamic_location(self, name: str, player_id: int) -> Optional[DynamicLocation]:
        """Busca um local dinâmico pelo nome"""
        # Buscar exato
        stmt = select(DynamicLocation).where(DynamicLocation.name == name)
        result = await self.session.execute(stmt)
        loc = result.scalar_one_or_none()
        
        if loc:
            return loc
        
        # Buscar por owner
        stmt = select(DynamicLocation).where(
            DynamicLocation.owner_player_id == player_id,
            DynamicLocation.name.ilike(f"%{name}%")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    def _check_static_location(self, name: str) -> Optional[Dict]:
        """Verifica locais estáticos definidos no jogo"""
        # Locais principais do Códice Triluna
        STATIC_LOCATIONS = {
            "vale dos mil picos": {
                "name": "Vale dos Mil Picos",
                "description": "Um vale cercado por montanhas pontiagudas que rasgam as nuvens."
            },
            "floresta nublada": {
                "name": "Floresta Nublada",
                "description": "Uma floresta antiga coberta por névoa eterna, lar de espíritos e bestas."
            },
            "vila crisântemos": {
                "name": "Vila Crisântemos",
                "description": "Uma pequena vila agrícola conhecida por suas flores douradas."
            },
            "cidade imperial": {
                "name": "Cidade Imperial",
                "description": "A capital do Império, sede do poder e centro de intrigas."
            },
            "seita da lua sombria": {
                "name": "Seita da Lua Sombria",
                "description": "Território da temida seita de assassinos e cultivadores das sombras."
            },
            "montanha do dragão adormecido": {
                "name": "Montanha do Dragão Adormecido",
                "description": "Pico lendário onde dizem dormir um dragão primordial."
            },
            "mercado celestial": {
                "name": "Mercado Celestial",
                "description": "O maior centro comercial do continente, onde tudo pode ser comprado."
            },
            "ruínas do império antigo": {
                "name": "Ruínas do Império Antigo",
                "description": "Restos de uma civilização perdida, cheios de tesouros e perigos."
            }
        }
        
        return STATIC_LOCATIONS.get(name.lower())
    
    async def create_location_from_session_zero(
        self,
        player: Player,
        home_description: str
    ) -> DynamicLocation:
        """
        Cria o lar do player baseado no Session Zero.
        """
        # Gerar nome para a casa
        home_name = f"Lar de {player.name}"
        
        location = DynamicLocation(
            name=home_name,
            location_type="residence",
            parent_location=player.origin_location,
            owner_player_id=player.id,
            description=home_description,
            created_by="session_zero",
            creation_context="Definido durante criação do personagem",
            is_public=False  # Casa é privada
        )
        
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        
        # Atualizar player com referência
        player.home_location = home_name
        player.home_location_id = location.id
        await self.session.commit()
        
        return location
    
    async def create_location_from_narrative(
        self,
        name: str,
        description: str,
        parent_location: str,
        location_type: str = "generic",
        owner_player_id: Optional[int] = None,
        context: str = "Criado durante narrativa"
    ) -> DynamicLocation:
        """
        Mestre cria um local durante a narrativa.
        Chamado quando o Mestre decide que um local mencionado deve existir.
        """
        location = DynamicLocation(
            name=name,
            location_type=location_type,
            parent_location=parent_location,
            owner_player_id=owner_player_id,
            description=description,
            created_by="narrative",
            creation_context=context,
            is_public=True
        )
        
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        
        return location
    
    async def should_create_location(
        self,
        player_request: str,
        current_location: str,
        player: Player
    ) -> Dict[str, Any]:
        """
        Usa IA para decidir se deve criar um local baseado no pedido do player.
        Retorna decisão e detalhes do local a criar.
        """
        if not self.gemini_client:
            return {"should_create": False, "reason": "no_ai"}
        
        prompt = f"""
Você é o Mestre de um RPG de cultivação.

O jogador {player.name} está em {current_location} e disse:
"{player_request}"

Ele quer ir a um local ou interagir com algo que não existe ainda no mundo.

DECISÃO: O pedido faz sentido narrativo? Deve-se criar esse local?

Considere:
1. Faz sentido para a história do personagem? (Origem: {player.origin_location}, Backstory: {player.backstory})
2. É algo razoável de existir em {current_location}?
3. Não é abuso (tipo "quero ir ao palácio do imperador" sendo ninguém)

Responda em JSON:
{{
    "should_create": true/false,
    "reason": "explicação breve",
    "location_name": "Nome do Local" (se criar),
    "location_type": "residence/shop/temple/dungeon/generic",
    "description": "Descrição narrativa do local" (se criar)
}}
"""
        
        try:
            response = await self.gemini_client.generate_content_async(
                prompt=prompt,
                model_type="flash"
            )
            
            # Parse JSON da resposta
            import json
            # Limpar markdown se houver
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            
            return json.loads(clean_response)
        except Exception as e:
            return {
                "should_create": False,
                "reason": f"Erro ao processar: {str(e)}"
            }
    
    async def add_alias(self, player_id: int, alias: str, location_id: int = None, static_name: str = None):
        """Adiciona um alias personalizado para o player"""
        loc_alias = LocationAlias(
            alias=alias.lower(),
            player_id=player_id,
            location_id=location_id,
            static_location_name=static_name
        )
        self.session.add(loc_alias)
        await self.session.commit()
