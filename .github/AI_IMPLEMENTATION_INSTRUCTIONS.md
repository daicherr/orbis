# INSTRUÇÕES DE IMPLEMENTAÇÃO - AGENTE IA
# GEM RPG ORBIS - ARQUITETURA COGNITIVA COMPLETA

**LEIA ESTE ARQUIVO ANTES DE CADA SESSÃO DE TRABALHO**

---

## 🚨 REGRAS ABSOLUTAS (NUNCA VIOLAR)

### 1. PROIBIDO CÓDIGO INCOMPLETO
- ❌ NUNCA usar `pass` como placeholder
- ❌ NUNCA usar `# TODO: implementar`
- ❌ NUNCA usar `raise NotImplementedError()`
- ❌ NUNCA deixar funções vazias
- ❌ NUNCA usar `...` como corpo de função
- ✅ SEMPRE implementar a lógica completa
- ✅ SEMPRE testar o código antes de passar para próxima tarefa

### 2. PROIBIDO TEMPLATES VAZIOS
- ❌ NUNCA criar classes só com `__init__` vazio
- ❌ NUNCA criar métodos que só retornam None
- ❌ NUNCA criar arquivos "esqueleto" para preencher depois
- ✅ SEMPRE implementar funcionalidade real
- ✅ SEMPRE conectar com o resto do sistema

### 3. PROIBIDO IGNORAR CONTEXTO
- ❌ NUNCA esquecer de imports necessários
- ❌ NUNCA criar duplicatas de código existente
- ❌ NUNCA quebrar funcionalidade existente
- ✅ SEMPRE verificar o que já existe antes de criar
- ✅ SEMPRE manter backward compatibility

### 4. PROIBIDO CÓDIGO PREGUIÇOSO
- ❌ NUNCA copiar/colar sem adaptar
- ❌ NUNCA simplificar demais a lógica
- ❌ NUNCA ignorar edge cases
- ✅ SEMPRE implementar tratamento de erros
- ✅ SEMPRE validar inputs
- ✅ SEMPRE logar informações úteis

---

## 📋 CHECKLIST POR FASE

### FASE 1: FOUNDATION (Implementar NESTA ORDEM)

#### 1.1 SessionContext
- [ ] Criar `backend/app/core/session_context.py`
- [ ] Implementar `SessionContext` dataclass com:
  - `session_id: str`
  - `player_id: int`
  - `current_location: str`
  - `present_entities: List[Entity]`
  - `last_n_turns: List[TurnSummary]`
  - `narrative_arc: NarrativeArc`
  - `tension_level: float`
  - `active_threads: List[PlotThread]`
  - `unresolved_hooks: List[NarrativeHook]`
  - `time_context: TimeContext`
- [ ] Implementar `TurnSummary` dataclass
- [ ] Implementar `PlotThread` dataclass
- [ ] Implementar `NarrativeHook` dataclass
- [ ] Implementar `TimeContext` dataclass
- [ ] Implementar métodos:
  - `get_last_n_turns(n: int) -> List[TurnSummary]`
  - `add_turn(turn: TurnSummary)`
  - `get_present_entities() -> List[Entity]`
  - `update_tension(delta: float)`
  - `add_plot_thread(thread: PlotThread)`
  - `resolve_hook(hook_id: str)`
  - `serialize() -> dict` (para persistência)
  - `deserialize(data: dict) -> SessionContext` (para recuperação)
- [ ] Testar com casos de uso reais
- [ ] Integrar com Director

#### 1.2 MemorySystem 2.0
- [ ] Criar `backend/app/core/memory/` diretório
- [ ] Criar `backend/app/core/memory/__init__.py`
- [ ] Criar `backend/app/core/memory/episodic.py`:
  - `EpisodicMemory` dataclass
  - `EpisodicStore` class com:
    - `add(entity_id: int, memory: EpisodicMemory)`
    - `query(entity_id: int, time_range: TimeRange, limit: int)`
    - `get_recent(entity_id: int, n: int)`
- [ ] Criar `backend/app/core/memory/semantic.py`:
  - `SemanticFact` dataclass
  - `SemanticStore` class com:
    - `upsert(entity_id: int, fact: SemanticFact)`
    - `query(entity_id: int, query: str, limit: int)`
    - `get_all_facts(entity_id: int)`
