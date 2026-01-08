# 📋 ANÁLISE COMPLETA: ARQUIVOS DE LORE E MAPA

**Data:** 07/01/2026  
**Sprint Atual:** Pós-Sprint 4 (Character Creation)  
**Objetivo:** Identificar arquivos vazios e estrutura do mapa

---

## 🚨 ARQUIVOS VAZIOS (CRÍTICO - PRECISAM SER PREENCHIDOS)

### 📁 Lore Library (lore_library/)

#### ❌ VAZIOS (4 arquivos):
1. **initial_economy.json** ❌ VAZIO
   - **Localização:** `lore_library/initial_economy.json`
   - **Propósito:** Economia inicial do mundo (preços, mercados, oferta/demanda)
   - **Usado por:** DailyTickSimulator, WorldSimulator
   - **Status:** CRÍTICO - Necessário para simulação econômica

2. **world_history.txt** ❌ VAZIO
   - **Localização:** `lore_library/world_history.txt`
   - **Propósito:** História do mundo (eras, eventos, facções)
   - **Usado por:** Narrator, Architect (contexto narrativo)
   - **Status:** IMPORTANTE - Enriquece narrativa

3. **villain_templates.txt** ❌ VAZIO
   - **Localização:** `lore_library/villain_templates.txt`
   - **Propósito:** Templates de vilões (personalidades, motivações)
   - **Usado por:** Architect, Profiler
   - **Status:** IMPORTANTE - Gera antagonistas

4. **bestiary.txt** ❌ VAZIO
   - **Localização:** `lore_library/bestiary.txt`
   - **Propósito:** Bestiário (monstros, comportamentos, habitats)
   - **Usado por:** Architect (spawn de inimigos)
   - **Status:** IMPORTANTE - Gera inimigos contextuais

#### ✅ PREENCHIDO:
5. **GDD_Codex_Triluna.md** ✅ COMPLETO (113 linhas)
   - **Localização:** `lore_library/GDD_Codex_Triluna.md`
   - **Conteúdo:** GDD completo (Tríade Energética, Tiers, Constituições)
   - **Status:** OK

---

### 📁 Ruleset Source - Lore Manual (ruleset_source/lore_manual/)

#### ❌ VAZIOS (4 arquivos):
6. **cultivation_rules.md** ❌ VAZIO
   - **Localização:** `ruleset_source/lore_manual/cultivation_rules.md`
   - **Propósito:** Regras de cultivo (Qi, Pílulas, Essence Soul)
   - **Usado por:** Narrator (consulta de regras)
   - **Status:** IMPORTANTE - Define mecânicas narrativas

7. **world_physics.md** ❌ VAZIO
   - **Localização:** `ruleset_source/lore_manual/world_physics.md`
   - **Propósito:** Física do mundo (gravidade, clima, leis mágicas)
   - **Usado por:** Narrator (descrição de cenas)
   - **Status:** IMPORTANTE - Consistência narrativa

8. **bestiary_lore.md** ❌ VAZIO
   - **Localização:** `ruleset_source/lore_manual/bestiary_lore.md`
   - **Propósito:** Lore de monstros (comportamento, ecologia)
   - **Usado por:** Narrator, Architect
   - **Status:** IMPORTANTE - Complementa bestiary.txt

9. **locations_desc.md** ❌ VAZIO ⚠️ CRÍTICO PARA MAPA
   - **Localização:** `ruleset_source/lore_manual/locations_desc.md`
   - **Propósito:** DESCRIÇÕES DAS LOCALIZAÇÕES DO MAPA
   - **Usado por:** Narrator (descrição de locais), Architect (spawn contextuais)
   - **Status:** CRÍTICO - É O ARQUIVO DO MAPA!

---

### 📁 Ruleset Source - Mechanics (ruleset_source/mechanics/)

