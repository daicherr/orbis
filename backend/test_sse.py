"""
Script para testar o endpoint SSE de streaming.
"""
import httpx
import asyncio

async def test_sse_stream():
    """Testa o streaming SSE."""
    url = "http://127.0.0.1:8000/v2/game/turn/stream"
    params = {
        "player_id": 23,
        "player_input": "Observo ao redor atentamente",
        "session_id": "test-sse"
    }
    
    print("=== Teste de Streaming SSE ===")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, params=params) as response:
            print(f"Status: {response.status_code}")
            print("-" * 40)
            
            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk
                # Processa linhas completas
                while "\n\n" in buffer:
                    event_block, buffer = buffer.split("\n\n", 1)
                    lines = event_block.strip().split("\n")
                    
                    event_type = "message"
                    event_data = ""
                    
                    for line in lines:
                        if line.startswith("event: "):
                            event_type = line[7:]
                        elif line.startswith("data: "):
                            event_data = line[6:]
                    
                    if event_type == "narrator_chunk":
                        # Imprime sem quebra de linha para efeito de digitação
                        import json
                        try:
                            data = json.loads(event_data)
                            print(data.get("text", ""), end="", flush=True)
                        except:
                            print(event_data, end="", flush=True)
                    elif event_type == "done":
                        print("\n" + "-" * 40)
                        print("[DONE] Streaming completo!")
                    elif event_type == "error":
                        print(f"\n[ERROR] {event_data}")
                    else:
                        print(f"[{event_type}] {event_data}")
    
    print("\n=== Fim do Teste ===")

if __name__ == "__main__":
    asyncio.run(test_sse_stream())