- [ ] Criar `backend/app/core/memory/procedural.py`:
  - `BehaviorPattern` dataclass
  - `ProceduralStore` class com:
    - `add(entity_id: int, pattern: BehaviorPattern)`
    - `get_patterns(entity_id: int)`
    - `detect_pattern(entity_id: int, recent_events: List)`
- [ ] Criar `backend/app/core/memory/memory_manager.py`:
  - `HierarchicalMemory` class que orquestra as 3 stores
  - `remember(entity_id, event, importance)`
  - `recall(entity_id, query, context) -> MemoryBundle`
  - `consolidate()` - compacta memórias antigas
- [ ] Migrar dados existentes do `memory` table
- [ ] Testar cada store individualmente
- [ ] Testar integração completa
- [ ] Integrar com Narrator e Director

#### 1.3 NPC Entity Enrichment
- [ ] Modificar `backend/app/database/models/npc.py`:
  - Adicionar campo `species: str` (human, beast, spirit, demon, etc)
  - Adicionar campo `gender: str` (male, female, unknown)
  - Adicionar campo `can_speak: bool`
  - Adicionar campo `daily_schedule: JSON` (rotina diária)
  - Adicionar campo `home_location: str`
  - Adicionar campo `faction_id: Optional[int]`
  - Adicionar campo `relationships: JSON` (relações com outros NPCs)
- [ ] Criar migration para adicionar campos
- [ ] Atualizar `NpcRepository` com novos métodos
- [ ] Atualizar `Architect.generate_enemy()` para preencher novos campos
- [ ] Atualizar `Architect.generate_friendly_npc()` para preencher novos campos
- [ ] Atualizar Narrator para usar `can_speak` e `species`
- [ ] Testar geração de NPCs com novos campos
- [ ] Testar narração com diferentes tipos de NPCs

#### 1.4 Location System
- [ ] Criar `backend/app/core/location.py`:
  - `Location` dataclass com:
    - `id: str`
    - `name: str`
    - `type: LocationType` (city, wilderness, dungeon, etc)
    - `security_level: int` (0-10)
    - `controlling_faction: Optional[str]`
    - `connected_locations: List[str]`
    - `ambient_description: str`
    - `time_descriptions: Dict[str, str]` (dawn, morning, etc)
    - `possible_encounters: List[EncounterType]`
    - `services: List[str]` (shop, inn, temple, etc)
- [ ] Criar `LocationRegistry` singleton:
  - `get(location_id: str) -> Location`
  - `get_connected(location_id: str) -> List[Location]`
  - `get_by_type(type: LocationType) -> List[Location]`
  - `calculate_travel_time(from: str, to: str) -> int`
- [ ] Carregar dados de `locations_desc.md` no boot
- [ ] Atualizar Director para usar Location objects
- [ ] Atualizar spawn logic para respeitar security_level
- [ ] Testar navegação entre localizações

---

### FASE 2: COGNITIVE CORE (Implementar NESTA ORDEM)

#### 2.1 ReAct Agent Framework
- [ ] Criar `backend/app/agents/cognitive/` diretório
- [ ] Criar `backend/app/agents/cognitive/__init__.py`
- [ ] Criar `backend/app/agents/cognitive/base_agent.py`:
  - `Thought` dataclass
  - `Action` dataclass
  - `Observation` dataclass
  - `ReActLoop` class com:
    - `think(context) -> Thought`
    - `act(thought) -> Observation`
    - `should_continue(thoughts, observations) -> bool`
    - `run(input, context, max_iterations) -> Result`
- [ ] Criar `backend/app/agents/cognitive/tools.py`:
  - `Tool` base class
  - `SearchRulesTool`
  - `SearchMemoryTool`
  - `ValidateActionTool`
  - `CalculateDamageTool`
  - `GetNPCInfoTool`
- [ ] Criar `backend/app/agents/cognitive/tool_executor.py`:
  - `ToolExecutor` class que executa tools
- [ ] Testar ReAct loop isoladamente
- [ ] Testar cada tool individualmente

#### 2.2 CognitiveReferee
- [ ] Criar `backend/app/agents/cognitive/cognitive_referee.py`:
  - Herdar conceitos do ReAct Framework
  - Implementar `interpret_action(input, session) -> ActionResolution`
  - Implementar gathering de contexto via RAG
  - Implementar reasoning trace
  - Implementar validation contra regras
