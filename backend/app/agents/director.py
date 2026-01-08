from typing import Dict, Any
from app.agents.narrator import Narrator
from app.agents.referee import Referee
from app.core.combat_engine import CombatEngine
from app.core.loot_manager import loot_manager
from app.database.repositories.player_repo import PlayerRepository
from app.database.repositories.npc_repo import NpcRepository
from app.database.repositories.gamelog_repo import GameLogRepository
from app.database.repositories.hybrid_search import HybridSearchRepository
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.agents.scribe import Scribe
from app.agents.architect import Architect
from app.agents.villains.profiler import Profiler
from app.core.chronos import world_clock

class Director:
    def __init__(
        self,
        narrator: Narrator,
        referee: Referee,
        combat_engine: CombatEngine,
        player_repo: PlayerRepository,
        npc_repo: NpcRepository,
        scribe: Scribe,
        architect: Architect,
        profiler,
        gamelog_repo: GameLogRepository = None,
        memory_repo: HybridSearchRepository = None
    ):
        self.narrator = narrator
        self.referee = referee
        self.combat_engine = combat_engine
        self.player_repo = player_repo
        self.npc_repo = npc_repo
        self.gamelog_repo = gamelog_repo
        self.memory_repo = memory_repo
        self.scribe = scribe
        self.architect = architect
        self.profiler = profiler
        self.game_state = {} # DEPRECATED: Use gamelog_repo instead
    
    async def _save_npc_memory(self, npc_id: int, event_type: str, details: str):
        """Salva uma memória vetorial para um NPC"""
        if not self.memory_repo:
            return
        
        memory_content = f"[{event_type}] {details}"
        try:
            await self.memory_repo.add_memory(npc_id, memory_content, embedding_dim=128)
            print(f"💾 Memória salva para NPC {npc_id}: {memory_content[:50]}...")
        except Exception as e:
            print(f"⚠️ Erro ao salvar memória: {e}")
    
    def _determine_location_type(self, location: str) -> str:
        """Determina o tipo de localização baseado no nome"""
        location_lower = location.lower()
        if any(word in location_lower for word in ["vila", "cidade", "town", "village", "forja", "mercado"]):
            return "settlement"
        elif any(word in location_lower for word in ["floresta", "forest", "selva", "jungle"]):
            return "wilderness"
        elif any(word in location_lower for word in ["caverna", "cave", "dungeon", "ruínas"]):
            return "dungeon"
        elif any(word in location_lower for word in ["templo", "mosteiro", "temple", "monastery"]):
            return "sacred"
        else:
            return "wilderness"
    
    async def _spawn_npc_if_needed(self, player: Player, location: str, npcs_in_scene: list):
        """
        Spawna NPCs baseado no tipo de localização
        - Settlements: NPCs amigáveis (merchants, elders)
        - Wilderness: Inimigos hostis
        - Sacred: NPCs neutros (monks, guardians)
        """
        if npcs_in_scene:
            return None  # Já tem NPCs na cena
        
        location_type = self._determine_location_type(location)
        print(f"Cena vazia. Tipo de localização: {location_type}")
        
        if location_type == "settlement":
            # Spawn friendly NPC
            roles = ["merchant", "elder", "quest_giver", "healer", "blacksmith"]
            import random
            role = random.choice(roles)
            
            npc_data = self.architect.generate_friendly_npc(location, role)
            if "error" not in npc_data:
                new_npc = NPC(
                    name=npc_data["name"],
                    rank=npc_data["stats"]["rank"],
                    current_hp=npc_data["stats"]["hp"],
                    max_hp=npc_data["stats"]["hp"],
                    defense=npc_data["stats"]["defense"],
                    personality_traits=npc_data.get("personality", ["friendly"]),
                    emotional_state="friendly",
                    current_location=location
                )
                created_npc = await self.npc_repo.create(new_npc)
                npcs_in_scene.append(created_npc)
                return f"Você encontra {created_npc.name}, que acena em sua direção com um sorriso acolhedor."
        
        elif location_type == "sacred":
            # Spawn neutral NPC
            occupations = ["monk", "guardian", "scholar", "hermit"]
            import random
            occupation = random.choice(occupations)
            
            npc_data = self.architect.generate_neutral_npc(location, occupation)
            if "error" not in npc_data:
                new_npc = NPC(
                    name=npc_data["name"],
                    rank=npc_data["stats"]["rank"],
                    current_hp=npc_data["stats"]["hp"],
                    max_hp=npc_data["stats"]["hp"],
                    defense=npc_data["stats"]["defense"],
                    personality_traits=npc_data.get("personality", ["cautious"]),
                    emotional_state="neutral",
                    current_location=location
                )
                created_npc = await self.npc_repo.create(new_npc)
                npcs_in_scene.append(created_npc)
                return f"{created_npc.name} observa você com olhos atentos, avaliando suas intenções."
        
        else:
            # Spawn enemy (wilderness/dungeon)
            new_enemy_data = self.architect.generate_enemy(tier=player.rank, biome=location_type)
            
            if "error" not in new_enemy_data:
                new_npc = NPC(
                    name=new_enemy_data["name"],
                    rank=new_enemy_data["stats"]["rank"],
                    current_hp=new_enemy_data["stats"]["hp"],
                    max_hp=new_enemy_data["stats"]["hp"],
                    defense=new_enemy_data["stats"]["defense"],
                    personality_traits=["hostile", "territorial"],
                    emotional_state="hostile",
                    current_location=location
                )
                created_npc = await self.npc_repo.create(new_npc)
                npcs_in_scene.append(created_npc)
                return f"Das sombras, um {created_npc.name} surge, rosnando ameaçadoramente!"
        
        return None

    async def _spawn_enemy_if_needed(self, player: Player, location: str, npcs_in_scene: list):
        """DEPRECATED: Use _spawn_npc_if_needed instead"""
        return await self._spawn_npc_if_needed(player, location, npcs_in_scene)

    async def process_player_turn(self, player_id: int, player_input: str) -> Dict[str, Any]:
        """
        Processa um turno completo do jogador, desde a entrada até o resultado.
        """
        player = await self.player_repo.get_by_id(player_id)
        if not player:
            return {"error": "Player not found"}
        
        turn_events = []

        # Processar efeitos de status do turno anterior
        dot_damage = self.combat_engine.process_turn_effects(player)
        if dot_damage > 0:
            turn_events.append(f"Você sofre {dot_damage} de dano de efeitos contínuos.")

        # Verificar consequências do Heart Demon
        heart_demon_effect = self.combat_engine.check_heart_demon_effects(player)
        if heart_demon_effect:
            turn_events.append(f"DEMÔNIO DO CORAÇÃO: {heart_demon_effect}!")
            if heart_demon_effect == "Hallucinations":
                player.willpower *= 0.9 # Aplica a penalidade
            # Lógica para Berserk e Morte seria mais complexa
            
        # ===== CHRONOS: ADVANCE TIME =====
        world_clock.advance_turn()
        current_time = world_clock.get_current_datetime()
        
        # Localização e NPCs na cena (FILTRADOS por localização)
        current_location = player.current_location or "Floresta Assombrada"
        npcs_in_scene = await self.npc_repo.get_by_location(current_location)

        # Lógica de Spawning JIT
        spawn_message = await self._spawn_enemy_if_needed(player, current_location, npcs_in_scene)
        if spawn_message:
            turn_events.append(spawn_message)

        # 1. Narrar a cena (com histórico do BANCO e MEMÓRIAS dos NPCs)
        previous_narration = ""
        is_first_scene = False
        if self.gamelog_repo:
            recent_turns = await self.gamelog_repo.get_recent_turns(player_id, limit=1)
            if recent_turns:
                previous_narration = recent_turns[-1].scene_description
            else:
                # Sem turnos anteriores = primeira cena
                is_first_scene = True
        
        scene_description = await self.narrator.generate_scene_description_async(
            player, 
            current_location, 
            npcs_in_scene,
            player_last_action=player_input,
            previous_narration=previous_narration,
            memory_repo=self.memory_repo,
            is_first_scene=is_first_scene
        )

        # 2. Interpretar a ação do jogador
        action = self.referee.parse_player_action(player_input, player, npcs_in_scene)
        
        # 3. Executar a ação
        action_result_message = ""
        if action.get("intent") == "attack":
            target_name = action.get("target_name")
            skill_id = action.get("skill_name", "basic_attack")
            target_npc = next((npc for npc in npcs_in_scene if npc.name == target_name), None)
            
            if target_npc:
                # Loga a ação com o Scribe
                action_key = f"attack_{skill_id}"
                self.scribe.log_action(player.id, action_key)

                damage = self.combat_engine.calculate_damage(player, target_npc, skill_id=skill_id)
                self.combat_engine.apply_skill_effects(target_npc, skill_id=skill_id)
                target_npc.current_hp -= damage
                
                # Verifica por epifania
                new_skill = self.scribe.check_for_epiphany(player.id, action_key)
                if new_skill:
                    turn_events.append(f"EPIFANIA! Você compreendeu uma nova técnica: {new_skill['name']}!")

                if target_npc.current_hp <= 0:
                    action_result_message = f"Você derrotou {target_npc.name}!"
                    
                    # ===== MEMORY: NPCs próximos testemunham a morte =====
                    for witness_npc in npcs_in_scene:
                        if witness_npc.id != target_npc.id:
                            await self._save_npc_memory(
                                witness_npc.id,
                                "WITNESSED_DEATH",
                                f"Vi {player.name} derrotar {target_npc.name} em combate na {current_location}"
                            )
                    
                    # Lógica de Loot
                    # Supondo que o target_npc.name pode ser usado como monster_id
                    monster_id = target_npc.name.lower().replace(" ", "_") # Ex: "Serpente Vil" -> "serpente_vil"
                    drops = loot_manager.calculate_loot(monster_id)
                    if drops:
                        action_result_message += " Loot encontrado:"
                        for drop in drops:
                            # Adicionar ao inventário do jogador (lógica simplificada)
                            existing_item = next((item for item in player.inventory if item["item_id"] == drop["item_id"]), None)
                            if existing_item:
                                existing_item["quantity"] += drop["quantity"]
                            else:
                                player.inventory.append(drop)
                            action_result_message += f" {drop['quantity']}x {drop['item_id']},"

                    # Lógica de absorção de cultivo
                    if self.combat_engine.absorb_cultivation(player, target_npc):
                        action_result_message += f" Você sentiu seu poder aumentar!"
                    
                    # ===== PROFILER: Processar morte de NPC =====
                    await self.profiler.process_event(
                        event_type="player_killed_npc",
                        actor=player,
                        target=target_npc,
                        npc_repo=self.npc_repo
                    )
                    
                    # ===== WORLDSIMULATOR: Adicionar evento para rumor =====
                    # Acessa o WorldSimulator global para registrar evento
                    from app.main import app_state
                    world_sim = app_state.get("world_simulator")
                    if world_sim:
                        world_sim.add_event({
                            "type": "npc_death",
                            "actor": player.name,
                            "victim": target_npc.name,
                            "location": player.current_location,
                            "cultivation_tier": target_npc.cultivation_tier
                        })
                    
                    npcs_in_scene.remove(target_npc)
                else:
                    await self.npc_repo.update(target_npc)
                    action_result_message = f"Você usa {skill_id} em {target_npc.name}, causando {damage} de dano! HP restante: {target_npc.current_hp}"
                    
                    # ===== MEMORY: NPC lembra do ataque =====
                    await self._save_npc_memory(
                        target_npc.id,
                        "ATTACKED_BY_PLAYER",
                        f"{player.name} me atacou com {skill_id} causando {damage} de dano na {current_location}"
                    )
                    
                    # ===== PROFILER: Processar ataque a NPC (sem matar) =====
                    await self.profiler.process_event(
                        event_type="player_attacked_npc",
                        actor=player,
                        target=target_npc,
                        npc_repo=self.npc_repo
                    )
            else:
                action_result_message = f"Alvo '{target_name}' não encontrado."
        
        elif action.get("intent") == "talk":
            target_name = action.get("target_name")
            target_npc = next((npc for npc in npcs_in_scene if npc.name == target_name), None)
            
            if target_npc:
                # ===== MEMORY: NPC lembra da conversa =====
                await self._save_npc_memory(
                    target_npc.id,
                    "TALKED_WITH_PLAYER",
                    f"{player.name} iniciou conversa comigo na {current_location}. Disse: '{player_input}'"
                )
                
                # Generate NPC response based on personality
                response = f"{target_npc.name} ouve suas palavras atentamente."
                if "friendly" in target_npc.emotional_state:
                    response = f"{target_npc.name} sorri e responde cordialmente."
                elif "hostile" in target_npc.emotional_state:
                    response = f"{target_npc.name} rosna: 'Não tenho nada para dizer a você!'"
                elif "neutral" in target_npc.emotional_state:
                    response = f"{target_npc.name} observa você com cautela antes de falar."
                
                action_result_message = response
            else:
                action_result_message = f"Não há ninguém chamado '{target_name}' aqui."
        
        # ... (outras intenções)

        # Adiciona os eventos do início do turno à mensagem de resultado
        full_action_result = ". ".join(turn_events + [action_result_message])
        
        # ===== GAMELOG: SAVE TURN TO DATABASE =====
        if self.gamelog_repo:
            turn_count = await self.gamelog_repo.get_turn_count(player_id)
            npc_ids = [npc.id for npc in npcs_in_scene]
            await self.gamelog_repo.save_turn(
                player_id=player_id,
                turn_number=turn_count + 1,
                player_input=player_input,
                scene_description=scene_description,
                action_result=full_action_result,
                location=current_location,
                npcs_present=npc_ids,
                world_time=current_time
            )
            
            # ===== WORLDSIMULATOR: Run every 10 turns =====
            if (turn_count + 1) % 10 == 0:
                from app.main import app_state
                world_sim = app_state.get("world_simulator")
                if world_sim:
                    print(f"[WORLDSIM] Executando tick de mundo (turno {turn_count + 1})...")
                    await world_sim.run_simulation_tick(
                        npc_repo=self.npc_repo,
                        player_repo=self.player_repo
                    )
            
        return {
            "scene_description": scene_description,
            "action_result": full_action_result,
            "player_state": player,
            "npcs_in_scene": npcs_in_scene
        }
