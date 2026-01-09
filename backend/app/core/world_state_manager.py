"""
World State Manager - Gerenciador Centralizado do Estado do Mundo
GEM RPG ORBIS - Arquitetura Cognitiva

O World State Manager é o cérebro central que:
1. Mantém o estado global do mundo em memória
2. Sincroniza com o banco de dados
3. Fornece consultas rápidas sobre qualquer aspecto do mundo
4. Gerencia eventos globais e propagação de mudanças
5. Coordena simulações em background

Este é o "Oracle" - sabe tudo sobre o estado atual do mundo.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import asyncio


class WorldRegion(str, Enum):
    """Regiões do mundo."""
    INITIAL_ZONE = "initial_zone"
    MISTY_FOREST = "misty_forest"
    DRAGON_MOUNTAINS = "dragon_mountains"
    MERCHANT_DISTRICT = "merchant_district"
    SWORD_SECT = "sword_sect"
    POISON_SWAMP = "poison_swamp"
    SPIRIT_LAKE = "spirit_lake"
    ANCIENT_RUINS = "ancient_ruins"


class WeatherType(str, Enum):
    """Tipos de clima."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    FOG = "fog"
    SNOW = "snow"
    SPIRIT_RAIN = "spirit_rain"  # Chuva de energia espiritual


class MoonPhase(str, Enum):
    """Fases da lua (afetam cultivo)."""
    NEW_MOON = "new_moon"
    WAXING_CRESCENT = "waxing_crescent"
    FIRST_QUARTER = "first_quarter"
    WAXING_GIBBOUS = "waxing_gibbous"
    FULL_MOON = "full_moon"
    WANING_GIBBOUS = "waning_gibbous"
    LAST_QUARTER = "last_quarter"
    WANING_CRESCENT = "waning_crescent"


@dataclass
class LocationState:
    """Estado de uma localização específica."""
    name: str
    region: WorldRegion
    
    # Estado atual
    current_weather: WeatherType = WeatherType.CLEAR
    danger_level: int = 1  # 1-10
    qi_density: float = 1.0  # Multiplicador de cultivo
    
    # NPCs e entidades
    npc_ids: Set[int] = field(default_factory=set)
    beast_ids: Set[int] = field(default_factory=set)
    player_ids: Set[int] = field(default_factory=set)
    
    # Estado da localização
    is_destroyed: bool = False
    controlling_faction: Optional[str] = None
    resources: Dict[str, int] = field(default_factory=dict)
    
    # Eventos ativos
    active_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FactionState:
    """Estado de uma facção."""
    name: str
    influence: float = 50.0  # 0-100
    treasury: int = 10000
    territory: List[str] = field(default_factory=list)
    allies: List[str] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)
    leader_id: Optional[int] = None
    member_ids: Set[int] = field(default_factory=set)
    at_war: bool = False
    war_target: Optional[str] = None


@dataclass
class EconomyState:
    """Estado da economia global."""
    base_gold_value: float = 1.0
    inflation_rate: float = 0.0
    
    # Preços por categoria
    item_prices: Dict[str, float] = field(default_factory=dict)
    
    # Escassez por região
    scarcity: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Eventos econômicos ativos
    active_modifiers: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GlobalWorldState:
    """Estado global completo do mundo."""
    # Tempo
    current_datetime: datetime
    moon_phase: MoonPhase
    season: str  # spring, summer, autumn, winter
    
    # Clima global
    global_weather_trend: WeatherType
    
    # Localizações
    locations: Dict[str, LocationState]
    
    # Facções
    factions: Dict[str, FactionState]
    
    # Economia
    economy: EconomyState
    
    # Eventos globais ativos
    global_events: List[Dict[str, Any]]
    
    # Estatísticas
    total_npcs: int = 0
    total_players: int = 0
    
    # Versão do estado (para sincronização)
    version: int = 0
    last_sync: datetime = field(default_factory=datetime.utcnow)


