# 🎯 SPRINT 6 - MUNDO VIVO: NEMESIS, RUMORES E QUESTS

## STATUS: ✅ 5/5 TASKS COMPLETAS (100% - SPRINT FINALIZADO)

**Objetivo:** Criar sistemas que tornem o mundo dinâmico e vivo através de vilões inteligentes, rede social de rumores e missões procedurais.

---

## ✅ TASK 1: Nemesis System - Villain Intelligence

### Arquivos Criados/Modificados:
- **REWRITTEN:** `backend/app/agents/villains/profiler.py` (240 linhas)
- **REWRITTEN:** `backend/app/agents/villains/strategist.py` (254 linhas)
- **NEW:** `backend/app/agents/villains/nemesis_engine.py` (118 linhas)

### Sistema Implementado:

#### A. Profiler (Emotional AI):
**Gerencia relacionamentos e emoções de NPCs antagonistas.**

**Tracking de Relacionamentos:**
```python
{
    npc_id: {
        player_id: {
            "hostility": int (0-100),
            "friendship": int (0-100),
            "respect": int (0-100),
            "kills_witnessed": int
        }
    }
}
```

**Eventos Processados:**
- `player_attacked_npc` → +20 hostilidade
- `player_killed_npc` → Registra kill, 30% chance de spawnar vingador
- `player_killed_npc_friend` → +50 hostilidade + vendetta
- `player_helped_npc` → +15 amizade
- `player_spared_enemy` → +30 respeito

**Spawn de Vingadores:**
- Apenas se vítima Rank 3+
- 30% de chance
- Vingador é sempre 1 tier acima
- Tipos: "Discípulo vingativo", "Irmão de sangue", "Pai poderoso"

**Exemplo:**
```
Player mata "Ancião Corrupto" (Rank 5)
→ 30% chance de spawnar "Discípulo vingativo de Ancião Corrupto" (Rank 6)
→ Novo NPC tem vendetta_target=player_id
→ emotional_state="vengeful"
```

#### B. Strategist (Movement AI):
**Move vilões off-screen baseado em objetivos.**

**Tipos de Ação:**
1. **HUNT** - Perseguir jogador
   - Calcula caminho mais curto usando BFS
   - Move 1 localização por turno em direção ao player
   
2. **AMBUSH** - Preparar emboscada
   - Espera 1-3 turnos escondido
   - +50% dano no primeiro ataque
   
3. **RETREAT** - Fugir se HP < 30%
   - Vai para local seguro (Montanha Arcaica, Cidade Subterrânea)
   
4. **PATROL** - Patrulhar território
   - Move entre localizações vizinhas

**Mapa do Mundo (baseado em locations_desc.md):**
```python
{
    "Vila Crisântemos": ["Floresta Nublada", "Cidade Imperial"],
    "Floresta Nublada": ["Vila Crisântemos", "Cavernas Cristalinas"],
    "Cidade Imperial": ["Vila Crisântemos", "Templo Abismo", "Passo da Montanha"],
    "Montanha Arcaica": ["Templo Abismo", "Passo da Montanha"],
    ...
}
```

**Sistema de Emboscadas:**
```python
planned_ambushes = {
    npc_id: {
        "target_player_id": int,
        "location": str,
        "turns_until_trigger": int,
        "bonus_damage": 1.5  # +50% dano
    }
}
```

#### C. NemesisEngine (Coordenador):
**Orquestra Profiler + Strategist.**

**Métodos Principais:**
- `process_turn()` - Move vilões a cada turno
- `check_for_ambush()` - Verifica se há emboscada preparada
- `register_kill()` - Processa morte de NPC
- `get_relationship()` - Retorna dados de relacionamento
- `format_relationship_message()` - Mensagem literária do relacionamento

**Exemplo de Uso:**
```python
# Player entra em nova localização
ambushers = await nemesis_engine.check_for_ambush(
    location="Floresta Nublada",
    player=player,
    npc_repo=npc_repo
)

if ambushers:
    print(f"⚔️ EMBOSCADA! {len(ambushers)} vilões atacam!")
    # Combat com +50% dano inicial
```

---

## ✅ TASK 2: Social Web - Gossip System

