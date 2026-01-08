"""
Quest Generator Agent - Sprint 12
Gera missões dinamicamente via IA adaptadas ao caminho do player.

Filosofia:
- Quests surgem organicamente do contexto (não de NPCs com "!" na cabeça)
- Adaptadas ao tier, localização e histórico do player
- Respeita o estilo sandbox (não força caminhos)
- Integra com o lore do mundo (facções, eventos)
"""

from typing import Dict, Any, Optional, List
from app.services.gemini_client import GeminiClient
from app.database.models.player import Player
import random


# Tipos de quest baseados no contexto
QUEST_TYPES = {
    "hunt": {
        "description": "Eliminar criaturas ou inimigos",
        "suitable_locations": ["floresta", "montanha", "caverna", "pântano", "deserto"],
        "base_difficulty": 1.0
    },
    "gather": {
        "description": "Coletar recursos ou ingredientes",
        "suitable_locations": ["floresta", "montanha", "caverna", "planície"],
        "base_difficulty": 0.7
    },
    "escort": {
        "description": "Proteger NPC durante viagem",
        "suitable_locations": ["cidade", "vila", "porto", "estrada"],
        "base_difficulty": 1.2
    },
    "investigate": {
        "description": "Descobrir informações ou segredos",
        "suitable_locations": ["cidade", "templo", "ruínas", "biblioteca"],
        "base_difficulty": 0.8
    },
    "delivery": {
        "description": "Entregar item ou mensagem",
        "suitable_locations": ["cidade", "vila", "porto", "mercado"],
        "base_difficulty": 0.5
    },
    "duel": {
        "description": "Derrotar um cultivador específico",
        "suitable_locations": ["arena", "cidade", "seita"],
        "base_difficulty": 1.5
    },
    "rescue": {
        "description": "Salvar NPC capturado",
        "suitable_locations": ["caverna", "ruínas", "acampamento", "dungeon"],
        "base_difficulty": 1.3
    },
    "artifact": {
        "description": "Recuperar item antigo ou poderoso",
        "suitable_locations": ["ruínas", "templo", "tumba", "abismo"],
        "base_difficulty": 1.4
    }
}


