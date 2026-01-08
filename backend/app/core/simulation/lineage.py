"""
Lineage Simulator - Hereditary vendettas and family systems
Based on GDD: If player kills NPC, their father gains 'Vendetta: Player' trait
"""

from typing import List, Dict, Any, Optional
import random


class LineageSimulator:
    """
    Simula sistema de linhagem e vingança hereditária.
    Quando um NPC morre, seus parentes podem buscar vingança.
    """
    
    def __init__(self, npc_repo=None):
        """
        Inicializa o simulador de linhagem.
        
        Args:
            npc_repo: Repository de NPCs
        """
        self.npc_repo = npc_repo
        
        # Cache de relações familiares (NPC_ID -> lista de parentes)
        self.family_relations: Dict[int, List[Dict[str, Any]]] = {}
        
        # Vendetas ativas (killer_id -> lista de NPCs buscando vingança)
        self.active_vendettas: Dict[int, List[int]] = {}
        
        # Mortes recentes para processamento
        self.recent_deaths: List[Dict[str, Any]] = []

    async def register_death(
        self, 
        victim_id: int, 
        victim_name: str,
        victim_rank: int,
        killer_id: int,
        killer_type: str = "player",  # "player" ou "npc"
        location: str = None
    ) -> List[Dict[str, Any]]:
        """
        Registra a morte de um NPC e processa consequências de linhagem.
        
        Returns:
            Lista de eventos gerados (vinganças, spawns de parentes, etc.)
        """
        
        events = []
        
        # Registrar morte
        death_record = {
            "victim_id": victim_id,
            "victim_name": victim_name,
            "victim_rank": victim_rank,
            "killer_id": killer_id,
            "killer_type": killer_type,
            "location": location
        }
        
        self.recent_deaths.append(death_record)
        
        print(f"[LINEAGE] Morte registrada: {victim_name} (Rank {victim_rank}) morto por {killer_type} {killer_id}")
        
        # Processar vingança se vítima for importante (Rank 3+)
        if victim_rank >= 3:
            vendetta_events = await self._process_vendetta_trigger(death_record)
            events.extend(vendetta_events)
        
        # Chance de parente aparecer (30% para Rank 3+, 10% para outros)
        spawn_chance = 0.3 if victim_rank >= 3 else 0.1
        
        if random.random() < spawn_chance:
            spawn_event = await self._spawn_vengeful_relative(death_record)
            if spawn_event:
                events.append(spawn_event)
        
        return events

    async def check_for_vendetta(
        self, 
        killed_npc: Dict[str, Any], 
        killer_id: int
    ) -> bool:
        """
        Verifica se o NPC morto tem parentes e atribui vendeta.
        Interface simplificada para uso externo.
        """
        
        victim_id = killed_npc.get("id", 0)
        victim_name = killed_npc.get("name", "Unknown")
        victim_rank = killed_npc.get("rank", 1)
        
        events = await self.register_death(
            victim_id=victim_id,
            victim_name=victim_name,
            victim_rank=victim_rank,
            killer_id=killer_id,
            killer_type="player"
        )
        
        return len(events) > 0

    async def _process_vendetta_trigger(
        self, 
        death_record: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Processa trigger de vingança quando NPC importante morre.
        """
        
        events = []
        killer_id = death_record["killer_id"]
        victim_name = death_record["victim_name"]
        victim_rank = death_record["victim_rank"]
        
        # Buscar parentes existentes
        relatives = await self._find_relatives(death_record["victim_id"])
        
        for relative in relatives:
            # Atribuir vendeta ao parente
            if self.npc_repo:
                relative_npc = await self.npc_repo.get_by_id(relative["id"])
                
                if relative_npc:
                    relative_npc.vendetta_target = killer_id
                    relative_npc.emotional_state = "vengeful"
                    await self.npc_repo.update(relative_npc)
                    
                    events.append({
                        "type": "vendetta_assigned",
                        "avenger_id": relative["id"],
                        "avenger_name": relative["name"],
                        "target_id": killer_id,
                        "reason": f"vingança por {victim_name}",
                        "description": f"{relative['name']} jurou vingança pela morte de {victim_name}!"
                    })
                    
                    print(f"[LINEAGE] {relative['name']} busca vingança por {victim_name}!")
        
        # Registrar vendeta ativa
        if killer_id not in self.active_vendettas:
            self.active_vendettas[killer_id] = []
        
        for relative in relatives:
            if relative["id"] not in self.active_vendettas[killer_id]:
                self.active_vendettas[killer_id].append(relative["id"])
        
        return events

    async def _find_relatives(self, npc_id: int) -> List[Dict[str, Any]]:
        """
        Busca parentes de um NPC.
        """
        
        # Primeiro verificar cache
        if npc_id in self.family_relations:
            return self.family_relations[npc_id]
        
        # Se não tiver repo, retornar vazio
        if not self.npc_repo:
            return []
        
        # Buscar NPCs com mesmo family_id ou que mencionam este NPC
        # Na implementação real, usaria campo family_id no modelo NPC
        # Por agora, retorna lista vazia (parentes serão gerados dinamicamente)
        
        return []

    async def _spawn_vengeful_relative(
        self, 
        death_record: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Gera um parente vingativo quando NPC importante morre.
        """
        
        victim_name = death_record["victim_name"]
        victim_rank = death_record["victim_rank"]
        killer_id = death_record["killer_id"]
        location = death_record["location"]
        
        # Determinar tipo de parente
        relative_types = [
            {"title": "Pai", "rank_bonus": 2, "weight": 3},
            {"title": "Mãe", "rank_bonus": 2, "weight": 2},
            {"title": "Irmão mais velho", "rank_bonus": 1, "weight": 4},
            {"title": "Irmã mais velha", "rank_bonus": 1, "weight": 3},
            {"title": "Mestre", "rank_bonus": 3, "weight": 2},
            {"title": "Discípulo sênior", "rank_bonus": 0, "weight": 5},
            {"title": "Tio", "rank_bonus": 1, "weight": 3},
            {"title": "Primo", "rank_bonus": 0, "weight": 4},
        ]
        
        # Weighted random choice
        total_weight = sum(r["weight"] for r in relative_types)
        roll = random.randint(1, total_weight)
        
        cumulative = 0
        chosen = relative_types[0]
        
        for rel_type in relative_types:
            cumulative += rel_type["weight"]
            if roll <= cumulative:
                chosen = rel_type
                break
        
        # Calcular rank do parente
        new_rank = min(9, victim_rank + chosen["rank_bonus"])
        
        # Gerar nome
        new_name = f"{chosen['title']} de {victim_name}"
        
        # Personalidade vingativa
        personality = ["vengeful", "ruthless", "relentless"]
        
        # Criar NPC se tiver repo
        new_npc = None
        
        if self.npc_repo:
            new_npc = await self.npc_repo.create(
                name=new_name,
                rank=new_rank,
                personality_traits=personality,
                emotional_state="vengeful",
                vendetta_target=killer_id,
                current_location=location or "Cidade Imperial"
            )
            
            # Registrar relação familiar
            if death_record["victim_id"] not in self.family_relations:
                self.family_relations[death_record["victim_id"]] = []
            
            self.family_relations[death_record["victim_id"]].append({
                "id": new_npc.id,
                "name": new_name,
                "relationship": chosen["title"]
            })
        
        event = {
            "type": "avenger_spawned",
            "avenger_name": new_name,
            "avenger_rank": new_rank,
            "target_id": killer_id,
            "victim_name": victim_name,
            "location": location,
            "description": f"{new_name} (Rank {new_rank}) surgiu buscando vingança pela morte de {victim_name}!"
        }
        
        print(f"[LINEAGE SPAWN] {event['description']}")
        
        return event

    # === MÉTODOS PÚBLICOS ===
    
    def get_vendettas_against(self, player_id: int) -> List[int]:
        """
        Retorna lista de NPC IDs que têm vendeta contra o jogador.
        """
        return self.active_vendettas.get(player_id, [])
    
    def get_vendetta_count(self, player_id: int) -> int:
        """
        Retorna número de NPCs buscando vingança contra o jogador.
        """
        return len(self.active_vendettas.get(player_id, []))
    
    async def resolve_vendetta(self, avenger_id: int, target_id: int):
        """
        Resolve uma vendeta (vingador matou ou foi morto).
        """
        
        if target_id in self.active_vendettas:
            if avenger_id in self.active_vendettas[target_id]:
                self.active_vendettas[target_id].remove(avenger_id)
                print(f"[LINEAGE] Vendeta resolvida: NPC {avenger_id} vs Player {target_id}")
    
    def register_family_bond(
        self, 
        npc_id: int, 
        relative_id: int, 
        relationship: str
    ):
        """
        Registra uma relação familiar entre dois NPCs.
        """
        
        if npc_id not in self.family_relations:
            self.family_relations[npc_id] = []
        
        self.family_relations[npc_id].append({
            "id": relative_id,
            "relationship": relationship
        })
        
        # Relação bidirecional
        if relative_id not in self.family_relations:
            self.family_relations[relative_id] = []
        
        # Inverter relacionamento
        inverse_relations = {
            "Pai": "Filho/Filha",
            "Mãe": "Filho/Filha",
            "Irmão": "Irmão/Irmã",
            "Irmã": "Irmão/Irmã",
            "Mestre": "Discípulo",
            "Discípulo": "Mestre",
        }
        
        inverse = inverse_relations.get(relationship, relationship)
        
        self.family_relations[relative_id].append({
            "id": npc_id,
            "relationship": inverse
        })
    
    def get_lineage_report(self, player_id: int = None) -> Dict[str, Any]:
        """
        Retorna relatório de linhagem para debug/admin.
        """
        
        report = {
            "total_families": len(self.family_relations),
            "total_vendettas": sum(len(v) for v in self.active_vendettas.values()),
            "recent_deaths": len(self.recent_deaths),
            "active_vendettas": self.active_vendettas
        }
        
        if player_id:
            report["vendettas_against_player"] = self.get_vendettas_against(player_id)
        
        return report
