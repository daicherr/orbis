# PROJETO CÓDICE TRILUNA: GDD MESTRE
**Arquitetura de Design de Sistemas, Narrativa Emergente e Engenharia de Lore para RPG Híbrido**

**Status:** Documento de Design de Jogo (GDD) - Versão Mestre
**Classificação:** Fonte da Verdade (Source of Truth)

---

## 1. Manifesto de Design e Filosofia do Núcleo

Este relatório delineia a arquitetura completa para o "Projeto Códice Triluna", um RPG híbrido que sintetiza três pilares da ficção oriental:
1.  **Fundação Biológica:** Cang Yuan Tu (The Demon Hunter)
2.  **Combate Visceral:** Legend of the Northern Blade
3.  **Gestão Maquiavélica:** Magic Emperor

**Tese Central:** "A Assimétrica da Ascensão". Ao contrário de RPGs ocidentais que buscam equilíbrio, este sistema abraça a disparidade. A vitória depende da exploração de recursos, otimização genética e gestão da corrupção moral.

### A Lógica de Camadas
1.  **Hardware (O Corpo):** Definido por *Cang Yuan Tu*. Capacidade de processar energia e evoluir.
2.  **Software (O Combate):** Definido por *Northern Blade*. Técnicas, fluxo, stealth.
3.  **Sistema Operacional (A Mente):** Definido por *Magic Emperor*. Alquimia, Arrays, Política e Heart Demon.

---

## 2. Cosmologia: O Domínio do Crepúsculo Primordial

### 2.1. A Tríade Energética (Economia de Recursos)
O jogo não usa "Mana" genérica. [cite_start]Usa três vetores distintos[cite: 22, 23]:

| Tipo de Energia | Origem | Função Mecânica | Recurso Associado |
| :--- | :--- | :--- | :--- |
| **Quintessência** (Quintessential Essence) | *Cang Yuan Tu* | **Vitalidade & Estrutura.** Determina HP, regeneração, defesa física. Energia Yang. Se zerar, o corpo desintegra. | Pílulas de Sangue, Carne de Bestas, Treino Físico. |
| **Chi das Sombras** (Shadow Chi) | *Northern Blade* | **Cinética & Letalidade.** Governa DPS, velocidade, stealth. Energia "Negativa" que anula luz/som. | Meditação, Absorção de Yin, Combate (Adrenalina). |
| **Yuan Qi** (Energia Primordial) | *Magic Emperor* | **Controle & Realidade.** Usado para Alquimia, Arrays, manipulação da Alma. Necessária para suprimir o Heart Demon. | Pedras Espirituais, Absorção (Demon Transformation). |

### 2.2. Estratificação Dimensional (Tiers)
[cite_start]A progressão é dimensional, não linear[cite: 30]:

* **Tier 1-2 (Reino da Poeira):** Física Newtoniana. Foco em espada e gravidade normal. (Níveis 1-10).
* **Tier 3-5 (Reino Sagrado):** Física Maleável. Voo desbloqueado, manipulação espacial. (Níveis 11-20).
* **Tier 6+ (Rio do Espaço-Tempo):** Física Conceitual. Manipulação temporal, criação de mundos. (Níveis 21+).

---

## 3. Pilar I: Fundação Biológica (Engenharia de Cang Yuan Tu)

[cite_start]Não escolhemos classes; construímos corpos através da "Purificação de Medula"[cite: 43].

### 3.1. Corpos de Deus-Demônio (Classes/Arquétipos)