#### ⚠️ QUASE VAZIO (1 arquivo):
10. **loot_tables.json** ⚠️ ESTRUTURA VAZIA
    - **Localização:** `ruleset_source/mechanics/loot_tables.json`
    - **Conteúdo Atual:** `{ "monsters": {} }`
    - **Propósito:** Tabelas de drop (por monstro)
    - **Usado por:** CombatEngine, LootManager
    - **Status:** CRÍTICO - Sem drops, sem recompensas!

#### ✅ PREENCHIDOS:
11. **compatibility.json** ✅ OK (Elementos e matriz)
12. **techniques.json** ✅ OK (Meteor Soul, Wall of Northern Heavens, etc.)
13. **items.json** ✅ OK (Pedras Espirituais, Pílulas, Espadas)
14. **classes.json** ✅ OK (Stats por tier)
15. **cultivation_ranks.json** ✅ OK (9 tiers)
16. **constitutions.json** ✅ OK (Godfiend, Mortal, Taboo)
17. **godfiend_transformations.json** ✅ OK (Black Sand, Phoenix, etc.)
18. **skills.json** ✅ OK (Silent Strike, etc.)

---

## 🗺️ MAPA DO MUNDO: ESTRUTURA ATUAL

### Arquivo Principal do Mapa
**Localização:** `ruleset_source/lore_manual/locations_desc.md` ❌ VAZIO

### Localizações Mencionadas no Sistema (Character Creation)

Baseado em [CharacterCreationWizard.js](frontend/src/components/CharacterCreationWizard.js), temos **5 locais de origem**:

#### 1. 🌲 **Floresta Nublada** (Floresta Nublada)
- **Tipo:** Zona Neutra / Wilderness
- **NPCs Esperados:** Friendly (merchants, monks)
- **Descrição Atual:** "Zona neutra com NPCs amigáveis"
- **Status:** Sem descrição detalhada no mapa

#### 2. 🏘️ **Vila dos Crisântemos** (Vila dos Crisântemos)
- **Tipo:** Settlement / Comunidade
- **NPCs Esperados:** Friendly (villagers, merchants)
- **Descrição Atual:** "Comunidade pacífica"
- **Status:** Sem descrição detalhada no mapa

#### 3. 🏯 **Templo do Abismo** (Templo do Abismo)
- **Tipo:** Sacred Site
- **NPCs Esperados:** Neutral (monks, cultivators)
- **Descrição Atual:** "Monges e cultivadores solitários"
- **Status:** Sem descrição detalhada no mapa

#### 4. 💎 **Cavernas Cristalinas** (Cavernas Cristalinas)
- **Tipo:** Wilderness / Dungeon
- **NPCs Esperados:** Hostile (beasts, demons)
- **Descrição Atual:** "Rica em recursos, perigosa"
- **Status:** Sem descrição detalhada no mapa

#### 5. 🏛️ **Cidade Imperial** (Cidade Imperial)
- **Tipo:** Settlement / Capital
- **NPCs Esperados:** Mixed (nobles, guards, merchants)
- **Descrição Atual:** "Centro político, intrigas"
- **Status:** Sem descrição detalhada no mapa

### Localização Padrão (Default)
6. **"Início da Jornada"** (Default em Player model)
   - Localização genérica, precisa ser substituída

---

## 📊 RESUMO ESTATÍSTICO

### Por Categoria:
- **Total de Arquivos de Lore:** 18
- **Vazios:** 9 (50%)
- **Quase Vazios:** 1 (6%)
- **Preenchidos:** 8 (44%)

### Por Criticidade:
- **CRÍTICO (Bloqueiam funcionalidades):** 3 arquivos
  - initial_economy.json (DailyTickSimulator)
  - loot_tables.json (CombatEngine)
  - locations_desc.md (Narrator, Mapa)
  
- **IMPORTANTE (Empobrecem experiência):** 6 arquivos
  - world_history.txt
  - villain_templates.txt
  - bestiary.txt
  - cultivation_rules.md
  - world_physics.md
  - bestiary_lore.md

---

## 🎯 RECOMENDAÇÕES PRIORITÁRIAS

### SPRINT 5: PREENCHER ARQUIVOS CRÍTICOS

