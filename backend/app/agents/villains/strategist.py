"""
Villain Strategist - Off-Screen Movement AI
Moves villains around the map and plans ambushes (Sprint 6)
"""

from typing import Dict, Any, List
from app.database.models.npc import NPC
from app.database.models.player import Player
import random

class Strategist:
    """
    IA estratégica para vilões.
    Opera no mapa-múndi, movendo NPCs off-screen.
    [SPRINT 6] Sistema de emboscadas e caça.
    """
    
    def __init__(self, world_map: Dict[str, Any] = None):
        """
        Inicializa o estrategista com um mapa do mundo.
        
        Args:
            world_map: Estrutura com locations e conexões
        """
        
        # Mapa padrão baseado em locations_desc.md
        self.world_map = world_map or {
            "Vila Crisântemos": ["Floresta Nublada", "Cidade Imperial"],
            "Floresta Nublada": ["Vila Crisântemos", "Cavernas Cristalinas"],
            "Cavernas Cristalinas": ["Floresta Nublada", "Cidade Subterrânea"],
            "Templo Abismo": ["Cidade Imperial", "Montanha Arcaica"],
            "Cidade Imperial": ["Vila Crisântemos", "Templo Abismo", "Passo da Montanha"],
            "Montanha Arcaica": ["Templo Abismo", "Passo da Montanha"],
            "Passo da Montanha": ["Cidade Imperial", "Montanha Arcaica", "Cidade Subterrânea"],
            "Cidade Subterrânea": ["Cavernas Cristalinas", "Passo da Montanha"]
        }
        
        # Tracking de ambushes planejadas
        self.planned_ambushes: Dict[int, Dict[str, Any]] = {}  # NPC_ID -> ambush_data

    def decide_next_action(self, villain: NPC, player: Player) -> Dict[str, Any]:
        """
        Determina a próxima ação estratégica para um vilão.
        
        [SPRINT 6] Tipos de ação:
        - hunt: Perseguir jogador
        - ambush: Preparar emboscada
        - retreat: Fugir se ferido
        - patrol: Patrulhar território
        - idle: Sem ação
        
        Returns:
            {
                "type": str,
                "destination": str,
                "target": str,
                "wait_turns": int
            }
        """
        
        action = {"type": "idle", "target": None, "destination": None, "wait_turns": 0}
        
        # 1. RETREAT se HP baixo
        if villain.current_hp < villain.max_hp * 0.3:
            action["type"] = "retreat"
            action["destination"] = self._find_safe_location(villain)
            print(f"[RUN] Strategist: {villain.name} esta fugindo para {action['destination']}!")
            return action
        
        # 2. HUNT se tem vendetta
        if villain.vendetta_target == player.id:
            action["type"] = "hunt"
            action["target"] = player.name
            
            # Calcular rota para o jogador
            player_location = player.current_location
            
            if villain.current_location != player_location:
                # Mover em direção ao jogador
                action["destination"] = self._get_next_step(villain.current_location, player_location)
                print(f"[HUNT] Strategist: {villain.name} esta cacando {player.name}. Movendo para {action['destination']}.")
            else:
                # Já está no mesmo local - preparar emboscada
                action["type"] = "ambush"
                action["wait_turns"] = random.randint(1, 3)  # Esperar 1-3 turnos
                self._plan_ambush(villain, player)
                print(f"[AMBUSH] Strategist: {villain.name} esta preparando uma emboscada em {villain.current_location}!")
            
            return action
        
        # 3. PATROL território se hostil
        if villain.emotional_state == "hostile":
            action["type"] = "patrol"
            action["destination"] = self._get_random_neighbor(villain.current_location)
            print(f"[PATROL] Strategist: {villain.name} esta patrulhando {action['destination']}.")
            return action
        
        # 4. IDLE caso padrão
        print(f"[IDLE] Strategist: {villain.name} esta idle em {villain.current_location}.")
        return action

    def _get_next_step(self, from_location: str, to_location: str) -> str:
        """
        [SPRINT 6] Calcula o próximo passo na rota.
        Usa BFS simples para encontrar caminho mais curto.
        """
        
        if from_location == to_location:
            return from_location
        
        # BFS para encontrar caminho
        queue = [(from_location, [from_location])]
        visited = {from_location}
        
        while queue:
            current, path = queue.pop(0)
            
            # Verificar vizinhos
            neighbors = self.world_map.get(current, [])
            
            for neighbor in neighbors:
                if neighbor == to_location:
                    # Chegamos! Retornar próximo passo
                    if len(path) > 0:
                        return path[1] if len(path) > 1 else neighbor
                    return neighbor
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        # Se não encontrou rota, ficar parado
        return from_location

    def _get_random_neighbor(self, location: str) -> str:
        """Retorna uma localização vizinha aleatória."""
        
        neighbors = self.world_map.get(location, [])
        
        if neighbors:
            return random.choice(neighbors)
        
        return location  # Ficar no mesmo lugar

    def _find_safe_location(self, villain: NPC) -> str:
        """
        [SPRINT 6] Encontra local seguro para fugir.
        Prioriza locais remotos (Montanha Arcaica, Cidade Subterrânea).
        """
        
        safe_locations = ["Montanha Arcaica", "Cidade Subterrânea", "Templo Abismo"]
        
        # Se já estiver em local seguro, ficar lá
        if villain.current_location in safe_locations:
            return villain.current_location
        
        # Encontrar local seguro mais próximo
        for safe_loc in safe_locations:
            if safe_loc in self.world_map.get(villain.current_location, []):
                return safe_loc
        
        # Fallback: qualquer vizinho
        return self._get_random_neighbor(villain.current_location)

    def _plan_ambush(self, villain: NPC, player: Player):
        """
        [SPRINT 6] Registra emboscada planejada.
        """
        
        self.planned_ambushes[villain.id] = {
            "target_player_id": player.id,
            "location": villain.current_location,
            "turns_until_trigger": random.randint(1, 3),
            "bonus_damage": 1.5  # +50% dano no primeiro ataque
        }

    def check_for_ambush(self, location: str, player_id: int) -> List[NPC]:
        """
        [SPRINT 6] Verifica se há emboscadas prontas nesta localização.
        
        Returns:
            Lista de NPCs prontos para emboscar o jogador
        """
        
        ambushers = []
        
        for npc_id, ambush_data in list(self.planned_ambushes.items()):
            if (ambush_data["location"] == location and 
                ambush_data["target_player_id"] == player_id and
                ambush_data["turns_until_trigger"] <= 0):
                
                ambushers.append(npc_id)
                del self.planned_ambushes[npc_id]
        
        return ambushers

    def update_ambush_timers(self):
        """
        [SPRINT 6] Atualiza os timers de emboscadas.
        Deve ser chamado a cada turno.
        """
        
        for npc_id in self.planned_ambushes:
            self.planned_ambushes[npc_id]["turns_until_trigger"] -= 1

    def get_ambush_bonus(self, npc_id: int) -> float:
        """[SPRINT 6] Retorna multiplicador de dano de emboscada."""
        
        if npc_id in self.planned_ambushes:
            return self.planned_ambushes[npc_id].get("bonus_damage", 1.0)
        
        return 1.0

