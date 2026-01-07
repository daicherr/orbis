# Gem RPG: Orbis (Projeto Códice Triluna)

Este é um RPG híbrido que combina mecânicas de cultivo, combate visceral e gestão de facções, com uma forte integração de IA generativa para criar uma experiência de jogo dinâmica e emergente.

O projeto é baseado no GDD (Game Design Document) encontrado em `lore_library/GDD_Codex_Triluna.md`.

## Arquitetura

-   **Backend:** FastAPI (Python) com PostgreSQL e pgvector.
-   **Frontend:** Next.js (React) com Tailwind CSS.
-   **IA:** Google Gemini 1.5 Pro.

---

## Como Executar o Ambiente de Desenvolvimento

### Pré-requisitos

-   Python 3.10+
-   Node.js e npm
-   PostgreSQL com a extensão `pgvector` instalada.
-   Um arquivo `.env` na pasta `backend/` (veja abaixo).

### 1. Configuração do Backend

a. **Crie um arquivo `.env`** na pasta `backend/`. Ele deve conter as credenciais do seu banco de dados e a chave da API do Gemini:

   ```env
   # Exemplo de backend/.env
   DATABASE_URL="postgresql+asyncpg://seu_usuario:sua_senha@localhost/gemrpg"
   GEMINI_API_KEY="sua_chave_de_api_aqui"
   ```

b. **Instale as dependências Python** (é recomendado usar um ambiente virtual):

   ```bash
   # Navegue até a pasta do backend
   cd backend

   # Crie e ative um ambiente virtual (opcional, mas recomendado)
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate

   # Instale os pacotes
   pip install -r requirements.txt
   ```

c. **Inicie o servidor do backend:**

   ```bash
   # Dentro da pasta backend/
   uvicorn app.main:app --reload
   ```

   O servidor estará rodando em `http://localhost:8000`.

### 2. Configuração do Frontend

a. **Instale as dependências do Node.js:**

   ```bash
   # Navegue até a pasta do frontend
   cd frontend

   # Instale os pacotes
   npm install
   ```

b. **Inicie o servidor de desenvolvimento do frontend:**

   ```bash
   # Dentro da pasta frontend/
   npm run dev
   ```

   O servidor estará rodando em `http://localhost:3000`. Abra este endereço no seu navegador para ver a aplicação.

---

## Próximos Passos

Com ambos os servidores rodando, a aplicação estará funcional. O frontend se comunicará com o backend para criar o jogador e processar os turnos de jogo.
