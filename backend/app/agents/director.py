from typing import Dict, Any
from app.agents.narrator import Narrator
from app.agents.referee import Referee
from app.core.combat_engine import CombatEngine
from app.core.loot_manager import loot_manager
from app.core.npc_population import npc_population_manager
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
            print(f"[MEMORY] Salva para NPC {npc_id}: {memory_content[:50]}...")
        except Exception as e:
            print(f"[WARN] Erro ao salvar memoria: {e}")
    
    def _determine_location_type(self, location: str) -> str:
        """Determina o tipo de localização baseado no nome"""
        profile = npc_population_manager.get_location_profile(location)
        return profile.location_type
    
    async def _spawn_npc_if_needed(self, player: Player, location: str, npcs_in_scene: list):
        """
        Spawna NPCs dinamicamente baseado no perfil da localização.
        
        Sprint 11: Usa o NPCPopulationManager para densidade contextual:
        - Cidades: 3-5 NPCs, maioria amigável
        - Wilderness: 0-2 NPCs, maioria hostil
        - Estabelecimentos: 1-4 NPCs específicos do tipo (taverna, loja, etc)
        """
        import random
        
        # Obter hora do dia para ajustar densidade
        time_of_day = world_clock.get_time_of_day()
        
        # Calcular quantos NPCs spawnar
        spawn_count, spawn_roles = npc_population_manager.calculate_spawn_count(
            location=location,
            current_npcs=len(npcs_in_scene),
            time_of_day=time_of_day
        )
        
        if spawn_count == 0:
            return None
        
        print(f"[NPC POPULATION] {location}: Spawnando {spawn_count} NPCs. Hora: {time_of_day}")
        
        spawn_messages = []
        
        for disposition, role in spawn_roles:
            try:
                if disposition == "hostile":
                    # Gerar inimigo
                    profile = npc_population_manager.get_location_profile(location)
                    new_enemy_data = self.architect.generate_enemy(
                        tier=player.rank, 
                        biome=profile.location_type
                    )
                    
                    if "error" not in new_enemy_data:
                        new_npc = NPC(
                            name=new_enemy_data["name"],
                            rank=new_enemy_data["stats"]["rank"],
                            current_hp=new_enemy_data["stats"]["hp"],
                            max_hp=new_enemy_data["stats"]["hp"],
                            defense=new_enemy_data["stats"]["defense"],
                            personality_traits=["hostile", role],
                            emotional_state="hostile",
                            current_location=location
                        )
                        created_npc = await self.npc_repo.create(new_npc)
                        npcs_in_scene.append(created_npc)
                        spawn_messages.append(f"Um {created_npc.name} surge das sombras!")
                
                elif disposition == "friendly":
                    # Gerar NPC amigável
                    npc_data = self.architect.generate_friendly_npc(location, role)
                    
                    if "error" not in npc_data:
                        new_npc = NPC(
                            name=npc_data["name"],
                            rank=npc_data["stats"]["rank"],
                            current_hp=npc_data["stats"]["hp"],
                            max_hp=npc_data["stats"]["hp"],
                            defense=npc_data["stats"]["defense"],
                            personality_traits=npc_data.get("personality", ["friendly", role]),
                            emotional_state="friendly",
                            current_location=location
                        )
                        created_npc = await self.npc_repo.create(new_npc)
                        npcs_in_scene.append(created_npc)
                        spawn_messages.append(f"{created_npc.name} está por perto.")
                
                else:  # neutral
                    npc_data = self.architect.generate_neutral_npc(location, role)
                    
                    if "error" not in npc_data:
                        new_npc = NPC(
                            name=npc_data["name"],
                            rank=npc_data["stats"]["rank"],
                            current_hp=npc_data["stats"]["hp"],
                            max_hp=npc_data["stats"]["hp"],
                            defense=npc_data["stats"]["defense"],
                            personality_traits=npc_data.get("personality", ["cautious", role]),
                            emotional_state="neutral",
                            current_location=location
                        )
                        created_npc = await self.npc_repo.create(new_npc)
                        npcs_in_scene.append(created_npc)
                        spawn_messages.append(f"{created_npc.name} observa você com atenção.")
                        
            except Exception as e:
                print(f"[NPC POPULATION] Erro ao spawnar NPC ({role}): {e}")
                continue
        
        if spawn_messages:
            return " ".join(spawn_messages)
        return None

    async def _spawn_enemy_if_needed(self, player: Player, location: str, npcs_in_scene: list):
        """DEPRECATED: Use _spawn_npc_if_needed instead"""
        return await self._spawn_npc_if_needed(player, location, npcs_in_scene)

    async def _run_dawn_world_tick(self) -> dict:
        """
        Executa o tick automático do mundo ao amanhecer (6am).
        Roda economia, facções e ecologia em background.
        """
        from app.core.simulation.daily_tick import DailyTickSimulator
        from app.database.repositories.faction_repo import FactionRepository
        from app.database.repositories.economy_repo import GlobalEconomyRepository
        from app.database.repositories.world_event_repo import WorldEventRepository
        
        try:
            print("🌅 [DAWN TICK] Executando simulação automática do mundo...")
            
            # Usa a session do npc_repo (já está no contexto)
            session = self.npc_repo.session
            
            faction_repo = FactionRepository(session)
            economy_repo = GlobalEconomyRepository(session)
            event_repo = WorldEventRepository(session)
            
            daily_sim = DailyTickSimulator(
                npc_repo=self.npc_repo,
                faction_repo=faction_repo,
                economy_repo=economy_repo,
                world_event_repo=event_repo
            )
            
            report = await daily_sim.run_daily_simulation(
                current_turn=world_clock.get_current_turn()
            )
            
            print(f"🌅 [DAWN TICK] Completo: {len(report.get('events', []))} eventos gerados")
            return report
            
        except Exception as e:
            print(f"⚠️ [DAWN TICK] Erro na simulação: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def process_player_turn(self, player_id: int, player_input: str) -> Dict[str, Any]:
        """
        Processa um turno completo do jogador, desde a entrada até o resultado.
        """
        player = await self.player_repo.get_by_id(player_id)
        if not player:
            return {"error": "Player not found"}
        
        # CRITICAL: Força carregar todos os atributos agora (antes de qualquer lazy load)
        await self.player_repo.session.refresh(player)
        
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
        time_result = world_clock.advance_turn()
        current_time = world_clock.get_current_datetime()
        current_time_str = current_time.isoformat() if hasattr(current_time, 'isoformat') else str(current_time)
        
        # ===== WORLD TICK AUTOMÁTICO ÀS 6AM =====
        if time_result.get("new_dawn"):
            dawn_report = await self._run_dawn_world_tick()
            if dawn_report:
                turn_events.append("🌅 O sol nasce sobre Orbis. O mundo desperta e as facções se movem...")
        
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
            skill_id = action.get("skill_name") or "basic_attack"  # Garante que None vira basic_attack
            
            # Valida target_name
            if not target_name or target_name == "None" or target_name == "null":
                action_result_message = "Você precisa especificar um alvo para atacar."
            else:
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
                                "rank": target_npc.rank  # NPCs usam rank, não cultivation_tier
                            })
                        
                        npcs_in_scene.remove(target_npc)
                    else:
                        await self.npc_repo.update(target_npc)
                        action_result_message = f"Você usa {skill_id} em {target_npc.name}, causando {damage} de dano! HP restante: {target_npc.current_hp}"
                        
                        # [SPRINT 17] CONTRA-ATAQUE DO NPC
                        if target_npc.emotional_state == "hostile" and target_npc.current_hp > 0:
                            # NPC hostil contra-ataca
                            npc_damage = self.combat_engine.calculate_damage(target_npc, player, skill_id="basic_attack")
                            player.current_hp -= npc_damage
                            
                            # Aplicar redução de constituição se tiver
                            constitution_defense_info = ""
                            if player.constitution_type:
                                from app.core.constitution_effects import ConstitutionEffects
                                defense_mult = ConstitutionEffects.get_modifiers(player.constitution_type).get("defense_multiplier", 1.0)
                                if defense_mult > 1.0:
                                    constitution_defense_info = f" (Constituição {player.constitution_type}: +{int((defense_mult-1)*100)}% defesa)"
                            
                            action_result_message += f"\n\n{target_npc.name} contra-atacou você: -{npc_damage} HP{constitution_defense_info}. Seu HP: {player.current_hp}/{player.max_hp}"
                            
                            if player.current_hp <= 0:
                                action_result_message += "\n\n💀 Você foi derrotado!"
                        
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
            
            # Verifica se target_name é válido (não None nem string "None")
            if not target_name or target_name == "None" or target_name == "null":
                # Sem alvo específico, é só uma fala geral
                action_result_message = f"Você fala, mas ninguém em particular parece responder."
            else:
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
        
        elif action.get("intent") == "move":
            destination = action.get("destination") or action.get("target_name")
            if destination:
                # Usar LocationManager para resolver destino (inclui "casa", aliases, etc.)
                from app.core.location_manager import LocationManager
                
                # Preciso da session do banco - vou obter do player_repo
                session = self.player_repo.session
                location_manager = LocationManager(session, self.narrator.gemini_client if hasattr(self.narrator, 'gemini_client') else None)
                
                location_result = await location_manager.resolve_location(destination, player.id)
                
                if location_result.get("found"):
                    # Local encontrado!
                    matched_location = location_result.get("name")
                    
                    # Verificar se foi destruído
                    if location_result.get("is_destroyed"):
                        action_result_message = f"Você viaja até {matched_location}, mas encontra apenas ruínas. O local foi destruído."
                        player.current_location = matched_location + " (Ruínas)"
                    else:
                        old_location = player.current_location
                        player.current_location = matched_location
                        
                        # Mensagem especial se for a casa
                        if location_result.get("type") in ["dynamic_home", "static_home", "origin_fallback"]:
                            action_result_message = f"Você retorna ao seu lar: {matched_location}. Um sentimento de familiaridade o envolve."
                        else:
                            action_result_message = f"Você viaja de {old_location} para {matched_location}."
                else:
                    # Local não encontrado - verificar se o Mestre deve criar
                    should_create = await location_manager.should_create_location(
                        player_request=destination,
                        current_location=player.current_location,
                        player=player
                    )
                    
                    if should_create.get("should_create"):
                        # Mestre decide criar o local!
                        new_location = await location_manager.create_location_from_narrative(
                            name=should_create.get("location_name", destination),
                            description=should_create.get("description", f"Um local em {player.current_location}."),
                            parent_location=player.current_location,
                            location_type=should_create.get("location_type", "generic"),
                            owner_player_id=None,
                            context=f"Player pediu para ir a '{destination}'"
                        )
                        
                        old_location = player.current_location
                        player.current_location = new_location.name
                        action_result_message = f"Você descobre um novo local: {new_location.name}. {new_location.description}"
                    else:
                        # Realmente não existe
                        action_result_message = f"Você não conhece o caminho para '{destination}'. {should_create.get('reason', '')}"
            else:
                action_result_message = "Você precisa especificar um destino."
        
        elif action.get("intent") == "observe":
            action_result_message = f"Você observa atentamente seus arredores em {current_location}."
            if npcs_in_scene:
                npc_names = [npc.name for npc in npcs_in_scene]
                action_result_message += f" Você nota: {', '.join(npc_names)}."
            else:
                action_result_message += " O local parece vazio."
        
        elif action.get("intent") == "meditate" or action.get("intent") == "cultivate":
            # Cultivar Qi
            qi_gain = 10 * player.rank
            player.yuan_qi = min(player.max_yuan_qi, player.yuan_qi + qi_gain)
            player.shadow_chi = min(player.max_shadow_chi, player.shadow_chi + qi_gain * 0.5)
            action_result_message = f"Você medita e recupera {qi_gain} Yuan Qi."
        
        elif action.get("intent") == "speak":
            # Falar algo em voz alta (diálogo contextual)
            spoken_words = action.get("spoken_words", player_input)
            target_name = action.get("target_name")
            
            if target_name and target_name != "None":
                target_npc = next((npc for npc in npcs_in_scene if npc.name == target_name), None)
                if target_npc:
                    # Salvar memória do NPC
                    await self._save_npc_memory(
                        target_npc.id,
                        "HEARD_PLAYER_SPEAK",
                        f"{player.name} disse: '{spoken_words}' para mim na {current_location}"
                    )
                    action_result_message = f"Você disse: \"{spoken_words}\" para {target_npc.name}."
                else:
                    action_result_message = f"Você disse: \"{spoken_words}\" em voz alta."
            else:
                action_result_message = f"Você disse: \"{spoken_words}\" em voz alta."
        
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
                world_time=current_time_str
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
        
        # ===== SALVAR PLAYER NO BANCO (inventário, stats, etc) =====
        await self.player_repo.update(player)
            
        return {
            "scene_description": scene_description,
            "action_result": full_action_result,
            "player_state": player,
            "npcs_in_scene": npcs_in_scene
        }
