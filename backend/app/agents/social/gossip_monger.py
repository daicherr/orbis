"""
Gossip Monger - Social Web System
Gera rumores baseados em eventos do mundo (Sprint 6)
"""

from typing import Dict, Any, List
from app.services.gemini_client import GeminiClient
import random

class GossipMonger:
    """
    Sistema de rumores e reputação.
    
    Funcionalidades:
    - Gera rumores baseados em eventos do mundo
    - Rumores se espalham entre localizações
    - NPCs comentam sobre ações do player
    - Reputação afeta diálogos e quests
    
    [SPRINT 6] Sistema social expandido.
    """
    
    def __init__(self, gemini_client: GeminiClient = None):
        self.gemini_client = gemini_client
        
        # Event Queue (eventos aguardando para virar rumores)
        self.event_queue: List[Dict[str, Any]] = []
        
        # Rumor Pool (rumores ativos por localização)
        self.rumors_by_location: Dict[str, List[Dict[str, Any]]] = {}
        
        # Reputação do player por facção/localização
        self.reputation: Dict[str, int] = {
            "Vila Crisântemos": 0,
            "Floresta Nublada": 0,
            "Cidade Imperial": 0,
            "Templo Abismo": 0,
            "Montanha Arcaica": 0,
            "Cidade Subterrânea": 0,
            "Cavernas Cristalinas": 0,
            "Passo da Montanha": 0
        }
    
    def add_event(self, event: Dict[str, Any]):
        """
        Adiciona um evento à fila para processamento.
        
        Args:
            event: {
                "type": "npc_death" | "kill" | "betrayal" | "breakthrough",
                "actor": str (nome do player),
                "victim"/"target": str (nome do NPC),
                "location": str,
                "cultivation_tier": int
            }
        """
        
        self.event_queue.append(event)
        print(f"[GOSSIP] GossipMonger: Novo evento registrado - {event['type']} em {event.get('location', 'Unknown')}")
    
    async def process_events(self) -> List[str]:
        """
        Processa eventos da fila e gera rumores.
        
        Returns:
            Lista de rumores gerados (strings literárias)
        """
        
        new_rumors = []
        
        while self.event_queue:
            event = self.event_queue.pop(0)
            rumor = await self._generate_rumor_async(event)
            
            if rumor:
                # Adicionar rumor à localização
                location = event.get("location", "Vila Crisântemos")
                
                if location not in self.rumors_by_location:
                    self.rumors_by_location[location] = []
                
                self.rumors_by_location[location].append({
                    "text": rumor,
                    "age": 0,
                    "spread_factor": 1.0
                })
                
                new_rumors.append(rumor)
                
                # Atualizar reputação
                self._update_reputation(event)
        
        return new_rumors
    
    def generate_rumor(self, event: Dict[str, Any]) -> str:
        """
        [LEGACY] Método síncrono para backward compatibility.
        Gera rumor baseado em templates simples.
        """
        
        event_type = event.get("type")
        actor = event.get("actor")
        target = event.get("target") or event.get("victim")
        location = event.get("location", "lugar desconhecido")

        if event_type == "kill" or event_type == "npc_death":
            return f"Dizem que {actor} derrotou {target} em {location}. Alguns chamam de justiça, outros de assassinato."
        elif event_type == "theft":
            return f"Mercadores sussurram: {actor} roubou algo valioso de {target} em {location}!"
        elif event_type == "faction_war_start":
            return f"A guerra eclode! {actor} declarou combate contra {target}!"
        elif event_type == "breakthrough":
            return f"Uma explosão de Qi sacudiu {location}. Dizem que {actor} alcançou novo poder!"
        else:
            return "Rumores estranhos circulam pelas tavernas..."
    
    async def _generate_rumor_async(self, event: Dict[str, Any]) -> str:
        """Gera rumor usando IA se disponível, senão usa template."""
        
        # Tentar gerar com IA
        if self.gemini_client:
            try:
                prompt = self._build_rumor_prompt(event)
                if prompt:
                    rumor = await self.gemini_client.generate_content_async(
                        prompt=prompt,
                        model_type="flash"
                    )
                    return rumor.strip()
            except Exception as e:
                print(f"GossipMonger: Erro ao gerar rumor com IA: {e}")
        
        # Fallback: usar template
        return self.generate_rumor(event)
    
    def _build_rumor_prompt(self, event: Dict[str, Any]) -> str:
        """Cria prompt para IA."""
        
        event_type = event.get("type")
        actor = event.get("actor")
        victim = event.get("victim") or event.get("target")
        location = event.get("location", "lugar desconhecido")
        
        if event_type in ["npc_death", "kill"]:
            return f"""
Você é um narrador de rumores em um mundo de cultivação xianxia.
Um evento ocorreu: {actor} derrotou {victim} em {location}.

Escreva UM rumor curto (1-2 frases) que NPCs contariam.
O rumor deve ser ambíguo, literário e provocativo.

Exemplo: "Dizem que {actor} emergiu de {location} com sangue nas mãos."

Escreva em português brasileiro:
"""
        
        return ""
    
    def _update_reputation(self, event: Dict[str, Any]):
        """Atualiza reputação baseado no evento."""
        
        event_type = event.get("type")
        location = event.get("location", "Vila Crisântemos")
        
        if event_type in ["npc_death", "kill"]:
            victim_name = event.get("victim") or event.get("target", "")
            
            if any(word in victim_name for word in ["Demônio", "Demon", "Vil", "Evil"]):
                self.reputation[location] += 10
            else:
                self.reputation[location] -= 15
        
        elif event_type == "breakthrough":
            self.reputation[location] += 5
        
        elif event_type == "betrayal":
            self.reputation[location] -= 30
    
    def get_rumors(self, location: str, max_rumors: int = 3) -> List[str]:
        """Retorna rumores ativos em uma localização."""
        
        if location not in self.rumors_by_location:
            return []
        
        rumors = self.rumors_by_location[location]
        rumors.sort(key=lambda r: r["age"])
        
        return [r["text"] for r in rumors[:max_rumors]]
    
    def spread_rumor(self, rumor: str, npcs: List[Any]):
        """[LEGACY] Espalha rumor para NPCs."""
        print(f"Espalhando rumor para {len(npcs)} NPCs...")
    
    def spread_rumors(self):
        """Espalha rumores para localizações vizinhas."""
        
        connections = {
            "Vila Crisântemos": ["Floresta Nublada", "Cidade Imperial"],
            "Floresta Nublada": ["Vila Crisântemos", "Cavernas Cristalinas"],
            "Cidade Imperial": ["Vila Crisântemos", "Templo Abismo"],
        }
        
        for location, rumors in self.rumors_by_location.items():
            for rumor in rumors:
                if random.random() < 0.4:
                    neighbors = connections.get(location, [])
                    
                    for neighbor in neighbors:
                        if neighbor not in self.rumors_by_location:
                            self.rumors_by_location[neighbor] = []
                        
                        self.rumors_by_location[neighbor].append({
                            "text": rumor["text"],
                            "age": rumor["age"] + 1,
                            "spread_factor": rumor["spread_factor"] * 0.7
                        })
                
                rumor["age"] += 1
        
        # Remover rumores antigos
        for location in list(self.rumors_by_location.keys()):
            self.rumors_by_location[location] = [
                r for r in self.rumors_by_location[location] if r["age"] <= 10
            ]
    
    def get_reputation(self, location: str) -> int:
        """Retorna reputação em uma localização."""
        return self.reputation.get(location, 0)
    
    def get_reputation_title(self, location: str) -> str:
        """Retorna título de reputação."""
        
        rep = self.get_reputation(location)
        
        if rep >= 50:
            return "Herói Reverenciado"
        elif rep >= 30:
            return "Cultivador Respeitado"
        elif rep >= 10:
            return "Conhecido"
        elif rep >= -10:
            return "Desconhecido"
        elif rep >= -30:
            return "Suspeito"
        elif rep >= -50:
            return "Criminoso Procurado"
        else:
            return "Vilão Caçado"

