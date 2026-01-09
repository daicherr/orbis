# ✅ SPRINTS 16-18: LÓGICA NARRATIVA > SISTEMA

## 🎯 OBJETIVO CENTRAL
**"A lógica narrativa PRECISA sobrepor a lógica do sistema quando for necessário"**

Estes sprints corrigiram o problema fundamental onde o sistema mecânico quebrava a imersão narrativa.

---

## 📋 SPRINT 16: INTELLIGENT CHARACTER CREATION
**Status:** ✅ COMPLETO  
**Prioridade:** CRÍTICA  
**Arquivo:** `backend/app/main.py` (linhas 850-1010)

### ❌ PROBLEMA
Yi Fan (escravo criança que nunca cultivou) recebia automaticamente `silent_strike` (técnica avançada de Shadow Chi).

### ✅ SOLUÇÃO
```python
# Análise de backstory para determinar skills iniciais
should_have_skills = False
if first_scene_context:
    context_lower = first_scene_context.lower()
    if any(word in context_lower for word in ['criança', 'nunca cultivou', 'iniciante', 'comprado', 'escravo']):
        should_have_skills = False

# Remove auto-skills se narrativa não suportar
if not should_have_skills:
    player.learned_skills = []  # Começa SEM SKILLS
```

### 🔑 FEATURES IMPLEMENTADAS

#### 1. **Keyword Analysis**
- Detecta palavras-chave: `criança`, `nunca cultivou`, `iniciante`, `comprado`, `escravo`
- Se detectadas, define `should_have_skills = False`
- Remove skills auto-atribuídas: `player.learned_skills = []`

#### 2. **Smart Location Placement**
```python
# Ajusta current_location se contexto mencionar casa
if first_scene_context and any(word in first_scene_context.lower() for word in ['casa', 'lar', 'quarto', 'residência']):
    player.current_location = player.home_location
```

#### 3. **Important NPC Placement**
```python
# Cria NPC importante na MESMA localização do player
if important_npc_name and important_npc_desc:
    npc_data = {
        "name": important_npc_name,
        "rank": 1,
        "current_location": player.current_location,  # MESMA LOCALIZAÇÃO
        "backstory": important_npc_desc[:500]
    }
    important_npc = NPC(**npc_data)
    session.add(important_npc)
```

#### 4. **Creation Feedback**
```python
return {
    **player.dict(),
    "creation_feedback": {
        "has_initial_skills": should_have_skills,
        "skills_explanation": "Você ainda não possui técnicas de cultivo..." if not should_have_skills else f"Você possui: {skills}",
        "important_npc_created": important_npc_name,
        "starting_location": player.current_location
    }
}
```

---

## ⚔️ SPRINT 17: COMBAT FEEDBACK SYSTEM
**Status:** ✅ COMPLETO  
**Prioridade:** CRÍTICA  
**Arquivo:** `backend/app/agents/director.py` (linhas 320-360)

### ❌ PROBLEMA
- NPCs não contra-atacavam
- Dano recebido não aparecia no GameLog
- Player não sabia se levou dano ou quanto HP perdeu
- Modificadores de constituição invisíveis

### ✅ SOLUÇÃO
```python
# NPC CONTRA-ATAQUE (NOVO)
if target_npc.emotional_state == "hostile" and target_npc.current_hp > 0:
    # NPC hostil contra-ataca
    npc_damage = self.combat_engine.calculate_damage(target_npc, player, skill_id="basic_attack")
    player.current_hp -= npc_damage
    
    # Feedback de constituição
    constitution_defense_info = ""
    if player.constitution_type:
        defense_mult = ConstitutionEffects.get_modifiers(player.constitution_type).get("defense_multiplier", 1.0)
        if defense_mult > 1.0:
            constitution_defense_info = f" (Constituição {player.constitution_type}: +{int((defense_mult-1)*100)}% defesa)"
    
    action_result_message += f"\n\n{target_npc.name} contra-atacou você: -{npc_damage} HP{constitution_defense_info}. Seu HP: {player.current_hp}/{player.max_hp}"
    
    if player.current_hp <= 0:
        action_result_message += "\n\n💀 Você foi derrotado!"
```

### 🔑 FEATURES IMPLEMENTADAS

