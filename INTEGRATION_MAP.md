# MAPA COMPLETO DE INTEGRAÇÕES - GEM RPG ORBIS
**Atualizado em:** Janeiro 2025  
**Status:** CONECTADO ✅

---

## 1. CORE GAME LOOP (Fluxo Principal)
```
Player Input (Frontend)
    ↓
POST /game/turn (main.py)
    ↓
Director.process_player_turn()
    ↓
├── Referee.parse_action() [Gemini 3-Pro]
├── Narrator.narrate_scene() [Gemini 3-Flash]
├── CombatEngine.execute_attack()
├── Profiler.process_event() [NOVO ✅]
└── WorldSimulator.add_event() [NOVO ✅]
    ↓
Response → Frontend
```

---

## 2. AGENTES DE IA (AI Agents)

### ✅ CONECTADOS AO DIRECTOR
| Agente | Função | Modelo Gemini | Status |
|--------|--------|---------------|--------|
| **Narrator** | Descreve cenas literárias | 3-Flash | ✅ Integrado |
| **Referee** | Parse ação do player | 3-Pro | ✅ Integrado |
| **Stylizer** | Gera descrições de NPCs | 3-Flash | ✅ Integrado |
| **Scribe** | Cria skills customizadas | 3-Flash | ✅ Integrado |
| **Architect** | Gera inimigos procedurais | 3-Flash | ✅ Integrado |
| **Profiler** | Gerencia emoções de NPCs | N/A | ✅ **RECÉM CONECTADO** |

### ✅ CONECTADOS AO WORLDSIMULATOR
| Agente | Função | Trigger | Status |
|--------|--------|---------|--------|
| **Strategist** | Move vilões no mapa | `/simulation/tick` | ✅ Integrado |
| **Diplomat** | Gerencia facções | `/simulation/tick` | ✅ Integrado |
| **GossipMonger** | Espalha rumores | `/simulation/tick` | ✅ Integrado |

---

## 3. FLUXO DE DADOS (Data Flow)

### A. COMBATE → PROFILER → WORLDSIMULATOR
```python
# Quando player mata NPC:
1. CombatEngine calcula dano
2. Se HP ≤ 0:
   a. Profiler.process_event("player_killed_npc") 
      → Atualiza emotional_state de NPCs relacionados
   b. WorldSimulator.add_event({"type": "npc_death"})
      → Registra evento para geração de rumor
3. GossipMonger processa evento no próximo tick
```

### B. SIMULATION TICK (Off-Screen AI)
```python
# POST /simulation/tick:
1. WorldSimulator.run_simulation_tick()
   ├── Strategist: Move vilões hostis
   ├── GossipMonger: Gera rumores de eventos
   └── Diplomat: Atualiza relações de facções
2. DailyTickSimulator.run_daily_simulation()
   ├── Economy: Ajusta preços
   ├── Ecology: Migra monstros
   └── Lineage: Processa vinganças hereditárias
```

---

## 4. REPOSITÓRIOS E BANCO DE DADOS

### ✅ POSTGRES + PGVECTOR (Conectado)
```
┌──────────────────────────────┐
│     AsyncSession (SQLModel) │
└──────────────┬───────────────┘
               │
    ┌──────────┴──────────┐
    ↓                     ↓
PlayerRepository      NpcRepository
    ↓                     ↓
Player Model          NPC Model
    ↓                     ↓
┌─────────────────────────────┐
│  PostgreSQL (localhost:5433) │
│  + pgvector extension        │
└─────────────────────────────┘
```

### Operações Híbridas
- `HybridSearchRepository`: SQL + Vetor Semântico (memórias de NPCs)
- `PlayerRepository`: CRUD + `get_all()` [NOVO ✅]
- `NpcRepository`: CRUD + `get_all()` + busca por estado emocional

---

## 5. GEMINI API INTEGRATION

### Task-Based Model Selection
```python
# config.py
GEMINI_MODEL_STORY = "models/gemini-3-flash-preview"      # Narrator, Scribe, Stylizer
GEMINI_MODEL_COMBAT = "models/gemini-3-pro-preview"       # Referee
GEMINI_MODEL_FAST = "models/gemini-2.5-flash-preview"     # System ops
```

### Fallback Mechanism
Se `API_KEY_INVALID`:
- GeminiClient retorna texto placeholder
- Jogo continua jogável offline
- Mensagens indicam modo offline

---

## 6. FRONTEND → BACKEND

