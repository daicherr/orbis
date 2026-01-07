from google import genai
from app.config import settings
import json
from typing import Literal


GeminiTask = Literal["story", "combat", "fast", "default"]


class GeminiClient:
    def __init__(self):
        self._ai_enabled = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY")
        if not self._ai_enabled:
            self.client = None
            print("Aviso: GEMINI_API_KEY ausente. Rodando em modo 'AI desativada'.")
        else:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        # Modelo padrão compatível com o SDK novo (usa prefixo 'models/')
        self.model_name = (
            getattr(settings, "GEMINI_MODEL_DEFAULT", None)
            or getattr(settings, "GEMINI_MODEL", None)
            or "models/gemini-2.5-flash-preview-09-2025"
        )

        self._task_models: dict[str, str] = {
            "default": self.model_name,
            "story": getattr(settings, "GEMINI_MODEL_STORY", None) or self.model_name,
            "combat": getattr(settings, "GEMINI_MODEL_COMBAT", None) or self.model_name,
            "fast": getattr(settings, "GEMINI_MODEL_FAST", None) or self.model_name,
        }

    def _resolve_model(self, model: str | None = None, task: GeminiTask | None = None) -> str:
        if model:
            return model
        if task and task in self._task_models:
            return self._task_models[task]
        return self.model_name

    def list_models(self) -> list[dict]:
        """Retorna os modelos disponíveis com seus métodos suportados."""
        models = []
        try:
            for m in self.client.models.list():
                models.append({
                    "name": m.name,
                    "input_token_limit": getattr(m, "input_token_limit", None),
                    "output_token_limit": getattr(m, "output_token_limit", None),
                    "supported_generation_methods": getattr(m, "supported_generation_methods", None),
                })
        except Exception as e:
            print(f"Failed to list Gemini models: {e}")
        return models

    def generate_text(self, prompt: str, *, model: str | None = None, task: GeminiTask | None = None) -> str:
        """Gera texto a partir de um prompt usando o modelo Gemini (SDK google.genai)."""
        try:
            if self.client is None:
                # Modo offline para testes locais
                if task == "story":
                    return "(AI desativada) Você observa o ambiente, o vento corta as árvores e a floresta parece prender a respiração."
                return "(AI desativada)"
            resolved_model = self._resolve_model(model=model, task=task)
            resp = self.client.models.generate_content(
                model=resolved_model,
                contents=prompt,
            )
            # Resposta do SDK já expõe .text
            return getattr(resp, "text", "")
        except Exception as e:
            msg = str(e)
            print(f"An error occurred with the Gemini API: {e}")
            # Se a chave estiver inválida (ou auth falhar), desativa IA e continua o jogo.
            if "API_KEY_INVALID" in msg or "API key not valid" in msg or "UNAUTHENTICATED" in msg:
                self.client = None
                if task == "story":
                    return "(AI indisponível) A cena se desenha diante de você: sombras longas, ar frio e um silêncio inquietante." 
                return "(AI indisponível)"
            # Para o jogo não exibir stack/erro cru
            if task == "story":
                return "(IA instável) O mundo ao seu redor parece distorcido por um instante, mas você segue adiante." 
            return "(IA instável)"

    def generate_json(self, prompt: str, *, model: str | None = None, task: GeminiTask | None = None) -> dict:
        """Gera uma resposta em formato JSON; tenta parsear o texto retornado."""
        try:
            if self.client is None:
                # Modo offline para testes locais
                if task == "combat":
                    return {"intent": "unknown", "target_name": None, "skill_name": None}
                return {"error": "AI disabled"}
            json_prompt = f"{prompt}\n\nResponda apenas com um único objeto JSON válido, sem explicações."
            resolved_model = self._resolve_model(model=model, task=task)
            resp = self.client.models.generate_content(
                model=resolved_model,
                contents=json_prompt,
            )
            text = getattr(resp, "text", "").strip()
            cleaned = text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON from Gemini response: {e}")
            print(f"Raw response was: {text if 'text' in locals() else ''}")
            return {"error": "Failed to parse JSON response."}
        except Exception as e:
            msg = str(e)
            print(f"An error occurred with the Gemini API: {e}")
            if "API_KEY_INVALID" in msg or "API key not valid" in msg or "UNAUTHENTICATED" in msg:
                self.client = None
                if task == "combat":
                    return {"intent": "unknown", "target_name": None, "skill_name": None}
                return {"error": "AI unavailable"}
            return {"error": f"An error occurred: {e}"}

# Exemplo de uso (não será executado diretamente)
# if __name__ == '__main__':
#     # Carregar .env (requer python-dotenv)
#     from dotenv import load_dotenv
#     load_dotenv()
#
#     try:
#         client = GeminiClient()
#         test_prompt = "Descreva um item mágico chamado 'Orbe do Trovão' em 2 frases."
#         result = client.generate_text(test_prompt)
#         print("--- Teste de Geração de Texto ---")
#         print(result)
#
#         json_prompt = "Gere os stats de um 'Goblin Warrior' em JSON com chaves 'hp', 'attack', 'defense'."
#         json_result = client.generate_json(json_prompt)
#         print("\n--- Teste de Geração de JSON ---")
#         print(json_result)
#
#     except ValueError as e:
#         print(e)