class WorldStateManager:
    """
    Gerenciador singleton do estado do mundo.
    
    Responsabilidades:
    - Manter estado em memória para consultas rápidas
    - Sincronizar com banco de dados periodicamente
    - Propagar mudanças para sistemas dependentes
    - Fornecer API consistente para consultas
    """
    
    _instance: Optional["WorldStateManager"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Estado global
        self._state: Optional[GlobalWorldState] = None
        
        # Repositórios (injetados externamente)
        self._location_repo = None
        self._faction_repo = None
        self._economy_repo = None
        self._npc_repo = None
        self._event_repo = None
        
        # Cache de consultas frequentes
        self._npc_location_cache: Dict[int, str] = {}
        self._player_location_cache: Dict[int, str] = {}
        
        # Listeners para mudanças
        self._change_listeners: List[callable] = []
        
        # Lock para operações thread-safe
        self._lock = asyncio.Lock()
        
        # Background task
        self._sync_task: Optional[asyncio.Task] = None
        
        self._initialized = True
    
    def set_repositories(
        self,
        location_repo=None,
        faction_repo=None,
        economy_repo=None,
        npc_repo=None,
        event_repo=None
    ):
        """Injeta repositórios necessários."""
        self._location_repo = location_repo
        self._faction_repo = faction_repo
        self._economy_repo = economy_repo
        self._npc_repo = npc_repo
        self._event_repo = event_repo
    
    async def initialize(self):
        """Inicializa o estado do mundo a partir do banco de dados."""
        async with self._lock:
            # Inicializar estado base
            from app.core.chronos import world_clock
            current_dt = world_clock.get_current_datetime()
            
            # Calcular fase da lua (simplificado)
            day_of_month = current_dt.day
            if day_of_month <= 3:
                moon = MoonPhase.NEW_MOON
            elif day_of_month <= 7:
                moon = MoonPhase.WAXING_CRESCENT
            elif day_of_month <= 11:
                moon = MoonPhase.FIRST_QUARTER
            elif day_of_month <= 14:
                moon = MoonPhase.WAXING_GIBBOUS
            elif day_of_month <= 17:
                moon = MoonPhase.FULL_MOON
            elif day_of_month <= 21:
                moon = MoonPhase.WANING_GIBBOUS
            elif day_of_month <= 25:
                moon = MoonPhase.LAST_QUARTER
            else:
                moon = MoonPhase.WANING_CRESCENT
            
            # Calcular estação
            month = current_dt.month
            if month in [3, 4, 5]:
                season = "spring"
            elif month in [6, 7, 8]:
                season = "summer"
            elif month in [9, 10, 11]:
                season = "autumn"
            else:
                season = "winter"
            
            # Inicializar localizações
            locations = await self._load_locations()
            
            # Inicializar facções
            factions = await self._load_factions()
            
            # Inicializar economia
            economy = await self._load_economy()
            
            # Carregar eventos globais
            global_events = await self._load_global_events()
            
            self._state = GlobalWorldState(
                current_datetime=current_dt,
                moon_phase=moon,
                season=season,
                global_weather_trend=WeatherType.CLEAR,
                locations=locations,
                factions=factions,
                economy=economy,
                global_events=global_events,
                version=1
            )
            
            print(f"[WorldState] Inicializado com {len(locations)} locais, {len(factions)} facções")
    
    async def _load_locations(self) -> Dict[str, LocationState]:
        """Carrega localizações do banco de dados ou usa defaults."""
        locations = {}
        
        # Localizações default
        default_locations = [
            ("Initial Village", WorldRegion.INITIAL_ZONE, 1, 1.0),
            ("Misty Forest", WorldRegion.MISTY_FOREST, 3, 1.2),
            ("Dragon Mountains", WorldRegion.DRAGON_MOUNTAINS, 6, 1.5),
            ("Merchant City", WorldRegion.MERCHANT_DISTRICT, 2, 0.8),
            ("Sword Sect", WorldRegion.SWORD_SECT, 4, 1.3),
            ("Poison Swamp", WorldRegion.POISON_SWAMP, 5, 0.7),
            ("Spirit Lake", WorldRegion.SPIRIT_LAKE, 4, 2.0),
            ("Ancient Ruins", WorldRegion.ANCIENT_RUINS, 7, 1.8),
        ]
        
        for name, region, danger, qi in default_locations:
            locations[name] = LocationState(
                name=name,
                region=region,
                danger_level=danger,
                qi_density=qi
            )
        
        # Tentar carregar do banco se disponível
        if self._location_repo:
            try:
                db_locations = await self._location_repo.get_all()
                for loc in db_locations:
                    if loc.name in locations:
                        # Atualizar com dados do banco
                        locations[loc.name].is_destroyed = getattr(loc, 'is_destroyed', False)
                        locations[loc.name].controlling_faction = getattr(loc, 'controlling_faction', None)
            except Exception as e:
                print(f"[WorldState] Erro ao carregar locais do DB: {e}")
        
        return locations
    
    async def _load_factions(self) -> Dict[str, FactionState]:
        """Carrega facções."""
        factions = {}
        
        # Facções default
        default_factions = [
            ("Sword Sect", 70.0, ["Dragon Mountains"], [], ["Poison Valley"]),
            ("Poison Valley", 40.0, ["Poison Swamp"], [], ["Sword Sect"]),
            ("Merchant Guild", 60.0, ["Merchant City"], ["Sword Sect"], []),
            ("Azure Dragon Clan", 50.0, ["Spirit Lake"], [], []),
        ]
        
        for name, influence, territory, allies, enemies in default_factions:
            factions[name] = FactionState(
                name=name,
                influence=influence,
                territory=territory,
                allies=allies,
                enemies=enemies
            )
        
        return factions
    
    async def _load_economy(self) -> EconomyState:
        """Carrega estado da economia."""
        # Preços base
        item_prices = {
            "healing_pill": 50.0,
            "qi_pill": 100.0,
            "iron_sword": 200.0,
            "spirit_stone": 1000.0,
            "rice": 2.0,
            "meat": 5.0,
            "herb": 10.0,
        }
        
        # Escassez por região
        scarcity = {
            "Initial Village": {"spirit_stone": 1.5, "meat": 0.8},
            "Merchant City": {"spirit_stone": 0.9, "iron_sword": 0.7},
            "Dragon Mountains": {"rice": 1.8, "healing_pill": 1.2},
        }
        
        return EconomyState(
            item_prices=item_prices,
            scarcity=scarcity
        )
    
    async def _load_global_events(self) -> List[Dict[str, Any]]:
        """Carrega eventos globais ativos."""
        events = []
        
        # Eventos podem vir do banco ou ser gerados
        if self._event_repo:
            try:
                db_events = await self._event_repo.get_active_events()
                events = [e.to_dict() for e in db_events]
            except:
                pass
        
        return events
    
    # ==================== CONSULTAS ====================
    
    def get_state(self) -> Optional[GlobalWorldState]:
        """Retorna o estado global completo."""
        return self._state
    
    def get_location_state(self, location_name: str) -> Optional[LocationState]:
        """Retorna o estado de uma localização específica."""
        if not self._state:
            return None
        return self._state.locations.get(location_name)
    
    def get_faction_state(self, faction_name: str) -> Optional[FactionState]:
        """Retorna o estado de uma facção."""
        if not self._state:
            return None
        return self._state.factions.get(faction_name)
    
    def get_item_price(self, item_id: str, location: str = "") -> float:
        """Retorna o preço de um item, ajustado por localização."""
        if not self._state:
            return 100.0  # Default
        
        base_price = self._state.economy.item_prices.get(item_id, 100.0)
        
        # Aplicar escassez da região
        if location and location in self._state.economy.scarcity:
            scarcity_mod = self._state.economy.scarcity[location].get(item_id, 1.0)
            base_price *= scarcity_mod
        
        # Aplicar inflação
        base_price *= (1 + self._state.economy.inflation_rate)
        
        return round(base_price, 2)
    
    def get_weather(self, location: str = "") -> WeatherType:
        """Retorna o clima atual."""
        if not self._state:
            return WeatherType.CLEAR
        
        if location and location in self._state.locations:
            return self._state.locations[location].current_weather
        
        return self._state.global_weather_trend
    
    def get_qi_density(self, location: str) -> float:
        """Retorna a densidade de Qi em uma localização."""
        if not self._state:
            return 1.0
        
        loc_state = self._state.locations.get(location)
        if not loc_state:
            return 1.0
        
        base_density = loc_state.qi_density
        
        # Modificadores baseados na lua
        if self._state.moon_phase == MoonPhase.FULL_MOON:
            base_density *= 1.5
        elif self._state.moon_phase == MoonPhase.NEW_MOON:
            base_density *= 0.7
        
        return base_density
    
    def get_danger_level(self, location: str) -> int:
        """Retorna o nível de perigo de uma localização."""
        if not self._state:
            return 1
        
        loc_state = self._state.locations.get(location)
        return loc_state.danger_level if loc_state else 1
    
    def get_npcs_at_location(self, location: str) -> Set[int]:
        """Retorna IDs de NPCs em uma localização."""
        if not self._state:
            return set()
        
        loc_state = self._state.locations.get(location)
        return loc_state.npc_ids if loc_state else set()
    
    def get_players_at_location(self, location: str) -> Set[int]:
        """Retorna IDs de jogadores em uma localização."""
        if not self._state:
            return set()
        
        loc_state = self._state.locations.get(location)
        return loc_state.player_ids if loc_state else set()
    
    def get_active_events(self, location: str = "") -> List[Dict[str, Any]]:
        """Retorna eventos ativos, opcionalmente filtrados por localização."""
        if not self._state:
            return []
        
        events = self._state.global_events.copy()
        
        if location and location in self._state.locations:
            events.extend(self._state.locations[location].active_events)
        
        return events
    
    def get_faction_controlling_location(self, location: str) -> Optional[str]:
        """Retorna a facção que controla uma localização."""
        if not self._state:
            return None
        
        loc_state = self._state.locations.get(location)
        return loc_state.controlling_faction if loc_state else None
    
    def get_moon_cultivation_modifier(self) -> float:
        """Retorna o modificador de cultivo baseado na fase da lua."""
        if not self._state:
            return 1.0
        
        modifiers = {
            MoonPhase.NEW_MOON: 0.7,
            MoonPhase.WAXING_CRESCENT: 0.85,
            MoonPhase.FIRST_QUARTER: 1.0,
            MoonPhase.WAXING_GIBBOUS: 1.1,
            MoonPhase.FULL_MOON: 1.5,
            MoonPhase.WANING_GIBBOUS: 1.1,
            MoonPhase.LAST_QUARTER: 1.0,
            MoonPhase.WANING_CRESCENT: 0.85,
        }
        
        return modifiers.get(self._state.moon_phase, 1.0)
    
    # ==================== ATUALIZAÇÕES ====================
    
    async def update_npc_location(self, npc_id: int, old_location: str, new_location: str):
        """Atualiza a localização de um NPC."""
        async with self._lock:
            if not self._state:
                return
            
            # Remover da localização antiga
            if old_location in self._state.locations:
                self._state.locations[old_location].npc_ids.discard(npc_id)
            
            # Adicionar à nova localização
            if new_location in self._state.locations:
                self._state.locations[new_location].npc_ids.add(npc_id)
            
            # Atualizar cache
            self._npc_location_cache[npc_id] = new_location
            
            # Incrementar versão
            self._state.version += 1
            
            # Notificar listeners
            await self._notify_change("npc_moved", {
                "npc_id": npc_id,
                "from": old_location,
                "to": new_location
            })
    
    async def update_player_location(self, player_id: int, old_location: str, new_location: str):
        """Atualiza a localização de um jogador."""
        async with self._lock:
            if not self._state:
                return
            
            # Remover da localização antiga
            if old_location in self._state.locations:
                self._state.locations[old_location].player_ids.discard(player_id)
            
            # Adicionar à nova localização
            if new_location in self._state.locations:
                self._state.locations[new_location].player_ids.add(player_id)
            
            # Atualizar cache
            self._player_location_cache[player_id] = new_location
            
            self._state.version += 1
    
    async def update_weather(self, location: str, new_weather: WeatherType):
        """Atualiza o clima de uma localização."""
        async with self._lock:
            if not self._state:
                return
            
            if location in self._state.locations:
                self._state.locations[location].current_weather = new_weather
                self._state.locations[location].last_updated = datetime.utcnow()
                self._state.version += 1
    
    async def add_global_event(self, event: Dict[str, Any]):
        """Adiciona um evento global."""
        async with self._lock:
            if not self._state:
                return
            
            event["timestamp"] = datetime.utcnow().isoformat()
            self._state.global_events.append(event)
            self._state.version += 1
            
            await self._notify_change("global_event", event)
    
    async def add_location_event(self, location: str, event: Dict[str, Any]):
        """Adiciona um evento a uma localização específica."""
        async with self._lock:
            if not self._state or location not in self._state.locations:
                return
            
            event["timestamp"] = datetime.utcnow().isoformat()
            self._state.locations[location].active_events.append(event)
            self._state.version += 1
    
    async def update_faction_influence(self, faction_name: str, delta: float):
        """Atualiza a influência de uma facção."""
        async with self._lock:
            if not self._state or faction_name not in self._state.factions:
                return
            
            faction = self._state.factions[faction_name]
            faction.influence = max(0, min(100, faction.influence + delta))
            self._state.version += 1
    
    async def destroy_location(self, location: str):
        """Marca uma localização como destruída."""
        async with self._lock:
            if not self._state or location not in self._state.locations:
                return
            
            self._state.locations[location].is_destroyed = True
            self._state.locations[location].danger_level = 10
            self._state.version += 1
            
            await self._notify_change("location_destroyed", {"location": location})
    
    async def update_economy(self, item_id: str, price_modifier: float):
        """Atualiza preço de um item."""
        async with self._lock:
            if not self._state:
                return
            
            if item_id in self._state.economy.item_prices:
                self._state.economy.item_prices[item_id] *= price_modifier
            self._state.version += 1
    
    # ==================== EVENTOS E SINCRONIZAÇÃO ====================
    
    def add_change_listener(self, callback: callable):
        """Adiciona um listener para mudanças no estado."""
        self._change_listeners.append(callback)
    
    def remove_change_listener(self, callback: callable):
        """Remove um listener."""
        if callback in self._change_listeners:
            self._change_listeners.remove(callback)
    
    async def _notify_change(self, event_type: str, data: Dict[str, Any]):
        """Notifica todos os listeners sobre uma mudança."""
        for listener in self._change_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event_type, data)
                else:
                    listener(event_type, data)
            except Exception as e:
                print(f"[WorldState] Erro em listener: {e}")
    
    async def sync_to_database(self):
        """Sincroniza o estado em memória com o banco de dados."""
        if not self._state:
            return
        
        async with self._lock:
            # Sincronizar localizações
            if self._location_repo:
                try:
                    for name, loc_state in self._state.locations.items():
                        await self._location_repo.update_state(
                            name=name,
                            is_destroyed=loc_state.is_destroyed,
                            controlling_faction=loc_state.controlling_faction
                        )
                except Exception as e:
                    print(f"[WorldState] Erro ao sincronizar locais: {e}")
            
            # Sincronizar facções
            if self._faction_repo:
                try:
                    for name, faction_state in self._state.factions.items():
                        await self._faction_repo.update(
                            name=name,
                            influence=faction_state.influence,
                            treasury=faction_state.treasury
                        )
                except Exception as e:
                    print(f"[WorldState] Erro ao sincronizar facções: {e}")
            
            self._state.last_sync = datetime.utcnow()
            print(f"[WorldState] Sincronizado (versão {self._state.version})")
    
    async def start_background_sync(self, interval_seconds: int = 60):
        """Inicia sincronização em background."""
        async def sync_loop():
            while True:
                await asyncio.sleep(interval_seconds)
                await self.sync_to_database()
        
        self._sync_task = asyncio.create_task(sync_loop())
    
    async def stop_background_sync(self):
        """Para a sincronização em background."""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
    
    # ==================== SIMULAÇÃO ====================
    
    async def advance_world_time(self, hours: int = 1):
        """Avança o tempo do mundo e processa mudanças."""
        if not self._state:
            return
        
        async with self._lock:
            # Avançar datetime
            self._state.current_datetime += timedelta(hours=hours)
            
            # Atualizar fase da lua se necessário
            day = self._state.current_datetime.day
            # (Mesmo cálculo de initialize)
            
            # Chance de mudança de clima
            import random
            for loc_name, loc_state in self._state.locations.items():
                if random.random() < 0.1:  # 10% de chance por hora
                    weather_options = list(WeatherType)
                    loc_state.current_weather = random.choice(weather_options)
            
            # Limpar eventos expirados
            self._state.global_events = [
                e for e in self._state.global_events
                if not e.get("expired", False)
            ]
            
            for loc_state in self._state.locations.values():
                loc_state.active_events = [
                    e for e in loc_state.active_events
                    if not e.get("expired", False)
                ]
            
            self._state.version += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa o estado para dicionário."""
        if not self._state:
            return {}
        
        return {
            "current_datetime": self._state.current_datetime.isoformat(),
            "moon_phase": self._state.moon_phase.value,
            "season": self._state.season,
            "global_weather": self._state.global_weather_trend.value,
            "locations": {
                name: {
                    "region": loc.region.value,
                    "weather": loc.current_weather.value,
                    "danger_level": loc.danger_level,
                    "qi_density": loc.qi_density,
                    "npc_count": len(loc.npc_ids),
                    "player_count": len(loc.player_ids),
                    "is_destroyed": loc.is_destroyed,
                    "controlling_faction": loc.controlling_faction
                }
                for name, loc in self._state.locations.items()
            },
            "factions": {
                name: {
                    "influence": faction.influence,
                    "territory": faction.territory,
                    "at_war": faction.at_war
                }
                for name, faction in self._state.factions.items()
            },
            "economy": {
                "inflation_rate": self._state.economy.inflation_rate,
                "item_count": len(self._state.economy.item_prices)
            },
            "global_events_count": len(self._state.global_events),
            "version": self._state.version
        }


# Singleton global
world_state_manager = WorldStateManager()
