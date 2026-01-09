"""Análise dos logs do Yi Fan"""
import requests

BASE_URL = "http://localhost:8000"

# Buscar player 14 (Yi Fan original)
player_id = 14
player = requests.get(f"{BASE_URL}/player/{player_id}").json()

print("=" * 70)
print(f" YI FAN (ID {player_id})")
print("=" * 70)
print(f"Nome: {player.get('name')}")
print(f"Location: {player.get('current_location')}")
print(f"Origin: {player.get('origin_location')}")
print(f"\nBackstory:")
print(player.get('backstory', 'N/A'))

# Buscar histórico
history = requests.get(f"{BASE_URL}/player/{player_id}/history?limit=20").json()

print(f"\n{'=' * 70}")
print(f" HISTÓRICO DE TURNOS ({len(history)} turnos)")
print("=" * 70)

for log in sorted(history, key=lambda x: x.get('turn_number', 0)):
    print(f"\n{'=' * 60}")
    print(f"TURNO {log.get('turn_number')} | {log.get('world_time')} | {log.get('location')}")
    print("=" * 60)
    
    print(f"\n[INPUT]: {log.get('player_input', 'N/A')}")
    
    scene = log.get('scene_description', '')
    if scene:
        print(f"\n[NARRAÇÃO]:")
        print(scene)
    else:
        print(f"\n[NARRAÇÃO]: (VAZIO)")
    
    result = log.get('action_result', '')
    if result:
        print(f"\n[RESULTADO]: {result}")
    
    npcs = log.get('npcs_present')
    if npcs:
        print(f"\n[NPCs]: {npcs}")