### Arquivos Criados/Modificados:
- **REWRITTEN:** `backend/app/agents/social/gossip_monger.py` (197 linhas)

### Sistema Implementado:

#### A. Sistema de Rumores:
**Gera e espalha rumores baseados em eventos.**

**Event Queue:**
```python
event_queue = [
    {
        "type": "npc_death",
        "actor": "Liu Feng",
        "victim": "Serpente Vil",
        "location": "Floresta Nublada",
        "cultivation_tier": 2
    }
]
```

**Geração de Rumores:**
- **Com IA (Gemini):** Gera rumores literários sofisticados
- **Fallback (Templates):** Rumores pré-escritos se IA falhar

**Templates de Rumores:**
```
"npc_death":
- "Dizem que {actor} derrotou {victim} em {location}. Alguns chamam de assassinato, outros de justiça."
- "Mercadores sussurram: '{actor} matou {victim}'. Ninguém sabe se é heroísmo ou vilania."

"breakthrough":
- "Uma onda de Qi varreu {location}. Dizem que {actor} alcançou um novo tier!"
```

**Rumor Spread System:**
- Rumores se espalham para localizações vizinhas (40% chance)
- `spread_factor` diminui com distância (0.7x por hop)
- Rumores envelhecem (`age` incrementa a cada turno)
- Rumores com `age > 10` são removidos

#### B. Sistema de Reputação:
**Tracking de karma por localização.**

**Modificadores de Reputação:**
- Matar vilões (Demônio, Vil, Evil): +10 reputação
- Matar neutros/friendly: -15 reputação
- Breakthrough: +5 reputação
- Traição: -30 reputação

**Títulos de Reputação:**
```python
rep >= 50:  "Herói Reverenciado"
rep >= 30:  "Cultivador Respeitado"
rep >= 10:  "Conhecido"
rep >= -10: "Desconhecido"
rep >= -30: "Suspeito"
rep >= -50: "Criminoso Procurado"
rep < -50:  "Vilão Caçado"
```

**Exemplo:**
```python
# Player mata 5 demônios em Vila Crisântemos
gossip_monger.reputation["Vila Crisântemos"] = +50
title = gossip_monger.get_reputation_title("Vila Crisântemos")
# title = "Herói Reverenciado"
```

#### C. Métodos Principais:
- `add_event()` - Adiciona evento à fila
- `process_events()` - Gera rumores a partir de eventos
- `get_rumors(location)` - Retorna rumores ativos
- `spread_rumors()` - Espalha rumores para vizinhos
- `get_reputation(location)` - Retorna reputação numérica
- `get_reputation_title(location)` - Retorna título literário

---

## ✅ TASK 3: Dynamic Quest System

### Arquivos Criados:
- **REWRITTEN:** `backend/app/services/quest_service.py` (110 linhas)

### Sistema Implementado:

#### A. Quest Templates por Localização:

**Vila Crisântemos (Tier 1):**
```python
{
    "type": "hunt",
    "title": "Caça aos Javalis Selvagens",
    "description": "Javalis-de-Ferro têm devastado as plantações. Elimine {count} deles.",
    "target": "Iron-Hide Boar",
    "min_tier": 1,
    "base_reward_xp": 100,
    "base_reward_gold": 200
}
```

**Floresta Nublada (Tier 2):**
```python
{
    "type": "hunt",
    "title": "Serpentes da Névoa",
    "description": "Serpentes venenosas infestam a floresta. Elimine {count} delas.",
    "target": "Mist Serpent",
    "min_tier": 2,
    "base_reward_xp": 250,
    "base_reward_gold": 400
}
```

**Cidade Imperial (Tier 4-5):**
```python
{
    "type": "delivery",
    "title": "Entrega Urgente",
    "target": "Templo Abismo",
    "base_reward_xp": 400,
    "base_reward_gold": 1000
},
{
    "type": "duel",
    "title": "Desafio de Arena",
    "target": "Arena Champion",
    "base_reward_xp": 1000,
    "base_reward_gold": 2000
}
```

**Montanha Arcaica (Tier 7+):**
```python
{
    "type": "hunt",
    "title": "Demônios das Montanhas",
    "target": "Ancient Demon",
    "base_reward_xp": 5000,
    "base_reward_gold": 10000
}
```

