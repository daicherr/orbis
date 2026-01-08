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
      className="fixed inset-0 bg-black/90 backdrop-blur-xl flex items-center justify-center p-4 z-50 animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="mystic-glass-gold p-8 max-w-2xl w-full animate-scale-in shadow-2xl rounded-2xl border-2 border-amber-500/50"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-6 border-b-2 border-amber-500/30 pb-4">
          <div>
            <h2 className="font-title text-3xl text-celestial-gold text-mystic-glow">{npc.name}</h2>
            <p className="font-display text-sm text-white/70 mt-1">Cultivador Tier {npc.cultivation_tier || 1}</p>
          </div>
          <button
            onClick={onClose}
            className="text-3xl hover:text-red-400 transition-colors font-bold"
          >
            ×
          </button>
        </div>

        <div className="space-y-3 mb-6">
          <div className="flex justify-between p-4 bg-black/50 rounded-xl border border-purple-500/30">
            <span className="font-body text-white/70">Estado Emocional</span>
            <span className={`font-display font-semibold capitalize ${
              npc.emotional_state === 'hostile' ? 'text-red-300' :
              npc.emotional_state === 'friendly' ? 'text-green-300' :
              'text-blue-300'
            }`}>
              {npc.emotional_state || 'neutral'}
            </span>
          </div>
          <div className="flex justify-between p-4 bg-black/50 rounded-xl border border-red-500/30">
            <span className="font-body text-white/70">Vitalidade</span>
            <span className="font-mono font-semibold text-red-300">
              {Math.round(npc.current_hp)}/{Math.round(npc.max_hp)} HP
            </span>
          </div>
        </div>

        <div className="p-6 bg-gradient-to-br from-purple-900/40 to-indigo-900/40 rounded-xl border border-purple-500/40 backdrop-blur-sm">
          {isObserving ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner border-celestial-gold"></div>
            </div>
          ) : (
            <p className="font-body text-base leading-relaxed text-white/90">{description}</p>
          )}
        </div>

        <button
          onClick={onClose}
          className="btn-celestial w-full mt-6 px-6 py-3 font-display text-base"
        >
          Fechar Inspeção
        </button>
      </div>
    </div>
  );
};

export default NpcInspector;
