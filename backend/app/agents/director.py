from typing import Dict, Any
from app.agents.narrator import Narrator
from app.agents.referee import Referee
from app.core.combat_engine import CombatEngine
from app.core.loot_manager import loot_manager
from app.database.repositories.player_repo import PlayerRepository
from app.database.repositories.npc_repo import NpcRepository
from app.database.models.player import Player
from app.agents.scribe import Scribe
from app.agents.architect import Architect
from app.database.models.npc import NPC

class Director:
    def __init__(
        self,
        narrator: Narrator,
        referee: Referee,
        combat_engine: CombatEngine,
        player_repo: PlayerRepository,
        npc_repo: NpcRepository,
        scribe: Scribe,
        architect: Architect
    ):
        self.narrator = narrator
        self.referee = referee
        self.combat_engine = combat_engine
        self.player_repo = player_repo
        self.npc_repo = npc_repo
        self.scribe = scribe
        self.architect = architect
        self.game_state = {} # Armazena o estado atual, como 'combat' ou 'explore'

    async def _spawn_enemy_if_needed(self, player: Player, location: str, npcs_in_scene: list):
        """Chama o Architect para criar um inimigo se a cena estiver vazia e for provocada."""
        if not npcs_in_scene:
            print("Cena vazia. Gerando um novo inimigo...")
            # Tier e bioma seriam determinados pela localização do jogador no futuro
            new_enemy_data = self.architect.generate_enemy(tier=player.rank, biome="Floresta")
            
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
            
        # No futuro, a localização e os NPCs viriam do estado do jogo
        current_location = "Floresta Assombrada"
        npcs_in_scene = await self.npc_repo.get_all() # Simplificação

        # Lógica de Spawning JIT
        spawn_message = await self._spawn_enemy_if_needed(player, current_location, npcs_in_scene)
        if spawn_message:
            turn_events.append(spawn_message)

        # 1. Narrar a cena
        scene_description = self.narrator.generate_scene_description(player, current_location, npcs_in_scene)

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
                    npcs_in_scene.remove(target_npc)
                else:
                    await self.npc_repo.update(target_npc)
                    action_result_message = f"Você usa {skill_id} em {target_npc.name}, causando {damage} de dano! HP restante: {target_npc.current_hp}"
            else:
                action_result_message = f"Alvo '{target_name}' não encontrado."
        # ... (outras intenções)

        # Adiciona os eventos do início do turno à mensagem de resultado
        full_action_result = ". ".join(turn_events + [action_result_message])
            
        return {
            "scene_description": scene_description,
            "action_result": full_action_result,
            "player_state": player,
            "npcs_in_scene": npcs_in_scene
        }
