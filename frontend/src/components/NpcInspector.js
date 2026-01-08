import React, { useState, useEffect } from 'react';

const NpcInspector = ({ npc, onClose, onObserve }) => {
  const [isObserving, setIsObserving] = useState(false);
  const [description, setDescription] = useState('');

  useEffect(() => {
    if (npc) {
      handleObserve();
    }
  }, [npc]);

  const handleObserve = async () => {
    setIsObserving(true);
    try {
      const response = await fetch(`http://localhost:8000/npc/${npc.id}/observe`, {
        method: 'POST'
      });
      const data = await response.json();
      setDescription(data.description || 'Nenhuma descrição disponível.');
    } catch (error) {
      console.error('Failed to observe NPC:', error);
      setDescription('Erro ao observar NPC.');
    } finally {
      setIsObserving(false);
    }
  };

  if (!npc) return null;

  return (
    <div 
      style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.92)', backdropFilter: 'blur(16px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)', zIndex: 50 }}
      onClick={onClose}
    >
      <div 
        className="card card-gold fade-in"
        style={{ maxWidth: '700px', width: '100%' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start" style={{ marginBottom: 'var(--spacing-lg)', paddingBottom: 'var(--spacing-md)', borderBottom: '1px solid var(--border-accent)' }}>
          <div>
            <h2 className="glow-gold">{npc.name}</h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Cultivador Tier {npc.cultivation_tier || 1}</p>
          </div>
          <button
            onClick={onClose}
            className="btn-icon btn-ghost"
            style={{ fontSize: '2rem', lineHeight: 1 }}
          >
            ×
          </button>
        </div>

        <div className="flex flex-col gap-sm" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <div className="stat-item panel">
            <span className="stat-label">Estado Emocional</span>
            <span className={`stat-value ${
              npc.emotional_state === 'hostile' ? 'demon' :
              npc.emotional_state === 'friendly' ? 'jade' :
              ''
            }`} style={{ textTransform: 'capitalize' }}>
              {npc.emotional_state || 'neutral'}
            </span>
          </div>
          <div className="stat-item panel">
            <span className="stat-label">Vitalidade</span>
            <span className="stat-value demon">
              {Math.round(npc.current_hp)}/{Math.round(npc.max_hp)} HP
            </span>
          </div>
        </div>

        <div className="panel card-jade">
          {isObserving ? (
            <div className="flex items-center justify-center" style={{ padding: 'var(--spacing-xl)' }}>
              <div style={{ width: '32px', height: '32px', border: '4px solid rgba(212, 175, 55, 0.3)', borderTopColor: 'var(--gold)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
            </div>
          ) : (
            <p style={{ lineHeight: '1.7', color: 'var(--text-secondary)' }}>{description}</p>
          )}
        </div>

        <button
          onClick={onClose}
          className="btn btn-primary btn-block mt-lg"
        >
          Fechar Inspeção
        </button>
      </div>
    </div>
  );
};

export default NpcInspector;