#### Prioridade 1 (MAPA):
1. **locations_desc.md** - Criar descrições detalhadas das 5 localizações
   - Geografia, clima, cultura, história
   - NPCs típicos, perigos, recursos
   - Conexões entre locais (mapa de grafo)

#### Prioridade 2 (ECONOMIA):
2. **initial_economy.json** - Criar economia inicial
   ```json
   {
     "locations": {
       "Floresta Nublada": {
         "resources": ["herbs", "beast_meat"],
         "prices": {
           "spirit_stone": 100,
           "blood_pill": 50
         }
       }
     }
   }
   ```

#### Prioridade 3 (LOOT):
3. **loot_tables.json** - Criar tabelas de drop
   ```json
   {
     "monsters": {
       "wolf": {
         "common": [{"item": "beast_meat", "chance": 0.8}],
         "rare": [{"item": "wolf_pelt", "chance": 0.2}]
       }
     }
   }
   ```

### SPRINT 6: ENRIQUECER LORE

4. **bestiary.txt** + **bestiary_lore.md** - Bestiário completo
5. **world_history.txt** - História do mundo (3 eras)
6. **villain_templates.txt** - Templates de vilões (5-10 tipos)
7. **cultivation_rules.md** - Regras narrativas de cultivo
8. **world_physics.md** - Leis físicas/mágicas

---

## 🗺️ PROPOSTA DE ESTRUTURA PARA locations_desc.md

```markdown
# CÓDICE TRILUNA: ATLAS DO MUNDO

## Mapa Conceitual

```
                    [Cidade Imperial]
                           │
                           │ (Estrada Imperial)
                           │
          ┌────────────────┼────────────────┐
          │                │                │
[Vila Crisântemos]  [Templo Abismo]  [Floresta Nublada]
          │                                 │
          └─────────────────────────────────┘
                           │
                           │ (Trilha Perigosa)
                           │
                  [Cavernas Cristalinas]
