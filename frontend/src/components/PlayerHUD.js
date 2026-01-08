import React from 'react';

const StatBar = ({ label, value, maxValue, type, icon }) => {
  const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
  
  return (
    <div style={{ marginBottom: '12px' }}>
      <div className="flex justify-between" style={{ marginBottom: '6px' }}>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>{icon}</span>
          <span>{label}</span>
        </span>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
          {Math.round(value)}/{Math.round(maxValue)}
        </span>
      </div>
      <div className="progress-bar">
        <div 
          className={`progress-fill ${type}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const PlayerHUD = ({ playerStats }) => {
  if (!playerStats) {
    return (
      <div className="panel">
        <div className="flex items-center gap-md">
          <div className="loading-spinner"></div>
          <span style={{ color: 'var(--jade)' }}>Carregando dados do cultivador...</span>
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
    <div className="flex flex-col gap-md">
      {/* HP */}
      <div className="panel card-demon" style={{ borderColor: 'var(--demon)' }}>
        <h3 className="panel-header" style={{ color: 'var(--demon)', marginBottom: 'var(--spacing-sm)' }}>
          <span>❤️</span> Vitalidade
        </h3>
        <StatBar 
          label="HP" 
          value={playerStats.current_hp || 0} 
          maxValue={playerStats.max_hp || 100} 
          type="health"
          icon="💓"
        />
      </div>

      {/* Tríade Energética */}
      <div className="panel card-jade">
        <h3 className="panel-header" style={{ color: 'var(--jade)', marginBottom: 'var(--spacing-md)' }}>
          <span>✨</span> Tríade Energética
        </h3>
        <div className="flex flex-col gap-sm">
          <StatBar 
            label="Quintessência" 
            value={playerStats.quintessential_essence || 0} 
            maxValue={playerStats.max_quintessential_essence || 100}
            type="energy"
            icon="💎"
          />
          <StatBar 
            label="Shadow Chi" 
            value={playerStats.shadow_chi || 0} 
            maxValue={playerStats.max_shadow_chi || 100}
            type="shadow"
            icon="🌙"
          />
          <StatBar 
            label="Yuan Qi" 
            value={playerStats.yuan_qi || 0} 
            maxValue={playerStats.max_yuan_qi || 100}
            type="energy"
            icon="⚡"
          />
        </div>
      </div>

      {/* Atributos */}
      <div className="panel">
        <h3 className="panel-header" style={{ marginBottom: 'var(--spacing-md)' }}>
          <span>📊</span> Atributos
        </h3>
        <div className="grid grid-cols-2 gap-sm">
          <div className="stat-box">
            <div className="stat-value glow-gold">{playerStats.cultivation_tier || 1}</div>
            <div className="stat-label">{getTierName(playerStats.cultivation_tier || 1)}</div>
          </div>
          <div className="stat-box">
            <div className="stat-value" style={{ color: 'var(--jade)' }}>{Math.round(playerStats.xp || 0)}</div>
            <div className="stat-label">Experiência</div>
          </div>
          <div className="stat-box">
            <div className="stat-value" style={{ color: 'var(--demon)' }}>{Math.round(playerStats.corruption || 0)}%</div>
            <div className="stat-label">Corrupção</div>
          </div>
          <div className="stat-box">
            <div className="stat-value" style={{ color: 'var(--purple)' }}>{Math.round(playerStats.willpower || 50)}</div>
            <div className="stat-label">Vontade</div>
          </div>
        </div>
        
        {/* Stats Secundários */}
        <div style={{ marginTop: 'var(--spacing-md)', paddingTop: 'var(--spacing-md)', borderTop: '1px solid var(--border-color)' }} className="grid grid-cols-3 gap-sm">
          <div className="stat-box-mini">
            <div className="stat-value-mini">{playerStats.strength || 10}</div>
            <div className="stat-label-mini">FOR</div>
          </div>
          <div className="stat-box-mini">
            <div className="stat-value-mini">{playerStats.defense || 5}</div>
            <div className="stat-label-mini">DEF</div>
          </div>
          <div className="stat-box-mini">
            <div className="stat-value-mini">{playerStats.speed || 10}</div>
            <div className="stat-label-mini">VEL</div>
          </div>
        </div>
      </div>

      {/* Localização Atual */}
      {playerStats.current_location && (
        <div className="panel" style={{ padding: 'var(--spacing-md)' }}>
          <div className="flex items-center gap-sm">
            <span style={{ fontSize: '1.5rem' }}>📍</span>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Localização</div>
              <div style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--gold)', textTransform: 'capitalize' }}>
                {playerStats.current_location.replace(/_/g, ' ')}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerHUD;
