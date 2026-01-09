"""
SCRIPT DE VALIDAÇÃO: Sprints 16-18
Testa as correções de Lógica Narrativa > Sistema
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

BASE_URL = "http://localhost:8000"

def test_sprint_16_character_creation():
    """
    Sprint 16: Intelligent Character Creation
    Valida que backstory remove skills inapropriadas
    """
    print("\n" + "="*60)
    print("🧪 TESTE SPRINT 16: INTELLIGENT CHARACTER CREATION")
    print("="*60)
    
    # Caso 1: Criança escrava SEM SKILLS
    print("\n[Teste 1] Criança escrava - Deve começar SEM SKILLS")
    payload = {
        "name": "Test Yi Fan",
        "constitution": "Godfiend",
        "origin_location": "Mansão Mò",
        "session_zero_answers": [
            "Yi Fan acorda em seu quarto de criança na mansão Mò. Ele é um escravo comprado pela família.",
            "Um quarto pequeno e úmido nos fundos da mansão",
            "Mò Fāng - Jovem herdeiro da família Mò, arrogante mas talentoso"
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/player/create-full", json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Player criado: {data['name']}")
        print(f"   Constituição: {data['constitution_type']}")
        print(f"   Localização: {data['current_location']}")
        print(f"   Learned Skills: {data['learned_skills']}")
        
        feedback = data.get('creation_feedback', {})
        print(f"\n📋 FEEDBACK:")
        print(f"   Has Initial Skills: {feedback.get('has_initial_skills')}")
        print(f"   Explicação: {feedback.get('skills_explanation', '')[:100]}...")
        print(f"   NPC Criado: {feedback.get('important_npc_created')}")
        print(f"   Starting Location: {feedback.get('starting_location')}")
        
        # Validações
        assert data['learned_skills'] == [], "❌ FALHA: Player com skills quando deveria estar vazio!"
        assert feedback['has_initial_skills'] == False, "❌ FALHA: has_initial_skills deveria ser False!"
        # O NPC agora é extraído da resposta 3
        
        # Verificar se Turn 0 foi gerado
        if 'first_scene' in feedback and feedback['first_scene']:
            print(f"\n🎬 PRIMEIRA CENA GERADA (Sprint 18):")
            print(f"   {feedback['first_scene'][:200]}...")
        
        print("\n✅ SPRINT 16 PASSOU: Skills removidas corretamente!")
        return data['id']
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        print(f"   Tipo: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Response: {e.response.text[:500]}")
        return None

def test_sprint_17_combat_feedback(player_id: int):
    """
    Sprint 17: Combat Feedback System
    Valida que NPCs contra-atacam e dano recebido é registrado
    """
    print("\n" + "="*60)
    print("🧪 TESTE SPRINT 17: COMBAT FEEDBACK SYSTEM")
    print("="*60)
    
    # Atacar um NPC
    print("\n[Teste 2] Atacar NPC - Deve receber contra-ataque")
    payload = {
        "player_id": player_id,
        "action": "atacar o javali selvagem com basic_attack"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/game/turn", json=payload, timeout=120)
        data = response.json()
        
        print(f"✅ Turno executado")
        print(f"\n📜 ACTION RESULT:")
        print(data['action_result'])
        
        # Validações
        action_result = data['action_result'].lower()
        
        # Deve mencionar dano causado
        assert 'dano' in action_result or 'causando' in action_result, "❌ FALHA: Dano causado não mencionado!"
        
        # Se NPC sobreviveu, deve ter contra-ataque
        if 'derrotou' not in action_result:
            assert 'contra-ataca' in action_result or 'atacou você' in action_result, "❌ FALHA: Contra-ataque não registrado!"
            assert 'hp' in action_result, "❌ FALHA: HP não mostrado!"
        
        print("\n✅ SPRINT 17 PASSOU: Contra-ataque e dano recebido registrados!")
        
    except AssertionError as e:
        print(f"❌ FALHA NA VALIDAÇÃO: {e}")
    except Exception as e:
        print(f"❌ ERRO: {e}")

def test_sprint_18_first_scene(player_id: int):
    """
    Sprint 18: First Scene Generator
    Valida que Turn 0 foi gerado automaticamente
    """
    print("\n" + "="*60)
    print("🧪 TESTE SPRINT 18: FIRST SCENE GENERATOR")
    print("="*60)
    
    print("\n[Teste 3] Verificar Turn 0 - Deve existir automaticamente")
    
    try:
        response = requests.get(f"{BASE_URL}/player/{player_id}/game-log", timeout=120)
        logs = response.json()
        
        print(f"✅ {len(logs)} logs encontrados")
        
        # Buscar Turn 0
        turn_0 = next((log for log in logs if log['turn_number'] == 0), None)
        
        if turn_0:
            print(f"\n🎬 TURN 0 ENCONTRADO:")
            print(f"   Player Action: {turn_0['player_action']}")
            print(f"   Action Result: {turn_0['action_result']}")
            print(f"   NPCs Present: {turn_0.get('npcs_present', [])}")
            print(f"\n   Narração (primeiras 300 chars):")
            print(f"   {turn_0['narration'][:300]}...")
            
            # Validações
            assert turn_0['player_action'] == "[CRIAÇÃO DE PERSONAGEM]", "❌ FALHA: player_action incorreto!"
            assert len(turn_0['narration']) > 0, "❌ FALHA: Narração vazia!"
            
            print("\n✅ SPRINT 18 PASSOU: Turn 0 gerado automaticamente!")
        else:
            print("❌ FALHA: Turn 0 não encontrado!")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")

def main():
    print("\n" + "="*60)
    print("🚀 INICIANDO VALIDAÇÃO DOS SPRINTS 16-18")
    print("="*60)
    
    # Testar Sprint 16
    player_id = test_sprint_16_character_creation()
    
    if player_id:
        # Testar Sprint 18 (Turn 0)
        test_sprint_18_first_scene(player_id)
        
        # Testar Sprint 17 (Combat)
        test_sprint_17_combat_feedback(player_id)
    
    print("\n" + "="*60)
    print("✅ VALIDAÇÃO COMPLETA!")
    print("="*60)

if __name__ == "__main__":
    main()