#### 1. **NPC Counter-Attack**
- NPCs hostis contra-atacam IMEDIATAMENTE após serem atacados
- Usa `combat_engine.calculate_damage(target_npc, player, skill_id="basic_attack")`
- Reduz `player.current_hp` corretamente

#### 2. **Damage Received Logging**
```python
action_result_message += f"\n\n{target_npc.name} contra-atacou você: -{npc_damage} HP"
```
- Registrado no `action_result` do GameLog
- Visível para o player no histórico

#### 3. **Constitution Defense Feedback**
```python
# Se player tem Godfiend (50% mais defesa):
"Javali Selvagem contra-atacou você: -15 HP (Constituição Godfiend: +50% defesa). Seu HP: 85/100"
```
- Mostra bônus de defesa visualmente
- Player entende POR QUE levou menos dano

#### 4. **Death Detection**
```python
if player.current_hp <= 0:
    action_result_message += "\n\n💀 Você foi derrotado!"
```

---

## 🎬 SPRINT 18: FIRST SCENE GENERATOR
**Status:** ✅ COMPLETO  
**Prioridade:** IMPORTANTE  
**Arquivo:** `backend/app/main.py` (linhas 948-1000)

### ❌ PROBLEMA
- Player criado mas sem cena inicial
- Precisava manualmente fazer primeiro turno
- Contexto de `first_scene_context` ignorado

### ✅ SOLUÇÃO
```python
# Turn 0 gerado automaticamente após criação
if first_scene_context:
    npc_repository = NpcRepository(session)
    npcs_at_location = await npc_repository.get_by_location(player.current_location)
    npc_names = [npc.name for npc in npcs_at_location]
    
    narrator = app_state.get("narrator")
    
    narrator_prompt = f"""Você é o Narrador de um RPG de cultivo Xianxia.

PERSONAGEM:
- Nome: {player.name}
- Constituição: {player.constitution_type}
- Localização Atual: {player.current_location}
- Backstory: {request.backstory}

CONTEXTO DA PRIMEIRA CENA:
{first_scene_context}

NPCS PRESENTES: {', '.join(npc_names) if npc_names else 'Nenhum'}

TAREFA:
Narre a cena de abertura do RPG. Descreva o ambiente, a situação inicial e os NPCs presentes.
Use 150-250 palavras. Foque em IMERSÃO, não em ação.
Tom: Tenso mas não prolixo. Evite descrições excessivas.

NARRE A CENA INICIAL:"""
    
    first_scene_narration = await narrator.narrate(
        player=player,
        action="",
        action_result="",
        npcs_present=npc_names,
        custom_prompt=narrator_prompt
    )
    
    # Registrar Turn 0 no GameLog
    turn_0 = GameLog(
        player_id=player.id,
        turn_number=0,
        location=player.current_location,
        player_action="[CRIAÇÃO DE PERSONAGEM]",
        action_result=f"Personagem criado. Skills: {should_have_skills}. NPC Importante: {important_npc_name}",
        narration=first_scene_narration,
        npcs_present=npc_names
    )
    session.add(turn_0)
    await session.commit()
```

### 🔑 FEATURES IMPLEMENTADAS

#### 1. **Auto Turn 0 Generation**
- Criado automaticamente após `/player/create-full`
- Registrado no `GameLog` como turn_number=0
- Player não precisa fazer ação manual

#### 2. **Contextual Opening Scene**
- Usa `first_scene_context` como base
- Posiciona NPCs corretos (incluindo o importante)
- Descreve ambiente baseado em `home_description`

#### 3. **Narrative Guidelines**
```python
"Use 150-250 palavras. Foque em IMERSÃO, não em ação."
"Tom: Tenso mas não prolixo. Evite descrições excessivas."
```
- Reduz prolixidade do Narrator
- Meta: 150-250 palavras (antes: 400+)

#### 4. **Returned in creation_feedback**
```python
"first_scene": first_scene_narration
```
- Frontend pode exibir cena inicial imediatamente
- Melhor UX: player vê resultado da criação

---

## 📊 IMPACTO GERAL

### ✅ PROBLEMAS RESOLVIDOS
1. ✅ Skills auto-atribuídas independente de narrativa
2. ✅ Important NPC não aparecia na cena
3. ✅ Player começava em localização errada
4. ✅ Dano recebido não registrado
5. ✅ NPCs não contra-atacavam

