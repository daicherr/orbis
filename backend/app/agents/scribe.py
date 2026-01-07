from typing import Dict, Any, List
from app.services.gemini_client import GeminiClient

class Scribe:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.action_history: Dict[str, int] = {}

    def log_action(self, player_id: int, action_key: str):
        """Registra uma ação do jogador (ex: 'attack_fireball')."""
        key = f"{player_id}_{action_key}"
        self.action_history[key] = self.action_history.get(key, 0) + 1

    def check_for_epiphany(self, player_id: int, action_key: str) -> Optional[Dict[str, Any]]:
        """Verifica se o jogador teve uma epifania e gera uma nova habilidade."""
        key = f"{player_id}_{action_key}"
        count = self.action_history.get(key, 0)

        # Epifania ocorre após 5 usos da mesma ação
        if count == 5:
            print(f"EPIFANIA! Jogador {player_id} teve uma ideia para uma nova habilidade baseada em {action_key}.")
            return self._generate_new_skill(action_key)
        
        return None

    def _generate_new_skill(self, base_action: str) -> Dict[str, Any]:
        """Usa a IA para gerar uma nova habilidade baseada em uma ação repetida."""
        
        prompt = (
            f"Você é um mestre de RPG criando uma nova habilidade (technique) para um jogador. "
            f"O jogador teve uma epifania ao repetir a ação: '{base_action}'. "
            f"Crie uma nova habilidade que seja uma versão mais poderosa ou uma variação interessante desta ação. "
            f"Responda com um objeto JSON contendo 'id', 'name', 'description', 'cost_type', 'cost_amount', 'base_damage', e 'effects'.\n\n"
            f"Exemplo de Ação Base: 'attack_fireball'\n"
            f"Exemplo de Habilidade Gerada: {{'id': 'inferno_burst', 'name': 'Explosão Infernal', ...}}\n\n"
            f"--- JSON da Nova Habilidade ---"
        )
        
        new_skill = self.gemini_client.generate_json(prompt, task="story")
        # Lógica para salvar a nova skill em techniques.json ou no perfil do jogador
        print(f"Nova habilidade gerada: {new_skill.get('name')}")
        return new_skill
