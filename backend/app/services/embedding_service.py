from typing import List


class EmbeddingService:
    def __init__(self):
        """Carrega sentence-transformers se disponível, caso contrário usa fallback simples.
        """
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            # Modelo leve e popular para embeddings semânticos
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.dim = 384
            print("EmbeddingService: usando sentence-transformers (all-MiniLM-L6-v2).")
        except Exception:
            self.dim = 128
            print("EmbeddingService: fallback mock (sentence-transformers não disponível).")

    def generate_embedding(self, text: str) -> List[float]:
        """Gera embedding (384D com modelo real; 128D no fallback)."""
        if self.model is not None:
            vec = self.model.encode(text, normalize_embeddings=True)
            return vec.tolist()

        # Fallback simples determinístico
        t = text.lower()
        vec = [0.0] * self.dim
        if "ajudou" in t or "obrigado" in t:
            vec[0] = 0.9
        if "atacou" in t or "odeio" in t:
            vec[1] = 0.9
        if "comprar" in t or "vender" in t:
            vec[2] = 0.9
        return vec
