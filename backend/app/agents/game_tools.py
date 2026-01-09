"""
Game Tools - Ferramentas para Agentes do Jogo
GEM RPG ORBIS - Arquitetura Cognitiva

Coleção de ferramentas que os agentes podem usar para:
- Consultar estado do mundo
- Verificar stats de jogadores e NPCs
- Realizar ações mecânicas (combate, economia, etc)
- Acessar conhecimento do mundo
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import json
import random
from pathlib import Path


@dataclass
class Tool:
    """
    Definição de uma ferramenta que pode ser usada pelos agentes.
    Standalone para evitar dependência circular.
    """
    name: str
    description: str
    func: Callable[..., Awaitable[Any]]
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    async def execute(self, **kwargs) -> Any:
        """Executa a ferramenta com os parâmetros fornecidos."""
        return await self.func(**kwargs)


# ==================== FERRAMENTAS DE CONHECIMENTO ====================

async def search_lore(query: str, category: str = "all") -> Dict[str, Any]:
    """
    Busca informações no lore do mundo.
    
    Args:
        query: O que buscar
        category: all, cultivation, world, factions, history
    """
    repo_root = Path(__file__).resolve().parents[3]
    
    results = []
    
    # Buscar em cultivation_rules.md
    if category in ["all", "cultivation"]:
        cult_path = repo_root / "ruleset_source/lore_manual/cultivation_rules.md"
        if cult_path.exists():
            content = cult_path.read_text(encoding="utf-8")
            # Busca simples por presença da query
            if query.lower() in content.lower():
                # Extrair contexto ao redor da query
                idx = content.lower().find(query.lower())
                start = max(0, idx - 200)
                end = min(len(content), idx + 200)
                results.append({
                    "source": "cultivation_rules.md",
                    "excerpt": content[start:end].strip()
                })
    
    # Buscar em world_physics.md
    if category in ["all", "world"]:
        world_path = repo_root / "ruleset_source/lore_manual/world_physics.md"
        if world_path.exists():
            content = world_path.read_text(encoding="utf-8")
            if query.lower() in content.lower():
                idx = content.lower().find(query.lower())
                start = max(0, idx - 200)
                end = min(len(content), idx + 200)
                results.append({
                    "source": "world_physics.md",
                    "excerpt": content[start:end].strip()
                })
    
    # Buscar em bestiary_lore.md
    if category in ["all", "creatures"]:
        best_path = repo_root / "ruleset_source/lore_manual/bestiary_lore.md"
        if best_path.exists():
            content = best_path.read_text(encoding="utf-8")
            if query.lower() in content.lower():
                idx = content.lower().find(query.lower())
                start = max(0, idx - 200)
                end = min(len(content), idx + 200)
                results.append({
                    "source": "bestiary_lore.md",
                    "excerpt": content[start:end].strip()
                })
    
    if not results:
        return {"found": False, "message": f"Nenhum resultado para '{query}' na categoria '{category}'"}
    
    return {"found": True, "results": results}


async def get_cultivation_ranks() -> Dict[str, Any]:
    """Retorna a lista de ranks de cultivo e seus requisitos."""
    repo_root = Path(__file__).resolve().parents[3]
    ranks_path = repo_root / "ruleset_source/mechanics/cultivation_ranks.json"
    
    if ranks_path.exists():
        with open(ranks_path, "r", encoding="utf-8") as f:
            return {"ranks": json.load(f)}
    
    return {"error": "Arquivo de ranks não encontrado"}


async def get_techniques_by_element(element: str) -> Dict[str, Any]:
    """Retorna técnicas de um elemento específico."""
    repo_root = Path(__file__).resolve().parents[3]
    tech_path = repo_root / "ruleset_source/mechanics/techniques.json"
    
    if tech_path.exists():
        with open(tech_path, "r", encoding="utf-8") as f:
            techniques = json.load(f)
            filtered = [t for t in techniques if t.get("element", "").lower() == element.lower()]
            return {"techniques": filtered, "count": len(filtered)}
    
    return {"error": "Arquivo de técnicas não encontrado"}


async def get_item_info(item_name: str) -> Dict[str, Any]:
    """Busca informações sobre um item específico."""
    repo_root = Path(__file__).resolve().parents[3]
    items_path = repo_root / "ruleset_source/mechanics/items.json"
    
    if items_path.exists():
        with open(items_path, "r", encoding="utf-8") as f:
            items = json.load(f)
            for item in items:
                if item.get("name", "").lower() == item_name.lower():
                    return {"found": True, "item": item}
                if item.get("id", "").lower() == item_name.lower():
                    return {"found": True, "item": item}
            
            # Busca parcial
            matches = [i for i in items if item_name.lower() in i.get("name", "").lower()]
            if matches:
                return {"found": True, "partial_matches": matches[:5]}
    
    return {"found": False, "message": f"Item '{item_name}' não encontrado"}


# ==================== FERRAMENTAS DE MECÂNICAS ====================

async def roll_dice(dice: str, modifier: int = 0) -> Dict[str, Any]:
    """
    Rola dados no formato XdY+Z.
    
    Args:
        dice: Formato "2d6", "1d20", etc
        modifier: Modificador a adicionar ao resultado
    """
    try:
        # Parse do formato XdY
        parts = dice.lower().split("d")
        if len(parts) != 2:
            return {"error": f"Formato inválido: {dice}. Use XdY (ex: 2d6)"}
        
        num_dice = int(parts[0])
        num_sides = int(parts[1])
        
        if num_dice < 1 or num_dice > 100:
            return {"error": "Número de dados deve ser entre 1 e 100"}
        if num_sides < 2 or num_sides > 100:
            return {"error": "Número de lados deve ser entre 2 e 100"}
        
        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        return {
            "dice": dice,
            "rolls": rolls,
            "modifier": modifier,
            "total": total,
            "formula": f"{dice}{'+' + str(modifier) if modifier > 0 else ''}"
        }
    except Exception as e:
        return {"error": f"Erro ao rolar dados: {str(e)}"}


async def calculate_damage(
    attacker_power: float,
    defender_defense: float,
    skill_multiplier: float = 1.0,
    critical: bool = False
) -> Dict[str, Any]:
    """
    Calcula dano de um ataque baseado nas fórmulas do sistema.
    
    Args:
        attacker_power: Poder de ataque do atacante
        defender_defense: Defesa do defensor
        skill_multiplier: Multiplicador da skill usada
        critical: Se é um acerto crítico
    """
    # Fórmula base: (ATK * Skill) - DEF, mínimo 1
    base_damage = max(1, (attacker_power * skill_multiplier) - (defender_defense * 0.5))
    
    # Crítico dobra o dano
    if critical:
        base_damage *= 2.0
    
    # Adicionar variação de 10%
    variation = random.uniform(0.9, 1.1)
    final_damage = round(base_damage * variation, 1)
    
    return {
        "base_damage": round(base_damage, 1),
        "final_damage": final_damage,
        "critical": critical,
        "formula": f"({attacker_power} * {skill_multiplier}) - ({defender_defense} * 0.5)",
        "variation_applied": round(variation, 2)
    }


async def check_cultivation_success(
    player_tier: int,
    cultivation_method: str = "meditation",
    bonus_items: List[str] = None
) -> Dict[str, Any]:
    """
    Verifica se uma tentativa de cultivo foi bem-sucedida.
    
    Args:
        player_tier: Tier atual do jogador
        cultivation_method: meditation, pill, resource, training
        bonus_items: Lista de itens bônus usados
    """
    # Base chance diminui com o tier
    base_chance = max(5, 50 - (player_tier * 5))
    
    # Modificadores por método
    method_modifiers = {
        "meditation": 0,
        "pill": 20,
        "resource": 15,
        "training": 10,
        "spirit_vein": 30
    }
    
    method_bonus = method_modifiers.get(cultivation_method, 0)
    
    # Bônus de itens (simulado)
    item_bonus = len(bonus_items) * 5 if bonus_items else 0
    
    final_chance = min(95, base_chance + method_bonus + item_bonus)
    roll = random.randint(1, 100)
    success = roll <= final_chance
    
    # Qi ganho
    qi_gained = 0
    if success:
        qi_gained = random.randint(10, 30) * (1 + player_tier * 0.1)
        if cultivation_method == "pill":
            qi_gained *= 1.5
    
    return {
        "success": success,
        "roll": roll,
        "required": final_chance,
        "method": cultivation_method,
        "qi_gained": round(qi_gained, 1),
        "breakdown": {
            "base_chance": base_chance,
            "method_bonus": method_bonus,
            "item_bonus": item_bonus
        }
    }


# ==================== FERRAMENTAS DE ECONOMIA ====================

async def get_market_prices(location: str = "default") -> Dict[str, Any]:
    """Retorna preços do mercado em uma localização."""
    repo_root = Path(__file__).resolve().parents[3]
    items_path = repo_root / "ruleset_source/mechanics/items.json"
    
    # Modificadores por localização
    location_mods = {
        "Initial Village": 1.0,
        "Merchant City": 0.9,  # 10% desconto
        "Sword Sect": 1.1,     # 10% mais caro
        "Misty Forest": 1.2,   # 20% mais caro (remoto)
        "default": 1.0
    }
    
    modifier = location_mods.get(location, 1.0)
    
    if items_path.exists():
        with open(items_path, "r", encoding="utf-8") as f:
            items = json.load(f)
            prices = []
            for item in items[:20]:  # Limitar a 20 itens
                if "value" in item:
                    prices.append({
                        "name": item["name"],
                        "base_price": item["value"],
                        "local_price": round(item["value"] * modifier, 1),
                        "type": item.get("type", "misc")
                    })
            
            return {
                "location": location,
                "modifier": modifier,
                "prices": prices
            }
    
    return {"error": "Arquivo de itens não encontrado"}


async def calculate_transaction(
    item_name: str,
    quantity: int,
    action: str,  # buy ou sell
    player_gold: int,
    location: str = "default"
) -> Dict[str, Any]:
    """
    Calcula uma transação de compra/venda.
    
    Args:
        item_name: Nome do item
        quantity: Quantidade
        action: "buy" ou "sell"
        player_gold: Ouro atual do jogador
        location: Localização para modificador de preço
    """
    # Buscar item
    item_info = await get_item_info(item_name)
    
    if not item_info.get("found"):
        return {"success": False, "error": f"Item '{item_name}' não encontrado"}
    
    item = item_info.get("item", item_info.get("partial_matches", [{}])[0])
    base_price = item.get("value", 100)
    
    # Modificador de localização
    location_mods = {
        "Initial Village": 1.0,
        "Merchant City": 0.9,
        "Sword Sect": 1.1,
        "Misty Forest": 1.2,
        "default": 1.0
    }
    loc_mod = location_mods.get(location, 1.0)
    
    # Compra = preço cheio, Venda = 50% do preço
    if action == "buy":
        unit_price = round(base_price * loc_mod)
        total_cost = unit_price * quantity
        can_afford = player_gold >= total_cost
        new_gold = player_gold - total_cost if can_afford else player_gold
        
        return {
            "success": can_afford,
            "action": "buy",
            "item": item_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_cost": total_cost,
            "player_gold": player_gold,
            "new_gold": new_gold,
            "can_afford": can_afford
        }
    else:  # sell
        unit_price = round(base_price * loc_mod * 0.5)  # 50% do preço
        total_value = unit_price * quantity
        new_gold = player_gold + total_value
        
        return {
            "success": True,
            "action": "sell",
            "item": item_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_value": total_value,
            "player_gold": player_gold,
            "new_gold": new_gold
        }


# ==================== FERRAMENTAS DE NAVEGAÇÃO ====================

async def get_location_info(location_name: str) -> Dict[str, Any]:
    """Busca informações detalhadas sobre uma localização."""
    repo_root = Path(__file__).resolve().parents[3]
    locations_path = repo_root / "ruleset_source/lore_manual/locations_desc.md"
    
    # Tentar buscar no arquivo de descrições
    if locations_path.exists():
        content = locations_path.read_text(encoding="utf-8")
        if location_name.lower() in content.lower():
            idx = content.lower().find(location_name.lower())
            start = max(0, idx - 50)
            end = min(len(content), idx + 500)
            return {
                "found": True,
                "location": location_name,
                "description": content[start:end].strip()
            }
    
    # Fallback para localizações conhecidas
    known_locations = {
        "Initial Village": {
            "name": "Vila das Nuvens Brancas",
            "type": "village",
            "danger": "safe",
            "description": "Uma pequena vila pacífica aos pés das montanhas."
        },
        "Misty Forest": {
            "name": "Floresta Nublada",
            "type": "forest",
            "danger": "low",
            "description": "Uma floresta densa coberta por névoa mística."
        },
        "Dragon Mountains": {
            "name": "Montanhas do Dragão Adormecido",
            "type": "mountain",
            "danger": "moderate",
            "description": "Picos gelados onde antigos dragões supostamente dormem."
        },
        "Merchant City": {
            "name": "Cidade do Comércio Celestial",
            "type": "city",
            "danger": "safe",
            "description": "A maior cidade comercial da região."
        }
    }
    
    if location_name in known_locations:
        return {"found": True, "location": known_locations[location_name]}
    
    return {"found": False, "message": f"Localização '{location_name}' não encontrada"}


async def get_travel_options(current_location: str) -> Dict[str, Any]:
    """Retorna opções de viagem a partir de uma localização."""
    # Mapa de conexões simples
    connections = {
        "Initial Village": [
            {"destination": "Misty Forest", "travel_time": "2 hours", "danger": "low"},
            {"destination": "Merchant City", "travel_time": "1 day", "danger": "safe"},
        ],
        "Misty Forest": [
            {"destination": "Initial Village", "travel_time": "2 hours", "danger": "low"},
            {"destination": "Dragon Mountains", "travel_time": "6 hours", "danger": "moderate"},
            {"destination": "Spirit Lake", "travel_time": "4 hours", "danger": "low"},
        ],
        "Dragon Mountains": [
            {"destination": "Misty Forest", "travel_time": "6 hours", "danger": "moderate"},
            {"destination": "Ancient Ruins", "travel_time": "1 day", "danger": "high"},
        ],
        "Merchant City": [
            {"destination": "Initial Village", "travel_time": "1 day", "danger": "safe"},
            {"destination": "Sword Sect", "travel_time": "8 hours", "danger": "safe"},
            {"destination": "Poison Swamp", "travel_time": "2 days", "danger": "moderate"},
        ],
    }
    
    if current_location in connections:
        return {
            "current": current_location,
            "destinations": connections[current_location]
        }
    
    return {"error": f"Não há conexões conhecidas de '{current_location}'"}


# ==================== REGISTRO DE FERRAMENTAS ====================

def get_knowledge_tools() -> List[Tool]:
    """Retorna ferramentas de consulta de conhecimento."""
    return [
        Tool(
            name="search_lore",
            description="Busca informações no lore do mundo (cultivation, world, factions, history)",
            parameters={
                "query": {"type": "string", "description": "O que buscar"},
                "category": {"type": "string", "description": "all, cultivation, world, creatures"}
            },
            handler=search_lore
        ),
        Tool(
            name="get_cultivation_ranks",
            description="Retorna a lista de ranks de cultivo e seus requisitos",
            parameters={},
            handler=get_cultivation_ranks
        ),
        Tool(
            name="get_techniques",
            description="Retorna técnicas de um elemento específico",
            parameters={
                "element": {"type": "string", "description": "fire, water, earth, wind, lightning, etc"}
            },
            handler=get_techniques_by_element
        ),
        Tool(
            name="get_item_info",
            description="Busca informações sobre um item específico",
            parameters={
                "item_name": {"type": "string", "description": "Nome do item"}
            },
            handler=get_item_info
        ),
    ]


def get_mechanics_tools() -> List[Tool]:
    """Retorna ferramentas de mecânicas de jogo."""
    return [
        Tool(
            name="roll_dice",
            description="Rola dados no formato XdY (ex: 2d6, 1d20)",
            parameters={
                "dice": {"type": "string", "description": "Formato XdY"},
                "modifier": {"type": "integer", "description": "Modificador a adicionar", "default": 0}
            },
            handler=roll_dice
        ),
        Tool(
            name="calculate_damage",
            description="Calcula dano de um ataque baseado nas fórmulas do sistema",
            parameters={
                "attacker_power": {"type": "number", "description": "Poder de ataque"},
                "defender_defense": {"type": "number", "description": "Defesa do alvo"},
                "skill_multiplier": {"type": "number", "description": "Multiplicador da skill", "default": 1.0},
                "critical": {"type": "boolean", "description": "Se é crítico", "default": False}
            },
            handler=calculate_damage
        ),
        Tool(
            name="check_cultivation",
            description="Verifica sucesso de uma tentativa de cultivo",
            parameters={
                "player_tier": {"type": "integer", "description": "Tier atual do jogador"},
                "cultivation_method": {"type": "string", "description": "meditation, pill, resource, training"},
                "bonus_items": {"type": "array", "description": "Itens bônus usados"}
            },
            handler=check_cultivation_success
        ),
    ]


def get_economy_tools() -> List[Tool]:
    """Retorna ferramentas de economia."""
    return [
        Tool(
            name="get_market_prices",
            description="Retorna preços do mercado em uma localização",
            parameters={
                "location": {"type": "string", "description": "Nome da localização", "default": "default"}
            },
            handler=get_market_prices
        ),
        Tool(
            name="calculate_transaction",
            description="Calcula uma transação de compra/venda",
            parameters={
                "item_name": {"type": "string", "description": "Nome do item"},
                "quantity": {"type": "integer", "description": "Quantidade"},
                "action": {"type": "string", "description": "buy ou sell"},
                "player_gold": {"type": "integer", "description": "Ouro atual do jogador"},
                "location": {"type": "string", "description": "Localização", "default": "default"}
            },
            handler=calculate_transaction
        ),
    ]


def get_navigation_tools() -> List[Tool]:
    """Retorna ferramentas de navegação."""
    return [
        Tool(
            name="get_location_info",
            description="Busca informações detalhadas sobre uma localização",
            parameters={
                "location_name": {"type": "string", "description": "Nome da localização"}
            },
            handler=get_location_info
        ),
        Tool(
            name="get_travel_options",
            description="Retorna opções de viagem a partir de uma localização",
            parameters={
                "current_location": {"type": "string", "description": "Localização atual"}
            },
            handler=get_travel_options
        ),
    ]


def get_all_game_tools() -> List[Tool]:
    """Retorna todas as ferramentas de jogo."""
    return (
        get_knowledge_tools() +
        get_mechanics_tools() +
        get_economy_tools() +
        get_navigation_tools()
    )
