"""
Script de teste completo do sistema GEM RPG ORBIS.
Testa todos os endpoints, mecânicas e fluxos do jogo.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Fix encoding para Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

class SystemTester:
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.test_player_id = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log de mensagens com timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def test(self, name: str, func):
        """Executa um teste e registra o resultado."""
        self.log(f"Testando: {name}")
        try:
            func()
            self.results["passed"] += 1
            self.log(f"✅ PASS: {name}", "SUCCESS")
        except Exception as e:
            self.results["failed"] += 1
            error_msg = f"{name}: {str(e)}"
            self.results["errors"].append(error_msg)
            self.log(f"❌ FAIL: {error_msg}", "ERROR")
    
    def assert_status(self, response, expected=200):
        """Verifica status code da response."""
        if response.status_code != expected:
            raise Exception(f"Expected {expected}, got {response.status_code}: {response.text}")
    
    def assert_key(self, data: dict, key: str):
        """Verifica se chave existe no dict."""
        if key not in data:
            raise Exception(f"Key '{key}' not found in response: {list(data.keys())}")
    
    # ===== TESTES DE SISTEMA =====
    
    def test_health(self):
        """Teste básico de health."""
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "status")
        assert data["status"] == "ok"
    
    def test_health_db(self):
        """Teste de conexão com banco."""
        r = requests.get(f"{BASE_URL}/health/db", timeout=5)
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "db")
        assert data["db"] == "connected"
    
    def test_system_status(self):
        """Teste de status dos serviços."""
        r = requests.get(f"{BASE_URL}/system/status", timeout=5)
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "services")
        assert data["services"]["lore_cache"] == True
        assert data["services"]["gemini_client"] == True
    
    def test_system_warmup(self):
        """Teste de warmup do sistema."""
        r = requests.post(f"{BASE_URL}/system/warmup", timeout=120)
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "total_time_ms")
        assert data["status"] == "ok"
    
    # ===== TESTES DE PLAYER =====
    
    def test_player_create(self):
        """Teste de criação de player."""
        # Usa query params conforme o endpoint espera
        r = requests.post(
            f"{BASE_URL}/player/create",
            params={"name": "Test Hero"},
            timeout=10
        )
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "id")
        self.test_player_id = data["id"]
        self.log(f"Player criado com ID: {self.test_player_id}")
    
    def test_player_get(self):
        """Teste de busca de player."""
        if not self.test_player_id:
            raise Exception("Player não foi criado ainda")
        
        r = requests.get(f"{BASE_URL}/player/{self.test_player_id}", timeout=5)
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "id")
        self.assert_key(data, "name")
        assert data["id"] == self.test_player_id
    
    def test_player_inventory(self):
        """Teste de inventário do player."""
        if not self.test_player_id:
            raise Exception("Player não foi criado ainda")
        
        r = requests.get(f"{BASE_URL}/player/{self.test_player_id}/inventory", timeout=5)
        self.assert_status(r)
        data = r.json()
        assert isinstance(data, list)
    
    # ===== TESTES DE WORLD =====
    
    def test_world_time(self):
        """Teste de relógio do mundo."""
        r = requests.get(f"{BASE_URL}/world/time", timeout=5)
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "datetime")
        self.assert_key(data, "day")
    
    def test_world_factions(self):
        """Teste de listagem de facções."""
        r = requests.get(f"{BASE_URL}/world/factions", timeout=5)
        self.assert_status(r)
        data = r.json()
        assert isinstance(data, list)
    
    def test_world_economy(self):
        """Teste de economia global."""
        r = requests.get(f"{BASE_URL}/world/economy", timeout=5)
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "prices")
    
    # ===== TESTES DE NPC =====
    
    def test_npc_list(self):
        """Teste de listagem de NPCs."""
        r = requests.get(f"{BASE_URL}/npc/list/all", timeout=5)
        self.assert_status(r)
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    # ===== TESTES DE GAME =====
    
    def test_game_turn(self):
        """Teste de turno de jogo."""
        if not self.test_player_id:
            raise Exception("Player não foi criado ainda")
        
        r = requests.post(
            f"{BASE_URL}/game/turn",
            params={
                "player_id": self.test_player_id,
                "player_input": "olhar ao redor"
            },
            timeout=60
        )
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "scene_description")
        self.assert_key(data, "player_state")
    
    def test_game_turn_stream(self):
        """Teste de streaming SSE."""
        if not self.test_player_id:
            raise Exception("Player não foi criado ainda")
        
        r = requests.post(
            f"{BASE_URL}/game/turn/stream",
            params={
                "player_id": self.test_player_id,
                "player_input": "meditar"
            },
            timeout=60,
            stream=True
        )
        self.assert_status(r)
        
        # Verificar que recebe eventos SSE
        chunks_received = 0
        for line in r.iter_lines(decode_unicode=True):
            if line.startswith("event:"):
                chunks_received += 1
            if chunks_received >= 3:  # metadata + chunk + done
                break
        
        assert chunks_received >= 3, f"Expected 3+ SSE events, got {chunks_received}"
    
    # ===== TESTES DE QUEST =====
    
    def test_quest_generate(self):
        """Teste de geração de quest."""
        if not self.test_player_id:
            raise Exception("Player não foi criado ainda")
        
        r = requests.post(
            f"{BASE_URL}/quest/generate",
            params={
                "player_id": self.test_player_id,
                "use_ai": False  # Template para ser mais rápido
            },
            timeout=30
        )
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "quest")
        self.assert_key(data["quest"], "title")
    
    def test_quest_active(self):
        """Teste de quests ativas."""
        if not self.test_player_id:
            raise Exception("Player não foi criado ainda")
        
        r = requests.get(f"{BASE_URL}/quest/active/{self.test_player_id}", timeout=5)
        self.assert_status(r)
        data = r.json()
        self.assert_key(data, "quests")
    
    # ===== TESTES DE LOCATIONS =====
    
    def test_locations_all(self):
        """Teste de listagem de locations."""
        r = requests.get(f"{BASE_URL}/locations/all", timeout=5)
        self.assert_status(r)
        data = r.json()
        assert isinstance(data, list)
    
    # ===== TESTES DE LOG =====
    
    def test_game_log(self):
        """Teste de histórico de turnos."""
        if not self.test_player_id:
            raise Exception("Player não foi criado ainda")
        
        r = requests.get(
            f"{BASE_URL}/game/log/{self.test_player_id}",
            params={"limit": 5},
            timeout=5
        )
        self.assert_status(r)
        data = r.json()
        assert isinstance(data, list)
    
    # ===== EXECUÇÃO DOS TESTES =====
    
    def run_all(self):
        """Executa todos os testes."""
        self.log("=" * 60)
        self.log("INICIANDO TESTES COMPLETOS DO SISTEMA")
        self.log("=" * 60)
        
        # Sistema
        self.log("\n### TESTES DE SISTEMA ###")
        self.test("Health Check", self.test_health)
        self.test("Database Health", self.test_health_db)
        self.test("System Status", self.test_system_status)
        
        # World
        self.log("\n### TESTES DE WORLD ###")
        self.test("World Time", self.test_world_time)
        self.test("World Factions", self.test_world_factions)
        self.test("World Economy", self.test_world_economy)
        
        # NPC
        self.log("\n### TESTES DE NPC ###")
        self.test("NPC List", self.test_npc_list)
        
        # Locations
        self.log("\n### TESTES DE LOCATIONS ###")
        self.test("Locations List", self.test_locations_all)
        
        # Player (criar antes para usar nos outros testes)
        self.log("\n### TESTES DE PLAYER ###")
        self.test("Player Create", self.test_player_create)
        self.test("Player Get", self.test_player_get)
        self.test("Player Inventory", self.test_player_inventory)
        
        # Game (precisa de player)
        self.log("\n### TESTES DE GAME ###")
        self.test("Game Turn", self.test_game_turn)
        self.test("Game Log", self.test_game_log)
        self.test("Game Turn Stream", self.test_game_turn_stream)
        
        # Quest (precisa de player)
        self.log("\n### TESTES DE QUEST ###")
        self.test("Quest Generate", self.test_quest_generate)
        self.test("Quest Active", self.test_quest_active)
        
        # Warmup por último (mais lento)
        self.log("\n### TESTES DE OTIMIZAÇÃO ###")
        self.test("System Warmup", self.test_system_warmup)
        
        # Resultados
        self.log("\n" + "=" * 60)
        self.log("RESULTADOS DOS TESTES")
        self.log("=" * 60)
        self.log(f"✅ Testes Passaram: {self.results['passed']}")
        self.log(f"❌ Testes Falharam: {self.results['failed']}")
        
        if self.results['errors']:
            self.log("\nERROS ENCONTRADOS:")
            for i, error in enumerate(self.results['errors'], 1):
                self.log(f"{i}. {error}")
        
        total = self.results['passed'] + self.results['failed']
        success_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        self.log(f"\nTaxa de Sucesso: {success_rate:.1f}%")
        
        return self.results['failed'] == 0


if __name__ == "__main__":
    tester = SystemTester()
    success = tester.run_all()
    exit(0 if success else 1)