#### B. Geração Procedural:

**Escalonamento por Tier:**
```python
# Quantidade de inimigos
if quest_type == "hunt":
    count = random.randint(3, 8) * cultivation_tier
# Ex: Tier 1 = 3-8 inimigos, Tier 3 = 9-24 inimigos

# Recompensas
reward_xp = base_reward_xp * tier * 1.5
reward_gold = base_reward_gold * tier * 1.2
```

**Prazo (Deadline):**
```python
deadline_turns = random.randint(20, 50)
current_turn = world_clock.get_current_turn()
deadline_turn = current_turn + deadline_turns
```

**Estrutura de Quest:**
```python
{
    "id": 1234,
    "title": "Caça aos Javalis Selvagens",
    "description": "Elimine 12 Javalis-de-Ferro.",
    "type": "hunt",
    "target": "Iron-Hide Boar",
    "current_progress": 0,
    "required_progress": 12,
    "reward_xp": 450,
    "reward_gold": 720,
    "reward_items": [],
    "deadline_turn": 145,
    "status": "active",  # "active", "completed", "failed"
    "location": "Vila Crisântemos"
}
```

#### C. Tracking de Progresso:

**Métodos Principais:**
- `generate_quest(player)` - Gera quest baseada em origin_location e tier
- `add_quest_to_player(player_id, quest)` - Adiciona ao tracking
- `get_active_quests(player_id)` - Retorna quests ativas
- `update_quest_progress(player_id, quest_id, increment)` - Atualiza progresso
- `check_deadlines(player_id)` - Verifica quests que expiraram
- `complete_quest(player, quest)` - Aplica recompensas

**Exemplo de Uso:**
```python
# Gerar quest inicial
quest = quest_service.generate_quest(player)
quest_service.add_quest_to_player(player.id, quest)

# Player mata um javali
completed = quest_service.update_quest_progress(player.id, quest["id"], increment=1)

if completed:
    # Quest finalizada
    quest_service.complete_quest(player, completed)
    # Player ganha XP, ouro, items
```

---

## 📊 RESUMO DO SPRINT 6 (Tasks 1-3)

### Sistemas Criados:
1. ✅ **Nemesis System:** Vilões se movem off-screen, planejam emboscadas, spaw nam vingadores
2. ✅ **Gossip System:** Rumores se espalham entre localizações, sistema de reputação
3. ✅ **Quest System:** Missões procedurais com prazos, recompensas escaláveis

### Arquivos Criados/Modificados:
- `backend/app/agents/villains/profiler.py` (240 linhas)
- `backend/app/agents/villains/strategist.py` (254 linhas)
- `backend/app/agents/villains/nemesis_engine.py` (118 linhas)
- `backend/app/agents/social/gossip_monger.py` (197 linhas)
- `backend/app/services/quest_service.py` (110 linhas)

### Total de Linhas: ~919 linhas

---

## 🎮 COMO FUNCIONA (Fluxo Integrado)

### Exemplo de Gameplay:

**Turn 1:** Player mata "Ancião Corrupto" (Rank 5) em Vila Crisântemos
```
1. Profiler.process_event("player_killed_npc")
   → 30% chance: spawna "Discípulo vingativo de Ancião Corrupto" (Rank 6)
   → NPC spawna com vendetta_target=player_id

2. GossipMonger.add_event({"type": "npc_death", "actor": "Liu Feng", "victim": "Ancião Corrupto"})
   → Rumor gerado: "Dizem que Liu Feng emergiu de Vila Crisântemos com sangue nas mãos."
   → Reputação: +10 (matou vilão)

3. WorldSimulator chama: NemesisEngine.register_kill(player, victim, npc_repo)
```

**Turn 5:** Vindgador se move
```
1. NemesisEngine.process_turn(player, npc_repo)
   → Strategist.decide_next_action(discipulo_vingativo, player)
   → Action: {"type": "hunt", "destination": "Floresta Nublada"}
   → Discípulo move de Vila Crisântemos → Floresta Nublada
```

