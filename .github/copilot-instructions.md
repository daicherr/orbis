# PROJETO: GEM RPG ORBIS (CÓDICE TRILUNA)
# CONTEXTO MESTRE PARA O AGENTE DE IA

VOCÊ AGORA É O ARQUITETO SÊNIOR DESTE PROJETO.
Sua missão é implementar a estrutura e os arquivos baseados estritamente nas definições abaixo.

---

## 1. ARQUITETURA DO SISTEMA (MASTER BLUEPRINT)
Stack: Python 3.12+ (FastAPI), PostgreSQL (pgvector), React (Next.js), Gemini 1.5 Pro.

ESTRUTURA DE DIRETÓRIOS A SER CRIADA/RESPEITADA:

/GemRPG_Orbis
│
├── /ruleset_source (O DNA DO MUNDO - INPUT MANUAL)
│   ├── /mechanics (JSON - Regras Matemáticas)
│   │   ├── classes.json            # Stats base de cultivo (Qi, HP, Defesa)
│   │   ├── skills.json             # Fórmulas de dano, custos e cooldowns
│   │   ├── items.json              # Preços base e atributos de equipamentos
│   │   ├── loot_tables.json        # Tabelas de drop
│   │   ├── constitutions.json      # O "Grimório Genético" (Mortal, Godfiend, Taboo)
│   │   └── compatibility.json      # Matriz de conflito (Fogo vs Água)
│   │
│   └── /lore_manual (Markdown - Conhecimento da IA)
│       ├── cultivation_rules.md    # Regras de Qi, Pílulas e Essence Soul
│       ├── world_physics.md        # Geografia, Clima e Leis da Física Mágica
│       └── bestiary_lore.md        # Comportamento dos monstros
│
├── /backend (O CÉREBRO LÓGICO)
│   ├── /app
│   │   ├── main.py                 # API Gateway
│   │   ├── config.py               # Configurações (DB, API Keys)
│   │   │
│   │   ├── /agents (PERSONAS DA IA)
│   │   │   ├── narrator.py         # Mestre: Narra cenas baseado em Markdown + Contexto
│   │   │   ├── referee.py          # Juiz: Traduz texto do player em mecânica JSON
│   │   │   ├── stylizer.py         # Escritor: Transforma input simples em literatura
│   │   │   ├── scribe.py           # Epifania: Cria skills novas baseado no estilo do player
│   │   │   │
│   │   │   ├── /villains (NEMESIS ENGINE)
│   │   │   │   ├── strategist.py   # IA Tática: Move vilões no mapa (Off-screen)
│   │   │   │   └── profiler.py     # IA Emocional: Gerencia ódio/respeito
│   │   │   │
│   │   │   └── /social (SOCIAL WEB)
│   │   │       ├── gossip_monger.py# Gera rumores baseados em logs
│   │   │       └── diplomat.py     # Gerencia guerras de facção
│   │   │
│   │   ├── /core (LÓGICA PURA - SEM IA)
│   │   │   ├── combat_engine.py    # Calculadora de Dano (Usa as 3 energias)
│   │   │   ├── chronos.py          # Relógio Mestre (Tempo In-Game)
│   │   │   ├── world_sim.py        # Scheduler de NPCs
│   │   │   │
│   │   │   └── /simulation (GOD MODE - LOTE)
│   │   │       ├── daily_tick.py   # Loop diário de evolução do mundo
│   │   │       ├── economy.py      # Macro-economia dinâmica
│   │   │       ├── lineage.py      # Casamentos e Vinganças Hereditárias
│   │   │       └── ecology.py      # Migração de Monstros
│   │   │
│   │   └── /database (POSTGRESQL + PGVECTOR)
│   │       ├── /models (SQLModel)
│   │       │   ├── player.py       # Tabelas do Jogador
│   │       │   ├── npc.py          # NPC (Dados + Vetores de Memória)
│   │       │   ├── world_state.py  # Economia e Facções
│   │       │   └── quest.py        # Motor de Missões e Prazos
│   │       └── /repositories       # Queries Híbridas (SQL + Vetor)
│
├── /frontend (REACT/NEXT.JS)
│   ├── /components
│   │   ├── GameWindow.js           # Chat Principal
│   │   ├── DialogueInput.js        # Input Literário
│   │   ├── CombatInterface.js      # Input Tático
│   │   └── NpcInspector.js         # Detalhes de NPCs
│   └── /pages
│
└── setup_env.py                    # Script de setup inicial

