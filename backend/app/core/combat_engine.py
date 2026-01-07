from typing import Optional
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.core.skill_manager import skill_manager

class CombatEngine:
    
    @staticmethod
    def calculate_damage(
        attacker: Player | NPC, 
        defender: Player | NPC, 
        skill_id: str
    ) -> float:
        """
        Calcula o dano total com base em uma habilidade específica, usando o GDD.
        DanoTotal = (BaseDmg + (ShadowChi * 2)) * (100 / (100 + (DefesaAlvo - Penetração)))
        """
        skill = skill_manager.get_skill(skill_id)
        if not skill:
            return 0.0

        base_damage = skill.get('base_damage', 0.0)
        
        # Lógica de penetração baseada nos efeitos da habilidade
        penetration = 0.0
        if 'effects' in skill:
            for effect in skill['effects']:
                if effect.get('type') == 'armor_penetration':
                    # 1.0 significa 100% de penetração
                    penetration = defender.defense * effect.get('value', 0.0)

        # Bônus de Shadow Chi
        shadow_chi_bonus = 0
        if isinstance(attacker, Player) and skill.get('cost_type') == 'shadow_chi':
            shadow_chi_bonus = attacker.shadow_chi * 2
            
        total_base_damage = base_damage + shadow_chi_bonus
        
        effective_defense = defender.defense - penetration
        if effective_defense < 0:
            effective_defense = 0
            
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
        """
        
        if player.willpower <= 0:
            return player.corruption + 100
            
        corruption_increase = ((absorbed_cultivation * impurity) + (betrayals * 5)) / player.willpower
        
        player.corruption += corruption_increase
        return player.corruption
        
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
        """
        # A quantidade de cultivo ganho pode ser baseada no rank do inimigo
        cultivation_gain = defeated_enemy.rank * 20
        impurity_factor = 0.3
        
        print(f"{player.name} absorve {cultivation_gain} de cultivo de {defeated_enemy.name}.")
        player.xp += cultivation_gain
        
        CombatEngine.update_corruption(
            player, 
            absorbed_cultivation=cultivation_gain, 
            impurity=impurity_factor
        )
        print(f"A corrupção de {player.name} aumentou para {player.corruption:.2f}.")
        
        return CombatEngine.check_for_rank_up(player)

    @staticmethod
    def check_for_rank_up(player: Player) -> bool:
        """Verifica se o jogador tem XP suficiente para subir de rank."""
        # A fórmula de XP necessário pode ser mais complexa
        xp_needed = player.rank * 100 
        if player.xp >= xp_needed:
            player.rank += 1
            player.xp -= xp_needed
            print(f"AVANÇO! {player.name} alcançou o Rank {player.rank}!")
            # Lógica para desbloquear novas habilidades ou aumentar stats
            return True
        return False

