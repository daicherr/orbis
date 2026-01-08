"""
Ecology Simulator - Monster migration and population dynamics
Based on GDD: Godfiends need to eat, monsters migrate based on resources
"""

from typing import List, Dict, Any
import random


class EcologySimulator:
    """
    Simula ecologia do mundo: migração de monstros, populações, predadores.
    Monstros migram baseado em recursos e pressão de caça.
    """
    
    def __init__(self, world_map: Dict[str, List[str]] = None):
        """
        Inicializa o simulador de ecologia.
        
        Args:
            world_map: Mapa de conexões entre locais
        """
        
        # Mapa de conexões entre locais
        self.world_map = world_map or {
            "Floresta Nublada": ["Vila Crisântemos", "Cavernas Cristalinas", "Vale dos Mil Picos"],
            "Vale dos Mil Picos": ["Floresta Nublada", "Montanha Arcaica"],
            "Cavernas Cristalinas": ["Floresta Nublada", "Cidade Subterrânea"],
            "Montanha Arcaica": ["Vale dos Mil Picos", "Passo da Montanha"],
            "Passo da Montanha": ["Montanha Arcaica", "Cidade Imperial", "Geleiras Sussurrantes"],
            "Pântano dos Mil Venenos": ["Floresta Venenosa"],
            "Floresta Venenosa": ["Pântano dos Mil Venenos", "Seita Lua Sombria"],
            "Deserto Carmesim": ["Oásis Eterno", "Ruínas Solares"],
            "Geleiras Sussurrantes": ["Passo da Montanha", "Pico do Trovão Eterno"],
        }
        
        # População de monstros por região (tipo -> quantidade)
        self.monster_populations: Dict[str, Dict[str, int]] = {
            "Floresta Nublada": {
                "Javali de Ferro": 50,
                "Cobra de Névoa": 30,
                "Shadow Fox": 20,
                "Lobo de Névoa": 40,
                "Urso Espiritual": 5
            },
            "Vale dos Mil Picos": {
                "Águia de Trovão": 25,
                "Serpente de Pedra": 15,
                "Golem Natural": 10
            },
            "Cavernas Cristalinas": {
                "Besta de Cristal": 30,
                "Golem de Pedra": 20,
                "Morcego Espiritual": 100
            },
            "Montanha Arcaica": {
                "Dragão de Gelo": 3,
                "Fênix de Neve": 1,
                "Lobo de Gelo": 15
            },
            "Pântano dos Mil Venenos": {
                "Sapo Venenoso": 80,
                "Sanguessuga Gigante": 50,
                "Hidra do Pântano": 2
            },
            "Deserto Carmesim": {
                "Escorpião Gigante": 40,
                "Serpente de Areia": 30,
                "Wyrm do Deserto": 3
            },
            "Geleiras Sussurrantes": {
                "Urso Polar Espiritual": 10,
                "Lobo de Gelo": 25,
                "Mamute Fantasma": 5
            }
        }
        
        # Capacidade de carga por região (máximo de monstros)
        self.carrying_capacity: Dict[str, int] = {
            "Floresta Nublada": 200,
            "Vale dos Mil Picos": 80,
            "Cavernas Cristalinas": 200,
            "Montanha Arcaica": 50,
            "Pântano dos Mil Venenos": 150,
            "Deserto Carmesim": 100,
            "Geleiras Sussurrantes": 60
        }
        
        # Pressão de caça por região (aumenta quando jogadores caçam muito)
        self.hunting_pressure: Dict[str, int] = {}

    async def process_migrations(self) -> List[Dict[str, Any]]:
        """
        Processa migrações de monstros entre regiões.
        
        Returns:
            Lista de eventos de migração
        """
        
        events = []
        
        for region, populations in self.monster_populations.items():
            # Calcular população total
            total_pop = sum(populations.values())
            capacity = self.carrying_capacity.get(region, 100)
            pressure = self.hunting_pressure.get(region, 0)
            
            # Se população excede capacidade ou há muita caça, migrar
            if total_pop > capacity * 0.9 or pressure > 50:
                migration_event = await self._trigger_migration(region)
                if migration_event:
                    events.append(migration_event)
            
            # Reprodução natural (5% por turno)
            await self._process_reproduction(region)
        
        # Reduzir pressão de caça naturalmente
        for region in self.hunting_pressure:
            self.hunting_pressure[region] = max(0, self.hunting_pressure[region] - 5)
        
        return events

    async def _trigger_migration(self, from_region: str) -> Dict[str, Any]:
        """
        Executa migração de monstros de uma região superpopulada.
        """
        
        # Encontrar região vizinha com menor população
        neighbors = self.world_map.get(from_region, [])
        
        if not neighbors:
            return None
        
        # Escolher destino (menor população)
        dest = min(
            neighbors,
            key=lambda n: sum(self.monster_populations.get(n, {}).values())
        )
        
        # Escolher tipo de monstro que migra (o mais populoso)
        populations = self.monster_populations.get(from_region, {})
        
        if not populations:
            return None
        
        migrating_type = max(populations, key=populations.get)
        migrating_count = max(1, populations[migrating_type] // 5)  # 20% migra
        
        # Executar migração
        self.monster_populations[from_region][migrating_type] -= migrating_count
        
        if dest not in self.monster_populations:
            self.monster_populations[dest] = {}
        
        if migrating_type not in self.monster_populations[dest]:
            self.monster_populations[dest][migrating_type] = 0
        
        self.monster_populations[dest][migrating_type] += migrating_count
        
        event = {
            "type": "monster_migration",
            "from_region": from_region,
            "to_region": dest,
            "monster_type": migrating_type,
            "count": migrating_count,
            "description": f"Uma horda de {migrating_count} {migrating_type}s migrou de {from_region} para {dest}!"
        }
        
        print(f"[ECOLOGY] {event['description']}")
        return event

    async def _process_reproduction(self, region: str):
        """
        Processa reprodução natural de monstros.
        5% de aumento por turno, limitado pela capacidade de carga.
        """
        
        populations = self.monster_populations.get(region, {})
        capacity = self.carrying_capacity.get(region, 100)
        total_pop = sum(populations.values())
        
        # Só reproduz se abaixo da capacidade
        if total_pop >= capacity:
            return
        
        for monster_type, count in populations.items():
            if count > 0:
                # 5% de reprodução
                births = max(1, int(count * 0.05))
                
                # Limitar pelo espaço disponível
                space_left = capacity - sum(populations.values())
                births = min(births, space_left)
                
                if births > 0:
                    self.monster_populations[region][monster_type] += births

    # === MÉTODOS PÚBLICOS ===
    
    def register_hunt(self, region: str, monster_type: str, count: int = 1):
        """
        Registra que o jogador caçou monstros em uma região.
        Aumenta pressão de caça e reduz população.
        """
        
        # Reduzir população
        if region in self.monster_populations:
            if monster_type in self.monster_populations[region]:
                self.monster_populations[region][monster_type] = max(
                    0,
                    self.monster_populations[region][monster_type] - count
                )
        
        # Aumentar pressão de caça
        if region not in self.hunting_pressure:
            self.hunting_pressure[region] = 0
        
        self.hunting_pressure[region] += count * 2
        
        print(f"[ECOLOGY] {count} {monster_type}(s) caçados em {region}. Pressão: {self.hunting_pressure[region]}")

    def get_monster_population(self, region: str) -> Dict[str, int]:
        """Retorna população de monstros em uma região."""
        return self.monster_populations.get(region, {})
    
    def get_encounter_chance(self, region: str, monster_type: str) -> float:
        """
        Calcula chance de encontrar um tipo de monstro em uma região.
        Baseado na população atual.
        """
        
        populations = self.monster_populations.get(region, {})
        total = sum(populations.values())
        
        if total == 0:
            return 0.0
        
        monster_count = populations.get(monster_type, 0)
        return monster_count / total
    
    def get_random_encounter(self, region: str) -> str:
        """
        Retorna um monstro aleatório para encontro baseado na população.
        Monstros mais comuns têm mais chance de aparecer.
        """
        
        populations = self.monster_populations.get(region, {})
        
        if not populations:
            return None
        
        # Weighted random choice
        total = sum(populations.values())
        roll = random.randint(1, total)
        
        cumulative = 0
        for monster_type, count in populations.items():
            cumulative += count
            if roll <= cumulative:
                return monster_type
        
        return list(populations.keys())[0]
    
    def spawn_monster_horde(self, region: str) -> Dict[str, Any]:
        """
        Cria um evento de horda de monstros (evento mundial).
        Dobra a população de um tipo aleatório.
        """
        
        populations = self.monster_populations.get(region, {})
        
        if not populations:
            return None
        
        # Escolher monstro aleatório
        monster_type = random.choice(list(populations.keys()))
        original_count = populations[monster_type]
        new_count = original_count * 2
        
        self.monster_populations[region][monster_type] = new_count
        
        event = {
            "type": "monster_horde",
            "region": region,
            "monster_type": monster_type,
            "count": new_count - original_count,
            "description": f"Uma horda de {monster_type}s invadiu {region}! População dobrou!"
        }
        
        print(f"[ECOLOGY EVENT] {event['description']}")
        return event
    
    def get_ecology_report(self) -> Dict[str, Any]:
        """
        Retorna relatório completo de ecologia para debug/admin.
        """
        
        report = {
            "regions": {},
            "total_monsters": 0,
            "most_populated": None,
            "least_populated": None,
            "high_pressure_regions": []
        }
        
        max_pop = 0
        min_pop = float('inf')
        
        for region, populations in self.monster_populations.items():
            total = sum(populations.values())
            capacity = self.carrying_capacity.get(region, 100)
            pressure = self.hunting_pressure.get(region, 0)
            
            report["regions"][region] = {
                "population": total,
                "capacity": capacity,
                "fill_rate": round(total / capacity * 100, 1) if capacity > 0 else 0,
                "hunting_pressure": pressure,
                "monsters": populations
            }
            
            report["total_monsters"] += total
            
            if total > max_pop:
                max_pop = total
                report["most_populated"] = region
            
            if total < min_pop:
                min_pop = total
                report["least_populated"] = region
            
            if pressure > 30:
                report["high_pressure_regions"].append(region)
        
        return report