```

## 1. Floresta Nublada

**Tipo:** Wilderness (Zona Neutra)  
**Clima:** Névoa permanente, temperatura amena (15-20°C)  
**Tier Médio:** 1-2  
**População:** ~50 NPCs (ermitões, mercadores nômades)

### Geografia
Floresta densa com árvores de 50m de altura. A névoa nunca se dissipa completamente, criando um ambiente místico. Existem clareiras naturais onde a luz solar penetra, usadas como pontos de encontro.

### Recursos
- **Ervas Medicinais:** Moongrass, Shadowleaf (comuns)
- **Carne de Besta:** Lobos de Névoa (Tier 1)
- **Pedras Espirituais:** Veios pequenos nas raízes das árvores

### NPCs Típicos
- **Mercadores Viajantes:** Vendem pílulas e equipamentos básicos
- **Monges Errantes:** Oferecem treinamento em meditação
- **Caçadores:** Vendem carne e peles de besta

### Perigos
- **Lobos de Névoa:** Matilhas de 3-5, Tier 1, ataques em emboscada
- **Névoa Espiritual:** Pode causar desorientação (teste de Vontade)

### História Local
Antes da Era dos Três Sóis, esta floresta era o domínio da Fênix de Jade. Seus descendentes ainda habitam as copas mais altas, mas evitam humanos.

---

## 2. Vila dos Crisântemos

**Tipo:** Settlement (Comunidade Agrícola)  
**Clima:** Temperado, estações bem definidas  
**Tier Médio:** 1  
**População:** ~300 NPCs (agricultores, artesãos)

### Geografia
Vila murada com 20 casas de madeira e pedra. Campos de arroz e crisântemos cercam a vila. Um poço central alimentado por um veio de Yuan Qi fornece água pura.

### Recursos
- **Alimentos:** Arroz, legumes, crisântemos medicinais
- **Artesanato:** Ferramentas simples, roupas
- **Pílulas Básicas:** Pílulas de Sangue Pequenas (produção local)

### NPCs Típicos
- **Ancião da Vila:** Quest giver, conhecimento local
- **Ferreiro:** Vende armas Tier 1 (Espada de Ferro, Lança de Bambu)
- **Alquimista Aprendiz:** Refina pílulas básicas

### Perigos
- **Bandidos:** Ocasionalmente atacam durante colheita
- **Bestas Famintas:** No inverno, lobos descem das montanhas

### História Local
Fundada há 200 anos por refugiados da Guerra dos Demônios. O nome vem dos crisântemos dourados que crescem ao redor do poço central, símbolo de resistência.

---

## 3. Templo do Abismo

**Tipo:** Sacred Site (Local de Cultivo)  
**Clima:** Frio e úmido, névoa densa  
**Tier Médio:** 2-3  
**População:** ~50 NPCs (monges, cultivadores)

### Geografia
Templo de pedra escura construído na borda de um abismo sem fundo. Mil degraus levam à entrada. O abismo emite um som constante de vento uivante, propício à meditação.

### Recursos
- **Yuan Qi Concentrado:** O abismo é um veio natural
- **Pedras Espirituais Médias:** Vendidas pelos monges
- **Técnicas de Cultivo:** Biblioteca limitada (apenas para membros)

### NPCs Típicos
- **Monge Superior:** Oferece testes de cultivo
- **Cultivadores Solitários:** Treinam no abismo, neutros
- **Guardião do Templo:** Impede entrada de não-iniciados

### Perigos
- **Abismo:** Queda = morte instantânea
- **Demônios do Coração:** O Yuan Qi denso pode ativar Heart Demons
- **Cultivadores Hostis:** PvP ocasional por disputas

### História Local
Construído há 1000 anos pelo Imperador do Abismo. Diz-se que no fundo do abismo existe um portal para o Reino das Sombras.

---

## 4. Cavernas Cristalinas

**Tipo:** Dungeon (Zona Perigosa)  
**Clima:** Frio constante (5-10°C), escuridão total  
**Tier Médio:** 2-4  
**População:** ~20 NPCs (mineradores corajosos)

### Geografia
Sistema de cavernas com 10 níveis. Cristais de Yuan Qi iluminam as paredes com luz azulada. Quanto mais profundo, maior a concentração de recursos e perigo.

### Recursos
- **Cristais de Yuan Qi:** Equivalentes a 10 Pedras Espirituais
- **Minérios Raros:** Ferro Celestial, Cobre Espiritual
- **Bestas Poderosas:** Cascas de bestas Tier 3

### NPCs Típicos
- **Mineradores:** Vendem minérios a preços altos
- **Aventureiros:** Formam grupos para explorar níveis profundos
- **Ferreiro das Cavernas:** Forja equipamentos Tier 2-3

### Perigos
- **Bestas de Cristal:** Golems, Tier 2-3, imunes a ataques físicos normais
- **Desabamentos:** Teste de Agilidade ou dano massivo
- **Qi Venenoso:** Níveis 8-10 têm Yuan Qi corrompido

### História Local
Criadas durante a Queda da Estrela Celestial há 5000 anos. O impacto cristalizou o Yuan Qi subterrâneo. Rumores dizem que no nível 10 existe um Godfiend fossilizado.

---

## 5. Cidade Imperial

**Tipo:** Capital (Centro Político)  
**Clima:** Temperado, controlado por arrays  
**Tier Médio:** 3-5  
**População:** ~10.000 NPCs (nobres, guardas, mercadores)

### Geografia
Cidade murada com 3 distritos: Nobre (centro), Comercial (anel médio), Comum (periferia). Palácio Imperial domina o horizonte. Arrays gigantes protegem contra ataques Tier 6+.

### Recursos
- **Tudo Disponível:** Desde pílulas básicas até técnicas Tier 4
- **Mercado Negro:** Vende itens proibidos (Taboo, Demon Arts)
- **Academias:** Treinamento oficial de cultivo

### NPCs Típicos
- **Imperador:** Quest giver endgame, Tier 8
- **Nobres:** Oferecem missões políticas
- **Guardas Imperiais:** Tier 3-4, aplicam a lei
- **Mercadores Ricos:** Vendem itens raros

### Perigos
- **Intrigas Políticas:** Assassinatos, traições
- **Duelos Legais:** PvP organizado na Arena Imperial
- **Impostos:** Player paga 10% do loot em qualquer transação

### História Local
Fundada há 10.000 anos pelo Primeiro Imperador (Tier 9). A cidade nunca caiu, graças aos arrays ancestrais. Abriga o Tesouro Imperial (artefatos Tier 7+).

---

## Conexões e Distâncias

| De → Para | Distância | Tempo de Viagem (sem voo) | Perigos no Caminho |
|-----------|-----------|----------------------------|---------------------|
| Floresta → Vila | 20 km | 6 horas | Bandidos (baixo) |
| Floresta → Cavernas | 50 km | 2 dias | Bestas Tier 2 (médio) |
| Vila → Cidade | 100 km | 5 dias | Guardas (seguros) |
| Templo → Cidade | 150 km | 7 dias | Cultivadores hostis (alto) |
| Cavernas → Qualquer | Isolado | 3+ dias | Terreno perigoso |

**Nota:** Tier 3+ pode voar, reduzindo tempo em 80%.
```

