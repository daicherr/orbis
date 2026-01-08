# Sprint 7 - Correções de Bugs e Integração

## Resumo
Esta sprint focou em corrigir bugs críticos descobertos durante testes de integração completos do sistema de combate, vilões e persistência.

---

## 🐛 Bugs Corrigidos

### 1. Unicode Encoding Error (Windows)
**Problema:** Prints com emojis causavam `UnicodeEncodeError` no console Windows (cp1252)
**Arquivos afetados:**
- `backend/app/agents/director.py`
- `backend/app/agents/narrator.py`
- `backend/app/agents/social/gossip_monger.py`
- `backend/app/agents/villains/profiler.py`
- `backend/app/agents/villains/strategist.py`
- `backend/app/services/quest_service.py`

**Solução:** Substituir emojis por prefixos ASCII:
- `💾` → `[MEMORY]`
- `⚠️` → `[WARN]`
- `🏃` → `[RUN]`
- `🎯` → `[HUNT]`
- `⚔️` → `[AMBUSH]` / `[NEMESIS]`
- `👁️` → `[PATROL]`
- `💤` → `[IDLE]`
- `📰` → `[GOSSIP]`
- `📜` → `[QUEST]`
- `✅` → `[OK]`
- `📊` → `[PROGRESS]`
- `❌` → `[FAIL]`
- `🎉` → `[COMPLETE]`

---

### 2. SkillManager Carregando Arquivo Errado
**Problema:** `SkillManager` carregava `techniques.json` e usava `skill['id']` como chave
**Arquivo:** `backend/app/core/skill_manager.py`
**Solução:**
- Mudou de `techniques.json` para `skills.json`
- Mudou chave de `skill['id']` para `skill['skill_id']`
- Corrigiu `skill.get('silent_art')` para `skill.get('is_silent_art')`

---

### 3. Skill `basic_attack` Não Existia
**Problema:** Combate retornava 0 de dano porque `basic_attack` não existia no JSON
**Arquivo:** `ruleset_source/mechanics/skills.json`
**Solução:** Adicionadas skills:
```json
{
  "skill_id": "basic_attack",
  "name": "Ataque Básico",
  "base_damage": 25,
  "cost_type": "none",
  "cost_amount": 0
}
```
```json
{
  "skill_id": "silent_strike",
  "name": "Golpe Silencioso",
  "base_damage": 35,
  "cost_type": "shadow_chi",
  "cost_amount": 15,
  "is_silent_art": true
}
```

---

### 4. Campos `kill_count` e `kill_history` Ausentes
**Problema:** Profiler tentava acessar campos que não existiam no model Player
**Arquivo:** `backend/app/database/models/player.py`
**Solução:**
```python
kill_count: int = Field(default=0)
kill_history: List[dict] = Field(default=[], sa_column=Column(JSON))
```
**Migração:** `backend/migrate_kill_count.py`

---

### 5. Rumor Retornando String ao Invés de Dict
**Problema:** `world_sim.py` esperava `rumor['content']` mas recebia string
**Arquivo:** `backend/app/core/world_sim.py`
**Solução:**
```python
# Antes
print(f"SIM: Rumor espalhado - {rumor['content']}")
# Depois
print(f"SIM: Rumor espalhado - {rumor}")
```

---

### 6. Ações de Movimento/Observe/Meditate Não Implementadas
**Problema:** Referee parseava intent "move" mas Director não tratava
**Arquivos:**
- `backend/app/agents/referee.py` - Adicionado `destination` ao prompt
- `backend/app/agents/director.py` - Implementadas ações:
  - `move` - Viagem entre localizações
  - `observe` - Lista NPCs na cena
  - `meditate/cultivate` - Recupera Yuan Qi

---

### 7. Endpoint `/player/{id}/inventory` Ausente
**Problema:** Frontend chamava endpoint que não existia
**Arquivo:** `backend/app/main.py`
**Solução:** Adicionado endpoint:
```python
@app.get("/player/{player_id}/inventory")
async def get_player_inventory(player_id: int, ...):
    return player.inventory
```

---

### 8. Loot Não Persistia no Banco
**Problema:** Campos JSON (inventory, etc) não eram marcados como "dirty" pelo SQLAlchemy
**Arquivo:** `backend/app/database/repositories/player_repo.py`
**Solução:** Usar `flag_modified()`:
```python
from sqlalchemy.orm.attributes import flag_modified

async def update(self, player: Player) -> Player:
    flag_modified(player, 'inventory')
    flag_modified(player, 'status_effects')
    flag_modified(player, 'learned_skills')
    flag_modified(player, 'kill_history')
    # ...
```

---

## ✅ Sistemas Testados e Funcionando

### Combate
- ✅ Dano calculado corretamente com `basic_attack`
- ✅ Sistema de corrupção (Heart Demon)
- ✅ Loot gerado e persistido
- ✅ Kill count incrementado
- ✅ Epifania (Scribe) gerando novas skills

### Sistema de Vilões
- ✅ Profiler aumenta hostilidade quando player ataca
- ✅ Profiler registra kills
- ✅ Profiler pode triggerar vendetta
- ✅ Strategist move NPCs hostis

### Evolução do Mundo
- ✅ WorldSimulator tick funciona
- ✅ Rumores são espalhados
- ✅ GossipMonger processa eventos
- ✅ DailyTickSimulator inicializado

### Lógica Narrativa
- ✅ Attack - Combate funciona
- ✅ Move - Viagem entre localizações
- ✅ Observe - Lista NPCs
- ✅ Meditate - Recupera Qi
- ✅ Talk - Conversa com NPCs

### Frontend Connections
- ✅ `/player/create` - Criar jogador
- ✅ `/player/{id}` - Carregar jogador
- ✅ `/game/turn` - Enviar ação
- ✅ `/player/{id}/inventory` - Carregar inventário

---

## 📊 Estatísticas

- **Arquivos modificados:** 12
- **Bugs críticos corrigidos:** 8
- **Novos endpoints:** 1
- **Novas skills:** 2
- **Migrações de banco:** 1

---

## 🚀 Próximos Passos

1. Testar frontend completo com backend
2. Implementar tabelas de loot específicas para monstros
3. Expandir sistema de Nemesis Engine
4. Adicionar mais localizações ao mapa
5. Implementar sistema de economia completo
