# CHARACTER CREATION SYSTEM - DIAGRAMA DE ARQUITETURA

## 🎯 OVERVIEW DO SISTEMA

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CHARACTER CREATION WIZARD                          │
│                         (Frontend React)                              │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
        ┌───────▼────────┐  ┌─────▼──────┐  ┌───────▼────────┐
        │  STEP 1        │  │  STEP 2    │  │  STEP 3        │
        │  Nome +        │  │  Escolha   │  │  Local de      │
        │  Aparência     │  │  Constit.  │  │  Origem        │
        └────────────────┘  └────────────┘  └────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │    STEP 4         │
                         │  SESSION ZERO     │
                         │  (IA-Driven)      │
                         └─────────┬─────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        │   POST /character/       │     POST /player/        │
        │   session-zero           │     create-full          │
        │                          │                          │
┌───────▼─────────┐        ┌───────▼──────────┐      ┌──────▼───────┐
│  Architect      │        │  Architect +      │      │  Player      │
│  + Gemini       │        │  PlayerRepository │      │  Repository  │
│  (Generate      │        │  (Generate        │      │  (Save to    │
│   Questions)    │        │   Backstory)      │      │   Database)  │
└─────────────────┘        └───────────────────┘      └──────────────┘
        │                          │                          │
        └──────────────────────────┴──────────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │  PostgreSQL     │
                          │  (Player Table) │
                          │  + 4 New Fields │
                          └─────────────────┘
```

---

## 📊 FLUXO DE DADOS DETALHADO

### 1. SESSION ZERO REQUEST

```
Frontend (Step 4)
    │
    │ formData = {
    │   name: "Li Xiao",
    │   constitution: "Godfiend (Black Sand)",
    │   origin_location: "Cavernas Cristalinas"
    │ }
    │
    └──► POST /character/session-zero
            │
            ├──► Backend: main.py (SessionZeroRequest)
            │         │
            │         └──► Architect.gemini_client.generate_content_async()
            │                   │
            │                   └──► Gemini API (Flash Model)
            │                         Prompt: "Gere 3 perguntas para {name}
            │                                  que é {constitution} de
            │                                  {origin}..."
            │                         │
            │                         ◄──── Response: Text (3 perguntas)
            │                               │
            │                               └─► Parse + Split('\n')
            │                                       │
            │                                       └─► SessionZeroResponse
            │                                             questions: [...]
            │
            ◄──── { questions: ["Q1", "Q2", "Q3"] }
```

### 2. PLAYER CREATION REQUEST

```
Frontend (Step 4 - After Answers)
    │
    │ completeData = {
    │   name: "Li Xiao",
    │   appearance: "Jovem de 18 anos...",
    │   constitution: "Godfiend (Black Sand)",
    │   origin_location: "Cavernas Cristalinas",
    │   session_zero_answers: [
    │     "Quando meu mestre foi assassinado...",
    │     "Sacrifiquei minha família...",
    │     "Minha irmã mais nova..."
    │   ]
    │ }
    │
    └──► POST /player/create-full
            │
            ├──► Backend: main.py (CreateCharacterRequest)
            │         │
            │         ├─[1]─► Gemini: Generate Backstory
            │         │         Prompt: "Crie um parágrafo narrativo
            │         │                  para {name} com {constitution}
            │         │                  de {origin} que respondeu:
            │         │                  {answers}"
            │         │         │
            │         │         ◄─── Backstory (4-6 linhas xianxia)
            │         │
            │         └─[2]─► PlayerRepository.create()
            │                   │
            │                   └──► PostgreSQL INSERT
            │                         INSERT INTO player (
            │                           name,
            │                           appearance,
            │                           constitution_type,
            │                           origin_location,
            │                           backstory,
            │                           current_location,
            │                           ...default values...
            │                         )
            │                         │
            │                         ◄─── Player (id=1, ...)
            │
            ◄──── Player JSON {
                    id: 1,
                    name: "Li Xiao",
                    appearance: "...",
                    constitution_type: "Godfiend (Black Sand)",
                    origin_location: "Cavernas Cristalinas",
                    backstory: "Li Xiao, nascido nas...",
                    current_location: "Cavernas Cristalinas",
                    cultivation_tier: 1,
                    ...
                  }
