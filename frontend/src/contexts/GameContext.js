import React, { createContext, useContext, useState, useEffect } from 'react';

const GameContext = createContext();

export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame deve ser usado dentro de GameProvider');
  }
  return context;
};

export const GameProvider = ({ children }) => {
  const [playerId, setPlayerId] = useState(null);
  const [playerName, setPlayerName] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Inicializar player do localStorage
  useEffect(() => {
    const storedId = window.localStorage.getItem('playerId');
    const storedName = window.localStorage.getItem('playerName');
    
    if (storedId && storedName) {
      setPlayerId(Number(storedId));
      setPlayerName(storedName);
    }
    setIsLoading(false);
  }, []);

  // Recarregar do localStorage (útil após criar personagem)
  const refreshFromStorage = () => {
    const storedId = window.localStorage.getItem('playerId');
    const storedName = window.localStorage.getItem('playerName');
    
    if (storedId && storedName) {
      setPlayerId(Number(storedId));
      setPlayerName(storedName);
    }
  };

  // Criar novo jogador
  const createPlayer = async (playerData) => {
    try {
      const response = await fetch(`${API_URL}/player/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(playerData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao criar jogador');
      }

      const player = await response.json();
      
      // Salvar no localStorage e state
      window.localStorage.setItem('playerId', String(player.id));
      window.localStorage.setItem('playerName', player.name);
      setPlayerId(player.id);
      setPlayerName(player.name);

      return player;
    } catch (error) {
      console.error('Erro ao criar jogador:', error);
      throw error;
    }
  };

  // Carregar dados do jogador
  const loadPlayer = async (id = null) => {
    const currentId = id || Number(window.localStorage.getItem('playerId')) || playerId;
    if (!currentId) return null;

    try {
      const response = await fetch(`${API_URL}/player/${currentId}`);
      if (!response.ok) throw new Error('Jogador não encontrado');
      return await response.json();
    } catch (error) {
      console.error('Erro ao carregar jogador:', error);
      return null;
    }
  };

  // Enviar ação do jogador
  const sendAction = async (action, id = null) => {
    // Sempre verificar localStorage para obter o ID mais recente
    const currentId = id || Number(window.localStorage.getItem('playerId')) || playerId;
    if (!currentId) throw new Error('Player ID não definido');

    try {
      const response = await fetch(
        `${API_URL}/game/turn?player_id=${currentId}&player_input=${encodeURIComponent(action)}`,
        { 
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro no servidor');
      }

      return await response.json();
    } catch (error) {
      console.error('Erro ao enviar ação:', error);
      throw error;
    }
  };

  // Buscar inventário do jogador
  const loadInventory = async (id = null) => {
    const currentId = id || Number(window.localStorage.getItem('playerId')) || playerId;
    if (!currentId) return [];

    try {
      const response = await fetch(`${API_URL}/player/${currentId}/inventory`);
      if (!response.ok) return [];
      return await response.json();
    } catch (error) {
      console.error('Erro ao carregar inventário:', error);
      return [];
    }
  };

  // Logout
  const logout = () => {
    window.localStorage.removeItem('playerId');
    window.localStorage.removeItem('playerName');
    setPlayerId(null);
    setPlayerName(null);
    window.location.href = '/';
  };

  // Enviar ação com SSE streaming (retorna callbacks para controle)
  const sendActionSSE = (action, callbacks, id = null) => {
    const currentId = id || Number(window.localStorage.getItem('playerId')) || playerId;
    if (!currentId) {
      callbacks.onError?.('Player ID não definido');
      return null;
    }

    const url = `${API_URL}/v2/game/turn/stream?player_id=${currentId}&player_input=${encodeURIComponent(action)}`;
    
    // Usar fetch com POST para SSE
    fetch(url, { method: 'POST' })
      .then(response => {
        if (!response.ok) throw new Error('Erro no servidor');
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentEventType = 'message';
        
        const processStream = async () => {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
              if (line.startsWith('event:')) {
                // Capturar o tipo de evento
                currentEventType = line.substring(6).trim();
                continue;
              }
              if (line.startsWith('data:')) {
                try {
                  const data = JSON.parse(line.substring(5).trim());
                  
                  // Usar currentEventType capturado da linha event:
                  if (currentEventType === 'narrator_chunk') {
                    callbacks.onChunk?.(data.text);
                  } else if (currentEventType === 'done') {
                    callbacks.onDone?.(data);
                  } else if (currentEventType === 'error') {
                    callbacks.onError?.(data.error || data.message);
                  } else if (currentEventType === 'planner') {
                    callbacks.onPlanner?.(data);
                  } else if (currentEventType === 'executor') {
                    callbacks.onExecutor?.(data);
                  } else if (currentEventType === 'validator') {
                    callbacks.onValidator?.(data);
                  }
                  
                  // Reset event type após processar
                  currentEventType = 'message';
                } catch (e) {
                  // Ignore parse errors for incomplete JSON
                }
              }
            }
          }
        };
        
        processStream().catch(err => callbacks.onError?.(err.message));
      })
      .catch(err => callbacks.onError?.(err.message));
  };

  const value = {
    playerId,
    playerName,
    isLoading,
    API_URL,
    createPlayer,
    loadPlayer,
    sendAction,
    sendActionSSE,
    loadInventory,
    logout,
    refreshFromStorage,
  };

  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
};
