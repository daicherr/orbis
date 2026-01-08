import React, { useState, useEffect } from 'react';

/**
 * 📜 QUEST LOG - Sistema de Missões Dinâmicas
 * 
 * Mostra missões ativas do player com:
 * - Progresso (barra visual)
 * - Deadline (turnos restantes)
 * - Recompensas (XP, Gold, Items)
 * - Status (Ativa, Completa, Falhou)
 */
export default function QuestLog({ playerId, isOpen, onClose }) {
  const [quests, setQuests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentTurn, setCurrentTurn] = useState(0);

  useEffect(() => {
    if (isOpen && playerId) {
      fetchQuests();
    }
  }, [isOpen, playerId]);

  const fetchQuests = async () => {
    try {
      setLoading(true);
      
      // Buscar quests ativas
      const questsResponse = await fetch(`http://localhost:8000/quest/active/${playerId}`);
      const questsData = await questsResponse.json();
      
      // Buscar turno atual
      const turnResponse = await fetch('http://localhost:8000/game/current-turn');
      const turnData = await turnResponse.json();
      
      setQuests(questsData.quests || []);
      setCurrentTurn(turnData.current_turn || 0);
    } catch (error) {
      console.error('Erro ao buscar quests:', error);
      setQuests([]);
    } finally {
      setLoading(false);
    }
  };

  const getProgressPercent = (quest) => {
    if (quest.required_progress === 0) return 0;
    return Math.min(100, (quest.current_progress / quest.required_progress) * 100);
  };

  const getDeadlineColor = (quest) => {
    const turnsRemaining = quest.deadline_turn - currentTurn;
    
    if (quest.status === 'completed') return 'text-green-400';
    if (quest.status === 'failed') return 'text-red-400';
    if (turnsRemaining > 20) return 'text-green-400';
    if (turnsRemaining > 10) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getStatusBadge = (quest) => {
    const turnsRemaining = quest.deadline_turn - currentTurn;
    
    if (quest.status === 'completed') {
      return (
        <span className="px-3 py-1 bg-green-600/30 border border-green-500 rounded-full text-green-300 text-sm">
          ✅ COMPLETA
        </span>
      );
    }
    
    if (quest.status === 'failed') {
      return (
        <span className="px-3 py-1 bg-red-600/30 border border-red-500 rounded-full text-red-300 text-sm">
          ❌ FALHOU
        </span>
      );
    }
    
    return (
      <span className="px-3 py-1 bg-blue-600/30 border border-blue-500 rounded-full text-blue-300 text-sm">
        🔥 ATIVA
      </span>
    );
  };

  const getQuestTypeIcon = (type) => {
    const icons = {
      hunt: '⚔️',
      delivery: '📦',
      duel: '🤺',
      explore: '🗺️',
      gather: '🌿'
    };
    return icons[type] || '📜';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[90vh] bg-gradient-to-br from-slate-900 to-slate-800 border-2 border-amber-600/50 rounded-lg shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="relative bg-gradient-to-r from-amber-900/40 to-orange-900/40 border-b-2 border-amber-600/50 p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-bold text-amber-300 mb-1">
                📜 REGISTRO DE MISSÕES
              </h2>
              <p className="text-amber-200/60 text-sm">
                Turno Atual: {currentTurn} | Missões Ativas: {quests.filter(q => q.status === 'active').length}
              </p>
            </div>
            
            <button
              onClick={onClose}
              className="px-4 py-2 bg-red-600/20 hover:bg-red-600/40 border border-red-500 rounded text-red-300 transition-colors"
            >
              ✕ Fechar
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto mb-4"></div>
              <p className="text-amber-300">Carregando missões...</p>
            </div>
          ) : quests.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-amber-300/60 text-xl mb-2">📜</p>
              <p className="text-amber-300/60">Nenhuma missão disponível</p>
              <p className="text-amber-300/40 text-sm mt-2">
                Visite locais para desbloquear novas missões
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {quests.map((quest) => {
                const progressPercent = getProgressPercent(quest);
                const deadlineColor = getDeadlineColor(quest);
                const turnsRemaining = quest.deadline_turn - currentTurn;

                return (
                  <div
                    key={quest.id}
                    className="bg-slate-800/50 border border-amber-600/30 rounded-lg p-5 hover:border-amber-600/50 transition-all"
                  >
                    {/* Quest Header */}
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-2xl">{getQuestTypeIcon(quest.type)}</span>
                          <h3 className="text-xl font-bold text-amber-200">
                            {quest.title}
                          </h3>
                        </div>
                        <p className="text-amber-100/80 text-sm mb-2">
                          {quest.description}
                        </p>
                        <p className="text-amber-300/60 text-xs">
                          📍 {quest.location}
                        </p>
                      </div>
                      
                      <div className="ml-4">
                        {getStatusBadge(quest)}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    {quest.type === 'hunt' && quest.status === 'active' && (
                      <div className="mb-3">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-amber-300">Progresso:</span>
                          <span className="text-amber-200">
                            {quest.current_progress} / {quest.required_progress}
                          </span>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2.5 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-amber-500 to-orange-500 h-2.5 rounded-full transition-all duration-300"
                            style={{ width: `${progressPercent}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Deadline */}
                    <div className="mb-3">
                      <span className={`text-sm font-semibold ${deadlineColor}`}>
                        ⏳ Prazo: {turnsRemaining > 0 ? `${turnsRemaining} turnos restantes` : 'EXPIRADO'}
                      </span>
                    </div>

                    {/* Rewards */}
                    <div className="bg-slate-900/50 border border-amber-600/20 rounded p-3">
                      <p className="text-amber-300/80 text-sm mb-2 font-semibold">
                        💰 RECOMPENSAS:
                      </p>
                      <div className="flex gap-4 text-sm">
                        <span className="text-blue-300">
                          ⚡ {quest.reward_xp} XP
                        </span>
                        <span className="text-yellow-300">
                          💎 {quest.reward_gold} Gold
                        </span>
                        {quest.reward_items && quest.reward_items.length > 0 && (
                          <span className="text-purple-300">
                            🎁 {quest.reward_items.length} items
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-t-2 border-amber-600/30 p-4 text-center">
          <p className="text-amber-300/60 text-sm">
            💡 Missões falham automaticamente ao atingir o prazo limite
          </p>
        </div>
      </div>
    </div>
  );
}
