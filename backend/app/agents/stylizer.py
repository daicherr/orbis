from app.database.models.npc import NPC
from app.services.gemini_client import GeminiClient

class Stylizer:

    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client

    def generate_npc_description(self, npc: NPC) -> str:
        """
        Gera uma descrição literária e estilizada de um NPC usando IA.
        """
        
        prompt = (
            f"Você é um escritor de romances de cultivo (xianxia). "
            f"Descreva a aparência, a aura e os maneirismos do seguinte NPC em um parágrafo curto e evocativo. "
            f"Seja criativo e use o estilo do gênero.\n\n"
            f"--- Ficha do NPC ---\n"
            f"Nome: {npc.name}\n"
            f"Rank: {npc.rank}\n"
            f"Estado Emocional: {npc.emotional_state}\n"
            f"Traços de Personalidade: {', '.join(npc.personality_traits)}\n\n"
            f"--- Descrição Literária ---\n"
        )

        print(f"--- Gerando descrição estilizada para {npc.name} via Gemini ---")
        
        description = self.gemini_client.generate_text(prompt)
        
        return description
