"""
Sprint 14: LoreCache - Cache singleton para contexto de lore.

Carrega os arquivos de lore uma única vez e mantém em memória.
Reduz tempo de startup ao evitar recarregamentos desnecessários.
"""

import os
from pathlib import Path
from typing import Optional
import threading


class LoreCache:
    """
    Singleton para cache de lore do mundo.
    Thread-safe e lazy loading.
    """
    _instance: Optional["LoreCache"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._lore_context: Optional[str] = None
        self._lore_snippets: dict[str, str] = {}
        self._initialized = True
    
    def _get_lore_path(self) -> Path:
        """Retorna o caminho para os arquivos de lore."""
        repo_root = Path(__file__).resolve().parents[3]
        return repo_root / 'ruleset_source' / 'lore_manual'
    
    def load(self, force_reload: bool = False) -> str:
        """
        Carrega o contexto de lore.
        
        Args:
            force_reload: Se True, recarrega mesmo se já carregado.
            
        Returns:
            String com todo o contexto de lore concatenado.
        """
        if self._lore_context is not None and not force_reload:
            return self._lore_context
        
        print("[LORE CACHE] Carregando contexto de lore...")
        context_parts = []
        lore_path = self._get_lore_path()
        
        if os.path.exists(lore_path):
            for filename in sorted(os.listdir(str(lore_path))):
                if filename.endswith(".md"):
                    file_path = lore_path / filename
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self._lore_snippets[filename] = content
                        context_parts.append(f"--- {filename.upper()} ---\n{content}\n")
        
        self._lore_context = "\n".join(context_parts)
        print(f"[LORE CACHE] {len(self._lore_snippets)} arquivos carregados.")
        return self._lore_context
    
    def get_snippet(self, filename: str) -> Optional[str]:
        """Retorna um arquivo de lore específico."""
        if not self._lore_snippets:
            self.load()
        return self._lore_snippets.get(filename)
    
    def get_context(self, max_chars: int = 0) -> str:
        """
        Retorna o contexto de lore, opcionalmente truncado.
        
        Args:
            max_chars: Limite de caracteres (0 = sem limite)
        """
        context = self.load()
        if max_chars > 0:
            return context[:max_chars]
        return context
    
    def is_loaded(self) -> bool:
        """Verifica se o lore já foi carregado."""
        return self._lore_context is not None
    
    def clear(self):
        """Limpa o cache (útil para testes)."""
        self._lore_context = None
        self._lore_snippets = {}


# Singleton global
lore_cache = LoreCache()