```

---

## 🗂️ ESTRUTURA DE ARQUIVOS (Sprint 4)

```
RPG cultivo/
│
├── frontend/
│   └── src/
│       ├── components/
│       │   └── CharacterCreationWizard.js  ← [NOVO] 560 linhas
│       │       ├─ Step 1: Nome + Aparência
│       │       ├─ Step 2: Constituição (3 tipos)
│       │       ├─ Step 3: Origem (5 locais)
│       │       └─ Step 4: Session Zero (3Q+3A)
│       │
│       └── pages/
│           └── index.js  ← [MODIFICADO]
│               ├─ showWizard toggle
│               └─ handleWizardComplete()
│
├── backend/
│   ├── migrate_character_creation.py  ← [NOVO] Migração SQL
│   │
│   ├── test_character_creation.py  ← [NOVO] Teste automatizado
│   │
│   └── app/
│       ├── main.py  ← [MODIFICADO]
│       │   ├─ POST /character/session-zero
│       │   └─ POST /player/create-full
│       │
│       └── database/
│           ├── models/
│           │   └── player.py  ← [MODIFICADO]
│           │       ├─ +appearance: Optional[str]
│           │       ├─ +constitution_type: str
│           │       ├─ +origin_location: str
│           │       └─ +backstory: Optional[str]
│           │
│           └── repositories/
│               └── player_repo.py  ← [MODIFICADO]
│                   └─ create() com novos params
│
└── SPRINT_4_*.md  ← [NOVOS] Documentação
    ├─ SPRINT_4_CHARACTER_CREATION.md (Técnico)
    ├─ SPRINT_4_SUMMARY.md (Executivo)
    └─ SPRINT_4_IMPLEMENTATION_COMPLETE.md (Checklist)
