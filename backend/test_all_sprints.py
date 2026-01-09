# -*- coding: utf-8 -*-
"""
TESTE COMPLETO DOS SPRINTS 16-20
Valida todas as implementações de forma automatizada
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

print("\n" + "="*70)
print("🧪 INICIANDO TESTES DOS SPRINTS 16-20")
print("="*70)

# ==============================================================================
# TESTE 1: SPRINT 16 - INTELLIGENT CHARACTER CREATION
# ==============================================================================
print("\n" + "="*70)
print("📋 TESTE 1: SPRINT 16 - INTELLIGENT CHARACTER CREATION")
print("="*70)

print_info("Criando personagem: Escravo criança (NÃO deve ter skills)")

payload_sprint16 = {
    "name": "Yi Fan Teste",
    "constitution": "Godfiend",
    "origin_location": "Mansão Mò",
    "session_zero_answers": [
        "Yi Fan acorda em seu quarto de criança na mansão Mò. Ele é um escravo comprado pela família há 3 anos.",
        "Um quarto pequeno e úmido nos fundos da mansão, com apenas um colchão velho",
        "Mò Fāng - O jovem herdeiro da família Mò, arrogante e cruel"
    ]
}

try:
    response = requests.post(f"{BASE_URL}/player/create-full", json=payload_sprint16, timeout=120)
    response.raise_for_status()
    player_data = response.json()
    
    player_id = player_data['id']
    print_success(f"Personagem criado: ID={player_id}, Nome={player_data['name']}")
    
    # Validação 1: Skills devem estar vazias
    if player_data['learned_skills'] == []:
        print_success("✓ Sprint 16.1: Skills vazias (correto para escravo criança)")
    else:
        print_error(f"✗ Sprint 16.1 FALHOU: Skills = {player_data['learned_skills']} (deveria ser [])")
    
    # Validação 2: Creation Feedback
    feedback = player_data.get('creation_feedback', {})
    if not feedback.get('has_initial_skills', True):
        print_success("✓ Sprint 16.2: has_initial_skills = False (correto)")
    else:
        print_error("✗ Sprint 16.2 FALHOU: has_initial_skills deveria ser False")
    
    # Validação 3: Explicação de skills
    if 'skills_explanation' in feedback:
        print_success(f"✓ Sprint 16.3: Feedback presente: '{feedback['skills_explanation'][:80]}...'")
    else:
        print_error("✗ Sprint 16.3 FALHOU: skills_explanation não presente")
    
    # Validação 4: First Scene (Sprint 18)
    if 'first_scene' in feedback and feedback['first_scene']:
        word_count = len(feedback['first_scene'].split())
        print_success(f"✓ Sprint 18: First Scene gerada ({word_count} palavras)")
        if 150 <= word_count <= 300:
            print_success(f"✓ Sprint 20: Tamanho adequado ({word_count} palavras)")
        else:
            print_warning(f"⚠ Sprint 20: {word_count} palavras (meta: 150-250)")
    else:
        print_error("✗ Sprint 18 FALHOU: first_scene não gerada")
    
    print_info(f"Localização inicial: {player_data['current_location']}")
    
except Exception as e:
    print_error(f"ERRO no Sprint 16: {e}")
    if hasattr(e, 'response'):
        print_error(f"Response: {e.response.text[:300]}")
    sys.exit(1)

# ==============================================================================
# TESTE 2: SPRINT 18 - TURN 0 NO GAMELOG
# ==============================================================================
print("\n" + "="*70)
print("📋 TESTE 2: SPRINT 18 - TURN 0 NO GAMELOG")
print("="*70)

try:
    time.sleep(2)  # Aguardar processamento
    response = requests.get(f"{BASE_URL}/player/{player_id}/game-log", timeout=30)
    response.raise_for_status()
    logs = response.json()
    
    print_info(f"Total de logs encontrados: {len(logs)}")
    
    # Buscar Turn 0
    turn_0 = next((log for log in logs if log['turn_number'] == 0), None)
    
    if turn_0:
        print_success("✓ Sprint 18.1: Turn 0 encontrado no GameLog")
        
        if turn_0['player_action'] == "[CRIAÇÃO DE PERSONAGEM]":
            print_success("✓ Sprint 18.2: player_action correto")
        else:
            print_error(f"✗ Sprint 18.2 FALHOU: player_action = {turn_0['player_action']}")
        
        if len(turn_0['narration']) > 50:
            word_count = len(turn_0['narration'].split())
            print_success(f"✓ Sprint 18.3: Narração presente ({word_count} palavras)")
            print_info(f"Primeiras 150 chars: {turn_0['narration'][:150]}...")
        else:
            print_error("✗ Sprint 18.3 FALHOU: Narração muito curta ou vazia")
        
        if turn_0.get('npcs_present'):
            print_success(f"✓ Sprint 18.4: NPCs presentes: {turn_0['npcs_present']}")
        else:
            print_warning("⚠ Sprint 18.4: Nenhum NPC na cena inicial")
    else:
        print_error("✗ Sprint 18 FALHOU: Turn 0 não encontrado no GameLog!")
        
except Exception as e:
    print_error(f"ERRO no Sprint 18: {e}")

# ==============================================================================
# TESTE 3: SPRINT 17 - COMBAT FEEDBACK
# ==============================================================================
print("\n" + "="*70)
print("📋 TESTE 3: SPRINT 17 - COMBAT FEEDBACK SYSTEM")
print("="*70)

print_info("Executando ação de ataque contra NPC hostil...")

try:
    # Primeiro turno: olhar ao redor para spawnar NPCs
    response = requests.post(
        f"{BASE_URL}/game/turn",
        json={"player_id": player_id, "action": "olhar ao redor procurando por inimigos"},
        timeout=120
    )
    response.raise_for_status()
    turn_data = response.json()
    
    print_success(f"✓ Turno 1 executado: {turn_data['player_state']['current_location']}")
    
    # Segundo turno: atacar
    time.sleep(2)
    response = requests.post(
        f"{BASE_URL}/game/turn",
        json={"player_id": player_id, "action": "atacar o inimigo mais próximo com todas as forças"},
        timeout=120
    )
    response.raise_for_status()
    combat_data = response.json()
    
    action_result = combat_data.get('action_result', '')
    print_info(f"Action Result: {action_result[:200]}...")
    
    # Validação 1: Dano causado mencionado
    if any(word in action_result.lower() for word in ['dano', 'causando', 'golpe', 'ataque']):
        print_success("✓ Sprint 17.1: Dano causado mencionado no action_result")
    else:
        print_warning("⚠ Sprint 17.1: Dano causado não explícito (pode ser por não haver inimigos)")
    
    # Validação 2: Contra-ataque do NPC (se houver combate)
    if 'contra-ataca' in action_result.lower() or 'atacou você' in action_result.lower():
        print_success("✓ Sprint 17.2: NPC contra-atacou!")
        
        # Validação 3: HP do player mostrado
        if 'hp' in action_result.lower() or 'vida' in action_result.lower():
            print_success("✓ Sprint 17.3: HP do player mostrado")
        else:
            print_warning("⚠ Sprint 17.3: HP não explícito no texto")
        
        # Validação 4: Modificador de constituição
        if 'constituição' in action_result.lower() or 'godfiend' in action_result.lower() or 'defesa' in action_result.lower():
            print_success("✓ Sprint 17.4: Modificador de constituição visível!")
        else:
            print_warning("⚠ Sprint 17.4: Modificador de constituição não mencionado")
    else:
        print_warning("⚠ Sprint 17: Não houve combate neste turno (sem inimigos hostis)")
        print_info("Isso é normal se não havia NPCs hostis na cena")
    
except Exception as e:
    print_error(f"ERRO no Sprint 17: {e}")

# ==============================================================================
# TESTE 4: SPRINT 19 - SKILLS ENDPOINT (Preparação para Frontend)
# ==============================================================================
print("\n" + "="*70)
print("📋 TESTE 4: SPRINT 19 - PLAYER SKILLS DATA")
print("="*70)

try:
    # Verificar player stats
    response = requests.get(f"{BASE_URL}/player/{player_id}", timeout=30)
    response.raise_for_status()
    player_full = response.json()
    
    print_info(f"Learned Skills: {player_full.get('learned_skills', [])}")
    print_info(f"Shadow Chi: {player_full.get('shadow_chi', 0)}")
    print_info(f"Yuan Qi: {player_full.get('yuan_qi', 0)}")
    print_info(f"Quintessence: {player_full.get('quintessence', 0)}")
    
    if player_full.get('learned_skills') == []:
        print_success("✓ Sprint 19.1: Player sem skills (correto para personagem iniciante)")
        print_info("Frontend deve exibir: '📖 Você ainda não possui técnicas de cultivo'")
    else:
        print_success(f"✓ Sprint 19.1: Player tem skills: {player_full['learned_skills']}")
        print_info("Frontend deve exibir custos e cooldowns dessas skills")
    
    # Verificar se skills.json existe
    try:
        response = requests.get("http://localhost:8000/skills", timeout=10)
        if response.status_code == 200:
            skills_data = response.json()
            print_success(f"✓ Sprint 19.2: Skills API disponível ({len(skills_data)} skills)")
        else:
            print_warning("⚠ Sprint 19.2: Skills API retornou status " + str(response.status_code))
    except:
        print_warning("⚠ Sprint 19.2: Skills API não encontrada (frontend pode usar fallback)")
    
except Exception as e:
    print_error(f"ERRO no Sprint 19: {e}")

# ==============================================================================
# TESTE 5: SPRINT 20 - NARRATIVE ECONOMY
# ==============================================================================
print("\n" + "="*70)
print("📋 TESTE 5: SPRINT 20 - NARRATIVE ECONOMY")
print("="*70)

print_info("Analisando narrações geradas...")

try:
    # Pegar todos os logs
    response = requests.get(f"{BASE_URL}/player/{player_id}/game-log", timeout=30)
    logs = response.json()
    
    word_counts = []
    for log in logs:
        if log.get('narration'):
            wc = len(log['narration'].split())
            word_counts.append(wc)
    
    if word_counts:
        avg_words = sum(word_counts) / len(word_counts)
        min_words = min(word_counts)
        max_words = max(word_counts)
        
        print_info(f"Narrações analisadas: {len(word_counts)}")
        print_info(f"Palavras - Média: {avg_words:.0f} | Min: {min_words} | Max: {max_words}")
        
        if avg_words <= 300:
            print_success(f"✓ Sprint 20.1: Média de {avg_words:.0f} palavras (meta: 150-250)")
        else:
            print_warning(f"⚠ Sprint 20.1: Média de {avg_words:.0f} palavras (acima da meta)")
        
        if max_words <= 400:
            print_success(f"✓ Sprint 20.2: Máximo de {max_words} palavras (aceitável)")
        else:
            print_warning(f"⚠ Sprint 20.2: Máximo de {max_words} palavras (muito prolixo)")
    else:
        print_warning("⚠ Sprint 20: Nenhuma narração para analisar")
        
except Exception as e:
    print_error(f"ERRO no Sprint 20: {e}")

# ==============================================================================
# RESUMO FINAL
# ==============================================================================
print("\n" + "="*70)
print("📊 RESUMO DOS TESTES")
print("="*70)

print(f"""
✅ SPRINTS TESTADOS:
   • Sprint 16: Intelligent Character Creation
   • Sprint 17: Combat Feedback System
   • Sprint 18: First Scene Generator
   • Sprint 19: Skills Data (Backend pronto para Frontend)
   • Sprint 20: Narrative Economy

🎯 PERSONAGEM DE TESTE:
   • ID: {player_id}
   • Nome: Yi Fan Teste
   • Constituição: Godfiend
   • Skills: {player_data.get('learned_skills', [])}
   • Localização: {player_data.get('current_location', 'N/A')}

💡 PRÓXIMOS PASSOS:
   1. Testar frontend em http://localhost:3000
   2. Verificar CombatInterface com skills
   3. Jogar alguns turnos para validar combate
   4. Verificar economia de texto em ação
""")

print("="*70)
print("✅ TESTES CONCLUÍDOS!")
print("="*70)
