"""Teste do histórico com scene_description"""
import requests

history = requests.get('http://localhost:8000/player/18/history?limit=3').json()
print('HISTORICO COM SCENE_DESCRIPTION:')
for log in history:
    print(f"\nTurno {log.get('turn_number')}:")
    scene = log.get('scene_description')
    if scene:
        print(f"  scene_description: {scene[:200]}...")
    else:
        print(f"  scene_description: NONE")
    result = log.get('action_result')
    if result:
        print(f"  action_result: {result[:150]}...")
    else:
        print(f"  action_result: NONE")
