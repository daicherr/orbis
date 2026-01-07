import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


def _repo_root() -> Path:
    # backend/app/core/skill_manager.py -> repo root
    return Path(__file__).resolve().parents[3]


def _resolve_repo_path(path_str: str) -> str:
    p = Path(path_str)
    if p.is_absolute():
        return str(p)
    return str((_repo_root() / p).resolve())

class SkillManager:
    def __init__(self, techniques_file_path: str):
        self.skills: Dict[str, Dict[str, Any]] = self._load_skills(_resolve_repo_path(techniques_file_path))

    def _load_skills(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        """Carrega as habilidades do arquivo JSON e as armazena em um dicionário."""
        if not os.path.exists(file_path):
            print(f"Error: Skill file not found at {file_path}")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            skill_list = json.load(f)
        
        # Converte a lista de skills em um dicionário para acesso rápido por ID
        return {skill['id']: skill for skill in skill_list}

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Retorna os dados de uma habilidade específica pelo seu ID."""
        return self.skills.get(skill_id)

    def is_silent_art(self, skill_id: str) -> bool:
        """Verifica se uma habilidade é uma 'Silent Art'."""
        skill = self.get_skill(skill_id)
        return skill.get('silent_art', False) if skill else False

# Instância global para ser usada em toda a aplicação
skill_manager = SkillManager(techniques_file_path="ruleset_source/mechanics/techniques.json")