- [ ] Manter backward compatibility com Referee antigo
- [ ] Migrar Director para usar CognitiveReferee
- [ ] Testar com casos complexos de interpretação
- [ ] Testar edge cases (inputs ambíguos, etc)

#### 2.3 CognitiveNarrator
- [ ] Criar `backend/app/agents/cognitive/cognitive_narrator.py`:
  - Implementar `NarrativeStrategy` enum
  - Implementar `NarratorPersona` enum
  - Implementar `generate(context, strategy, persona) -> str`
  - Implementar seleção de persona baseada em beat
  - Implementar foreshadowing injection
  - Implementar callback planting
- [ ] Manter backward compatibility com Narrator antigo
- [ ] Migrar Director para usar CognitiveNarrator
- [ ] Testar diferentes personas
- [ ] Testar consistência narrativa

#### 2.4 NarrativeArcTracker
- [ ] Criar `backend/app/core/narrative_arc.py`:
  - `NarrativeBeat` enum (setup, rising, climax, falling, resolution)
  - `NarrativeArc` class com:
    - `current_beat: NarrativeBeat`
    - `tension: float`
    - `pending_hooks: List[NarrativeHook]`
    - `resolved_hooks: List[NarrativeHook]`
    - `setup_opportunities: List[SetupOpportunity]`
  - Métodos:
    - `update(action: ActionResolution)`
    - `calculate_tension() -> float`
    - `get_current_beat() -> NarrativeBeat`
    - `plant_hook(hook: NarrativeHook)`
    - `resolve_hook(hook_id: str)`
    - `get_pending_hooks() -> List[NarrativeHook]`
- [ ] Integrar com SessionContext
- [ ] Integrar com CognitiveNarrator
- [ ] Testar tracking de arco

#### 2.5 RulesEngine
- [ ] Criar `backend/app/core/rules_engine.py`:
  - `Rule` dataclass
  - `ValidationResult` dataclass
  - `RulesEngine` class com:
    - `load_rules(path: str)`
    - `validate(action: ActionResolution) -> ValidationResult`
    - `get_applicable_rules(action_type: str) -> List[Rule]`
    - `check_prerequisites(action, player) -> bool`
- [ ] Carregar regras de `ruleset_source/mechanics/`
- [ ] Carregar regras de `ruleset_source/lore_manual/`
- [ ] Integrar com CognitiveReferee
- [ ] Testar validação de ações

---

### FASE 3: LIVING WORLD (Implementar NESTA ORDEM)

#### 3.1 WorldSimulator
- [ ] Criar `backend/app/core/simulation/` diretório
- [ ] Criar `backend/app/core/simulation/__init__.py`
- [ ] Criar `backend/app/core/simulation/world_simulator.py`:
  - `WorldSimulator` class com:
    - `tick(current_time: GameTime)`
    - `process_npc_routines()`
    - `process_villain_plans()`
    - `propagate_rumors()`
    - `generate_world_events()`
    - `save_snapshot()`
- [ ] Integrar com Chronos (world_clock)
- [ ] Criar scheduler para ticks automáticos
- [ ] Testar simulação de mundo

#### 3.2 NPC Routine System
- [ ] Criar `backend/app/core/simulation/npc_routines.py`:
  - `DailySchedule` dataclass
  - `ScheduleEntry` dataclass
  - `NPCRoutineManager` class com:
    - `get_schedule(npc_id: int) -> DailySchedule`
    - `get_current_activity(npc_id: int, time: GameTime) -> str`
    - `should_move(npc_id: int, time: GameTime) -> bool`
    - `get_destination(npc_id: int, time: GameTime) -> str`
- [ ] Gerar schedules default por tipo de NPC
- [ ] Integrar com WorldSimulator
- [ ] Testar movimentação de NPCs

#### 3.3 Advanced Strategist
- [ ] Refatorar `backend/app/agents/villains/strategist.py`:
  - Implementar planejamento de longo prazo
  - Implementar sistema de goals
  - Implementar avaliação de ameaças
  - Implementar formação de alianças
  - Implementar emboscadas complexas
- [ ] Integrar com WorldSimulator
- [ ] Testar comportamento de vilões

#### 3.4 Economy Engine
- [ ] Criar `backend/app/core/simulation/economy.py`:
  - `Market` dataclass
  - `PriceHistory` dataclass
  - `EconomyEngine` class com:
    - `update_prices(location: str, time: GameTime)`
    - `process_trade(buyer, seller, item, quantity)`
    - `get_price(item_id: str, location: str) -> int`
    - `apply_supply_demand()`
    - `apply_world_events()`