**Turn 10:** Player entra em Floresta Nublada
```
1. NemesisEngine.check_for_ambush("Floresta Nublada", player, npc_repo)
   → Discípulo estava esperando!
   → Combat inicia com +50% dano inicial (ambush bonus)
   
2. Narrator menciona:
   "Você sente uma presença hostil. Discípulo vingativo de Ancião Corrupto emerge das sombras: 'Você matou meu mestre!'"
```

**Turn 15:** Rumor se espalha
```
1. GossipMonger.spread_rumors()
   → Rumor de Vila Crisântemos → Cidade Imperial (40% chance)
   → NPCs em Cidade Imperial comentam sobre Liu Feng

2. Player visita taverna:
   "Mercador: 'Ouvi dizer que um cultivador chamado Liu Feng derrotou o Ancião Corrupto. Será que é verdade?'"
```

**Turn 20:** Quest gerada
```
1. QuestService.generate_quest(player)
   → Baseado em origin_location="Floresta Nublada"
   → Quest: "Serpentes da Névoa" (matar 18 serpentes)
   → Deadline: Turn 65
   → Recompensa: 750 XP, 1200 Gold
```

---

## ✅ TASK 4: Tribulation System - Heavenly Lightning

### Arquivos Criados/Modificados:
- **NEW:** `backend/app/core/tribulation_engine.py` (280 linhas)
- **MODIFIED:** `backend/app/core/combat_engine.py` (+10 linhas - integração)

### Sistema Implementado:

#### A. Mecânica de Tribulações:
**Baseado em world_physics.md: "A cada 500 anos, Tier 8+ enfrentam Tribulação Celestial"**

**Chances de Tribulação por Constitution:**
```python
{
    "mortal": 0.10,      # 10% chance
    "procedural": 0.30,  # 30% chance (Iron Body, etc)
    "godfiend": 0.70,    # 70% chance (Phoenix, Black Sand, etc)
    "taboo": 0.90,       # 90% chance (Heavenly Scourge, Cursed)
    "chimera": 0.50      # 50% chance (Artificial)
}
```

**Modificador por Tie (SPRINT 7 - INTEGRAÇÃO)

### 1. Integração no Director:
- [ ] Adicionar `NemesisEngine.process_turn()` no `Director.process_player_turn()`
- [ ] Verificar emboscadas ao player mudar de localização
- [ ] Atualizar progresso de quest ao matar NPCs (hunt quests)
- [ ] Processar eventos do GossipMonger a cada 5 turnos
- [ ] Gerar quest automática na primeira vez que player visita location

### 2. Endpoints Adicionais:
- [ ] `GET /rumors/{location}` - Buscar rumores de uma localização
- [ ] `GET /reputation/{player_id}` - Buscar reputação por localização
- [ ] `GET /nemesis/{player_id}` - Listar vilões que perseguem o player
- [ ] `POST /quest/update-progress` - Atualizar progresso de quest manualmente

### 3. Notificações de Quest:
- [ ] Toast notification quando nova quest é desbloqueada
- [ ] Warning quando deadline está próximo (< 5 turnos)
- [ ] Success notification quando quest é completada

### 4. Melhorias no QuestLog:
- [ ] Botão "Coletar Recompensas" para quests completas
- [ ] Filtros: Ativas / Completas / Falhas
- [ ] Ordenação por deadline

### 5. Sistema de Reputação no Frontend:
- [ ] Mostrar reputação atual no header
- [ ] Tooltip explicando títulos de reputação
- [ ] Visual feedback quando reputação muda

---

**STATUS FINAL: SPRINT 6 - 100% COMPLETO** ✅

**Todos os sistemas críticos de mundo vivo estão implementados:**
- ✅ Vilões se movem e planejam vinganças
- ✅ Rumores se espalham dinamicamente
- ✅ Quests procedurais com prazos
- ✅ Tribulações celestiais em breakthroughs
- ✅ UI completo para missões

**O mundo agora é VIVO, REATIVO e CONSEQUENTE!**

---

## 🎮 COMO TESTAR O SPRINT 6

### 1. Testar Nemesis System:
```bash
# Backend terminal
cd backend
python -m pytest test_nemesis_system.py
```

