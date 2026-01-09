"""Teste rápido de todos os endpoints"""
import requests
import json
import sys

BASE = 'http://localhost:8000'

def test_basic_endpoints():
    print('='*60)
    print('1. TESTANDO ENDPOINTS BASICOS')
    print('='*60)
    
    # Health
    r = requests.get(f'{BASE}/health')
    print(f'[OK] GET /health: {r.status_code}')
    
    # NPCs
    r = requests.get(f'{BASE}/npc/list/all')
    print(f'[OK] GET /npc/list/all: {r.status_code} - {len(r.json())} NPCs')
    
    # Players
    r = requests.get(f'{BASE}/player/list/all')
    print(f'[OK] GET /player/list/all: {r.status_code} - {len(r.json())} players')
    
    return True

def test_character_creation():
    print('\n' + '='*60)
    print('2. TESTANDO CRIACAO DE PERSONAGEM')
    print('='*60)
    
    payload = {
        'name': 'TesteCompleto2',
        'constitution': 'Human',
        'appearance': 'Um jovem de olhos escuros',
        'origin_location': 'Vila das Nuvens',
        'session_zero_answers': [
            'Meu nome e TesteCompleto2',
            'Sou um escravo crianca que nunca cultivou',
            'Tenho um irmao chamado Wei Ming',
            'Quero ficar forte',
            'Minha casa e um barraco simples'
        ]
    }
    
    print('Enviando requisicao...')
    r = requests.post(f'{BASE}/player/create-full', json=payload, timeout=120)
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        print(f'  Player ID: {data.get("id")}')
        print(f'  Nome: {data.get("name")}')
        print(f'  Skills: {data.get("learned_skills")}')
        print(f'  Localizacao: {data.get("current_location")}')
        print(f'  Home: {data.get("home_location")}')
        
        feedback = data.get('creation_feedback', {})
        print(f'\n  Feedback de criacao:')
        print(f'    Has Skills: {feedback.get("has_initial_skills")}')
        print(f'    NPC criado: {feedback.get("important_npc_created")}')
        first_scene = feedback.get("first_scene_narration", "")
        print(f'    First Scene: {len(first_scene)} chars')
        
        return data.get("id")
    else:
        print(f'ERRO: {r.text[:500]}')
        return None

def test_game_turn(player_id):
    print('\n' + '='*60)
    print('3. TESTANDO TURNO DE JOGO')
    print('='*60)
    
    if not player_id:
        print('[SKIP] Sem player_id')
        return False
    
    # Endpoint usa query params, não JSON body
    params = {
        "player_id": player_id,
        "player_input": "Olho ao redor tentando entender onde estou"
    }
    
    print(f'Executando turno para player {player_id}...')
    r = requests.post(f'{BASE}/game/turn', params=params, timeout=120)
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        narration = data.get('narration', '')
        print(f'  Narração: {len(narration)} chars')
        print(f'  Primeiros 200 chars: {narration[:200]}...')
        return True
    else:
        print(f'ERRO: {r.text[:300]}')
        return False

def test_npc_interaction(player_id):
    print('\n' + '='*60)
    print('4. TESTANDO INTERACAO COM NPC')
    print('='*60)
    
    # Buscar um NPC
    r = requests.get(f'{BASE}/npc/list/all')
    npcs = r.json()
    if not npcs:
        print('[SKIP] Sem NPCs')
        return False
    
    npc = npcs[0]
    print(f'  NPC escolhido: {npc["name"]} (ID: {npc["id"]})')
    
    # Observar NPC
    r = requests.get(f'{BASE}/npc/{npc["id"]}/observe?player_id={player_id}')
    print(f'  GET /npc/{npc["id"]}/observe: {r.status_code}')
    
    return True

def test_combat(player_id):
    print('\n' + '='*60)
    print('5. TESTANDO COMBATE')
    print('='*60)
    
    if not player_id:
        print('[SKIP] Sem player_id')
        return False
    
    # Buscar um NPC hostil ou qualquer um
    r = requests.get(f'{BASE}/npc/list/all')
    npcs = r.json()
    if not npcs:
        print('[SKIP] Sem NPCs')
        return False
    
    npc = npcs[0]
    
    # Endpoint usa query params
    params = {
        "player_id": player_id,
        "player_input": f"Eu ataco {npc['name']} com um soco!"
    }
    
    print(f'Atacando {npc["name"]}...')
    r = requests.post(f'{BASE}/game/turn', params=params, timeout=120)
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        action_result = data.get('action_result', '')
        print(f'  Action Result: {action_result[:300]}...' if len(action_result) > 300 else f'  Action Result: {action_result}')
        
        # Verificar se houve contra-ataque (Sprint 17)
        if 'contra-atac' in action_result.lower():
            print('  [SPRINT 17] Contra-ataque detectado!')
        return True
    else:
        print(f'ERRO: {r.text[:300]}')
        return False

if __name__ == '__main__':
    print('='*60)
    print(' SUITE DE TESTES COMPLETA - RPG CULTIVO')
    print('='*60)
    
    try:
        # 1. Endpoints básicos
        test_basic_endpoints()
        
        # 2. Criação de personagem
        player_id = test_character_creation()
        
        # 3. Turno de jogo
        test_game_turn(player_id)
        
        # 4. Interação com NPC
        test_npc_interaction(player_id)
        
        # 5. Combate
        test_combat(player_id)
        
        print('\n' + '='*60)
        print(' TESTES CONCLUIDOS')
        print('='*60)
        
    except Exception as e:
        print(f'\nERRO FATAL: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