- [ ] Carregar dados de `initial_economy.json`
- [ ] Integrar com WorldSimulator
- [ ] Testar economia dinâmica

#### 3.5 Faction System
- [ ] Criar `backend/app/core/simulation/factions.py`:
  - `Faction` dataclass
  - `FactionRelation` dataclass
  - `FactionSystem` class com:
    - `get_faction(faction_id: str) -> Faction`
    - `get_relation(faction_a: str, faction_b: str) -> FactionRelation`
    - `update_relation(faction_a: str, faction_b: str, delta: int)`
    - `process_politics()`
    - `declare_war(aggressor: str, target: str)`
    - `make_alliance(faction_a: str, faction_b: str)`
- [ ] Definir facções iniciais
- [ ] Integrar com WorldSimulator
- [ ] Integrar com NPC spawning
- [ ] Testar política entre facções

---

### FASE 4: POLISH (Implementar NESTA ORDEM)

#### 4.1 Consistency Validator
- [ ] Criar `backend/app/core/consistency.py`:
  - `ConsistencyValidator` class com:
    - `validate_narration(text: str, session: SessionContext) -> List[Issue]`
    - `validate_npc_behavior(npc: NPC, action: str) -> List[Issue]`
    - `validate_world_state(state: WorldState) -> List[Issue]`
    - `auto_fix(issues: List[Issue]) -> str`
- [ ] Implementar detecção de:
  - Inconsistências de gênero
  - Inconsistências de localização
  - Inconsistências de tempo
  - Animais falando
  - NPCs mortos aparecendo
- [ ] Integrar com CognitiveNarrator
- [ ] Testar detecção de inconsistências

#### 4.2 Performance Optimization
- [ ] Implementar caching de:
  - Lore context (já existe parcialmente)
  - Location data
  - NPC schedules
  - Rule lookups
- [ ] Implementar batching de:
  - Memory queries
  - Database writes
  - Gemini calls onde possível
- [ ] Otimizar queries do PostgreSQL
- [ ] Adicionar índices necessários
- [ ] Testar performance sob carga

#### 4.3 Error Recovery
- [ ] Implementar fallbacks para:
  - Gemini API failures
  - Database connection issues
  - Invalid player inputs
  - Corrupted session state
- [ ] Implementar logging estruturado
- [ ] Implementar health checks
- [ ] Testar cenários de falha

---

## 🔧 COMANDOS ÚTEIS

### Testar Backend
```bash
cd backend
python -m pytest tests/ -v
```

### Rodar Migration
```bash
cd backend
alembic upgrade head
```

### Verificar Tipos
```bash
cd backend
mypy app/ --ignore-missing-imports
```

### Reiniciar Servidor
```bash
# Matar processo existente
Get-Process -Name python | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process

# Iniciar novo
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

---

## 📝 NOTAS DE IMPLEMENTAÇÃO

### Ao criar novos arquivos:
1. Sempre adicionar docstring no topo explicando o propósito
2. Sempre adicionar type hints em todas as funções
3. Sempre importar de forma explícita (não usar `from x import *`)
4. Sempre adicionar logging para debug
5. Sempre adicionar `__all__` para exports públicos

### Ao modificar arquivos existentes:
1. Primeiro ler o arquivo inteiro para entender o contexto
2. Manter estilo consistente com o código existente
3. Não quebrar imports de outros arquivos
4. Testar que funcionalidade existente ainda funciona

### Ao integrar componentes:
1. Sempre criar interface clara entre componentes
2. Usar dependency injection onde possível
3. Evitar acoplamento forte
4. Documentar a integração

---

## 🎯 OBJETIVO FINAL

Ao completar todas as fases, o sistema deve:

1. **LEMBRAR** - NPCs lembram do jogador, eventos têm consequências duradouras
2. **RACIOCINAR** - IA pensa antes de agir, considera contexto completo
3. **NARRAR** - Histórias consistentes com arco dramático e tensão
4. **SIMULAR** - Mundo vive independente do jogador
5. **VALIDAR** - Regras são seguidas, inconsistências são detectadas
6. **ESCALAR** - Performance adequada mesmo com histórico longo

---

**ÚLTIMA ATUALIZAÇÃO:** 2026-01-09
**STATUS:** PRONTO PARA IMPLEMENTAÇÃO