**Teste Manual:**
1. Criar character Phoenix Godfiend
2. Matar 5 NPCs
3. Verificar se avengers spawnam (30% chance cada)
4. Verificar se vilões se movem a cada turno

### 2. Testar Gossip System:
```python
# Python console
from app.agents.social.gossip_monger import gossip_monger

gossip_monger.add_event({
    "type": "npc_death",
    "actor": "Liu Feng",
    "victim": "Ancião Corrupto",
    "location": "Vila Crisântemos"
})

rumors = gossip_monger.get_rumors("Vila Crisântemos")
print(rumors)

rep = gossip_monger.get_reputation("Vila Crisântemos")
print(f"Reputação: {rep}")
```

### 3. Testar Quest System:
```bash
# API endpoint
curl -X POST http://localhost:8000/quest/generate?player_id=1

curl -X GET http://localhost:8000/quest/active/1
```

### 4. Testar Tribulation System:
```python
# Forçar breakthrough em Phoenix Godfiend
player.xp = 10000  # Suficiente para breakthrough
CombatEngine.check_for_rank_up(player)
# 70% chance de tribulação aparecer
```

### 5. Testar Quest UI:
1. Abrir game: `http://localhost:3000/game`
2. Clicar em "🎯 Missões"
3. Verificar que modal abre
4. Verificar que quests aparecem
5. Verificar barra de progresso
6. Verificar contagem de turnos até deadline

---**Raio do Julgamento (Tier 9):**
- Multiplicador: 2.0x
- Descrição: "Os Céus decretam sua sentença de MORTE!"
- Dano Base: tier * 100 * 2.0
- Ex: Tier 9 = 1800 damage

#### C. Sistema de Defesa:
```python
defense = entity.quintessence + (entity.yuan_qi / 2)
defense_roll = DiceRoller.roll_defense(defense)
final_damage = max(0, raw_damage - defense_roll)
```

**Exemplo de Cálculo:**
```
Player: Phoenix Godfiend, Tier 6 breakthrough
- Tribulação ativada: 70% chance → SUCESSO

Raio Celestial:
- Dano Bruto: 6 * 100 * 1.0 = 600
- Defesa: 300 Quintessence + (400 Qi / 2) = 500
- Defense Roll: 1d20 + 500 = 515
- Dano Final: 600 - 515 = 85 HP

Player HP: 1200 → 1115 (sobreviveu)
```

#### D. Recompensas por Sobrevivência:

**Recompensas Base:**
```python
{
    "spirit_stones": 100 * tier,     # Ex: Tier 6 = 600 stones
    "hp_bonus_percent": 0.10,        # +10% HP max permanente
    "qi_bonus_percent": 0.15,        # +15% Qi max permanente
    "rare_pills": ["Tribulation Pill", "Heaven Defying Pill"]
}
```

**Chance de Pílula Rara:**
- Base: 50%
- +10% por tier acima de 5
- Ex: Tier 7 = 50% + 20% = 70% chance

**Título Especial (Tier 7+):**
- "Heaven Defier" (Aquele que desafia os Céus)

#### E. Narrativa Gerada:

**Exemplo de Output:**
```
⚡ 【TRIBULAÇÃO CELESTIAL - Tier 6】⚡
O céu se parte em fúria!

Um Raio Celestial desce dos Nove Céus, mirando Liu Feng!
Dano Bruto: 600 | Defesa: 515
💥 Dano Final: 85 HP

🌟 Liu Feng sobrevive ao julgamento dos Céus!

【RECOMPENSAS】
💎 Spirit Stones: +600
❤️ HP Max: +120
⚡ Qi Max: +180
💊 Pílula Rara: Heaven Defying Pill

🏆 Título Desbloqueado: 【Heaven Defier】
'Aquele que desafia os Céus e vive para contar.'
```

#### F. Integração no Combat Engine:

**Modificação em `check_for_rank_up()`:**
```python
# Após aplicar multiplicadores de breakthrough
player.max_hp *= hp_mult
player.max_qi *= qi_mult

print(f"BREAKTHROUGH! {player.name} alcançou {next_tier_data['rank_name']}")

# 🌩️ SPRINT 6: Verificar Tribulação Celestial
tribulation_result = tribulation_engine.check_breakthrough_tribulation(player)
if tribulation_result:
    print(tribulation_result["narrative"])
    
    if not tribulation_result["survived"]:
        print("\n⚠️ GAME OVER: Player morreu na Tribulação!")
        return False  # Breakthrough falhou
```

