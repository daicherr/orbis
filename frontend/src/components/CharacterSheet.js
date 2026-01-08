import React, { useState, useEffect } from 'react';

export default function CharacterSheet({ playerId, onClose }) {
  const [characterData, setCharacterData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('stats'); // 'stats', 'backstory', 'inventory'

  useEffect(() => {
    if (playerId) {
      fetchCharacterData();
    }
  }, [playerId]);

  const fetchCharacterData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/player/${playerId}`);
      if (!response.ok) throw new Error('Failed to fetch character');
      const data = await response.json();
      setCharacterData(data);
    } catch (error) {
      console.error('Error fetching character:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="card card-gold" style={{ padding: 'var(--spacing-xl)', textAlign: 'center' }}>
          <div className="loading-spinner" style={{ margin: '0 auto var(--spacing-md)' }}></div>
          <p style={{ color: 'var(--text-primary)' }}>Carregando dados do cultivador...</p>
        </div>
      </div>
    );
  }

  if (!characterData) {
    return null;
  }

  const { 
    name, 
    appearance, 
    constitution_type, 
    origin_location, 
    backstory,
    cultivation_tier,
    current_hp,
    max_hp,
    quintessential_essence,
    max_quintessential_essence,
    shadow_chi,
    max_shadow_chi,
    yuan_qi,
    max_yuan_qi,
    gold,
    inventory,
    learned_skills
  } = characterData;

  const getTierName = (tier) => {
    const tiers = {
      1: "Fundação", 2: "Despertar", 3: "Ascensão",
      4: "Transcendência", 5: "Soberania", 6: "Divindade",
      7: "Imortalidade", 8: "Ancestral", 9: "Criação"
    };
    return tiers[tier] || `Tier ${tier}`;
  };

  const renderProgressBar = (value, maxValue, type) => {
    const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
    return (
      <div className="progress-bar" style={{ height: '10px' }}>
        <div className={`progress-fill ${type}`} style={{ width: `${percentage}%` }} />
      </div>
    );
  };

  const renderStatsTab = () => (
    <div className="flex flex-col gap-md">
      {/* Cultivation Tier */}
      <div className="card card-gold" style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--gold)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 'var(--spacing-xs)' }}>
          Nível de Cultivo
        </div>
        <div className="glow-gold" style={{ fontSize: '2.5rem', fontWeight: 700 }}>
          Tier {cultivation_tier}
        </div>
        <div style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>
          {getTierName(cultivation_tier)}
        </div>
      </div>

      {/* Health Bar */}
      <div className="panel">
        <div className="flex justify-between" style={{ marginBottom: 'var(--spacing-sm)' }}>
          <span style={{ color: 'var(--demon)', fontWeight: 600 }}>❤️ HP</span>
          <span style={{ color: 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>
            {current_hp} / {max_hp}
          </span>
        </div>
        {renderProgressBar(current_hp, max_hp, 'health')}
      </div>

      {/* Energy Bars (Tri-Vector System) */}
      <div className="panel">
        <h3 className="panel-header" style={{ marginBottom: 'var(--spacing-md)' }}>
          ✨ Tríade Energética
        </h3>
        <div className="flex flex-col gap-md">
          {/* Quintessential Essence */}
          <div>
            <div className="flex justify-between" style={{ marginBottom: 'var(--spacing-xs)' }}>
              <span style={{ color: 'var(--jade)', fontSize: '0.875rem' }}>💎 Quintessência</span>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontFamily: 'JetBrains Mono, monospace' }}>
                {quintessential_essence} / {max_quintessential_essence}
              </span>
            </div>
            {renderProgressBar(quintessential_essence, max_quintessential_essence, 'energy')}
          </div>

          {/* Shadow Chi */}
          <div>
            <div className="flex justify-between" style={{ marginBottom: 'var(--spacing-xs)' }}>
              <span style={{ color: 'var(--purple)', fontSize: '0.875rem' }}>🌙 Shadow Chi</span>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontFamily: 'JetBrains Mono, monospace' }}>
                {shadow_chi} / {max_shadow_chi}
              </span>
            </div>
            {renderProgressBar(shadow_chi, max_shadow_chi, 'shadow')}
          </div>

          {/* Yuan Qi */}
          <div>
            <div className="flex justify-between" style={{ marginBottom: 'var(--spacing-xs)' }}>
              <span style={{ color: '#22d3ee', fontSize: '0.875rem' }}>⚡ Yuan Qi</span>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontFamily: 'JetBrains Mono, monospace' }}>
                {yuan_qi} / {max_yuan_qi}
              </span>
            </div>
            <div className="progress-bar" style={{ height: '8px' }}>
              <div style={{ 
                height: '100%', 
                width: `${max_yuan_qi > 0 ? (yuan_qi / max_yuan_qi) * 100 : 0}%`,
                background: 'linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%)',
                borderRadius: '999px',
                boxShadow: '0 0 10px rgba(6, 182, 212, 0.5)'
              }} />
            </div>
          </div>
        </div>
      </div>

      {/* Gold */}
      <div className="panel" style={{ 
        background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(255, 215, 0, 0.1) 100%)',
        borderColor: 'var(--gold)'
      }}>
        <div className="flex justify-between items-center">
          <span style={{ color: 'var(--gold)', fontWeight: 600 }}>🪙 Gold Tael</span>
          <span className="glow-gold" style={{ fontSize: '1.5rem', fontWeight: 700 }}>{gold}</span>
        </div>
      </div>
    </div>
  );

  const renderBackstoryTab = () => (
    <div className="flex flex-col gap-md">
      {/* Appearance */}
      <div className="panel">
        <h3 className="panel-header" style={{ color: 'var(--purple)' }}>👤 Aparência</h3>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, marginTop: 'var(--spacing-sm)' }}>
          {appearance || 'Não especificada'}
        </p>
      </div>

      {/* Constitution */}
      <div className="card card-gold">
        <h3 className="panel-header">⚗️ Constituição</h3>
        <p className="glow-gold" style={{ fontSize: '1.25rem', fontWeight: 600, marginTop: 'var(--spacing-sm)' }}>
          {constitution_type}
        </p>
      </div>

      {/* Origin */}
      <div className="panel">
        <h3 className="panel-header" style={{ color: 'var(--jade)' }}>📍 Local de Origem</h3>
        <p style={{ color: 'var(--text-primary)', marginTop: 'var(--spacing-sm)', textTransform: 'capitalize' }}>
          {origin_location?.replace(/_/g, ' ')}
        </p>
      </div>

      {/* Backstory */}
      <div className="panel" style={{ borderColor: 'var(--gold)' }}>
        <h3 className="panel-header">📜 História</h3>
        <p style={{ 
          color: 'var(--text-secondary)', 
          lineHeight: 1.8, 
          marginTop: 'var(--spacing-md)',
          fontStyle: 'italic'
        }}>
          {backstory}
        </p>
      </div>
    </div>
  );

  const renderInventoryTab = () => (
    <div className="flex flex-col gap-md">
      {/* Skills */}
      <div className="panel">
        <h3 className="panel-header" style={{ color: '#22d3ee' }}>⚔️ Habilidades Aprendidas</h3>
        {learned_skills && learned_skills.length > 0 ? (
          <div className="grid grid-cols-2 gap-sm" style={{ marginTop: 'var(--spacing-md)' }}>
            {learned_skills.map((skill, idx) => (
              <div key={idx} className="badge badge-jade" style={{ 
                padding: 'var(--spacing-sm) var(--spacing-md)',
                fontSize: '0.875rem'
              }}>
                {skill}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--text-tertiary)', fontStyle: 'italic', marginTop: 'var(--spacing-sm)' }}>
            Nenhuma habilidade aprendida ainda
          </p>
        )}
      </div>

      {/* Inventory Items */}
      <div className="panel">
        <h3 className="panel-header">🎒 Inventário</h3>
        {inventory && inventory.length > 0 ? (
          <div className="flex flex-col gap-sm" style={{ marginTop: 'var(--spacing-md)', maxHeight: '300px', overflowY: 'auto' }}>
            {inventory.map((item, idx) => (
              <div key={idx} className="panel" style={{ 
                padding: 'var(--spacing-sm) var(--spacing-md)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                    {item.item_id.replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <div style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>
                    Tier {item.tier} | {item.category}
                    {item.quantity > 1 && ` | x${item.quantity}`}
                  </div>
                </div>
                {item.buy_price && (
                  <span style={{ color: 'var(--gold)', fontSize: '0.875rem' }}>🪙 {item.buy_price}</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--text-tertiary)', fontStyle: 'italic', marginTop: 'var(--spacing-sm)' }}>
            Inventário vazio
          </p>
        )}
      </div>
    </div>
  );

  const tabStyle = (isActive) => ({
    flex: 1,
    padding: 'var(--spacing-md)',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    border: 'none',
    background: isActive ? 'var(--gold)' : 'transparent',
    color: isActive ? 'var(--bg-primary)' : 'var(--text-secondary)',
    borderBottom: isActive ? 'none' : '1px solid var(--border-color)'
  });

  return (
    <div className="modal-overlay">
      <div className="card" style={{ 
        maxWidth: '700px', 
        width: '100%', 
        maxHeight: '90vh', 
        overflow: 'hidden',
        border: '2px solid var(--gold)',
        boxShadow: 'var(--shadow-lg), 0 0 40px rgba(212, 175, 55, 0.2)'
      }}>
        {/* Header */}
        <div style={{ 
          padding: 'var(--spacing-lg)',
          borderBottom: '2px solid var(--gold)',
          background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, transparent 100%)'
        }}>
          <div className="flex justify-between items-center">
            <h2 className="glow-gold" style={{ 
              fontSize: '1.75rem', 
              fontWeight: 700,
              fontFamily: 'Playfair Display, serif'
            }}>
              {name}
            </h2>
            <button
              onClick={onClose}
              className="btn btn-ghost btn-icon"
              style={{ fontSize: '1.5rem', padding: 'var(--spacing-sm)' }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex" style={{ borderBottom: '1px solid var(--border-color)' }}>
          <button onClick={() => setActiveTab('stats')} style={tabStyle(activeTab === 'stats')}>
            📊 Stats
          </button>
          <button onClick={() => setActiveTab('backstory')} style={tabStyle(activeTab === 'backstory')}>
            📜 História
          </button>
          <button onClick={() => setActiveTab('inventory')} style={tabStyle(activeTab === 'inventory')}>
            🎒 Inventário
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: 'var(--spacing-lg)', overflowY: 'auto', maxHeight: 'calc(90vh - 180px)' }}>
          {activeTab === 'stats' && renderStatsTab()}
          {activeTab === 'backstory' && renderBackstoryTab()}
          {activeTab === 'inventory' && renderInventoryTab()}
        </div>
      </div>
    </div>
  );
}
