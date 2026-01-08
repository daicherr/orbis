import React from 'react';

const StatBar = ({ label, value, maxValue, colorClass, icon }) => {
  const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
  
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs mb-1.5">
        <span className="font-body text-white/70 flex items-center gap-1">
          <span>{icon}</span>
          <span>{label}</span>
        </span>
        <span className="font-mono text-white/80">{Math.round(value)}/{Math.round(maxValue)}</span>
      </div>
      <div className="h-2 bg-black/40 rounded-full overflow-hidden border border-white/10">
        <div 
          className={`h-full ${colorClass} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const PlayerHUD = ({ playerStats }) => {
  if (!playerStats) {
    return (
      <div className="glass-panel p-6 rounded-xl">
        <div className="flex items-center gap-3 text-jade font-body">
          <div className="w-6 h-6 border-4 border-jade/20 border-t-jade rounded-full animate-spin"></div>
          <span>Carregando dados do cultivador...</span>
        </div>
      </div>
    );
  }

  const getTierName = (tier) => {
    const tiers = {
      1: "Fundação", 2: "Despertar", 3: "Ascensão",
      4: "Transcendência", 5: "Soberania", 6: "Divindade",
      7: "Imortalidade", 8: "Ancestral", 9: "Criação"
    };
    return tiers[tier] || `Tier ${tier}`;
  };

  return (
    <div className="space-y-4">
      {/* HP */}
      <div className="mystic-glass p-4 rounded-xl border border-red-500/30">
        <StatBar 
          label="HP" 
          value={playerStats.current_hp || 0} 
          maxValue={playerStats.max_hp || 100} 
          colorClass="bg-gradient-to-r from-red-600 via-red-500 to-pink-500 shadow-glow-purple"
          icon="❤️"
        />
      </div>

      {/* Tríade Energética */}
      <div className="mystic-glass p-4 rounded-xl border border-purple-500/30">
        <h3 className="font-title text-sm text-celestial-gold mb-3 uppercase tracking-wider">Tríade Energética</h3>
        <div className="space-y-3">
          <StatBar 
            label="Quintessência" 
            value={playerStats.quintessential_essence || 0} 
            maxValue={playerStats.max_quintessential_essence || 100}
            colorClass="bg-gradient-to-r from-orange-600 to-yellow-500"
            icon="💎"
          />
          <StatBar 
            label="Shadow Chi" 
            value={playerStats.shadow_chi || 0} 
            maxValue={playerStats.max_shadow_chi || 100}
            colorClass="bg-gradient-to-r from-purple-600 to-violet-500 shadow-glow-purple"
            icon="🌙"
          />
          <StatBar 
            label="Yuan Qi" 
            value={playerStats.yuan_qi || 0} 
            maxValue={playerStats.max_yuan_qi || 100}
            colorClass="bg-gradient-to-r from-blue-600 to-cyan-500"
            icon="⚡"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="mystic-glass p-4 rounded-xl border border-amber-500/30">
        <h3 className="font-title text-sm text-celestial-gold mb-3 uppercase tracking-wider">Atributos</h3>
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-black/30 rounded-lg p-2 border border-blue-500/20">
            <div className="font-mono text-lg font-bold text-blue-300">{playerStats.rank || 1}</div>
            <div className="font-body text-xs text-white/60">Rank</div>
          </div>
          <div className="bg-black/30 rounded-lg p-2 border border-green-500/20">
            <div className="font-mono text-lg font-bold text-green-300">{Math.round(playerStats.xp || 0)}</div>
            <div className="font-body text-xs text-white/60">XP</div>
          </div>
          <div className="bg-black/30 rounded-lg p-2 border border-red-500/20">
            <div className="font-mono text-lg font-bold text-red-300">{Math.round(playerStats.corruption || 0)}%</div>
            <div className="font-body text-xs text-white/60">Corrupção</div>
          </div>
          <div className="bg-black/30 rounded-lg p-2 border border-purple-500/20">
            <div className="font-mono text-lg font-bold text-purple-300">{Math.round(playerStats.willpower || 50)}</div>
            <div className="font-body text-xs text-white/60">Vontade</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlayerHUD;
