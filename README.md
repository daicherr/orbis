# 🌙 CÓDICE TRILUNA - Cultivation RPG

Um RPG híbrido de cultivo que sintetiza três pilares da ficção oriental:
- **Fundação Biológica:** Cang Yuan Tu (The Demon Hunter)
- **Combate Visceral:** Legend of the Northern Blade  
- **Gestão Maquiavélica:** Magic Emperor

## ✨ Funcionalidades Implementadas

### Sistema de Cultivo (GDD Completo)
- ✅ **9 Tiers de Cultivo** (Fundação → Criação)
- ✅ **Tríade Energética**: Quintessência, Chi das Sombras, Yuan Qi
- ✅ **Sistema de Voo** (desbloqueado no Tier 3+)
- ✅ **Física Dimensional** (Newtoniana, Maleável, Conceitual)
- ✅ **6 Corpos Godfiend** (Black Sand, Eon Sea, Lightning Devastator, etc)

### Combate Avançado
- ✅ **Técnicas de Northern Blade**: Meteor Soul, Shadowstep, Wall of Northern Heavens
- ✅ **Silent Arts**: Stealth baseado em Shadow Chi
- ✅ **Impureza Dinâmica**: Corrupção varia por fonte (demônios = alta, humanos = baixa)
- ✅ **Heart Demon System**: Corrupção = ((CultivoAbsorvido * Impureza) + (Traições * 5)) / Vontade
- ✅ **Demon Transformation Art**: Absorve cultivo de inimigos derrotados

### IA e Simulação do Mundo
- ✅ **Profiler**: Gerencia emoções de NPCs e vinganças
- ✅ **Strategist**: Move vilões hostis no mapa off-screen
- ✅ **GossipMonger**: Gera rumores baseados em eventos do jogador
- ✅ **Diplomat**: Gerencia relações de facções
- ✅ **WorldSimulator**: Coordena todos os sistemas de IA

### Frontend Redesenhado
- ✅ **Glassmorphism UI** com tema cultivation
- ✅ **Barras de energia animadas** (Quintessência, Shadow Chi, Yuan Qi)
- ✅ **Badges de Tier dinâmicos**
- ✅ **Interface de combate com skills visuais**
- ✅ **Modal de inspeção de NPCs**
- ✅ **Animações suaves e efeitos de brilho**
- ✅ **Scrollbar customizada**
- ✅ **Background animado com gradientes**

## 🚀 Como Executar

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Database (PostgreSQL com Docker)
```bash
docker-compose up -d
```

### 3. Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:3000

## 📁 Estrutura do Projeto

```
/ruleset_source
  /mechanics
    - cultivation_ranks.json   ✅ 9 tiers completos
    - skills.json              ✅ 11 técnicas (incluindo Northern Blade)
    - constitutions.json       ✅ 6 Godfiends + Procedurais
    - items.json
    - loot_tables.json
  /lore_manual
    - cultivation_rules.md
    - world_physics.md
    - bestiary_lore.md

/backend
  /app
    /agents
      - narrator.py            ✅ Gemini 3-Flash
      - referee.py             ✅ Gemini 3-Pro
      - architect.py           ✅ Geração procedural
      - profiler.py            ✅ Sistema emocional
      - strategist.py          ✅ IA tática
      - gossip_monger.py       ✅ Rumores
      - diplomat.py            ✅ Facções
    /core
      - combat_engine.py       ✅ Silent Arts, Impureza Dinâmica
      - world_sim.py           ✅ Coordenação de IA
    /database
      - player.py              ✅ cultivation_tier, can_fly, physics_type

/frontend
  /src
    /pages
      - game.js                ✅ Redesign completo
    /styles
      - globals.css            ✅ Theme system cultivation
```

## 🎮 Mecânicas Principais

### Tríade Energética
| Energia | Função | Recurso |
|---------|--------|---------|
| **Quintessência** | Vitalidade, Defesa, Regeneração | Carne de Besta, Pílulas de Sangue |
| **Chi das Sombras** | DPS, Stealth, Silent Arts | Meditação, Absorção de Yin |
| **Yuan Qi** | Arrays, Alquimia, Ataques Mentais | Pedras Espirituais |

### Sistema de Progressão
- **Tier 1-2**: Física Newtoniana (sem voo)
- **Tier 3-5**: Física Maleável (**voo desbloqueado**)
- **Tier 6-9**: Física Conceitual (manipulação temporal)

### Técnicas Especiais
- **Meteor Soul**: Ignora 100% armadura + sangramento espiritual
- **Shadowstep**: Teleporte com contra-ataque crítico
- **Wall of Northern Heavens**: Barreira que reflete 50% dano
- **Phoenix Rebirth**: Ressurreição (exclusivo Phoenix Body)
- **Gravity Field**: Campo 10x gravidade (exclusivo Black Sand Body)

## 🔮 Tecnologias

- **Backend**: Python 3.12+, FastAPI, SQLModel
- **Database**: PostgreSQL + pgvector (Docker)
- **IA**: Google Gemini 1.5 (3-Flash, 3-Pro, 2.5-Flash)
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **Deployment**: Docker Compose

## 📚 Referências

Baseado no **GDD_Codex_Triluna.md** (Game Design Document) que define:
- Escala de poder (9 tiers rigorosos)
- Sistema de corrupção (Heart Demon)
- Fórmulas de combate
- Corpos Godfiend
- Tabela de progressão unificada

## 🐛 Status

✅ **COMPLETO** - Todas as mecânicas do GDD implementadas
✅ **CONECTADO** - Todos os agentes integrados
✅ **REDESENHADO** - Frontend modernizado com tema cultivation

---

**Criado por:** Felipe  
**Data:** Janeiro 2025  
**Repositório:** https://github.com/daicherr/orbis