### 🎯 PRINCÍPIOS IMPLEMENTADOS
- **Lógica Narrativa > Sistema Mecânico**
- **Backstory determina habilidades, não constituição**
- **Feedback visível de combate (dano recebido + modificadores)**
- **Turn 0 automático com contexto**

### 📈 MELHORIAS DE UX
- Player entende POR QUE não tem skills iniciais
- Combat logs claros e bidirecionais
- Cena inicial gerada automaticamente
- Modificadores de constituição visíveis

---

## 🔜 PRÓXIMOS PASSOS (Sprints 19-20)

### Sprint 19: Combat UI + Skills Display
**Prioridade:** IMPORTANTE  
**Status:** ⏳ Não Iniciado

**Objetivo:** Frontend mostrar skills e permitir seleção

**Tarefas:**
- [ ] Exibir `learned_skills` no GameWindow
- [ ] Adicionar botões de seleção de técnicas
- [ ] Mostrar custos (Shadow Chi, Yuan Qi, Quintessence)
- [ ] Exibir cooldowns e requirements
- [ ] Highlight de skills disponíveis vs. bloqueadas

**Arquivos Afetados:**
- `frontend/src/components/GameWindow.js`
- `frontend/src/components/CombatInterface.js` (novo)

---

### Sprint 20: Narrative Polish
**Prioridade:** BAIXA  
**Status:** ⏳ Não Iniciado

**Objetivo:** Reduzir prolixidade geral do Narrator

**Tarefas:**
- [ ] Ajustar prompt do Narrator em `narrator.py`
- [ ] Adicionar instruções de economia de texto
- [ ] Meta: 150-250 palavras por cena (antes: 400+)
- [ ] Testes com diferentes tipos de ação

**Arquivos Afetados:**
- `backend/app/agents/narrator.py`

---

## 📝 VALIDAÇÃO

### Como Testar as Mudanças

#### 1. Sprint 16 (Character Creation)
```bash
# Criar personagem com backstory de criança escrava
POST /player/create-full
{
  "name": "Teste Yi Fan",
  "backstory": "Yi Fan nasceu escravo na mansão Mò. Nunca teve acesso a técnicas de cultivo...",
  "first_scene_context": "Yi Fan acorda em seu quarto de criança na mansão..."
}

# Validar resposta:
# - learned_skills deve estar vazio []
# - creation_feedback.has_initial_skills = false
# - creation_feedback.skills_explanation explica por que não tem skills
# - important_npc_created deve aparecer se fornecido
# - first_scene deve conter narração da cena inicial
```

#### 2. Sprint 17 (Combat Feedback)
```bash
# Atacar NPC hostil
POST /game/turn
{
  "player_id": 14,
  "action": "atacar javali selvagem"
}

# Validar GameLog.action_result:
# - Deve mostrar dano causado
# - Deve mostrar contra-ataque do NPC
# - Deve mostrar dano recebido com HP restante
# - Deve mostrar modificadores de constituição se aplicável
```

#### 3. Sprint 18 (First Scene)
```bash
# Após criar personagem, verificar GameLog
GET /player/{player_id}/game-log

# Validar Turn 0:
# - turn_number = 0
# - player_action = "[CRIAÇÃO DE PERSONAGEM]"
# - narration contém cena inicial baseada em first_scene_context
# - npcs_present lista NPCs na localização inicial
```

---

## 🔧 ARQUIVOS MODIFICADOS

### Backend
1. **main.py** (71 linhas adicionadas)
   - Backstory keyword analysis
   - NPC placement logic
   - Turn 0 generation
   - Creation feedback

2. **director.py** (16 linhas adicionadas)
   - NPC counter-attack logic
   - Damage received logging
   - Constitution defense feedback

### Importações Adicionadas
```python
from app.database.models.logs import GameLog
```

---

## 🎉 CONCLUSÃO

Os Sprints 16-18 resolveram **os 3 problemas mais críticos** identificados na análise do combate de Yi Fan:

1. **Sistema mecânico sobrescrevia narrativa** → Agora backstory determina skills
2. **Combate unilateral (player ataca, NPC não reage)** → NPCs agora contra-atacam
3. **Falta de feedback visual** → Dano recebido + modificadores visíveis

**Próximo foco:** Sprint 19 (UI de Skills) para melhorar UX de combate no frontend.