class QuestGenerator:
    """
    Agente de IA para geração dinâmica de missões.
    """
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
    
    def _determine_quest_type(self, location: str, player_tier: int) -> str:
        """
        Determina o tipo de quest mais adequado para a localização.
        """
        location_lower = location.lower()
        
        suitable_types = []
        for qtype, config in QUEST_TYPES.items():
            for loc_keyword in config["suitable_locations"]:
                if loc_keyword in location_lower:
                    suitable_types.append(qtype)
                    break
        
        if not suitable_types:
            # Fallback baseado em tier
            if player_tier <= 2:
                suitable_types = ["hunt", "gather", "delivery"]
            elif player_tier <= 4:
                suitable_types = ["hunt", "investigate", "escort", "duel"]
            else:
                suitable_types = ["artifact", "rescue", "duel", "investigate"]
        
        return random.choice(suitable_types)
    
    def _calculate_rewards(self, player_tier: int, quest_type: str) -> Dict[str, int]:
        """
        Calcula recompensas baseado no tier e tipo.
        """
        base_xp = 100
        base_gold = 150
        
        difficulty = QUEST_TYPES.get(quest_type, {}).get("base_difficulty", 1.0)
        tier_mult = player_tier * 1.5
        
        return {
            "xp": int(base_xp * tier_mult * difficulty * random.uniform(0.9, 1.1)),
            "gold": int(base_gold * tier_mult * difficulty * random.uniform(0.8, 1.2))
        }
    
    async def generate_quest_async(
        self,
        player: Player,
        location: str,
        recent_events: List[str] = None,
        nearby_npcs: List[str] = None,
        world_context: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Gera uma quest dinamicamente via IA.
        
        Args:
            player: Dados do jogador
            location: Localização atual
            recent_events: Eventos recentes do log
            nearby_npcs: NPCs próximos que podem oferecer quest
            world_context: Contexto do mundo (facções, economia, etc)
        
        Returns:
            Dict com dados da quest ou None se falhar
        """
        quest_type = self._determine_quest_type(location, player.cultivation_tier)
        rewards = self._calculate_rewards(player.cultivation_tier, quest_type)
        
        # Construir prompt para IA
        prompt = self._build_generation_prompt(
            player=player,
            location=location,
            quest_type=quest_type,
            rewards=rewards,
            recent_events=recent_events or [],
            nearby_npcs=nearby_npcs or [],
            world_context=world_context
        )
        
        print(f"[QUEST GEN] Gerando quest tipo '{quest_type}' para tier {player.cultivation_tier} em {location}")
        
        try:
            result = self.gemini_client.generate_json(prompt, task="story")
            
            if "error" in result:
                print(f"[QUEST GEN] Erro: {result['error']}")
                return None
            
            # Montar estrutura final da quest
            quest = self._build_quest_structure(result, quest_type, rewards, player)
            print(f"[QUEST GEN] Quest gerada: '{quest['title']}'")
            return quest
            
        except Exception as e:
            print(f"[QUEST GEN] Erro ao gerar quest: {e}")
            return None
    
    def _build_generation_prompt(
        self,
        player: Player,
        location: str,
        quest_type: str,
        rewards: Dict[str, int],
        recent_events: List[str],
        nearby_npcs: List[str],
        world_context: str
    ) -> str:
        """
        Constrói o prompt para o Gemini gerar a quest.
        """
        tier_names = {
            1: "Fundação", 2: "Despertar", 3: "Ascensão", 4: "Transcendência",
            5: "Soberania", 6: "Divindade", 7: "Imortalidade", 8: "Ancestral", 9: "Criação"
        }
        tier_name = tier_names.get(player.cultivation_tier, "Desconhecido")
        
        events_text = "\n".join(f"- {e}" for e in recent_events[-5:]) if recent_events else "Nenhum evento recente."
        npcs_text = ", ".join(nearby_npcs) if nearby_npcs else "Nenhum NPC específico."
        
        prompt = f"""Você é um gerador de missões para um RPG de Cultivo (Wuxia/Xianxia).

CONTEXTO DO JOGADOR:
- Nome: {player.name}
- Tier de Cultivo: {player.cultivation_tier} ({tier_name})
- Constituição: {player.constitution_type or 'Mortal'}
- Localização Atual: {location}
- Gold: {player.gold}

EVENTOS RECENTES:
{events_text}

NPCs PRÓXIMOS:
{npcs_text}

CONTEXTO DO MUNDO:
{world_context or 'O mundo segue seu curso normal.'}

TIPO DE MISSÃO SOLICITADA: {quest_type.upper()}
Descrição do tipo: {QUEST_TYPES[quest_type]['description']}

REGRAS IMPORTANTES:
1. A missão deve surgir ORGANICAMENTE do contexto (não de um NPC com "!" na cabeça)
2. Deve ser desafiadora mas possível para o tier do jogador
3. NÃO mencione mecânicas de jogo (HP, XP, stats)
4. Use linguagem literária e imersiva
5. A missão deve ter consequências claras (não fazer = algo ruim acontece)
6. Integre com o lore do mundo de cultivo

Responda APENAS com um JSON:
{{
  "title": "Título evocativo da missão (máx 50 chars)",
  "hook": "Como a missão é apresentada ao jogador (1-2 frases literárias, como se um NPC falasse ou algo acontecesse)",
  "description": "Descrição completa do objetivo (2-3 frases)",
  "target": "Alvo específico (nome do monstro, NPC, item, local)",
  "required_count": {random.randint(1, 5) if quest_type == "hunt" else 1},
  "consequence_if_failed": "O que acontece se o jogador não completar (1 frase)",
  "lore_connection": "Conexão com o lore do mundo (1 frase)"
}}"""

        return prompt
    
    def _build_quest_structure(
        self,
        ai_result: Dict[str, Any],
        quest_type: str,
        rewards: Dict[str, int],
        player: Player
    ) -> Dict[str, Any]:
        """
        Monta a estrutura final da quest com dados da IA e cálculos.
        """
        from app.core.chronos import world_clock
        
        deadline_base = {
            "hunt": 30, "gather": 25, "escort": 40, "investigate": 50,
            "delivery": 20, "duel": 60, "rescue": 35, "artifact": 45
        }
        
        deadline_turns = deadline_base.get(quest_type, 30) * player.cultivation_tier
        current_turn = world_clock.get_current_turn()
        
        return {
            "id": random.randint(10000, 99999),
            "title": ai_result.get("title", "Missão Misteriosa"),
            "hook": ai_result.get("hook", "Uma oportunidade surge..."),
            "description": ai_result.get("description", "Complete esta missão."),
            "type": quest_type,
            "target": ai_result.get("target", "Desconhecido"),
            "current_progress": 0,
            "required_progress": ai_result.get("required_count", 1),
            "reward_xp": rewards["xp"],
            "reward_gold": rewards["gold"],
            "reward_items": [],  # Pode ser expandido depois
            "deadline_turn": current_turn + deadline_turns,
            "status": "active",
            "location": player.current_location,
            "consequence_if_failed": ai_result.get("consequence_if_failed", "A oportunidade se perde."),
            "lore_connection": ai_result.get("lore_connection", ""),
            "generated_by_ai": True
        }
    
    def generate_quest_sync(
        self,
        player: Player,
        location: str,
        quest_type: str = None
    ) -> Dict[str, Any]:
        """
        Versão síncrona simplificada (usa templates quando IA não disponível).
        """
        if quest_type is None:
            quest_type = self._determine_quest_type(location, player.cultivation_tier)
        
        rewards = self._calculate_rewards(player.cultivation_tier, quest_type)
        
        # Templates fallback
        templates = {
            "hunt": {
                "title": "Caçada nas Sombras",
                "hook": "Criaturas perigosas foram avistadas nas redondezas.",
                "description": "Elimine as criaturas hostis que ameaçam a área.",
                "target": "Criaturas Hostis",
                "required_count": random.randint(2, 5)
            },
            "gather": {
                "title": "Coleta de Recursos",
                "hook": "Um alquimista precisa de ingredientes raros.",
                "description": "Colete os recursos necessários para o refinamento.",
                "target": "Recursos Raros",
                "required_count": random.randint(3, 6)
            },
            "investigate": {
                "title": "Segredos Ocultos",
                "hook": "Rumores estranhos circulam sobre este local.",
                "description": "Investigue a origem dos eventos misteriosos.",
                "target": "Pistas",
                "required_count": 1
            }
        }
        
        template = templates.get(quest_type, templates["hunt"])
        
        from app.core.chronos import world_clock
        current_turn = world_clock.get_current_turn()
        
        return {
            "id": random.randint(10000, 99999),
            "title": template["title"],
            "hook": template["hook"],
            "description": template["description"],
            "type": quest_type,
            "target": template["target"],
            "current_progress": 0,
            "required_progress": template["required_count"],
            "reward_xp": rewards["xp"],
            "reward_gold": rewards["gold"],
            "reward_items": [],
            "deadline_turn": current_turn + (30 * player.cultivation_tier),
            "status": "active",
            "location": location,
            "consequence_if_failed": "A oportunidade se perde para sempre.",
            "lore_connection": "",
            "generated_by_ai": False
        }
