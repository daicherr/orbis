# Sprint 21 - LangGraph Full Implementation

## Status: ✅ COMPLETO (09/01/2026)

## Resumo

Esta sprint implementou a migração completa para LangGraph com StateGraph, checkpoints e streaming SSE.

## O que foi implementado

### 1. LangGraph Core Migration (✅ Completo)

**Arquivos criados/modificados:**
- `backend/app/agents/nodes/state.py` - AgentState TypedDict com PlayerContext, WorldContext, NPCContext
- `backend/app/agents/nodes/planner.py` - Nó planejador que interpreta input do usuário
- `backend/app/agents/nodes/executor.py` - Nó executor com dispatch por intent
- `backend/app/agents/nodes/validator.py` - Nó validador com routing condicional
- `backend/app/agents/nodes/narrator.py` - Nó narrador literário
- `backend/app/agents/graph_core.py` - StateGraph principal

**Fluxo do Grafo:**
```
START → planner → executor → validator ─┬─(retry)→ planner
                                        └─(success)→ narrator → END
```

### 2. Checkpointer com Time Travel (✅ Completo)

**Implementação:**
- `MemorySaver` para Windows (psycopg incompatível com ProactorEventLoop)
- `AsyncPostgresSaver` para Linux/Mac
- Detecção automática de plataforma via `sys.platform`
- GameGraph singleton em `app_state` para compartilhar checkpoints

**Endpoints:**
- `POST /v2/game/turn/persistent` - Turno com checkpoints
- `POST /v2/game/undo` - Desfaz último turno
- `GET /v2/game/checkpoints/{session_id}` - Lista checkpoints

### 3. Streaming SSE (✅ Implementado)

**Endpoint:**
- `POST /v2/game/turn/stream` - Streaming de eventos SSE

**Eventos:**
- `planner` - Ação planejada (intent, target)
- `executor` - Resultado da execução (success, summary)
- `validator` - Status de validação (status, attempts)
- `narrator_chunk` - Chunks de narrativa (50 chars cada)
- `done` - Turno completo
- `error` - Se houver erro

**Uso JavaScript:**
```javascript
const evtSource = new EventSource('/v2/game/turn/stream?player_id=1&player_input=...');

evtSource.addEventListener('narrator_chunk', (e) => {
    const data = JSON.parse(e.data);
    appendToNarrative(data.text);
});

evtSource.addEventListener('done', () => {
    evtSource.close();
});
```

## Próximos Passos

1. ~~**Integrar Frontend com v2 endpoints**~~ ✅ COMPLETO
   - Atualizado `GameContext.js` com função `sendActionSSE`
   - Atualizado `game.js` para usar streaming com efeito de digitação
   - Adicionado CSS para indicador de digitação piscante

2. **Testes E2E**
   - Testar streaming SSE via browser
   - Validar comportamento de undo/redo

## Implementação Frontend SSE

### GameContext.js
- Nova função `sendActionSSE(action, callbacks, id)` 
- Callbacks: `onChunk`, `onDone`, `onError`, `onPlanner`, `onExecutor`, `onValidator`
- Usa fetch com ReadableStream para processar SSE

### game.js  
- Novos estados: `streamingText`, `isStreaming`
- `handleSend` agora usa SSE e acumula texto progressivamente
- Input desabilitado durante streaming

### main.css
- Adicionado `.typing-indicator` com animação de blink

## Arquivos de Teste

- `backend/test_sse.py` - Script Python para testar streaming SSE

## Comandos de Teste

```powershell
# Iniciar servidor
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Turno normal (sem streaming)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v2/game/turn?player_id=23&player_input=Observo" -Method POST

# Turno com checkpoints
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v2/game/turn/persistent?player_id=23&player_input=Observo&session_id=test" -Method POST

# Listar checkpoints
Invoke-WebRequest -Uri "http://127.0.0.1:8000/v2/game/checkpoints/test" -Method GET

# Undo
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v2/game/undo?session_id=test" -Method POST

# Streaming SSE (usar Python script)
python backend/test_sse.py
```

## Notas Técnicas

### Windows e psycopg
O Windows usa `ProactorEventLoop` que não é compatível com psycopg async. Por isso usamos `MemorySaver` que não persiste checkpoints entre reinícios do servidor. Em produção (Linux), usar `AsyncPostgresSaver`.

### Sessão DB no SSE
O endpoint SSE usa sessões internas ao invés de `Depends(get_session)` para evitar que a sessão seja fechada antes do streaming completar.
