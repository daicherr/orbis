"""
SUITE DE VALIDAÇÃO COMPLETA - RPG CULTIVO
Testa todos os endpoints e fluxos do sistema
"""
import requests
import json
import time

BASE = 'http://localhost:8000'

def print_header(text):
    print('\n' + '='*60)
    print(f' {text}')
    print('='*60)

def print_ok(text):
    print(f'[✓] {text}')

def print_fail(text):
    print(f'[✗] {text}')

def print_info(text):
    print(f'    {text}')

# ============================================================
# TESTES
# ============================================================

def test_health():
    """Testa endpoints de saúde"""
    print_header('1. HEALTH ENDPOINTS')
    
    # /health
    r = requests.get(f'{BASE}/health')
    if r.status_code == 200:
        print_ok(f'GET /health: {r.status_code}')
    else:
        print_fail(f'GET /health: {r.status_code}')
        return False
    
    # /health/db
    r = requests.get(f'{BASE}/health/db')
    if r.status_code == 200:
        print_ok(f'GET /health/db: {r.status_code}')
    else:
        print_fail(f'GET /health/db: {r.status_code}')
    
    return True

def test_npcs():
    """Testa endpoints de NPCs"""
    print_header('2. NPC ENDPOINTS')
    
    # Lista todos NPCs
    r = requests.get(f'{BASE}/npc/list/all')
    if r.status_code == 200:
        npcs = r.json()
        print_ok(f'GET /npc/list/all: {len(npcs)} NPCs')
        
        # Verificar estrutura
        if npcs:
            npc = npcs[0]
            required_fields = ['id', 'name', 'rank', 'current_hp', 'current_location']
            missing = [f for f in required_fields if f not in npc]
            if missing:
                print_fail(f'Campos faltando: {missing}')
            else:
                print_ok(f'Estrutura NPC válida')
            return npcs[0]['id']
    else:
        print_fail(f'GET /npc/list/all: {r.status_code}')
    return None

def test_players():
    """Testa endpoints de players"""
    print_header('3. PLAYER ENDPOINTS')
    
    # Lista todos players
    r = requests.get(f'{BASE}/player/list/all')
    if r.status_code == 200:
        players = r.json()
        print_ok(f'GET /player/list/all: {len(players)} players')
        return players
    else:
        print_fail(f'GET /player/list/all: {r.status_code}')
    return []

def test_character_creation():
    """Testa criação de personagem com Sprint 16"""
    print_header('4. CHARACTER CREATION (Sprint 16 + 18)')
    
    # Criar personagem como escravo criança (não deve ter skills)
    payload = {
        'name': f'ValidacaoFinal_{int(time.time())}',
        'constitution': 'Human',
        'appearance': 'Um jovem magro de olhos tristes',
        'origin_location': 'Vila das Nuvens',
        'session_zero_answers': [
            'Meu nome e ValidacaoFinal',
            'Sou um escravo crianca que nunca cultivou, comprado por uma familia',
            'Tenho uma irma chamada Li Mei que foi separada de mim',
            'Quero encontrar minha irma e ficar forte',
            'Moro em um barraco no fundo da propriedade do mestre'
        ]
    }
    
    print_info('Criando personagem escravo criança...')
    r = requests.post(f'{BASE}/player/create-full', json=payload, timeout=120)
    
    if r.status_code == 200:
        data = r.json()
        player_id = data.get('id')
        print_ok(f'Player criado: ID {player_id}')
        
        # Verificar Sprint 16: Skills removidas
        skills = data.get('learned_skills', [])
        if len(skills) == 0:
            print_ok(f'[SPRINT 16] Skills corretamente removidas (escravo criança)')
        else:
            print_fail(f'[SPRINT 16] Skills deveriam estar vazias: {skills}')
        
        # Verificar NPC importante criado
        npc_name = data.get('important_npc_name')
        if npc_name:
            print_ok(f'[SPRINT 16] NPC importante detectado: {npc_name}')
        
        # Verificar home criada
        home = data.get('home_location')
        if home:
            print_ok(f'Casa criada: {home}')
        
        # Verificar feedback
        feedback = data.get('creation_feedback', {})
        first_scene = feedback.get('first_scene', '')
        if first_scene:
            word_count = len(first_scene.split())
            print_ok(f'[SPRINT 18] First Scene gerada: {word_count} palavras')
        
        return player_id
    else:
        print_fail(f'Erro ao criar: {r.status_code} - {r.text[:200]}')
    return None

