from typing import List
import threading


class EmbeddingService:
    """
    Sprint 14: Embedding service com lazy loading.
    O modelo só é carregado na primeira chamada, não no startup.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        
        self._model = None
        self._model_loaded = False
        self.dim = 384  # Dimensão padrão do modelo real
        self._initialized = True
    
    def _load_model(self):
        """Carrega o modelo de embedding (lazy loading)."""
        if self._model_loaded:
            return
        
        with self._lock:
            if self._model_loaded:
                return
            
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                print("EmbeddingService: carregando modelo sentence-transformers...")
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                self.dim = 384
                print("EmbeddingService: modelo all-MiniLM-L6-v2 carregado.")
            except Exception as e:
                print(f"EmbeddingService: fallback mock (erro: {e})")
                self._model = None
                self.dim = 128
            
            self._model_loaded = True

    def generate_embedding(self, text: str) -> List[float]:
        """Gera embedding (384D com modelo real; 128D no fallback)."""
        # Lazy load do modelo
        if not self._model_loaded:
            self._load_model()
        
        if self._model is not None:
            vec = self._model.encode(text, normalize_embeddings=True)
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
    
    def is_loaded(self) -> bool:
        """Verifica se o modelo já foi carregado."""
        return self._model_loaded
    
    def preload(self):
        """Pré-carrega o modelo (útil para warmup)."""
        self._load_model()


# Singleton global para reuso
embedding_service = EmbeddingService()
