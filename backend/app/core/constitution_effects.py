"""
Constitution Effects System
Implementa buffs/debuffs baseados em constitution_type (Sprint 4/5 integration)
"""

from typing import Dict, Any
from app.database.models.player import Player
from app.database.models.npc import NPC

class ConstitutionEffects:
    """
    Sistema de efeitos passivos baseados na constituição do personagem.
    Referência: GDD_Codex_Triluna.md e Character Creation Wizard
    """
    
    CONSTITUTION_MODIFIERS = {
        # MORTAL (Balanced)
        "Mortal": {
            "hp_multiplier": 1.0,
            "defense_multiplier": 1.0,
            "damage_multiplier": 1.0,
            "quintessence_regen": 1.0,
            "shadow_chi_cost": 1.0,
            "yuan_qi_cost": 1.0,
            "corruption_resistance": 0.0,
            "description": "Equilíbrio perfeito. Sem bônus ou penalidades."
        },
        
        # GODFIEND TYPES (High Power, High Cost)
        "Godfiend (Black Sand)": {
            "hp_multiplier": 1.3,
            "defense_multiplier": 1.5,  # Tank
            "damage_multiplier": 1.0,
            "quintessence_regen": 0.7,  # Regenera menos
            "shadow_chi_cost": 1.2,
            "yuan_qi_cost": 1.3,
            "corruption_resistance": -10.0,  # Mais suscetível
            "special": "gravity_control",  # Campo de gravidade (Ultimate)
            "description": "Defesa massiva (+50%), mas consome mais recursos."
        },
        
        "Godfiend (Phoenix)": {
            "hp_multiplier": 1.0,
            "defense_multiplier": 0.8,
            "damage_multiplier": 1.4,  # Alto dano de fogo
            "quintessence_regen": 1.5,  # Regeneração tipo Phoenix
            "shadow_chi_cost": 1.0,
            "yuan_qi_cost": 1.5,  # Alto custo de energia
            "corruption_resistance": 15.0,  # Purificação
            "special": "nirvana_rebirth",  # Ressurreição 1x
            "description": "Dano de fogo +40%, regeneração +50%, pode renascer 1x."
        },
        
        "Godfiend (Lightning Devastator)": {
            "hp_multiplier": 0.9,
            "defense_multiplier": 0.7,  # Vidro
            "damage_multiplier": 1.6,  # Altíssimo DPS
            "quintessence_regen": 1.0,
            "shadow_chi_cost": 1.4,  # Consome muito Chi
            "yuan_qi_cost": 1.2,
            "corruption_resistance": -5.0,
            "special": "lightning_speed",  # Sempre tem iniciativa
            "description": "Velocidade extrema, dano +60%, mas defesa -30%."
        },
        
        "Godfiend (Dragon Body)": {
            "hp_multiplier": 1.5,  # Tanque máximo
            "defense_multiplier": 1.3,
            "damage_multiplier": 1.3,  # Força bruta
            "quintessence_regen": 1.2,
            "shadow_chi_cost": 1.0,
            "yuan_qi_cost": 1.4,
            "corruption_resistance": 10.0,
            "special": "dragon_fear",  # Inimigos inferiores fogem
            "description": "HP +50%, defesa +30%, causa medo em inferiores."
        },
        
        "Godfiend (Eon Sea)": {
            "hp_multiplier": 1.2,
            "defense_multiplier": 1.0,
            "damage_multiplier": 0.9,
            "quintessence_regen": 2.0,  # Regeneração infinita
            "shadow_chi_cost": 1.0,
            "yuan_qi_cost": 1.0,
            "corruption_resistance": 5.0,
            "special": "endless_stamina",  # Nunca cansa
            "description": "Regeneração +100%, stamina infinita."
        },
        
        "Godfiend (Mercury Veins)": {
            "hp_multiplier": 0.8,
            "defense_multiplier": 0.9,
            "damage_multiplier": 1.2,
            "quintessence_regen": 1.0,
            "shadow_chi_cost": 0.8,  # Eficiente
            "yuan_qi_cost": 0.9,
            "corruption_resistance": -15.0,  # Artificial, instável
            "special": "alchemical_fusion",  # Bônus em alquimia
            "description": "Custos reduzidos, mas corrupção +15%."
        },
        
        # TABOO (Forbidden Power)
        "Taboo (Heavenly Scourge)": {
            "hp_multiplier": 1.1,
            "defense_multiplier": 0.6,  # Atrai tribulações
            "damage_multiplier": 1.8,  # Poder proibido
            "quintessence_regen": 1.0,
            "shadow_chi_cost": 1.5,
            "yuan_qi_cost": 1.5,
            "corruption_resistance": -20.0,  # Maldição permanente
            "special": "heavenly_tribulation",  # Atrai raios celestiais
            "description": "Dano +80%, mas defesa -40% e atrai tribulações."
        },
        
        "Taboo": {
            "hp_multiplier": 1.0,
            "defense_multiplier": 0.8,
            "damage_multiplier": 1.5,
            "quintessence_regen": 1.0,
            "shadow_chi_cost": 1.3,
            "yuan_qi_cost": 1.3,
            "corruption_resistance": -15.0,
            "special": "forbidden_power",
            "description": "Poder proibido: dano +50%, corrupção +15%."
        }
    }
    
    @staticmethod
    def get_modifiers(constitution_type: str) -> Dict[str, Any]:
        """Retorna os modificadores de uma constituição específica."""
        return ConstitutionEffects.CONSTITUTION_MODIFIERS.get(
            constitution_type,
            ConstitutionEffects.CONSTITUTION_MODIFIERS["Mortal"]  # Fallback
        )
    
    @staticmethod
    def apply_constitution_effects(entity: Player | NPC):
        """
        Aplica os efeitos passivos da constituição nos stats do personagem.
        Deve ser chamado ao criar o personagem ou ao evoluir a constituição.
        """
        if not hasattr(entity, 'constitution_type'):
            return  # Entidade não tem constituição definida
        
        constitution_type = entity.constitution_type
        modifiers = ConstitutionEffects.get_modifiers(constitution_type)
        
        # Aplicar multiplicadores nos stats base
        if hasattr(entity, 'max_hp'):
            entity.max_hp *= modifiers["hp_multiplier"]
            entity.current_hp = min(entity.current_hp, entity.max_hp)
        
        if hasattr(entity, 'defense'):
            entity.defense *= modifiers["defense_multiplier"]
        
        # Ajustar recursos máximos
        if hasattr(entity, 'max_quintessential_essence'):
            entity.max_quintessential_essence *= modifiers["quintessence_regen"]
        
        # Corrupção base
        if hasattr(entity, 'corruption'):
            entity.corruption += modifiers["corruption_resistance"]
            entity.corruption = max(0, min(100, entity.corruption))  # Clamp 0-100
    
    @staticmethod
    def get_damage_modifier(constitution_type: str) -> float:
        """Retorna o multiplicador de dano da constituição."""
        modifiers = ConstitutionEffects.get_modifiers(constitution_type)
        return modifiers.get("damage_multiplier", 1.0)
    
    @staticmethod
    def get_cost_modifier(constitution_type: str, resource_type: str) -> float:
        """
        Retorna o multiplicador de custo para um recurso específico.
        resource_type: 'shadow_chi', 'yuan_qi', 'quintessence'
        """
        modifiers = ConstitutionEffects.get_modifiers(constitution_type)
        
        if resource_type == "shadow_chi":
            return modifiers.get("shadow_chi_cost", 1.0)
        elif resource_type == "yuan_qi":
            return modifiers.get("yuan_qi_cost", 1.0)
        elif resource_type == "quintessence":
            return 1.0 / modifiers.get("quintessence_regen", 1.0)  # Inverso da regeneração
        
        return 1.0
    
    @staticmethod
    def has_special_ability(constitution_type: str) -> str:
        """Retorna a habilidade especial da constituição (se houver)."""
        modifiers = ConstitutionEffects.get_modifiers(constitution_type)
        return modifiers.get("special", None)
    
    @staticmethod
    def get_corruption_resistance(constitution_type: str) -> float:
        """Retorna a resistência à corrupção da constituição."""
        modifiers = ConstitutionEffects.get_modifiers(constitution_type)
        return modifiers.get("corruption_resistance", 0.0)
