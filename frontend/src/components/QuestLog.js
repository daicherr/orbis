import React, { useState, useEffect } from 'react';

/**
 * 📜 QUEST LOG - Sistema de Missões Dinâmicas
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
      const questsResponse = await fetch(`http://localhost:8000/quest/active/${playerId}`);
      if (questsResponse.ok) {
        const questsData = await questsResponse.json();
        setQuests(questsData.quests || []);
      } else {
        setQuests([]);
      }
    } catch (error) {
      console.error('Erro ao buscar quests:', error);
      setQuests([]);
    } finally {
      setLoading(false);
    }
  };

  const getProgressPercent = (quest) => {
    if (!quest.required_progress || quest.required_progress === 0) return 0;
    return Math.min(100, (quest.current_progress / quest.required_progress) * 100);
  };

  const getDeadlineStyle = (quest) => {
    const turnsRemaining = (quest.deadline_turn || 0) - currentTurn;
    if (quest.status === 'completed') return { color: 'var(--jade)' };
    if (quest.status === 'failed') return { color: 'var(--demon)' };
    if (turnsRemaining > 20) return { color: 'var(--jade)' };
    if (turnsRemaining > 10) return { color: 'var(--gold)' };
    return { color: 'var(--demon)' };
  };

  const getStatusBadge = (quest) => {
    if (quest.status === 'completed') return <span className="badge badge-jade">✅ COMPLETA</span>;
    if (quest.status === 'failed') return <span className="badge badge-demon">❌ FALHOU</span>;
    return <span className="badge badge-gold">🔥 ATIVA</span>;
  };

  const getQuestTypeIcon = (type) => {
    const icons = { hunt: '⚔️', delivery: '📦', duel: '🤺', explore: '🗺️', gather: '🌿' };
    return icons[type] || '📜';
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div 
        className="card card-gold fade-in" 
        style={{ maxWidth: '800px', width: '100%', maxHeight: '90vh', overflow: 'hidden' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ borderBottom: '2px solid var(--border-accent)', paddingBottom: 'var(--spacing-md)', marginBottom: 'var(--spacing-lg)' }}>
          <div className="flex justify-between items-center">
            <div>
              <h2 className="glow-gold" style={{ marginBottom: 'var(--spacing-xs)' }}>📜 REGISTRO DE MISSÕES</h2>
              <p style={{ color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
                Missões Ativas: {quests.filter(q => q.status === 'active').length}
              </p>
            </div>
            <button onClick={onClose} className="btn btn-ghost">✕ Fechar</button>
          </div>
        </div>

        {/* Content */}
        <div style={{ overflowY: 'auto', maxHeight: 'calc(90vh - 180px)' }}>
          {loading ? (
            <div className="text-center" style={{ padding: 'var(--spacing-2xl)' }}>
              <div className="spinner"></div>
              <p style={{ marginTop: 'var(--spacing-md)', color: 'var(--gold)' }}>Carregando missões...</p>
            </div>
          ) : quests.length === 0 ? (
            <div className="text-center" style={{ padding: 'var(--spacing-2xl)' }}>
              <p style={{ fontSize: '2rem', marginBottom: 'var(--spacing-sm)' }}>📜</p>
              <p style={{ color: 'var(--text-secondary)' }}>Nenhuma missão disponível</p>
            </div>
          ) : (
            <div className="flex flex-col gap-md">
              {quests.map((quest) => {
                const progressPercent = getProgressPercent(quest);
                const deadlineStyle = getDeadlineStyle(quest);
                const turnsRemaining = (quest.deadline_turn || 0) - currentTurn;

                return (
                  <div key={quest.id} className="card card-hover panel">
                    <div className="flex justify-between items-start" style={{ marginBottom: 'var(--spacing-md)' }}>
                      <div style={{ flex: 1 }}>
                        <div className="flex items-center gap-sm" style={{ marginBottom: 'var(--spacing-sm)' }}>
                          <span style={{ fontSize: '1.5rem' }}>{getQuestTypeIcon(quest.type)}</span>
                          <h3 className="glow-gold" style={{ fontSize: '1.25rem' }}>{quest.title}</h3>
                        </div>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{quest.description}</p>
                      </div>
                      <div style={{ marginLeft: 'var(--spacing-md)' }}>{getStatusBadge(quest)}</div>
                    </div>

                    {quest.type === 'hunt' && quest.status === 'active' && (
                      <div style={{ marginBottom: 'var(--spacing-md)' }}>
                        <div className="flex justify-between" style={{ marginBottom: 'var(--spacing-xs)', fontSize: '0.875rem' }}>
                          <span style={{ color: 'var(--gold)' }}>Progresso:</span>
                          <span>{quest.current_progress} / {quest.required_progress}</span>
                        </div>
                        <div className="progress-bar">
                          <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }}></div>
                        </div>
                      </div>
                    )}

                    <div style={{ marginBottom: 'var(--spacing-md)' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', ...deadlineStyle }}>
                        ⏳ Prazo: {turnsRemaining > 0 ? `${turnsRemaining} turnos` : 'EXPIRADO'}
                      </span>
                    </div>

                    <div className="panel" style={{ background: 'var(--bg-secondary)' }}>
                      <p style={{ color: 'var(--gold)', fontSize: '0.875rem', marginBottom: 'var(--spacing-sm)', fontWeight: '600' }}>💰 RECOMPENSAS:</p>
                      <div className="flex gap-lg" style={{ fontSize: '0.875rem' }}>
                        <span style={{ color: 'var(--jade)' }}>⚡ {quest.reward_xp} XP</span>
                        <span style={{ color: 'var(--gold-light)' }}>💎 {quest.reward_gold} Gold</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