def test_game_turn(player_id):
    """Testa turno de jogo"""
    print_header('5. GAME TURN')
    
    if not player_id:
        print_fail('Sem player_id para testar')
        return False
    
    # Turno simples: olhar ao redor
    params = {
        "player_id": player_id,
        "player_input": "Observo atentamente meus arredores"
    }
    
    print_info(f'Executando turno para player {player_id}...')
    r = requests.post(f'{BASE}/game/turn', params=params, timeout=120)
    
    if r.status_code == 200:
        data = r.json()
        print_ok(f'Turno processado com sucesso')
        
        # Verificar narração gerada
        narration = data.get('narration', data.get('scene_description', ''))
        if narration:
            word_count = len(narration.split())
            print_ok(f'Narração gerada: {word_count} palavras')
            
            # Sprint 20: verificar economia (150-250 palavras)
            if 100 <= word_count <= 350:  # Margem de tolerância
                print_ok(f'[SPRINT 20] Economia narrativa OK')
            else:
                print_info(f'[SPRINT 20] Palavras fora do target (150-250): {word_count}')
        
        return True
    else:
        print_fail(f'Erro no turno: {r.status_code} - {r.text[:200]}')
    return False

def test_player_details(player_id):
    """Testa detalhes do player"""
    print_header('6. PLAYER DETAILS')
    
    if not player_id:
        print_fail('Sem player_id para testar')
        return False
    
    r = requests.get(f'{BASE}/player/{player_id}')
    if r.status_code == 200:
        data = r.json()
        print_ok(f'GET /player/{player_id}: {data.get("name")}')
        
        # Verificar campos importantes
        print_info(f'HP: {data.get("current_hp")}/{data.get("max_hp")}')
        print_info(f'Location: {data.get("current_location")}')
        print_info(f'Gold: {data.get("gold")}')
        print_info(f'Skills: {data.get("learned_skills")}')
        
        return True
    else:
        print_fail(f'GET /player/{player_id}: {r.status_code}')
    return False

def test_player_history(player_id):
    """Testa histórico do player"""
    print_header('7. PLAYER HISTORY')
    
    if not player_id:
        print_fail('Sem player_id para testar')
        return False
    
    r = requests.get(f'{BASE}/player/{player_id}/history')
    if r.status_code == 200:
        history = r.json()
        print_ok(f'GET /player/{player_id}/history: {len(history)} entradas')
        
        # Verificar Turn 0
        turn_0_exists = any(h.get('turn_number') == 0 for h in history)
        if turn_0_exists:
            print_ok(f'[SPRINT 18] Turn 0 encontrado no histórico')
        else:
            print_info(f'Turn 0 não encontrado')
        
        return True
    else:
        print_fail(f'GET /player/{player_id}/history: {r.status_code}')
    return False

def test_inventory(player_id):
    """Testa inventário"""
    print_header('8. INVENTORY')
    
    if not player_id:
        print_fail('Sem player_id para testar')
        return False
    
    r = requests.get(f'{BASE}/player/{player_id}/inventory')
    if r.status_code == 200:
        inv = r.json()
        print_ok(f'GET /player/{player_id}/inventory: {len(inv)} items')
        return True
    else:
        print_fail(f'GET /player/{player_id}/inventory: {r.status_code}')
    return False

def test_system_status():
    """Testa status do sistema"""
    print_header('9. SYSTEM STATUS')
    
    r = requests.get(f'{BASE}/system/status')
    if r.status_code == 200:
        status = r.json()
        print_ok(f'GET /system/status')
        for key, value in status.items():
            print_info(f'{key}: {value}')
        return True
    else:
        print_fail(f'GET /system/status: {r.status_code}')
    return False

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print('\n' + '='*60)
    print(' VALIDAÇÃO COMPLETA DO SISTEMA RPG CULTIVO')
    print(' Sprints 16-20 + Sistema Base')
    print('='*60)
    
    results = {}
    
    # 1. Health
    results['health'] = test_health()
    
    # 2. NPCs
    npc_id = test_npcs()
    results['npcs'] = npc_id is not None
    
    # 3. Players
    players = test_players()
    results['players'] = len(players) > 0
    
    # 4. Character Creation (Sprint 16 + 18)
    new_player_id = test_character_creation()
    results['character_creation'] = new_player_id is not None
    
    # 5. Game Turn
    results['game_turn'] = test_game_turn(new_player_id)
    
    # 6. Player Details
    results['player_details'] = test_player_details(new_player_id)
    
    # 7. Player History
    results['player_history'] = test_player_history(new_player_id)
    
    # 8. Inventory
    results['inventory'] = test_inventory(new_player_id)
    
    # 9. System Status
    results['system_status'] = test_system_status()
    
    # ============================================================
    # RESUMO
    # ============================================================
    print_header('RESUMO DA VALIDAÇÃO')
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = '✓' if result else '✗'
        print(f'  [{status}] {test_name}')
    
    print(f'\n  RESULTADO: {passed}/{total} testes passaram')
    
    if passed == total:
        print('\n  🎉 SISTEMA TOTALMENTE FUNCIONAL!')
    elif passed >= total * 0.8:
        print('\n  ⚠️  Sistema funcional com pequenos problemas')
    else:
        print('\n  ❌ Sistema com problemas críticos')
    
    print('='*60)