---

## 🎨 ESTRUTURA PARA OUTROS ARQUIVOS VAZIOS

### initial_economy.json
```json
{
  "locations": {
    "Floresta Nublada": {
      "resources": ["herbs", "beast_meat"],
      "base_prices": {
        "spirit_stone_low": 100,
        "blood_pill_small": 50,
        "iron_sword": 200
      },
      "supply_demand": {
        "herbs": 1.2,
        "weapons": 0.8
      }
    },
    "Vila dos Crisântemos": {
      "resources": ["food", "basic_pills"],
      "base_prices": {
        "spirit_stone_low": 120,
        "blood_pill_small": 40,
        "iron_sword": 180
      }
    }
  },
  "global_modifiers": {
    "war_tax": 1.1,
    "festival_discount": 0.9
  }
}
```

### loot_tables.json
```json
{
  "monsters": {
    "wolf_tier1": {
      "common": [
        {"item": "beast_meat", "quantity": [1, 3], "chance": 0.8},
        {"item": "wolf_fang", "quantity": 1, "chance": 0.5}
      ],
      "rare": [
        {"item": "wolf_pelt", "quantity": 1, "chance": 0.2}
      ],
      "legendary": [
        {"item": "moonlit_fang", "quantity": 1, "chance": 0.01}
      ]
    },
    "crystal_golem_tier2": {
      "common": [
        {"item": "crystal_shard", "quantity": [2, 5], "chance": 1.0}
      ],
      "rare": [
        {"item": "yuan_qi_crystal", "quantity": 1, "chance": 0.3},
        {"item": "golem_core", "quantity": 1, "chance": 0.1}
      ]
    }
  }
}
```

---

## ✅ CHECKLIST DE AÇÃO

### Imediato (Sprint 5):
- [ ] Preencher **locations_desc.md** com descrições das 5 localizações
- [ ] Preencher **initial_economy.json** com economia básica
- [ ] Preencher **loot_tables.json** com drops de monstros

### Curto Prazo (Sprint 6):
- [ ] Preencher **bestiary.txt** com 10-15 monstros
- [ ] Preencher **bestiary_lore.md** com comportamento/ecologia
- [ ] Preencher **world_history.txt** com 3 eras históricas
- [ ] Preencher **villain_templates.txt** com 10 arquétipos

### Médio Prazo (Sprint 7):
- [ ] Preencher **cultivation_rules.md** com regras narrativas
- [ ] Preencher **world_physics.md** com leis físicas/mágicas
- [ ] Expandir **locations_desc.md** com mais localizações (Total: 10-15)

---

**Resumo Final:**
- **9 arquivos vazios críticos** identificados
- **Mapa atual:** 5 localizações definidas (sem descrições)
- **Recomendação:** Começar por **locations_desc.md** (é a base do mapa)
