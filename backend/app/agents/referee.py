from typing import List, Dict, Any
from app.database.models.player import Player
from app.database.models.npc import NPC
from app.services.gemini_client import GeminiClient

class Referee:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client

    def parse_player_action(
        self,
        player_input: str,
        player: Player,
        possible_targets: List[NPC]
    ) -> Dict[str, Any]:
        """
        Traduz o input em texto do jogador em uma ação mecânica estruturada
        usando o Gemini para extrair a intenção e as entidades.
        """
        target_names = ", ".join([npc.name for npc in possible_targets])

        prompt = (
            f"Você é um juiz de RPG (referee) que analisa a ação de um jogador. "
            f"Seu trabalho é converter o texto do jogador em um objeto JSON estruturado. "
            f"Analise o texto e preencha o JSON com as seguintes chaves:\n"
            f"- 'intent': A intenção principal do jogador. Válidas são: 'attack', 'talk', 'move', 'use_item', 'observe', 'unknown'.\n"
            f"- 'target_name': O nome exato do alvo da ação. Deve ser um dos 'Alvos Possíveis'. Se nenhum alvo for mencionado, deixe como null.\n"
            f"- 'skill_name': O nome da habilidade ou técnica usada, se mencionada. Se nenhuma for mencionada, deixe como null.\n"
            f"Seja rigoroso. Se uma informação não estiver claramente no texto, use null.\n\n"
            f"--- Contexto ---\n"
            f"Alvos Possíveis: {target_names}\n"
            f"Texto do Jogador: \"{player_input}\"\n\n"
            f"--- JSON de Saída ---\n"
        )

        print(f"--- Analisando a ação do jogador via Gemini: '{player_input}' ---")
        
        # Chamada real ao Gemini para gerar o JSON
        action_data = self.gemini_client.generate_json(prompt)

        # Validação básica da resposta
        if not isinstance(action_data, dict) or "intent" not in action_data:
            return {"intent": "unknown", "target_name": None, "skill_name": None, "error": "Invalid response from AI"}

        return action_data
