"""
🌩️ TRIBULATION ENGINE - Sistema de Tribulações Celestiais
Baseado em world_physics.md: "A cada 500 anos, Tier 8+ enfrentam Tribulação Celestial"

MECÂNICA:
- Godfiends atraem raios celestiais ao fazer breakthroughs
- Taboo Constitutions têm chance ainda maior
- Se sobreviver: recompensas poderosas
- Se falhar: dano massivo ou morte

FÓRMULAS:
- Chance de Tribulação:
  - Mortal: 10%
  - Godfiend: 70%
  - Taboo: 90%
- Dano dos Raios: (cultivation_tier * 100) - defesa
- Recompensas: Spirit Stones, Rare Pills, +10% HP permanente
"""

from typing import Dict, Optional, Tuple
import random
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.core.dice_roller import DiceRoller

class TribulationEngine:
    """Motor de Tribulações Celestiais para breakthroughs."""
    
    def __init__(self):
        # Chances de tribulação por tipo de constituição
        self.tribulation_chance = {
            "mortal": 0.10,  # 10%
            "procedural": 0.30,  # 30%
            "godfiend": 0.70,  # 70%
            "taboo": 0.90,  # 90%
            "chimera": 0.50  # 50%
        }
        
        # Tipos de raios (aumentam em intensidade)
        self.lightning_types = [
            {"name": "Raio Menor", "multiplier": 0.8, "description": "Nuvens escuras se formam..."},
            {"name": "Raio Celestial", "multiplier": 1.0, "description": "O céu se parte em fúria!"},
            {"name": "Raio da Aniquilação", "multiplier": 1.5, "description": "A própria Natureza rejeita sua existência!"},
            {"name": "Raio do Julgamento", "multiplier": 2.0, "description": "Os Céus decretam sua sentença de MORTE!"}
        ]
        
        # Recompensas por sobrevivência
        self.rewards = {
            "spirit_stones": 100,  # base * tier
            "rare_pills": ["Tribulation Pill", "Heaven Defying Pill"],
            "hp_bonus_percent": 0.10,  # +10% HP max permanente
            "qi_bonus_percent": 0.15,  # +15% Qi max permanente
            "special_title": "Heaven Defier"
        }
    
    def should_trigger_tribulation(self, entity: Player | NPC) -> bool:
        """
        Verifica se uma tribulação deve ocorrer no breakthrough.
        
        Args:
            entity: Player ou NPC fazendo breakthrough
        
        Returns:
            True se tribulação deve ocorrer
        """
        # Verificar tipo de constituição
        constitution_type = getattr(entity, 'constitution_type', 'mortal')
        
        # Taboo constitutions sempre têm nome específico
        if "Scourge" in constitution_type or "Cursed" in constitution_type:
            constitution_category = "taboo"
        elif constitution_type in ["Black Sand", "Eon Sea", "Phoenix", "Vermilion", "Azure Dragon", "White Tiger", "Black Tortoise"]:
            constitution_category = "godfiend"
        elif constitution_type == "Human" or constitution_type == "mortal":
            constitution_category = "mortal"
        elif "Chimera" in constitution_type:
            constitution_category = "chimera"
        else:
            constitution_category = "procedural"
        
        chance = self.tribulation_chance.get(constitution_category, 0.30)
        
        # Tier 8+ tem chance aumentada (+20%)
        if entity.cultivation_tier >= 8:
            chance = min(1.0, chance + 0.20)
        
        return random.random() < chance
    
    def calculate_tribulation_damage(self, entity: Player | NPC) -> Dict:
        """
        Calcula o dano da tribulação baseado no tier do cultivador.
        
        Args:
            entity: Player ou NPC sofrendo tribulação
        
        Returns:
            Dict com {damage, lightning_type, description}
        """
        tier = entity.cultivation_tier
        
        # Selecionar tipo de raio baseado no tier
        if tier <= 3:
            lightning = self.lightning_types[0]  # Raio Menor
        elif tier <= 6:
            lightning = self.lightning_types[1]  # Raio Celestial
        elif tier <= 8:
            lightning = self.lightning_types[2]  # Raio da Aniquilação
        else:
            lightning = self.lightning_types[3]  # Raio do Julgamento
        
        # Dano base: tier * 100
        base_damage = tier * 100
        
        # Aplicar multiplicador do tipo de raio
        raw_damage = int(base_damage * lightning["multiplier"])
        
        # Rolar defesa (Quintessence + Qi)
        defense = entity.quintessence + (entity.yuan_qi / 2)
        defense_roll = DiceRoller.roll_defense(defense)
        
        # Dano final
        final_damage = max(0, raw_damage - defense_roll)
        
        return {
            "raw_damage": raw_damage,
            "defense_roll": defense_roll,
            "final_damage": final_damage,
            "lightning_type": lightning["name"],
            "description": lightning["description"],
            "tier": tier
        }
    
    def calculate_rewards(self, entity: Player | NPC, survived: bool) -> Dict:
        """
        Calcula as recompensas por sobreviver à tribulação.
        
        Args:
            entity: Player ou NPC que sobreviveu
            survived: Se sobreviveu ou não
        
        Returns:
            Dict com recompensas
        """
        if not survived:
            return {
                "spirit_stones": 0,
                "pills": [],
                "hp_bonus": 0,
                "qi_bonus": 0,
                "title": None,
                "message": "💀 Você falhou na Tribulação. A morte o aguarda..."
            }
        
        tier = entity.cultivation_tier
        
        # Escalar recompensas com tier
        spirit_stones = self.rewards["spirit_stones"] * tier
        
        # Chance de pílula rara (50% base + 10% por tier acima de 5)
        pill_chance = 0.50 + (max(0, tier - 5) * 0.10)
        pills = []
        if random.random() < pill_chance:
            pills.append(random.choice(self.rewards["rare_pills"]))
        
        # Bônus permanente de HP e Qi
        hp_bonus = int(entity.hp_max * self.rewards["hp_bonus_percent"])
        qi_bonus = int(entity.yuan_qi_max * self.rewards["qi_bonus_percent"])
        
        # Título especial para tier 7+
        title = None
        if tier >= 7:
            title = self.rewards["special_title"]
        
        return {
            "spirit_stones": spirit_stones,
            "pills": pills,
            "hp_bonus": hp_bonus,
            "qi_bonus": qi_bonus,
            "title": title,
            "message": f"✨ Você sobreviveu à Tribulação! O Céu reconhece sua força."
        }
    
    def apply_tribulation(self, entity: Player | NPC) -> Dict:
        """
        Aplica uma tribulação completa em um cultivador.
        
        Args:
            entity: Player ou NPC fazendo breakthrough
        
        Returns:
            Dict com resultado completo da tribulação
        """
        # Calcular dano
        damage_result = self.calculate_tribulation_damage(entity)
        
        # Aplicar dano
        entity.hp_current = max(0, entity.hp_current - damage_result["final_damage"])
        
        # Verificar sobrevivência
        survived = entity.hp_current > 0
        
        # Calcular recompensas
        rewards = self.calculate_rewards(entity, survived)
        
        # Aplicar recompensas se sobreviveu
        if survived:
            entity.hp_max += rewards["hp_bonus"]
            entity.hp_current += rewards["hp_bonus"]  # Heal completo
            entity.yuan_qi_max += rewards["qi_bonus"]
            entity.yuan_qi += rewards["qi_bonus"]
            
            # Adicionar spirit stones se for Player
            if hasattr(entity, 'spirit_stones'):
                entity.spirit_stones = getattr(entity, 'spirit_stones', 0) + rewards["spirit_stones"]
        
        # Montar narrativa
        narrative = self._generate_narrative(entity, damage_result, rewards, survived)
        
        return {
            "triggered": True,
            "survived": survived,
            "damage": damage_result,
            "rewards": rewards,
            "narrative": narrative,
            "entity_hp": entity.hp_current
        }
    
    def _generate_narrative(self, entity, damage_result, rewards, survived: bool) -> str:
        """Gera narrativa literária da tribulação."""
        
        tier = entity.cultivation_tier
        name = entity.name
        lightning_desc = damage_result["description"]
        lightning_type = damage_result["lightning_type"]
        damage = damage_result["final_damage"]
        
        # Narrativa inicial
        lines = [
            f"\n⚡ 【TRIBULAÇÃO CELESTIAL - Tier {tier}】⚡",
            f"{lightning_desc}",
            f"",
            f"Um {lightning_type} desce dos Nove Céus, mirando {name}!",
            f"Dano Bruto: {damage_result['raw_damage']} | Defesa: {damage_result['defense_roll']}",
            f"💥 Dano Final: {damage} HP"
        ]
        
        if survived:
            lines.extend([
                f"",
                f"🌟 {name} sobrevive ao julgamento dos Céus!",
                f"",
                f"【RECOMPENSAS】",
                f"💎 Spirit Stones: +{rewards['spirit_stones']}",
                f"❤️ HP Max: +{rewards['hp_bonus']}",
                f"⚡ Qi Max: +{rewards['qi_bonus']}"
            ])
            
            if rewards['pills']:
                lines.append(f"💊 Pílula Rara: {rewards['pills'][0]}")
            
            if rewards['title']:
                lines.append(f"")
                lines.append(f"🏆 Título Desbloqueado: 【{rewards['title']}】")
                lines.append(f"'Aquele que desafia os Céus e vive para contar.'")
        else:
            lines.extend([
                f"",
                f"💀 {name} não resistiu à fúria celestial...",
                f"A alma se dispersa no vento, e o corpo retorna ao pó."
            ])
        
        return "\n".join(lines)
    
    def check_breakthrough_tribulation(self, entity: Player | NPC) -> Optional[Dict]:
        """
        Verifica e processa tribulação em um breakthrough.
        Método de conveniência para integração fácil.
        
        Args:
            entity: Entidade fazendo breakthrough
        
        Returns:
            Dict com resultado ou None se não houve tribulação
        """
        if self.should_trigger_tribulation(entity):
            return self.apply_tribulation(entity)
        return None

# Singleton
tribulation_engine = TribulationEngine()
