from typing import Optional
import json
import random
from pathlib import Path
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.core.skill_manager import skill_manager
from app.core.tribulation_engine import tribulation_engine
from app.core.constitution_effects import ConstitutionEffects

class CombatEngine:
    
    @staticmethod
    def _load_cultivation_ranks():
        """Carrega dados dos tiers de cultivation."""
        repo_root = Path(__file__).resolve().parents[3]
        ranks_file = repo_root / "ruleset_source" / "mechanics" / "cultivation_ranks.json"
        with open(ranks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def get_tier_data(tier: int):
        """Retorna os dados de um tier específico."""
        ranks_data = CombatEngine._load_cultivation_ranks()
        for tier_data in ranks_data.get("tiers", []):
            if tier_data["tier"] == tier:
                return tier_data
        return None
    
    @staticmethod
    def is_silent_art_detected(attacker, defender, skill_id: str) -> bool:
        """
        Verifica se uma Silent Art é detectada pelo defensor.
        Regra do GDD: Silent Arts não são detectadas a menos que
        o cultivation_tier do defensor seja MUITO superior (3+ tiers acima).
        """
        skill = skill_manager.get_skill(skill_id)
        if not skill or not skill.get('is_silent_art', False):
            return True  # Não é Silent Art, sempre detectada
        
        attacker_tier = getattr(attacker, 'cultivation_tier', 1)
        defender_tier = getattr(defender, 'cultivation_tier', 1)
        
        tier_difference = defender_tier - attacker_tier
        
        if tier_difference >= 3:
            return True  # Defensor detecta
        
        return False  # Silent Art passa despercebida
    
    @staticmethod
    def calculate_damage(
        attacker: Player | NPC, 
        defender: Player | NPC, 
        skill_id: str
    ) -> float:
        """
        Calcula o dano total com base em uma habilidade específica, usando o GDD.
        DanoTotal = (BaseDmg + (ShadowChi * 2)) * (100 / (100 + (DefesaAlvo - Penetração)))
        
        NOVO: Considera Silent Arts e stealth bonus.
        """
        skill = skill_manager.get_skill(skill_id)
        if not skill:
            return 0.0

        base_damage = skill.get('base_damage', 0.0)
        
        # Lógica de penetração baseada nos efeitos da habilidade
        penetration = 0.0
        stealth_bonus = 0.0
        
        if 'effects' in skill:
            for effect in skill['effects']:
                if effect.get('type') == 'armor_penetration':
                    penetration = defender.defense * effect.get('value', 0.0)
                
                # NOVO: Stealth bonus se não detectado
                if effect.get('type') == 'stealth_bonus':
                    if not CombatEngine.is_silent_art_detected(attacker, defender, skill_id):
                        stealth_bonus = base_damage * effect.get('value', 0.0)

        # Bônus de Shadow Chi (GDD: ShadowChi * 2)
        shadow_chi_bonus = 0
        if isinstance(attacker, Player) and skill.get('cost_type') == 'shadow_chi':
            shadow_chi_bonus = attacker.shadow_chi * 0.02  # 2% do shadow_chi atual
            
        total_base_damage = base_damage + shadow_chi_bonus + stealth_bonus
        
        # [SPRINT 5] Constitution Damage Modifier
        constitution_damage_mult = 1.0
        if hasattr(attacker, 'constitution_type') and attacker.constitution_type:
            constitution_damage_mult = ConstitutionEffects.get_damage_modifier(attacker.constitution_type)
            total_base_damage *= constitution_damage_mult
        
        effective_defense = defender.defense - penetration
        if effective_defense < 0:
            effective_defense = 0
        
        # [SPRINT 5] Constitution Defense Modifier (defender)
        constitution_defense_mult = 1.0
        if hasattr(defender, 'constitution_type') and defender.constitution_type:
            defense_modifiers = ConstitutionEffects.get_modifiers(defender.constitution_type)
            constitution_defense_mult = defense_modifiers.get("defense_multiplier", 1.0)
            effective_defense *= constitution_defense_mult
            
        damage_multiplier = 100 / (100 + effective_defense)
        final_damage = total_base_damage * damage_multiplier
        
        return round(final_damage, 2)
        
    @staticmethod
    def apply_skill_effects(target: Player | NPC, skill_id: str):
        """Aplica os efeitos secundários de uma habilidade ao alvo."""
        skill = skill_manager.get_skill(skill_id)
        if not skill or 'effects' not in skill:
            return

        for effect in skill['effects']:
            if effect.get('type') == 'dot':
                new_effect = {
                    "type": "dot",
                    "damage": effect.get("damage_per_turn", 0),
                    "damage_type": effect.get("damage_type", "physical"),
                    "duration": effect.get("duration", 0),
                    "turns_left": effect.get("duration", 0)
                }
                target.status_effects.append(new_effect)
                print(f"Efeito 'dot' aplicado a {target.name} por {new_effect['duration']} turnos.")
            # Adicionar lógica para outros tipos de efeitos (buffs, debuffs, etc.)
    
    @staticmethod
    def process_turn_effects(character: Player | NPC):
        """Processa todos os efeitos de status no início do turno do personagem."""
        new_status_effects = []
        damage_this_turn = 0
        
        for effect in character.status_effects:
            if effect.get("type") == "dot":
                dot_damage = effect.get("damage", 0)
                character.current_hp -= dot_damage
                damage_this_turn += dot_damage
                print(f"{character.name} sofre {dot_damage} de dano de '{effect['damage_type']}'.")
            
            effect["turns_left"] -= 1
            if effect["turns_left"] > 0:
                new_status_effects.append(effect)
            else:
                print(f"O efeito '{effect['type']}' em {character.name} acabou.")

        character.status_effects = new_status_effects
        
        # [SPRINT 5] Regeneração passiva baseada em Constitution
        if hasattr(character, 'constitution_type') and character.constitution_type:
            modifiers = ConstitutionEffects.get_modifiers(character.constitution_type)
            regen_rate = modifiers.get("quintessence_regen", 1.0)
            
            # Regeneração base: 5% do HP máximo por turno
            base_regen = character.max_hp * 0.05 * regen_rate
            character.current_hp = min(character.current_hp + base_regen, character.max_hp)
            
            if base_regen > 0:
                print(f"{character.name} regenera {base_regen:.1f} HP (Constitution: {regen_rate*100}%).")
        
        return damage_this_turn
        
    @staticmethod
    def update_corruption(
        player: Player,
        absorbed_cultivation: float = 0.0,
        impurity: float = 0.0, # Um fator de 0 a 1
        betrayals: int = 0
    ) -> float:
        """
        Atualiza a corrupção do jogador com base na fórmula do GDD.
        Corrupção = ((CultivoAbsorvido * Impureza) + (Traições * 5)) / Vontade
        
        NOVO: Impureza dinâmica baseada na fonte.
        [SPRINT 5] Constitution Resistance aplicada.
        """
        
        if player.willpower <= 0:
            return player.corruption + 100
        
        # Adiciona traições do player ao contador permanente
        player.betrayals += betrayals
        
        corruption_increase = ((absorbed_cultivation * impurity) + (player.betrayals * 5)) / player.willpower
        
        # [SPRINT 5] Constitution Corruption Resistance
        if hasattr(player, 'constitution_type') and player.constitution_type:
            constitution_resistance = ConstitutionEffects.get_corruption_resistance(player.constitution_type)
            # Resistência reduz ganho de corrupção (positivo = menos corrupção, negativo = mais corrupção)
            corruption_increase *= (1.0 - (constitution_resistance / 100.0))
        
        player.corruption += corruption_increase
        return player.corruption
    
    @staticmethod
    def get_impurity_by_source(source_type: str) -> float:
        """
        Retorna o fator de impureza baseado na fonte de cultivo.
        GDD: Demônios = alta impureza, Humanos = baixa.
        """
        impurity_map = {
            "demon": 0.8,
            "beast": 0.6,
            "evil_cultivator": 0.7,
            "righteous_cultivator": 0.2,
            "neutral_npc": 0.3,
            "environment": 0.1,
            "pill": 0.05
        }
        return impurity_map.get(source_type, 0.3)
    
    @staticmethod
    def check_heart_demon_effects(player: Player) -> Optional[str]:
        """
        Verifica os efeitos do Heart Demon com base no nível de corrupção.
        Retorna uma string descrevendo o efeito ou None se não houver efeito.
        """
        if player.corruption >= 100:
            return "Qi Deviation: Permanent Death"
        elif player.corruption >= 75:
            return "Berserk"
        elif player.corruption >= 50:
            return "Hallucinations"
        
        return None
        
    @staticmethod
    def absorb_cultivation(player: Player, defeated_enemy: NPC):
        """
        Implementa a Demon Transformation Art.
        O jogador absorve cultivo do inimigo, ganhando XP, mas aumentando a corrupção.
        
        NOVO: Usa impureza dinâmica baseada no tipo de inimigo.
        """
        # A quantidade de cultivo ganho pode ser baseada no rank do inimigo
        cultivation_gain = defeated_enemy.rank * 20
        
        # NOVO: Impureza dinâmica baseada no tipo de NPC
        source_type = getattr(defeated_enemy, 'source_type', 'neutral_npc')
        impurity_factor = CombatEngine.get_impurity_by_source(source_type)
        
        print(f"{player.name} absorve {cultivation_gain} de cultivo de {defeated_enemy.name}.")
        player.xp += cultivation_gain
        
        CombatEngine.update_corruption(
            player, 
            absorbed_cultivation=cultivation_gain, 
            impurity=impurity_factor
        )
        print(f"A corrupção de {player.name} aumentou para {player.corruption:.2f} (Impureza: {impurity_factor*100}%).")
        
        return CombatEngine.check_for_rank_up(player)

    @staticmethod
    def check_for_rank_up(player: Player) -> bool:
        """
        Verifica se o jogador tem XP suficiente para subir de rank/tier.
        NOVO: Considera o sistema de tiers do GDD.
        """
        tier_data = CombatEngine.get_tier_data(player.cultivation_tier)
        if not tier_data:
            return False
        
        xp_needed = tier_data.get('xp_to_next_tier')
        
        if xp_needed is None:  # Tier máximo
            return False
        
        if player.xp >= xp_needed:
            # Avança para o próximo tier
            next_tier = player.cultivation_tier + 1
            next_tier_data = CombatEngine.get_tier_data(next_tier)
            
            if next_tier_data:
                player.cultivation_tier = next_tier
                player.xp -= xp_needed
                
                # Atualiza propriedades do tier
                player.can_fly = next_tier_data.get('can_fly', False)
                player.physics_type = next_tier_data.get('physics_type', 'newtonian')
                
                # Aplica multiplicadores de stats
                hp_mult = next_tier_data.get('max_hp_multiplier', 1.0)
                qi_mult = next_tier_data.get('qi_multiplier', 1.0)
                
                player.max_hp *= hp_mult
                player.current_hp = player.max_hp
                player.max_quintessential_essence *= hp_mult
                player.max_shadow_chi *= qi_mult
                player.max_yuan_qi *= qi_mult
                
                print(f"BREAKTHROUGH! {player.name} alcançou {next_tier_data['rank_name']} (Tier {next_tier})!")
                if player.can_fly:
                    print("✨ Habilidade de VOO desbloqueada!")
                
                # 🌩️ SPRINT 6: Verificar Tribulação Celestial
                tribulation_result = tribulation_engine.check_breakthrough_tribulation(player)
                if tribulation_result:
                    print(tribulation_result["narrative"])
                    
                    if not tribulation_result["survived"]:
                        print("\n⚠️ GAME OVER: Player morreu na Tribulação!")
                        return False
                
                return True
        
        return False

