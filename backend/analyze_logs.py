"""Análise de logs do player 'teste'"""
import requests

BASE_URL = "http://localhost:8000"

# Buscar todos os players
players = requests.get(f"{BASE_URL}/player/list/all").json()

# Filtrar player teste
teste_players = [p for p in players if 'teste' in p['name'].lower()]

print("=" * 60)
print(" PLAYERS COM 'TESTE' NO NOME")
print("=" * 60)

for p in teste_players:
    print(f"ID: {p['id']}")
    print(f"Nome: {p['name']}")
    print(f"Location: {p['current_location']}")
    print(f"HP: {p['current_hp']}/{p['max_hp']}")
    print(f"Skills: {p['learned_skills']}")
    print("-" * 40)

# Buscar histórico do primeiro player teste
if teste_players:
    player_id = teste_players[0]['id']
    print(f"\n{'=' * 60}")
    print(f" HISTÓRICO DE LOGS - Player ID {player_id}")
    print("=" * 60)
    
    history = requests.get(f"{BASE_URL}/player/{player_id}/history").json()
    
    if isinstance(history, list):
        for log in history:
            print(f"\n--- TURNO {log.get('turn_number', '?')} ---")
            print(f"Tempo: {log.get('world_time', 'None')}")
            print(f"Location: {log.get('location', 'None')}")
            print(f"Input: {log.get('player_input', 'None')[:100] if log.get('player_input') else 'None'}...")
            print(f"Narração: {log.get('scene_description', 'None')[:200] if log.get('scene_description') else 'None'}...")
            print(f"Resultado: {log.get('action_result', 'None')}")
            print(f"NPCs: {log.get('npcs_present', 'None')}")
    else:
        print(f"Resposta: {history}")
else:
    print("Nenhum player 'teste' encontrado!")
