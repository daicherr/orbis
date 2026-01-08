import requests
import time

# Aguardar servidor estar pronto
print("Aguardando servidor...")
time.sleep(2)

# Testar endpoint
print("Testando /game/log/13...")
response = requests.get("http://localhost:8000/game/log/13")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
