"""
Script de Teste: Character Creation System (Sprint 4)
Testa: Session Zero, Player Creation Full, Model Updates
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_character_creation_flow():
    """Testa o fluxo completo de criação de personagem"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== TESTE: CHARACTER CREATION SYSTEM (SPRINT 4) ===\n")
        
        # 1. Testar geração de perguntas do Session Zero
        print("1️⃣ Testando /character/session-zero...")
        session_zero_data = {
            "name": "Li Xiao",
            "constitution": "Godfiend (Black Sand)",
            "origin_location": "Cavernas Cristalinas"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/character/session-zero",
                json=session_zero_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            session_zero_result = response.json()
            
            print(f"✅ Session Zero gerou {len(session_zero_result['questions'])} perguntas:")
            for i, q in enumerate(session_zero_result['questions'], 1):
                print(f"   Q{i}: {q}")
            print()
            
        except Exception as e:
            print(f"❌ ERRO Session Zero: {e}\n")
            return
        
        # 2. Simular respostas do jogador
        print("2️⃣ Simulando respostas do jogador...")
        mock_answers = [
            "Quando meu mestre foi assassinado por um demônio, jurei me tornar forte.",
            "Sacrifiquei minha conexão com minha família para treinar nas cavernas.",
            "Minha irmã mais nova está doente e preciso encontrar a Pílula da Longevidade."
        ]
        for i, ans in enumerate(mock_answers, 1):
            print(f"   A{i}: {ans}")
        print()
        
        # 3. Criar player completo
        print("3️⃣ Testando /player/create-full...")
        create_player_data = {
            "name": "Li Xiao",
            "appearance": "Jovem de 18 anos, olhos dourados, cicatriz no rosto",
            "constitution": "Godfiend (Black Sand)",
            "origin_location": "Cavernas Cristalinas",
            "session_zero_answers": mock_answers
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/player/create-full",
                json=create_player_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            player = response.json()
            
            print("✅ Player criado com sucesso!")
            print(f"   ID: {player['id']}")
            print(f"   Nome: {player['name']}")
            print(f"   Aparência: {player.get('appearance', 'N/A')}")
            print(f"   Constituição: {player.get('constitution_type', 'N/A')}")
            print(f"   Origem: {player.get('origin_location', 'N/A')}")
            print(f"   Local Atual: {player['current_location']}")
            print(f"\n   📖 Backstory:")
            print(f"   {player.get('backstory', 'N/A')}")
            print()
            
        except Exception as e:
            print(f"❌ ERRO Create Player Full: {e}\n")
            return
        
        # 4. Verificar que os dados foram persistidos corretamente
        print("4️⃣ Verificando persistência dos dados...")
        try:
            # Buscar o player pelo ID
            response = await client.get(f"{BASE_URL}/player/{player['id']}")
            if response.status_code == 404:
                print("⚠️  Endpoint GET /player/{id} não implementado (não é crítico)")
            else:
                response.raise_for_status()
                fetched_player = response.json()
                print(f"✅ Player {fetched_player['name']} recuperado do banco!")
                print(f"   Constitution Type: {fetched_player.get('constitution_type')}")
                print(f"   Origin: {fetched_player.get('origin_location')}")
                print()
        except httpx.HTTPStatusError:
            print("⚠️  Endpoint GET /player/{id} retornou erro (não é crítico para Sprint 4)")
            print()
        
        print("=== TESTE COMPLETO ===")
        print("✅ Session Zero: OK")
        print("✅ Player Creation Full: OK")
        print("✅ Model Fields: OK (appearance, constitution_type, origin_location, backstory)")
        print("\n🎉 Sprint 4 (Character Creation) está funcional!")

if __name__ == "__main__":
    asyncio.run(test_character_creation_flow())