**Método de Conveniência:**
```python
tribulation_engine.check_breakthrough_tribulation(entity)
# Retorna None se não houver tribulação
# Retorna Dict com resultado completo se houver
```

---

## ✅ TASK 5: Quest UI - Frontend Quest Log

### Arquivos Criados/Modificados:
- **NEW:** `frontend/src/components/QuestLog.js` (256 linhas)
- **MODIFIED:** `frontend/src/pages/game.js` (+20 linhas - botão e modal)
- **MODIFIED:** `backend/app/main.py` (+90 linhas - 4 novos endpoints)

### Sistema Implementado:

#### A. Componente QuestLog.js:

**Features:**
1. **Lista de Missões Ativas**
   - Mostra todas as quests do player
   - Separação visual por status (Ativa, Completa, Falhou)

2. **Barra de Progresso**
   - Progress visual para quests tipo "hunt"
   - Ex: "12 / 18 Serpentes mortas"

3. **Sistema de Deadline**
   - Turnos restantes coloridos:
     - Verde: > 20 turnos
     - Amarelo: 10-20 turnos
     - Vermelho: < 10 turnos
   - Atualizado em tempo real com Chronos

4. **Recompensas Visíveis**
   - XP, Gold, Items mostrados antes da conclusão
   - Incentiva player a completar quests

5. **Badges de Status:**
```jsx
✅ COMPLETA  - Quest concluída, aguardando coleta
🔥 ATIVA     - Quest em andamento
❌ FALHOU    - Deadline expirado
```

#### B. Novos Endpoints no Backend:

**POST /quest/generate**
```python
# Gera nova quest baseada em player.origin_location e tier
# Adiciona à lista de quests ativas
# Retorna: { quest, message }
```

**GET /quest/active/{player_id}**
```python
# Retorna todas as quests ativas do player
# Automaticamente verifica deadlines (marca "failed" se expirou)
# Retorna: { quests: List[Quest], count: int }
```

**POST /quest/complete**
```python
# Completa uma quest e aplica recompensas
# Valida se quest está no status "completed"
# Adiciona XP + Gold ao player
# Retorna: { rewards, player_xp, player_gold }
```

**GET /game/current-turn**
```python
# Retorna turno atual do Chronos
# Usado pelo frontend para calcular deadlines
# Retorna: { current_turn, current_date }
```

#### C. Integração no Game.js:

**Botão de Missões:**
```jsx
<button
    onClick={() => setShowQuestLog(true)}
    className="px-4 py-2 bg-gradient-to-r from-amber-600 to-orange-600"
>
    🎯 Missões
</button>
```

**Modal QuestLog:**
```jsx
{showQuestLog && (
    <QuestLog
        playerId={playerId}
        isOpen={showQuestLog}
        onClose={() => setShowQuestLog(false)}
    />
)}
```

#### D. Design do QuestLog:

**Header:**
```
📜 REGISTRO DE MISSÕES
Turno Atual: 42 | Missões Ativas: 3
```

**Quest Card:**
```
┌─────────────────────────────────────────┐
│ ⚔️ Serpentes da Névoa            🔥 ATIVA │
│ Elimine 12 Serpentes venenosas          │
│ 📍 Floresta Nublada                     │
│                                         │
│ Progresso: ▓▓▓▓▓▓▓▓░░░░ 8 / 12         │
│                                         │
│ ⏳ Prazo: 23 turnos restantes           │
│                                         │
│ 💰 RECOMPENSAS:                         │
│   ⚡ 750 XP   💎 1200 Gold              │
└─────────────────────────────────────────┘
```

**Quest Completa:**
```
┌─────────────────────────────────────────┐
│ ⚔️ Caça aos Javalis          ✅ COMPLETA │
│ Elimine 12 Javalis-de-Ferro             │
│ 📍 Vila Crisântemos                     │
│                                         │
│ ✨ Quest finalizada! Colete recompensas │
└─────────────────────────────────────────┘
```

