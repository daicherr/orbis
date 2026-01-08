"""
Faction Simulator - Manages faction wars, alliances, and influence
Based on GDD: World should feel alive with faction politics
"""

from typing import Dict, List, Optional, Any
import random


class FactionSimulator:
    """
    Simula política de facções: guerras, alianças, influência territorial.
    Opera no world tick para evoluir o mundo independente do jogador.
    """
    
    # Relações possíveis entre facções
    RELATION_ALLIED = "allied"
    RELATION_NEUTRAL = "neutral"
    RELATION_HOSTILE = "hostile"
    RELATION_WAR = "at_war"
    
    # Eventos de facção
    EVENT_WAR_DECLARED = "war_declared"
    EVENT_ALLIANCE_FORMED = "alliance_formed"
    EVENT_TERRITORY_CAPTURED = "territory_captured"
    EVENT_FACTION_WEAKENED = "faction_weakened"
    EVENT_LEADER_KILLED = "leader_killed"
    
    def __init__(self, faction_repo=None, world_event_repo=None):
        """
        Inicializa o simulador de facções.
        
        Args:
            faction_repo: Repository para operações de Faction
            world_event_repo: Repository para criar WorldEvents
        """
        self.faction_repo = faction_repo
        self.world_event_repo = world_event_repo
        
        # Territórios controlados por facção (cache)
        self.territories: Dict[str, str] = {
            "Cidade Imperial": "Império Central",
            "Montanha Arcaica": "Seita Arcaica",
            "Seita Lua Sombria": "Lua Sombria",
            "Monastério da Aurora": "Monastério da Aurora",
            "Porto Sul": "Guilda de Piratas",
            "Cavernas Cristalinas": "Clã Luo",
            "Deserto Carmesim": "Nômades do Deserto",
            "Vila Crisântemos": "Império Central",
            "Floresta Nublada": "Neutral",
            "Pântano dos Mil Venenos": "Lua Sombria",
        }
        
        # Poder base das facções
        self.faction_power: Dict[str, int] = {
            "Império Central": 1000,
            "Seita Arcaica": 800,
            "Lua Sombria": 500,
            "Monastério da Aurora": 600,
            "Guilda de Piratas": 400,
            "Clã Luo": 350,
            "Nômades do Deserto": 200,
        }
        
        # Recursos das facções
        self.faction_resources: Dict[str, int] = {
            "Império Central": 10000,
            "Seita Arcaica": 5000,
            "Lua Sombria": 3000,
            "Monastério da Aurora": 4000,
            "Guilda de Piratas": 6000,
            "Clã Luo": 8000,
            "Nômades do Deserto": 1500,
        }

    async def simulate_faction_turn(self, current_turn: int) -> List[Dict[str, Any]]:
        """
        Executa uma rodada de simulação de facções.
        Chamado pelo DailyTickSimulator.
        
        Returns:
            Lista de eventos gerados neste turno
        """
        events = []
        
        # 1. Processar guerras ativas
        war_events = await self._process_active_wars(current_turn)
        events.extend(war_events)
        
        # 2. Verificar novas tensões (chance de guerra)
        tension_events = await self._check_for_new_tensions(current_turn)
        events.extend(tension_events)
        
        # 3. Processar alianças
        alliance_events = await self._process_alliances(current_turn)
        events.extend(alliance_events)
        
        # 4. Atualizar influência territorial
        territory_events = await self._update_territorial_influence(current_turn)
        events.extend(territory_events)
        
        # 5. Regenerar recursos
        await self._regenerate_faction_resources()
        
        return events

    async def _process_active_wars(self, current_turn: int) -> List[Dict[str, Any]]:
        """Processa batalhas em guerras ativas."""
        events = []
        
        if not self.faction_repo:
            return events
        
        # Buscar todas as facções
        factions = await self.faction_repo.get_all()
        
        for faction in factions:
            relations = faction.relations or {}
            
            for other_name, relation in relations.items():
                if relation == self.RELATION_WAR:
                    # Simular batalha
                    battle_result = await self._simulate_battle(
                        faction.name, 
                        other_name, 
                        current_turn
                    )
                    
                    if battle_result:
                        events.append(battle_result)
        
        return events

    async def _simulate_battle(
        self, 
        attacker_name: str, 
        defender_name: str,
        current_turn: int
    ) -> Optional[Dict[str, Any]]:
        """
        Simula uma batalha entre duas facções.
        
        Returns:
            Evento de batalha ou None se não houver batalha
        """
        # 30% de chance de batalha por turno
        if random.random() > 0.3:
            return None
        
        attacker_power = self.faction_power.get(attacker_name, 100)
        defender_power = self.faction_power.get(defender_name, 100)
        
        # Adicionar variação aleatória
        attacker_roll = attacker_power * random.uniform(0.7, 1.3)
        defender_roll = defender_power * random.uniform(0.7, 1.3)
        
        if attacker_roll > defender_roll:
            # Atacante vence
            winner = attacker_name
            loser = defender_name
            power_lost = int(defender_power * 0.1)  # Perde 10% do poder
            self.faction_power[defender_name] = max(50, defender_power - power_lost)
        else:
            # Defensor vence
            winner = defender_name
            loser = attacker_name
            power_lost = int(attacker_power * 0.1)
            self.faction_power[attacker_name] = max(50, attacker_power - power_lost)
        
        # Criar evento
        event = {
            "type": self.EVENT_FACTION_WEAKENED,
            "description": f"Batalha entre {attacker_name} e {defender_name}! {winner} venceu.",
            "public_description": f"Rumores de batalha entre cultivadores do {attacker_name} e {defender_name} se espalham.",
            "winner": winner,
            "loser": loser,
            "power_lost": power_lost,
            "turn": current_turn
        }
        
        # Persistir evento se tiver repo
        if self.world_event_repo:
            await self.world_event_repo.create(
                event_type="faction_battle",
                description=event["description"],
                public_description=event["public_description"],
                turn_occurred=current_turn,
                effects={"winner": winner, "loser": loser, "power_lost": power_lost}
            )
        
        print(f"[FACTION WAR] {event['description']}")
        return event

    async def _check_for_new_tensions(self, current_turn: int) -> List[Dict[str, Any]]:
        """
        Verifica se novas tensões surgem entre facções.
        5% de chance por turno de conflito surgir.
        """
        events = []
        
        # Pares de facções com tensão natural
        tension_pairs = [
            ("Império Central", "Lua Sombria"),  # Luz vs Sombra
            ("Monastério da Aurora", "Lua Sombria"),  # Pureza vs Assassinos
            ("Clã Luo", "Guilda de Piratas"),  # Riqueza vs Saque
            ("Seita Arcaica", "Império Central"),  # Poder vs Controle
        ]
        
        for faction_a, faction_b in tension_pairs:
            # 5% de chance de guerra por turno
            if random.random() < 0.05:
                event = await self._declare_war(faction_a, faction_b, current_turn)
                if event:
                    events.append(event)
        
        return events

    async def _declare_war(
        self, 
        faction_a: str, 
        faction_b: str, 
        current_turn: int
    ) -> Optional[Dict[str, Any]]:
        """Declara guerra entre duas facções."""
        
        # Atualizar relações
        if self.faction_repo:
            faction_a_obj = await self.faction_repo.get_by_name(faction_a)
            faction_b_obj = await self.faction_repo.get_by_name(faction_b)
            
            if faction_a_obj and faction_b_obj:
                # Verificar se já estão em guerra
                if faction_a_obj.relations.get(faction_b) == self.RELATION_WAR:
                    return None
                
                # Atualizar relações para guerra
                faction_a_obj.relations[faction_b] = self.RELATION_WAR
                faction_b_obj.relations[faction_a] = self.RELATION_WAR
                
                await self.faction_repo.update(faction_a_obj)
                await self.faction_repo.update(faction_b_obj)
        
        event = {
            "type": self.EVENT_WAR_DECLARED,
            "description": f"{faction_a} declarou guerra contra {faction_b}!",
            "public_description": f"Tensões explodem! {faction_a} e {faction_b} estão em guerra aberta!",
            "factions": [faction_a, faction_b],
            "turn": current_turn
        }
        
        if self.world_event_repo:
            await self.world_event_repo.create(
                event_type="war_declared",
                description=event["description"],
                public_description=event["public_description"],
                turn_occurred=current_turn,
                effects={"factions": [faction_a, faction_b]}
            )
        
        print(f"[FACTION WAR] {event['description']}")
        return event

    async def _process_alliances(self, current_turn: int) -> List[Dict[str, Any]]:
        """
        Processa formação de novas alianças.
        Facções fracas buscam aliados.
        """
        events = []
        
        # Facções que podem se aliar
        potential_allies = [
            ("Clã Luo", "Império Central"),  # Riqueza + Poder
            ("Nômades do Deserto", "Guilda de Piratas"),  # Mercadores
        ]
        
        for faction_a, faction_b in potential_allies:
            power_a = self.faction_power.get(faction_a, 100)
            power_b = self.faction_power.get(faction_b, 100)
            
            # Se uma facção está fraca, 10% de chance de buscar aliança
            if power_a < 300 or power_b < 300:
                if random.random() < 0.1:
                    event = await self._form_alliance(faction_a, faction_b, current_turn)
                    if event:
                        events.append(event)
        
        return events

    async def _form_alliance(
        self, 
        faction_a: str, 
        faction_b: str, 
        current_turn: int
    ) -> Optional[Dict[str, Any]]:
        """Forma aliança entre duas facções."""
        
        if self.faction_repo:
            faction_a_obj = await self.faction_repo.get_by_name(faction_a)
            faction_b_obj = await self.faction_repo.get_by_name(faction_b)
            
            if faction_a_obj and faction_b_obj:
                # Verificar se já são aliados
                if faction_a_obj.relations.get(faction_b) == self.RELATION_ALLIED:
                    return None
                
                faction_a_obj.relations[faction_b] = self.RELATION_ALLIED
                faction_b_obj.relations[faction_a] = self.RELATION_ALLIED
                
                await self.faction_repo.update(faction_a_obj)
                await self.faction_repo.update(faction_b_obj)
        
        event = {
            "type": self.EVENT_ALLIANCE_FORMED,
            "description": f"{faction_a} e {faction_b} formaram uma aliança!",
            "public_description": f"Nova aliança! {faction_a} e {faction_b} unem forças.",
            "factions": [faction_a, faction_b],
            "turn": current_turn
        }
        
        print(f"[FACTION ALLIANCE] {event['description']}")
        return event

    async def _update_territorial_influence(self, current_turn: int) -> List[Dict[str, Any]]:
        """
        Atualiza controle territorial baseado em poder das facções.
        """
        events = []
        
        # Territórios neutros ou contestados podem ser capturados
        contestable = ["Floresta Nublada", "Vale dos Mil Picos"]
        
        for territory in contestable:
            current_owner = self.territories.get(territory, "Neutral")
            
            # Encontrar facção mais poderosa adjacente
            adjacent_factions = self._get_adjacent_factions(territory)
            
            if not adjacent_factions:
                continue
            
            # Facção mais forte tem chance de capturar
            strongest = max(adjacent_factions, key=lambda f: self.faction_power.get(f, 0))
            strongest_power = self.faction_power.get(strongest, 0)
            
            # 5% de chance de captura se poder > 400
            if strongest_power > 400 and random.random() < 0.05:
                if current_owner != strongest:
                    self.territories[territory] = strongest
                    
                    event = {
                        "type": self.EVENT_TERRITORY_CAPTURED,
                        "description": f"{strongest} capturou {territory}!",
                        "public_description": f"O território de {territory} agora está sob controle de {strongest}.",
                        "territory": territory,
                        "new_owner": strongest,
                        "previous_owner": current_owner,
                        "turn": current_turn
                    }
                    
                    events.append(event)
                    print(f"[TERRITORY] {event['description']}")
        
        return events

    def _get_adjacent_factions(self, territory: str) -> List[str]:
        """Retorna facções com territórios adjacentes."""
        
        # Mapa de adjacência simplificado
        adjacency = {
            "Floresta Nublada": ["Cidade Imperial", "Vila Crisântemos", "Cavernas Cristalinas"],
            "Vale dos Mil Picos": ["Montanha Arcaica", "Cidade Imperial"],
        }
        
        adjacent_territories = adjacency.get(territory, [])
        factions = set()
        
        for adj_territory in adjacent_territories:
            owner = self.territories.get(adj_territory)
            if owner and owner != "Neutral":
                factions.add(owner)
        
        return list(factions)

    async def _regenerate_faction_resources(self):
        """Regenera recursos das facções por turno."""
        
        for faction_name in self.faction_resources:
            # +5% de recursos por turno
            current = self.faction_resources[faction_name]
            self.faction_resources[faction_name] = int(current * 1.05)
            
            # Cap máximo
            self.faction_resources[faction_name] = min(
                self.faction_resources[faction_name], 
                50000
            )

    # === MÉTODOS PÚBLICOS PARA CONSULTA ===
    
    def get_territory_owner(self, location: str) -> str:
        """Retorna a facção que controla um território."""
        return self.territories.get(location, "Neutral")
    
    def get_faction_power(self, faction_name: str) -> int:
        """Retorna o poder de uma facção."""
        return self.faction_power.get(faction_name, 0)
    
    def get_faction_relations(self, faction_name: str) -> Dict[str, str]:
        """Retorna as relações de uma facção com outras."""
        # Implementação simplificada - em produção viria do banco
        default_relations = {
            "Império Central": {
                "Seita Arcaica": "neutral",
                "Lua Sombria": "hostile",
                "Monastério da Aurora": "allied",
            },
            "Lua Sombria": {
                "Império Central": "hostile",
                "Monastério da Aurora": "hostile",
            }
        }
        return default_relations.get(faction_name, {})
    
    def is_player_welcome(self, player_faction: str, location: str) -> bool:
        """Verifica se jogador é bem-vindo em um território."""
        
        territory_owner = self.get_territory_owner(location)
        
        if territory_owner == "Neutral":
            return True
        
        if territory_owner == player_faction:
            return True
        
        relations = self.get_faction_relations(territory_owner)
        player_relation = relations.get(player_faction, "neutral")
        
        return player_relation != "hostile" and player_relation != "at_war"

    async def player_action_affects_faction(
        self, 
        player_id: int, 
        action_type: str, 
        faction_name: str, 
        amount: int = 10
    ):
        """
        Processa ações do jogador que afetam reputação com facções.
        
        Args:
            player_id: ID do jogador
            action_type: "help", "attack", "betray"
            faction_name: Nome da facção afetada
            amount: Quantidade de mudança de reputação
        """
        
        # Este método seria expandido para atualizar a reputação do player
        # com a facção e potencialmente triggerar eventos
        
        if action_type == "help":
            print(f"[FACTION] Player {player_id} ganhou {amount} reputação com {faction_name}")
        elif action_type == "attack":
            print(f"[FACTION] Player {player_id} perdeu {amount} reputação com {faction_name}")
        elif action_type == "betray":
            print(f"[FACTION] Player {player_id} é agora INIMIGO de {faction_name}")