---

## 2. REGRAS DE LORE E MECÂNICA (CÓDICE TRILUNA)
[cite_start]Baseado no GDD "RPG Híbrido_ Lore e Mecânicas.pdf"[cite: 1].

### [cite_start]A. A TRÍADE ENERGÉTICA [cite: 24]
O sistema NÃO usa mana única. Usa 3 recursos distintos no `player.py`:
1. **Quintessência (Quintessential Essence):**
   - Fonte: *Cang Yuan Tu*.
   - Função: Vitalidade, Defesa Física, Regeneração. Combustível do corpo.
   - Recurso: Comida, Carne de Besta, Pílulas de Sangue.
2. **Chi das Sombras (Shadow Chi):**
   - Fonte: *Northern Blade*.
   - Função: DPS, Velocidade, Stealth, Artes Marciais.
   - Mecânica: "Silent Arts" (Não aparece no radar espiritual).
3. **Yuan Qi:**
   - Fonte: *Magic Emperor*.
   - Função: Controle, Alquimia, Arrays (Formações), Ataques Mentais.
   - Recurso: Pedras Espirituais.

### [cite_start]B. ESCALA DE PODER (TIERS) [cite: 215]
O jogo segue 9 Ranks estritos. A IA deve validar isso:
- **Tier 1 (Fundação):** Humano melhorado. Sem voo.
- **Tier 2 (Despertar):** Pele de ferro.
- **Tier 3 (Ascensão):** Voo desbloqueado. Ataques de energia médios.
- **Tier 4 (Transcendência):** Corpo de Energia. Imune a armas não-mágicas.
- **...**
- **Tier 9 (Soberano):** Destrói cidades/montanhas. NÃO destrói planetas.

### [cite_start]C. SISTEMA DE CORPOS (CONSTITUTIONS) [cite: 53]
Os NPCs e Jogadores têm constituições definidas em `constitutions.json`:
1. **Procedurais (Comuns):** Prefixo + Material (ex: "Iron Bone Body").
2. **Godfiends (Lendários):** Apenas 7 tipos (ex: Black Sand, Eon Sea, Phoenix).
3. **Quimeras (Artificiais):** Criados por alquimia (ex: Mercury Veins).
4. **Taboo (Amaldiçoados):** Heavenly Scourge (Atrai raios).

### [cite_start]D. FÓRMULA DE CORRUPÇÃO (HEART DEMON) [cite: 182]
O `combat_engine.py` deve implementar esta lógica:
`Corrupção = ((CultivoAbsorvido * Impureza) + (Traições * 5)) / Vontade`
- Se Corrupção atingir limites, o jogador entra em Berserk ou sofre Qi Deviation.

### E. MUNDO VIVO (SIMULATION)
- **Economia:** Se uma vila é destruída, o preço do arroz sobe globalmente.
- **Linhagem:** Se o jogador mata um NPC, o pai dele ganha o traço `Vendetta: Player`.
- **Fome:** Godfiends precisam comer muito. Adicionar mecânica de metabolismo.

---

## TAREFA IMEDIATA PARA O AGENTE:
1. Analise esta estrutura e o conteúdo das regras.
2. Comece criando os arquivos JSON essenciais na pasta `/ruleset_source/mechanics` para que o sistema tenha dados para operar.
3. Em seguida, configure o `main.py` do Backend para conectar ao Banco de Dados Postgres.