```

---

## 🎨 UI/UX FLOW (Visão do Usuário)

```
┌─────────────────────────────────────────────────────────────┐
│                    LANDING PAGE                             │
│                                                             │
│              ╔═══════════════════════╗                      │
│              ║  Códice Triluna       ║                      │
│              ╚═══════════════════════╝                      │
│                                                             │
│        ┌───────────────────────────────────┐               │
│        │  ✨ Novo Cultivador              │ ◄─── Clica    │
│        └───────────────────────────────────┘               │
│        ┌───────────────────────────────────┐               │
│        │  📖 Continuar Jornada            │               │
│        └───────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               CHARACTER CREATION WIZARD                      │
│                                                             │
│  [▓▓▓▓░░░░░░] 1/4                                          │
│                                                             │
│  PASSO 1: IDENTIDADE                                       │
│  ┌────────────────────────────────────┐                    │
│  │ Nome do Cultivador:                │                    │
│  │ [Li Xiao________________]          │                    │
│  └────────────────────────────────────┘                    │
│                                                             │
│  ┌────────────────────────────────────┐                    │
│  │ Aparência (opcional):              │                    │
│  │ [Jovem de 18 anos, olhos dourados]│                    │
│  │ [cicatriz no rosto...]             │                    │
│  └────────────────────────────────────┘                    │
│                                                             │
│                    [Próximo →]                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  [▓▓▓▓▓▓▓▓░░] 2/4                                          │
│                                                             │
│  PASSO 2: CONSTITUIÇÃO                                     │
│                                                             │
│  ⚪ Mortal 🌱                                              │
│     Pros: Versatilidade, equilíbrio                        │
│     Cons: Crescimento mais lento                           │
│                                                             │
│  ● Godfiend ⚡                                             │
│     Pros: Poder massivo, habilidades únicas                │
│     Cons: Requisitos extremos de recursos                  │
│     [Black Sand ▼]  ◄─── Dropdown com 7 tipos            │
│                                                             │
│  ⚪ Taboo ☠️                                               │
│     Pros: Poder proibido                                   │
│     Cons: Maldição permanente                              │
│                                                             │
│          [← Voltar]  [Próximo →]                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  [▓▓▓▓▓▓▓▓▓▓▓▓░░] 3/4                                      │
│                                                             │
│  PASSO 3: LOCAL DE ORIGEM                                  │
│                                                             │
│  ⚪ 🌲 Floresta Nublada                                    │
│     Zona neutra, NPCs amigáveis                            │
│                                                             │
│  ⚪ 🏘️ Vila dos Crisântemos                               │
│     Comunidade pacífica                                    │
│                                                             │
│  ⚪ 🏯 Templo do Abismo                                    │
│     Monges e cultivadores solitários                       │
│                                                             │
│  ● 💎 Cavernas Cristalinas                                │
│     Rica em recursos, perigosa                             │
│                                                             │
│  ⚪ 🏛️ Cidade Imperial                                    │
│     Centro político, intrigas                              │
│                                                             │
│          [← Voltar]  [Próximo →]                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                 [Loading: Gerando perguntas...]
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] 4/4                                    │
│                                                             │
│  PASSO 4: SESSION ZERO                                     │
│                                                             │
│  1. Qual foi o momento que definiu seu destino?            │
│  ┌────────────────────────────────────┐                    │
│  │ Quando meu mestre foi assassinado  │                    │
│  │ por um demônio, jurei me tornar    │                    │
│  │ forte o suficiente para vingar...  │                    │
│  └────────────────────────────────────┘                    │
│                                                             │
│  2. Que sacrifício você fez para obter poder?              │
│  ┌────────────────────────────────────┐                    │
│  │ Sacrifiquei minha conexão com      │                    │
│  │ minha família para treinar nas...  │                    │
│  └────────────────────────────────────┘                    │
│                                                             │
│  3. Quem você deseja proteger ou vingar?                   │
│  ┌────────────────────────────────────┐                    │
│  │ Minha irmã mais nova está doente   │                    │
│  │ e preciso encontrar a Pílula...    │                    │
│  └────────────────────────────────────┘                    │
│                                                             │
│          [← Voltar]  [Iniciar Jornada]                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                 [Loading: Criando personagem...]
                          │
                          ▼
                 [Redirect to /game]
```

---

## 🔄 STATE MANAGEMENT (Frontend)

### CharacterCreationWizard Component State

```javascript
const [step, setStep] = useState(1);  // 1-4
const [formData, setFormData] = useState({
  name: "",
  appearance: "",
  constitution: "",
  originLocation: "",
  sessionZeroAnswers: ["", "", ""]
});
const [sessionZeroQuestions, setSessionZeroQuestions] = useState([]);
const [isLoading, setIsLoading] = useState(false);
```

### State Transitions

```
STEP 1 → STEP 2:
  Validação: name !== ""
  Ação: setStep(2)

STEP 2 → STEP 3:
  Validação: constitution !== ""
  Ação: setStep(3)

STEP 3 → STEP 4:
  Validação: originLocation !== ""
  Ação: 
    1. setIsLoading(true)
    2. POST /character/session-zero
    3. setSessionZeroQuestions(response.questions)
    4. setIsLoading(false)
    5. setStep(4)

STEP 4 → GAME:
  Validação: sessionZeroAnswers.every(a => a !== "")
  Ação:
    1. setIsLoading(true)
    2. POST /player/create-full
    3. onComplete(player)  // Callback prop
    4. Redirect to /game
