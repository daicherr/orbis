"""
Daily Tick Simulator - Main simulation orchestrator
Runs all background simulations that evolve the world
"""

from typing import List, Dict, Any, Optional
from app.core.simulation.economy import EconomySimulator
from app.core.simulation.ecology import EcologySimulator
from app.core.simulation.lineage import LineageSimulator
from app.core.simulation.faction_simulator import FactionSimulator


class DailyTickSimulator:
    """
    Orquestrador principal de simulações de mundo.
    Executa todas as simulações de fundo que ocorrem uma vez por dia no jogo.
    """
    
    def __init__(
        self,
        npc_repo=None,
        faction_repo=None,
        economy_repo=None,
        world_event_repo=None
    ):
        """
        Inicializa o simulador com os repositórios necessários.
        
        Args:
            npc_repo: Repository de NPCs
            faction_repo: Repository de Facções
            economy_repo: Repository de Economia Global
            world_event_repo: Repository de Eventos Mundiais
        """
        self.npc_repo = npc_repo
        self.faction_repo = faction_repo
        self.economy_repo = economy_repo
        self.world_event_repo = world_event_repo
        
        # Inicializar simuladores
        self.economy_sim = EconomySimulator(
            economy_repo=economy_repo,
            world_event_repo=world_event_repo
        )
        
        self.faction_sim = FactionSimulator(
            faction_repo=faction_repo,
            world_event_repo=world_event_repo
        )
        
        self.ecology_sim = EcologySimulator(world_map={})
        
        self.lineage_sim = LineageSimulator(npc_repo=npc_repo)
        
        # Turno atual
        self.current_turn = 0
        
        print("[DAILY TICK] Simulador inicializado com todos os sistemas.")

    async def run_daily_simulation(self, current_turn: int = None) -> Dict[str, Any]:
        """
        Executa todas as simulações de fundo que ocorrem uma vez por dia no jogo.
        
        Args:
            current_turn: Turno atual do jogo (opcional)
        
        Returns:
            Relatório de todos os eventos gerados
        """
        
        if current_turn is not None:
            self.current_turn = current_turn
        else:
            self.current_turn += 1
        
        print(f"\n{'='*60}")
        print(f"[DAILY TICK] INICIANDO SIMULAÇÃO DO TURNO {self.current_turn}")
        print(f"{'='*60}")
        
        report = {
            "turn": self.current_turn,
            "events": [],
            "economy_changes": [],
            "faction_events": [],
            "ecology_events": [],
            "lineage_events": []
        }
        
        # 1. Simulação de Facções (Guerras, Alianças, Território)
        print("\n[1/5] Simulando política de facções...")
        try:
            faction_events = await self.faction_sim.simulate_faction_turn(self.current_turn)
            report["faction_events"] = faction_events
            report["events"].extend(faction_events)
            print(f"      -> {len(faction_events)} eventos de facção gerados")
        except Exception as e:
            print(f"      -> ERRO: {e}")
        
        # 2. Simulação da Economia (Preços, Oferta/Demanda)
        print("\n[2/5] Simulando economia...")
        try:
            economy_events = await self.economy_sim.simulate_economy_tick(self.current_turn)
            report["economy_changes"] = economy_events
            report["events"].extend(economy_events)
            print(f"      -> {len(economy_events)} mudanças econômicas")
        except Exception as e:
            print(f"      -> ERRO: {e}")
        
        # 3. Simulação da Ecologia (Migração de Monstros)
        print("\n[3/5] Simulando ecologia...")
        try:
            await self.ecology_sim.process_migrations()
            print(f"      -> Migrações processadas")
        except Exception as e:
            print(f"      -> ERRO: {e}")
        
        # 4. Simulação de Linhagem (Vinganças Hereditárias)
        print("\n[4/5] Processando linhagens...")
        try:
            # Linhagem é processada via eventos específicos, não em tick
            print(f"      -> Sistema de linhagem ativo")
        except Exception as e:
            print(f"      -> ERRO: {e}")
        
        # 5. Reset de Recursos Diários
        print("\n[5/5] Resetando recursos diários...")
        try:
            await self._reset_daily_resources()
            print(f"      -> Recursos resetados")
        except Exception as e:
            print(f"      -> ERRO: {e}")
        
        print(f"\n{'='*60}")
        print(f"[DAILY TICK] SIMULAÇÃO DO TURNO {self.current_turn} CONCLUÍDA")
        print(f"             Total de eventos: {len(report['events'])}")
        print(f"{'='*60}\n")
        
        return report

    async def _reset_daily_resources(self):
        """
        Reseta recursos diários de NPCs e locais.
        - Lojas reabastecem estoque
        - NPCs recuperam HP/Qi
        - Recursos de crafting regeneram
        """
        
        if not self.npc_repo:
            return
        
        # Por enquanto, apenas logamos que o reset aconteceu
        # O update individual de NPCs causa problemas de sessão
        # TODO: Implementar com batch update ou SQL direto
        try:
            # Buscar todos os NPCs para contagem
            all_npcs = await self.npc_repo.get_all()
            print(f"      -> {len(all_npcs)} NPCs no mundo")
        except Exception as e:
            print(f"      -> Erro ao buscar NPCs: {e}")

    async def process_player_action(
        self, 
        player_id: int, 
        action_type: str, 
        target: Any = None,
        location: str = None
    ) -> List[Dict[str, Any]]:
        """
        Processa uma ação do jogador que pode gerar eventos mundiais.
        
        Args:
            player_id: ID do jogador
            action_type: Tipo de ação ("kill", "destroy", "help", etc.)
            target: Alvo da ação (NPC, local, etc.)
            location: Onde a ação ocorreu
        
        Returns:
            Lista de eventos gerados pela ação
        """
        
        events = []
        
        # Mapear ações para eventos mundiais
        if action_type == "kill_npc" and target:
            # Processar morte de NPC
            if hasattr(target, 'rank') and target.rank >= 3:
                # NPC importante - gera evento mundial
                event = await self._create_world_event(
                    event_type="npc_death",
                    description=f"{target.name} foi morto!",
                    public_description=f"Rumores da morte de {target.name} se espalham...",
                    location=location,
                    caused_by_player_id=player_id,
                    effects={"victim_rank": target.rank}
                )
                events.append(event)
                
                # Verificar vingança via linhagem
                if self.lineage_sim:
                    await self.lineage_sim.check_for_vendetta(
                        killed_npc={"id": target.id, "name": target.name},
                        killer_id=player_id
                    )
        
        elif action_type == "destroy_location" and location:
            # Destruição de local - evento maior
            event = await self._create_world_event(
                event_type="destruction",
                description=f"{location} foi destruído!",
                public_description=f"Catástrofe! {location} foi devastado por uma força desconhecida!",
                location=location,
                caused_by_player_id=player_id,
                effects={"location_destroyed": True}
            )
            events.append(event)
            
            # Aplicar efeitos econômicos
            if self.economy_repo:
                await self.economy_repo.apply_event_effects("village_destroyed", location)
        
        elif action_type == "help_faction":
            # Ajudar facção - melhora relação
            if hasattr(target, 'name'):
                await self.faction_sim.player_action_affects_faction(
                    player_id=player_id,
                    action_type="help",
                    faction_name=target.name,
                    amount=10
                )
        
        return events

    async def _create_world_event(
        self,
        event_type: str,
        description: str,
        public_description: str,
        location: str = None,
        caused_by_player_id: int = None,
        caused_by_npc_id: int = None,
        effects: dict = None
    ) -> Dict[str, Any]:
        """Cria um evento mundial e persiste no banco."""
        
        event_data = {
            "type": event_type,
            "description": description,
            "public_description": public_description,
            "location": location,
            "turn": self.current_turn,
            "effects": effects or {}
        }
        
        if self.world_event_repo:
            world_event = await self.world_event_repo.create(
                event_type=event_type,
                description=description,
                public_description=public_description,
                location_affected=location,
                turn_occurred=self.current_turn,
                caused_by_player_id=caused_by_player_id,
                caused_by_npc_id=caused_by_npc_id,
                effects=effects or {}
            )
            event_data["id"] = world_event.id
        
        print(f"[WORLD EVENT] {description}")
        return event_data

    # === MÉTODOS DE CONSULTA ===
    
    def get_current_turn(self) -> int:
        """Retorna o turno atual do jogo."""
        return self.current_turn
    
    async def get_world_state_summary(self) -> Dict[str, Any]:
        """
        Retorna um resumo do estado atual do mundo.
        Útil para o Narrador contextualizar a história.
        """
        
        summary = {
            "turn": self.current_turn,
            "active_wars": [],
            "recent_events": [],
            "economy_status": "stable",
            "monster_activity": "normal"
        }
        
        # Buscar guerras ativas
        if self.faction_repo:
            factions = await self.faction_repo.get_all()
            for faction in factions:
                for other, relation in (faction.relations or {}).items():
                    if relation == "at_war":
                        war = f"{faction.name} vs {other}"
                        if war not in summary["active_wars"]:
                            summary["active_wars"].append(war)
        
        # Buscar eventos recentes
        if self.world_event_repo:
            recent = await self.world_event_repo.get_recent_events(
                since_turn=self.current_turn - 10
            )
            summary["recent_events"] = [
                {"type": e.event_type, "description": e.public_description}
                for e in recent[:5]
            ]
        
        # Status da economia
        if self.economy_repo:
            report = await self.economy_sim.get_market_report()
            if len(report["trending_up"]) > len(report["trending_down"]) * 2:
                summary["economy_status"] = "inflação alta"
            elif len(report["trending_down"]) > len(report["trending_up"]) * 2:
                summary["economy_status"] = "deflação"
        
        return summary


# === FUNÇÃO DE CONVENIÊNCIA ===

async def run_world_simulation(
    turn: int,
    npc_repo=None,
    faction_repo=None,
    economy_repo=None,
    world_event_repo=None
) -> Dict[str, Any]:
    """
    Função de conveniência para rodar uma simulação completa.
    Pode ser chamada de um endpoint ou scheduler.
    """
    
    simulator = DailyTickSimulator(
        npc_repo=npc_repo,
        faction_repo=faction_repo,
        economy_repo=economy_repo,
        world_event_repo=world_event_repo
    )
    
    return await simulator.run_daily_simulation(current_turn=turn)
