# from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    def __init__(self):
        # Em uma implementação real, carregaríamos um modelo pré-treinado.
        # Ex: self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("EmbeddingService inicializado (modo mock).")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Gera um vetor de embedding para um dado texto.
        """
        # Esta é uma simulação. O vetor real teria centenas de dimensões.
        # A posição dos valores seria determinada pelo modelo de embedding.
        text = text.lower()
        vector = [0.0] * 128 # Simula um vetor de 128 dimensões
        
        if "ajudou" in text or "obrigado" in text:
            vector[0] = 0.9
        if "atacou" in text or "odeio" in text:
            vector[1] = 0.9
        if "comprar" in text or "vender" in text:
            vector[2] = 0.9
            
        # hash_val = hash(text)
        # for i in range(4, 10):
        #     vector[i] = (hash_val >> (i*8)) & 0xff / 255.0
            
        print(f"Gerado embedding simulado para o texto: '{text}'")
        return vector