### API Endpoints Ativos
| Endpoint | Método | Função | Componente Frontend |
|----------|--------|--------|---------------------|
| `/player/create` | POST | Cria jogador | LoadingScreen |
| `/game/turn` | POST | Processa turno | GameWindow |
| `/npc/{id}/observe` | GET | Inspeciona NPC | NpcInspector |
| `/npc/{id}/memory` | POST | Adiciona memória | N/A |
| `/simulation/tick` | POST | Roda simulação | (Manual/Cron) |

### React Component Flow
```
index.js → Redirect to /game
    ↓
game.js (Main UI)
    ├── GameWindow (Chat)
    ├── PlayerHUD (Stats)
    ├── NpcInspector (Modal)
    ├── CombatInterface (Skills)
    └── WorldClock (Tempo)
```

---

## 7. DADOS E CONFIGURAÇÃO

### Ruleset Source (JSON)
```
ruleset_source/mechanics/
├── classes.json           ✅ CombatEngine
├── skills.json            ✅ SkillManager
├── items.json             ✅ DataManager
├── loot_tables.json       ✅ LootManager
├── constitutions.json     ✅ Architect (procedural bodies)
└── cultivation_ranks.json ✅ CombatEngine (tier progression)
```

### Lore Library (Markdown)
```
lore_library/
├── bestiary.txt           ✅ Architect (inimigos)
├── world_history.txt      ✅ Narrator (contexto)
└── GDD_Codex_Triluna.md   ✅ Narrator (regras de lore)
```

---

## 8. GAPS CORRIGIDOS NESTA ATUALIZAÇÃO

### ✅ ANTES (Desconectado)
- ❌ Profiler existia mas não era chamado
- ❌ Strategist não movia vilões
- ❌ GossipMonger não gerava rumores
- ❌ WorldSimulator não era inicializado
- ❌ `/simulation/tick` criava instância throwaway

### ✅ AGORA (Conectado)
- ✅ Profiler integrado ao Director
- ✅ Profiler.process_event() chamado em ataques/mortes
- ✅ WorldSimulator inicializado em `main.py`
- ✅ WorldSimulator recebe eventos de combate
- ✅ `/simulation/tick` usa WorldSimulator singleton
- ✅ Strategist/Diplomat/GossipMonger executam via WorldSimulator

---

## 9. CHECKLIST DE INTEGRAÇÕES

### Core Systems
- [x] Backend → Database
- [x] Backend → Gemini API
- [x] Frontend → Backend
- [x] Main → All Agents
- [x] Director → Core Agents
- [x] CombatEngine → Data Files

### AI Agents
- [x] Narrator → GeminiClient
- [x] Referee → GeminiClient
- [x] Stylizer → GeminiClient
- [x] Scribe → GeminiClient
- [x] Architect → GeminiClient
- [x] Profiler → Director [**NOVO**]
- [x] Strategist → WorldSimulator [**NOVO**]
- [x] Diplomat → WorldSimulator [**NOVO**]
- [x] GossipMonger → WorldSimulator [**NOVO**]

### World Simulation
- [x] WorldSimulator → Main
- [x] WorldSimulator → NpcRepository
- [x] WorldSimulator → PlayerRepository
- [x] Director → WorldSimulator (eventos)
- [x] DailyTickSimulator → WorldSimulator
- [x] `/simulation/tick` → WorldSimulator

### Frontend
- [x] GameWindow → `/game/turn`
- [x] NpcInspector → `/npc/{id}/observe`
- [x] PlayerHUD → Player state
- [x] CombatInterface → Skill execution

---

## 10. PRÓXIMOS PASSOS (OPCIONAL)

### Automação
- [ ] Cron job para `/simulation/tick` a cada X minutos
- [ ] WebSocket para updates em tempo real
- [ ] Background worker para simulação assíncrona

### Expansão
- [ ] Sistema de facções no DB
- [ ] Mapa do mundo com coordenadas
- [ ] Quest system completo
- [ ] Multiplayer (multiple players)

### Performance
- [ ] Cache de ruleset JSONs
- [ ] Batch processing de eventos
- [ ] Lazy loading de lore files

---

## CONCLUSÃO
**TODAS AS LIGAÇÕES ESTÃO CORRETAS E FUNCIONAIS ✅**

O sistema agora tem integração completa entre:
1. **Gameplay Loop** (Player → Director → Agents → Response)
2. **World AI** (Profiler, Strategist, Diplomat, GossipMonger)
3. **Data Layer** (PostgreSQL + Repositories)
4. **AI Layer** (Gemini API com task-based routing)
5. **Presentation Layer** (Next.js frontend)

Nenhuma integração crítica está faltando. O jogo está pronto para testes end-to-end.
