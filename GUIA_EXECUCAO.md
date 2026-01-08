# 🚀 GUIA DE EXECUÇÃO - CORREÇÕES SPRINT 1 & 2

## 📋 PASSO A PASSO

### 1️⃣ Preparar Ambiente

```powershell
# Ativar ambiente virtual
cd "C:\Users\felip\Documents\RPG cultivo"
.\.venv\Scripts\Activate.ps1
```

### 2️⃣ Migrar Banco de Dados

```powershell
# Criar tabela GameLog
cd backend
python migrate_gamelog.py
```

**Resultado esperado:**
```
Creating GameLog table...
✅ GameLog table created successfully!
```

### 3️⃣ Verificar Correções

```powershell
# Rodar script de verificação
python verify_corrections.py
```

**Resultado esperado:**
```
🔍 VERIFICANDO CORREÇÕES DO SPRINT 1 E 2...

1️⃣ Verificando tabela GameLog...
   ✅ Tabela GameLog existe e está acessível

2️⃣ Verificando Chronos (tempo do mundo)...
   📅 Data: 1/1/1000
   🕐 Hora: 00:00
   🌅 Período: midnight
   🌸 Estação: Spring
   ✅ Chronos avançou corretamente: 00:00 → 01:00

3️⃣ Verificando filtro de localização de NPCs...
   📊 Total de NPCs no banco: 4
   📍 NPCs em 'Floresta Assombrada': 2
   ✅ Filtro de localização funciona

============================================================
📊 RESUMO DA VERIFICAÇÃO

✅ gamelog_table
✅ chronos_time
✅ npc_location_filter

🎯 Resultado: 3/3 testes passaram (100%)

🎉 TODAS AS CORREÇÕES ESTÃO FUNCIONANDO!
```

### 4️⃣ Iniciar Backend

```powershell
# Na pasta backend
uvicorn app.main:app --reload
```

**Verificar:** `http://localhost:8000/health`

### 5️⃣ Iniciar Frontend

```powershell
# Nova janela do PowerShell
cd "C:\Users\felip\Documents\RPG cultivo\frontend"
npm run dev
```

**Acessar:** `http://localhost:3000`

---

## 🧪 TESTES FUNCIONAIS

### Teste 1: História Persistente

1. **Criar personagem** (se não tiver)
2. **Jogar 2 turnos** (ex: "olhar ao redor", "atacar")
3. **Fechar navegador**
4. **Reabrir jogo**
5. **Verificar:** Última narração NÃO se repete

✅ **ESPERADO:** Nova narração contextualizada com o passado

### Teste 2: Relógio do Mundo

1. **Observar header** - Deve ter relógio com hora e data
2. **Jogar 1 turno**
3. **Verificar:** Hora avança +1 hora

✅ **ESPERADO:** `00:00` → `01:00` → `02:00`

### Teste 3: NPCs por Localização

1. **Console do backend:** Observar logs
2. **Jogar turno em localização vazia**
3. **Verificar log:** `Cena vazia. Gerando um novo inimigo...`
4. **Verificar:** Apenas 1 NPC spawna (não todos)

✅ **ESPERADO:** Architect cria 1 inimigo, não carrega todos do banco

### Teste 4: WorldSimulator Automático

1. **Jogar 10 turnos**
2. **Console do backend:** Buscar log
3. **Verificar:** `[WORLDSIM] Executando tick de mundo (turno 10)...`

✅ **ESPERADO:** WorldSimulator roda automaticamente

---

## 🔍 ENDPOINTS PARA TESTAR

### GET /world/time
```bash
curl http://localhost:8000/world/time
```

**Resposta:**
```json
{
  "day": 1,
  "month": 1,
  "year": 1000,
  "hour": 5,
  "minute": 0,
  "time_of_day": "dawn",
  "season": "Spring"
}
```

### GET /health/db
```bash
curl http://localhost:8000/health/db
```

**Resposta:**
```json
{
  "status": "ok",
  "db": "connected"
}
```

---

## ⚠️ TROUBLESHOOTING

### Erro: "Table 'game_logs' doesn't exist"

**Solução:**
```powershell
cd backend
python migrate_gamelog.py
```

### Erro: "No module named 'app'"

**Solução:**
```powershell
# Certifique-se de estar na pasta backend
cd backend
# Rodar com módulo Python
python -m migrate_gamelog
```

### Frontend: "Failed to fetch world time"

**Causa:** Backend não está rodando

**Solução:**
```powershell
cd backend
uvicorn app.main:app --reload
```

### NPCs não aparecem

**Causa:** Banco não foi populado

**Solução:**
```powershell
# Reiniciar backend - seed_initial_npcs roda automaticamente
# Verificar console: "Seeding initial NPCs..."
```

---

## 📊 VERIFICAÇÃO MANUAL NO BANCO

### Query GameLogs

```sql
-- Ver todos os turnos salvos
SELECT 
    turn_number, 
    player_input, 
    LEFT(scene_description, 50) as scene_preview,
    world_time,
    location
FROM game_logs
ORDER BY turn_number DESC
LIMIT 5;
```

### Query NPCs por Localização

```sql
-- Ver NPCs filtrados
SELECT name, current_location, emotional_state
FROM npcs
WHERE current_location = 'Floresta Assombrada';
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

- [ ] Banco de dados conectado (`/health/db`)
- [ ] Tabela `game_logs` criada
- [ ] Script de verificação passou (3/3)
- [ ] Backend rodando (porta 8000)
- [ ] Frontend rodando (porta 3000)
- [ ] Relógio aparece no header
- [ ] Turnos salvam no banco
- [ ] Tempo avança a cada turno
- [ ] NPCs filtrados por localização
- [ ] WorldSimulator roda a cada 10 turnos

---

## 🎯 RESULTADO ESPERADO

Ao completar todos os passos:

1. **História persiste** - Jogador pode fechar e reabrir o jogo
2. **Tempo avança** - Relógio visível e funcional
3. **NPCs contextuais** - Apenas NPCs da localização aparecem
4. **Mundo dinâmico** - Vilões se movem off-screen a cada 10 turnos

**O jogo agora tem MEMÓRIA, TEMPO e um MUNDO VIVO.** 🎉