```

---

## 🗄️ DATABASE SCHEMA CHANGES

### ANTES (Sprint 3)

```sql
CREATE TABLE player (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    rank INT DEFAULT 1,
    xp FLOAT DEFAULT 0.0,
    cultivation_tier INT DEFAULT 1,
    can_fly BOOLEAN DEFAULT FALSE,
    physics_type VARCHAR DEFAULT 'newtonian',
    quintessential_essence FLOAT DEFAULT 100.0,
    max_quintessential_essence FLOAT DEFAULT 100.0,
    shadow_chi FLOAT DEFAULT 100.0,
    max_shadow_chi FLOAT DEFAULT 100.0,
    yuan_qi FLOAT DEFAULT 100.0,
    max_yuan_qi FLOAT DEFAULT 100.0,
    current_hp FLOAT DEFAULT 100.0,
    max_hp FLOAT DEFAULT 100.0,
    defense FLOAT DEFAULT 10.0,
    speed FLOAT DEFAULT 10.0,
    strength FLOAT DEFAULT 10.0,
    corruption FLOAT DEFAULT 0.0,
    willpower FLOAT DEFAULT 50.0,
    betrayals INT DEFAULT 0,
    constitution VARCHAR DEFAULT 'Mortal Body',
    current_location VARCHAR DEFAULT 'Início da Jornada',
    active_arrays JSON DEFAULT '[]',
    spiritual_flames JSON DEFAULT '[]',
    inventory JSON DEFAULT '[]',
    status_effects JSON DEFAULT '[]',
    learned_skills JSON DEFAULT '["silent_strike"]'
);
```

### DEPOIS (Sprint 4)

```sql
CREATE TABLE player (
    -- ... (todos os campos anteriores) ...
    
    -- NOVOS CAMPOS (Sprint 4)
    appearance TEXT DEFAULT NULL,
    constitution_type VARCHAR(50) DEFAULT 'Mortal' NOT NULL,
    origin_location VARCHAR(100) DEFAULT 'Floresta Nublada' NOT NULL,
    backstory TEXT DEFAULT NULL
);
```

---

## ⚙️ CONFIGURAÇÕES E VARIÁVEIS

### Backend Environment Variables

```bash
# .env
GEMINI_API_KEY=your_api_key_here  # Necessário para Session Zero
DATABASE_URL=postgresql+asyncpg://orbis:orbis@localhost:5433/orbis_rpg
```

### Frontend API Endpoints

```javascript
// CharacterCreationWizard.js
const SESSION_ZERO_ENDPOINT = 'http://localhost:8000/character/session-zero';
const CREATE_PLAYER_ENDPOINT = 'http://localhost:8000/player/create-full';
```

---

## 📈 PERFORMANCE E OTIMIZAÇÕES

### API Call Timings (Estimados)

```
POST /character/session-zero
  ├─ Gemini API Call (Flash): ~2-4s
  ├─ Parse + Validation: ~10ms
  └─ Total: ~2-5s

POST /player/create-full
  ├─ Gemini API Call (Flash): ~3-5s  (backstory generation)
  ├─ Database INSERT: ~50-100ms
  ├─ Session Commit: ~20ms
  └─ Total: ~3-7s
```

### Optimizations

1. **Flash Model:** Usa Gemini Flash (mais rápido) ao invés de Pro
2. **Fallback:** Se Gemini falhar, retorna perguntas/backstory genéricas
3. **Loading States:** UI mostra feedback durante API calls
4. **Async/Await:** Toda comunicação é assíncrona

---

## 🔒 SEGURANÇA E VALIDAÇÃO

### Frontend Validation

```javascript
// Step 1
if (!formData.name.trim()) {
  alert("Nome é obrigatório!");
  return;
}

// Step 2
if (!formData.constitution) {
  alert("Escolha uma constituição!");
  return;
}

// Step 3
if (!formData.originLocation) {
  alert("Escolha um local de origem!");
  return;
}

// Step 4
if (formData.sessionZeroAnswers.some(a => !a.trim())) {
  alert("Responda todas as perguntas!");
  return;
}
```

### Backend Validation

```python
# Pydantic Models (automático)
class SessionZeroRequest(BaseModel):
    name: str  # Required
    constitution: str  # Required
    origin_location: str  # Required

class CreateCharacterRequest(BaseModel):
    name: str  # Required
    appearance: Optional[str]  # Optional
    constitution: str  # Required
    origin_location: str  # Required
    session_zero_answers: List[str]  # Required
```

---

**Última Atualização:** 07/01/2026  
**Versão do Sistema:** Sprint 4 (Character Creation)
