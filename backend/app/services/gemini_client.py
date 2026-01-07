import google.generativeai as genai
from app.config import settings
import json

class GeminiClient:
    def __init__(self):
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
            raise ValueError("GEMINI_API_KEY not found in .env file or is not set.")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def generate_text(self, prompt: str) -> str:
        """
        Gera texto a partir de um prompt usando o modelo Gemini.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"An error occurred with the Gemini API: {e}")
            return f"Error: Could not generate text. Details: {e}"

    def generate_json(self, prompt: str) -> dict:
        """
        Gera uma resposta em formato JSON a partir de um prompt,
        instruindo o modelo a formatar sua saída.
        """
        try:
            # Adicionando instrução para garantir a saída JSON
            json_prompt = f"{prompt}\n\nPor favor, responda apenas com um objeto JSON válido."
            response = self.model.generate_content(json_prompt)
            
            # Limpeza básica para extrair o JSON
            cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
            
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON from Gemini response: {e}")
            print(f"Raw response was: {response.text}")
            return {"error": "Failed to parse JSON response."}
        except Exception as e:
            print(f"An error occurred with the Gemini API: {e}")
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
