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
  const loadPlayer = async (id = playerId) => {
    if (!id) return null;

    try {
      const response = await fetch(`${API_URL}/player/${id}`);
      if (!response.ok) throw new Error('Jogador não encontrado');
      return await response.json();
    } catch (error) {
      console.error('Erro ao carregar jogador:', error);
      return null;
    }
  };

  // Enviar ação do jogador
  const sendAction = async (action, id = playerId) => {
    if (!id) throw new Error('Player ID não definido');

    try {
      const response = await fetch(
        `${API_URL}/game/turn?player_id=${id}&player_input=${encodeURIComponent(action)}`,
        { method: 'POST' }
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
  const loadInventory = async (id = playerId) => {
    if (!id) return [];

    try {
      const response = await fetch(`${API_URL}/player/${id}/inventory`);
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

  const value = {
    playerId,
    playerName,
    isLoading,
    API_URL,
    createPlayer,
    loadPlayer,
    sendAction,
    loadInventory,
    logout,
  };

  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
};