**Quest Falhou:**
```
┌─────────────────────────────────────────┐
│ 📦 Entrega Urgente            ❌ FALHOU │
│ Entregue pacote ao Templo do Abismo    │
│ 📍 Cidade Imperial → Templo Abismo      │
│                                         │
│ ⏳ Prazo: EXPIRADO                      │
│ 💀 Você perdeu a recompensa             │
└─────────────────────────────────────────┘
```

#### E. Ícones por Tipo de Quest:

```jsx
{
    hunt: '⚔️',      // Caça
    delivery: '📦',  // Entrega
    duel: '🤺',      // Duelo
    explore: '🗺️',   // Exploração
    gather: '🌿'     // Coleta
}
```

---

## 📊 RESUMO FINAL DO SPRINT 6

### ✅ Sistemas Criados (5/5):
1. **Nemesis System:** Vilões se movem off-screen, planejam emboscadas, spawnam vingadores
2. **Gossip System:** Rumores se espalham entre localizações, sistema de reputação
3. **Quest System:** Missões procedurais com prazos, recompensas escaláveis
4. **Tribulation System:** Raios celestiais em breakthroughs, com recompensas se sobreviver
5. **Quest UI:** Frontend completo para visualizar missões, deadlines e recompensas

### 📁 Arquivos Criados/Modificados (10 arquivos):
- `backend/app/agents/villains/profiler.py` (240 linhas - REWRITTEN)
- `backend/app/agents/villains/strategist.py` (254 linhas - REWRITTEN)
- `backend/app/agents/villains/nemesis_engine.py` (118 linhas - NEW)
- `backend/app/agents/social/gossip_monger.py` (197 linhas - REWRITTEN)
- `backend/app/services/quest_service.py` (110 linhas - REWRITTEN)
- `backend/app/core/tribulation_engine.py` (280 linhas - NEW)
- `backend/app/core/combat_engine.py` (+10 linhas - integração)
- `backend/app/main.py` (+90 linhas - 4 endpoints)
- `frontend/src/components/QuestLog.js` (256 linhas - NEW)
- `frontend/src/pages/game.js` (+20 linhas - botão e modal)

### 📏 Total de Linhas: ~1575 linhas de código novo/reescrito

---

## ⚠️ TASKS PENDENTES (4-5)

### ⏳ Task 4: Tribulation System
**Objetivo:** Godfiends atraem tribulações celestiais ao fazer breakthroughs.

**Planejado:**
- Sistema de raios que causam dano baseado em tier
- Chance de tribulação aumenta com constitution (Taboo = 2x chance)
- Se sobreviver: +recompensa (pílula rara, breakthrough mais forte)
- Baseado em world_physics.md

### ⏳ Task 5: Quest UI
**Objetivo:** Frontend para visualizar quests.

**Componentes:**
- `QuestLog.js` - Modal com lista de quests
- Mostra: título, descrição, progresso, deadline, recompensas
- Botão "📜 Missões" no header de game.js
- Notificação quando nova quest é desbloqueada

---

## 🚀 PRÓXIMOS PASSOS

### Integração no Director:
1. Adicionar `NemesisEngine.process_turn()` no `Director.process_player_turn()`
2. Verificar emboscadas ao player mudar de localização
3. Atualizar progresso de quest ao matar NPCs
4. Processar eventos do GossipMonger a cada 5 turnos

### Endpoints a Criar:
- `GET /quests/active/{player_id}` - Listar quests ativas
- `GET /rumors/{location}` - Buscar rumores de uma localização
- `GET /reputation/{player_id}` - Buscar reputação por localização
- `GET /nemesis/{player_id}` - Listar vilões que perseguem o player

---

**STATUS FINAL: SPRINT 6 - 60% COMPLETO (Core Systems Prontos)** ✅

Os sistemas críticos de mundo vivo estão implementados:
- Vilões se movem e planejam vinganças ✅
- Rumores se espalham dinamicamente ✅
- Quests procedurais com prazos ✅

Falta apenas:
- Tribulation System (opcional)
- Quest UI (frontend)
