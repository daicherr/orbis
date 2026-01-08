"""
🎲 DICE ROLLER - Sistema de Rolagem de Dados
Usado para cálculos de combate, defesa e checks de skill.
"""

import random
from typing import Optional

class DiceRoller:
    """Sistema centralizado de rolagem de dados para RPG."""
    
    @staticmethod
    def roll(dice_notation: str) -> int:
        """
        Rola dados baseado em notação padrão (ex: '2d6', '1d20+5').
        
        Args:
            dice_notation: String no formato 'XdY+Z' onde:
                X = número de dados
                Y = lados do dado
                Z = modificador (opcional)
        
        Returns:
            Resultado total da rolagem
        
        Examples:
            roll('1d20') -> 1-20
            roll('2d6+3') -> 5-15
            roll('3d8-2') -> 1-22
        """
        # Parse da notação
        parts = dice_notation.lower().replace(' ', '')
        
        # Separar modificador
        modifier = 0
        if '+' in parts:
            parts, mod_str = parts.split('+')
            modifier = int(mod_str)
        elif '-' in parts:
            parts, mod_str = parts.split('-')
            modifier = -int(mod_str)
        
        # Parse de XdY
        if 'd' not in parts:
            return int(parts) + modifier
        
        num_dice, sides = parts.split('d')
        num_dice = int(num_dice)
        sides = int(sides)
        
        # Rolar dados
        total = sum(random.randint(1, sides) for _ in range(num_dice))
        return total + modifier
    
    @staticmethod
    def roll_attack(attack_power: int) -> int:
        """
        Rola ataque: 1d20 + attack_power.
        
        Args:
            attack_power: Poder de ataque base
        
        Returns:
            Resultado do roll de ataque
        """
        return random.randint(1, 20) + attack_power
    
    @staticmethod
    def roll_defense(defense_power: int) -> int:
        """
        Rola defesa: 1d20 + defense_power.
        
        Args:
            defense_power: Poder de defesa base
        
        Returns:
            Resultado do roll de defesa
        """
        return random.randint(1, 20) + defense_power
    
    @staticmethod
    def roll_skill_check(skill_bonus: int, difficulty: int = 15) -> bool:
        """
        Rola check de skill: 1d20 + skill_bonus vs difficulty.
        
        Args:
            skill_bonus: Bônus da skill
            difficulty: DC (Difficulty Class) padrão 15
        
        Returns:
            True se sucesso, False se falha
        """
        roll = random.randint(1, 20) + skill_bonus
        return roll >= difficulty
    
    @staticmethod
    def roll_damage(damage_dice: str, bonus: int = 0) -> int:
        """
        Rola dano: XdY + bonus.
        
        Args:
            damage_dice: Notação de dados (ex: '2d8')
            bonus: Bônus de dano
        
        Returns:
            Dano total
        """
        base_damage = DiceRoller.roll(damage_dice)
        return max(0, base_damage + bonus)
    
    @staticmethod
    def roll_critical() -> bool:
        """
        Verifica se houve crítico (1d20 >= 18).
        
        Returns:
            True se crítico, False caso contrário
        """
        return random.randint(1, 20) >= 18
    
    @staticmethod
    def roll_percentile() -> int:
        """
        Rola 1d100 (0-99).
        
        Returns:
            Número entre 0-99
        """
        return random.randint(0, 99)
    
    @staticmethod
    def advantage_roll(modifier: int = 0) -> int:
        """
        Rola com vantagem: rola 2d20, pega o maior.
        
        Args:
            modifier: Modificador adicional
        
        Returns:
            Maior resultado + modifier
        """
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        return max(roll1, roll2) + modifier
    
    @staticmethod
    def disadvantage_roll(modifier: int = 0) -> int:
        """
        Rola com desvantagem: rola 2d20, pega o menor.
        
        Args:
            modifier: Modificador adicional
        
        Returns:
            Menor resultado + modifier
        """
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        return min(roll1, roll2) + modifier
    
    @staticmethod
    def roll_initiative(dexterity_bonus: int = 0) -> int:
        """
        Rola iniciativa: 1d20 + dexterity.
        
        Args:
            dexterity_bonus: Bônus de destreza
        
        Returns:
            Iniciativa
        """
        return random.randint(1, 20) + dexterity_bonus
    
    @staticmethod
    def roll_saving_throw(save_bonus: int, dc: int) -> bool:
        """
        Rola saving throw: 1d20 + bonus vs DC.
        
        Args:
            save_bonus: Bônus do saving throw
            dc: Difficulty Class
        
        Returns:
            True se passou, False se falhou
        """
        roll = random.randint(1, 20) + save_bonus
        return roll >= dc
