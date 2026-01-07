import json
import os
from typing import Dict, Any, List

class DataManager:

    @staticmethod
    def _read_json_file(file_path: str) -> Any:
        """Lê um arquivo JSON, retornando uma lista ou dicionário vazio se não existir."""
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return [] if file_path.endswith('s.json') else {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] if file_path.endswith('s.json') else {}

    @staticmethod
    def _write_json_file(file_path: str, data: Any):
        """Escreve dados em um arquivo JSON com formatação."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def append_to_list_json(cls, file_path: str, new_entry: Dict):
        """Adiciona uma nova entrada a um arquivo JSON que contém uma lista."""
        data = cls._read_json_file(file_path)
        if not isinstance(data, list):
            print(f"Aviso: O arquivo {file_path} não continha uma lista. O conteúdo será sobrescrito.")
            data = []
        data.append(new_entry)
        cls._write_json_file(file_path, data)
        print(f"Nova entrada adicionada a {file_path}.")

    @classmethod
    def update_dict_json(cls, file_path: str, key: str, value: Any):
        """Adiciona ou atualiza um par chave-valor em um arquivo JSON que contém um dicionário."""
        data = cls._read_json_file(file_path)
        if not isinstance(data, dict):
            print(f"Aviso: O arquivo {file_path} não continha um dicionário. O conteúdo será sobrescrito.")
            data = {}
        data[key] = value
        cls._write_json_file(file_path, data)
        print(f"Chave '{key}' adicionada/atualizada em {file_path}.")

# Instância global para fácil acesso
data_manager = DataManager()