* **Corpo da Areia Divina (Black Sand):** Foco em Defesa e Gravidade. Mecânica de "Erosão". [cite_start]Ultimate: Campo Negro (Gravidade 10x). [cite: 54-60]
* **Corpo do Mar Eterno (Eon Sea):** Foco em Regeneração Infinita. Regenera membros em 1d4 turnos. [cite_start]Stamina inesgotável. [cite: 61-65]
* **Corpo Devastador do Raio (Lightning Devastator):** Foco em Velocidade Extrema. Iniciativa garantida. [cite_start]Dano escala com Velocidade de Movimento. [cite: 68-75]
* **Corpo do Buraco do Caos (Chaos Hole):** Endgame. Absorve dano de energia e converte em Quintessência. [cite_start]Requer sobreviver a Tribulação Mental. [cite: 76-83]
* **Corpo da Fênix (Phoenix):** Foco em Fogo e Renascimento (Nirvana). [cite_start]Purifica corrupção de aliados. [cite: 84-90]
* **Corpo do Dragão (Dragon):** Força bruta e escamas. [cite_start]Debuff de medo em inimigos inferiores. [cite: 91-96]

---

## 4. Pilar II: Combate (A Dança de Northern Blade)

[cite_start]O combate exige gestão do "Chi das Sombras"[cite: 139].

### 4.1. Mecânica "Silent Arts"
[cite_start]Habilidades com Shadow Chi não geram som e não aparecem no radar espiritual inimigo, a menos que o nível de cultivo do inimigo seja muito superior[cite: 145].

### 4.2. Técnicas Chave
* [cite_start]**Meteor Soul:** Estocada que ignora armadura e causa sangramento espiritual. [cite: 150]
* [cite_start]**Wall of Northern Heavens:** Barreira que reflete 50% do dano. [cite: 153]
* **Shadowstep:** Teleporte curto. [cite_start]Deixa imagem residual; se atacada, gera contra-ataque crítico. [cite: 146]

---

## 5. Pilar III: Sistemas e Gestão (Magic Emperor)

### 5.1. O Demônio do Coração (Heart Demon)
Mecânica de sanidade espiritual. [cite_start]Fórmula de Corrupção[cite: 182]:
`Corrupção = ((CultivoAbsorvido * Impureza) + (Traições * 5)) / Vontade`

* **Estágio 1:** Alucinações (-10% Vontade).
* **Estágio 2:** Berserk (Ataca aliados se HP < 30%).
* **Estágio 3:** Morte Permanente (Qi Deviation).

### 5.2. Demon Transformation Art
Permite absorver cultivo de inimigos para XP imediato. [cite_start]Custo: Aumenta drasticamente a Corrupção e requer teste de Purificação [cite: 193-196].

### 5.3. Arrays e Alquimia
* **Matriz de Batalha:** Conecta Chi de NPCs fracos para buffar o player.
* [cite_start]**Alquimia:** Necessário capturar "Chamas Espirituais" para refinar pílulas de alto nível[cite: 204].

---

## 6. Tabela de Progressão Unificada

| Tier | Rank (Nome) | Equivalente CYT | Equivalente NB | Equivalente ME | Descrição Mecânica |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Fundação | Mortal / Marrow Cleansing | 3rd/2nd Rank Warrior | Qi Condensation | Humano aprimorado. Sem voo. |
| **Tier 2** | Despertar | Mortal Shedding | 1st Rank Warrior | Bone Tempering | Pele de ferro. Uso limitado de Chi externo. |
| **Tier 3** | Ascensão | Core Cloud Godfiend | Peak Realm | Radiant Stage | **Voo desbloqueado.** Ataques de energia médio alcance. |
| **Tier 4** | Transcendência | Great Solar Godfiend | Transcendent Realm | Ethereal Stage | Corpo de energia. Imune a armas não-mágicas. |
| **Tier 5** | Soberania | Darkstar Godfiend | Unrestrained Realm | Spirit King | Manipulação espacial (Teleporte). |
| **Tier 6** | Divindade | Regis Godfiend | Profound Realm | Saint/Sovereign | Criação de dimensão de bolso (Domain). |
| **Tier 9** | Criação | Creation Realm | Heaven & Earth | Universe Realm | Criação de vida e leis. |

---

## 7. Referências e Scripts

### Fórmula de Dano Sugerida
[cite_start]`DanoTotal = (BaseDmg + (ShadowChi * 2)) * (100 / (100 + (DefesaAlvo - Penetração)))` [cite: 236]

---
**FIM DO DOCUMENTO**