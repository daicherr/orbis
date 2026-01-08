"""
Quest Service - Dynamic Quest System
Gera missões baseadas em origin_location, cultivation_tier e eventos do mundo (Sprint 6)
Atualizado Sprint 12: Integração com QuestGenerator (IA)
"""

from typing import Optional, List, Dict, Any
from app.database.models.player import Player
from app.core.chronos import world_clock
import random

class QuestService:
    """Sistema de missões dinâmicas [SPRINT 6 + 12]"""
    
    def __init__(self):
        # Templates de fallback (usados quando IA não disponível)
        self.quest_templates = {
            "Vila Crisântemos": [{
                "type": "hunt", "title": "Caça aos Javalis Selvagens",
                "description": "Javalis-de-Ferro têm devastado as plantações. Elimine {count} deles.",
                "target": "Iron-Hide Boar", "min_tier": 1, "base_reward_xp": 100, "base_reward_gold": 200
            }],
            "Floresta Nublada": [{
                "type": "hunt", "title": "Serpentes da Névoa",
                "description": "Serpentes venenosas infestam a floresta. Elimine {count} delas.",
                "target": "Mist Serpent", "min_tier": 2, "base_reward_xp": 250, "base_reward_gold": 400
            }]
        }
        self.active_quests: Dict[int, List[Dict[str, Any]]] = {}
        self._quest_generator = None  # Lazy init para evitar import circular
    
    def _get_quest_generator(self):
        """Lazy initialization do quest generator."""
        if self._quest_generator is None:
            try:
                from app.agents.quest_generator import QuestGenerator
                from app.services.gemini_client import GeminiClient
                gemini = GeminiClient()
                self._quest_generator = QuestGenerator(gemini)
            except Exception as e:
                print(f"[QUEST] Não foi possível inicializar QuestGenerator: {e}")
                return None
        return self._quest_generator
    
    async def generate_quest_ai(
        self, 
        player: Player, 
        recent_events: List[str] = None,
        nearby_npcs: List[str] = None,
        world_context: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Gera quest via IA (Sprint 12).
        Falls back para template se IA não disponível.
        """
        generator = self._get_quest_generator()
        if generator:
            try:
                quest = await generator.generate_quest_async(
                    player=player,
                    location=player.current_location or player.origin_location,
                    recent_events=recent_events,
                    nearby_npcs=nearby_npcs,
                    world_context=world_context
                )
                if quest:
                    return quest
            except Exception as e:
                print(f"[QUEST] Erro na geração IA: {e}")
        
        # Fallback para template
        return self.generate_quest(player)
    
    def generate_quest(self, player: Player) -> Optional[Dict[str, Any]]:
        """Gera quest baseada no player."""
        location = player.origin_location or "Vila Crisântemos"
        templates = self.quest_templates.get(location, [])
        if not templates:
            return None
        
        available = [t for t in templates if t["min_tier"] <= player.cultivation_tier]
        if not available:
            return None
        
        template = random.choice(available)
        return self._build_quest_from_template(template, player)
    
    def _build_quest_from_template(self, template: Dict[str, Any], player: Player) -> Dict[str, Any]:
        """Constrói quest a partir de template."""
        tier_mult = player.cultivation_tier
        count = random.randint(3, 8) * tier_mult if template["type"] == "hunt" else 1
        reward_xp = int(template["base_reward_xp"] * tier_mult * 1.5)
        reward_gold = int(template["base_reward_gold"] * tier_mult * 1.2)
        deadline_turns = random.randint(20, 50)
        current_turn = world_clock.get_current_turn()
        
        return {
            "id": random.randint(1000, 9999),
            "title": template["title"],
            "description": template["description"].format(count=count),
            "type": template["type"],
            "target": template["target"],
            "current_progress": 0,
            "required_progress": count,
            "reward_xp": reward_xp,
            "reward_gold": reward_gold,
            "reward_items": [],
            "deadline_turn": current_turn + deadline_turns,
            "status": "active",
            "location": player.origin_location
        }
    
    def add_quest_to_player(self, player_id: int, quest: Dict[str, Any]):
        """Adiciona quest ao tracking."""
        if player_id not in self.active_quests:
            self.active_quests[player_id] = []
        self.active_quests[player_id].append(quest)
        print(f"[QUEST] Quest adicionada: '{quest['title']}'")
    
    def get_active_quests(self, player_id: int) -> List[Dict[str, Any]]:
        """Retorna quests ativas."""
        return self.active_quests.get(player_id, [])
    
    def update_quest_progress(self, player_id: int, quest_id: int, progress_increment: int = 1) -> Optional[Dict[str, Any]]:
        """Atualiza progresso de quest."""
        player_quests = self.active_quests.get(player_id, [])
        for quest in player_quests:
            if quest["id"] == quest_id:
                quest["current_progress"] += progress_increment
                if quest["current_progress"] >= quest["required_progress"]:
                    quest["status"] = "completed"
                    print(f"[OK] Quest Completa: '{quest['title']}'!")
                    return quest
                print(f"[PROGRESS] Progresso: {quest['current_progress']}/{quest['required_progress']}")
        return None
    
    def check_deadlines(self, player_id: int) -> List[Dict[str, Any]]:
        """Verifica deadlines das quests."""
        current_turn = world_clock.get_current_turn()
        player_quests = self.active_quests.get(player_id, [])
        failed_quests = []
        for quest in player_quests:
            if quest["status"] == "active" and current_turn > quest["deadline_turn"]:
                quest["status"] = "failed"
                failed_quests.append(quest)
                print(f"[FAIL] Quest Falhou: '{quest['title']}'")
        return failed_quests
    
    def complete_quest(self, player: Player, quest: Dict[str, Any]):
        """Aplica recompensas."""
        player.xp += quest["reward_xp"]
        player.gold += quest["reward_gold"]
        print(f"[COMPLETE] QUEST COMPLETA: {quest['title']} (+{quest['reward_xp']} XP, +{quest['reward_gold']} Gold)")

quest_service = QuestService()
