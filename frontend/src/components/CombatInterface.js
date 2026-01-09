import React from 'react';

const CombatInterface = ({ skills, onSkillClick, isLoading = false, playerResources = {} }) => {
  if (!skills || skills.length === 0) {
    return (
      <div className="card" style={{ position: 'relative', overflow: 'hidden', opacity: 0.6 }}>
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'linear-gradient(90deg, var(--gold) 0%, var(--gold-light) 100%)', opacity: 0.5 }}></div>
        
        <h3 className="panel-header" style={{ marginBottom: 'var(--spacing-md)', display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <span style={{ fontSize: '1.5rem' }}>⚔️</span>
          <span>Técnicas de Cultivo</span>
        </h3>
        
        <div style={{ textAlign: 'center', padding: 'var(--spacing-lg)', color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
          <p>📖 Você ainda não possui técnicas de cultivo.</p>
          <p style={{ marginTop: 'var(--spacing-sm)' }}>Treine ou tenha uma epifania para aprender novas habilidades.</p>
        </div>
      </div>
    );
  }

  // Função para determinar se skill está disponível
  const isSkillAvailable = (skill) => {
    if (!skill.cost_type || !skill.cost_amount) return true;
    
    const resourceKey = skill.cost_type === 'shadow_chi' ? 'shadow_chi' 
      : skill.cost_type === 'yuan_qi' ? 'yuan_qi'
      : 'quintessence';
    
    const currentAmount = playerResources[resourceKey] || 0;
    return currentAmount >= skill.cost_amount;
  };

  // Mapear elemento para cor
  const getElementColor = (element) => {
    const colors = {
      shadow: 'var(--purple)',
      qi: 'var(--jade)',
      blood: 'var(--demon)',
      fire: '#ff6b35',
      water: '#4ecdc4',
      defense: 'var(--gold)'
    };
    return colors[element] || 'var(--text-secondary)';
  };

  // Mapear cost_type para ícone
  const getCostIcon = (costType) => {
    const icons = {
      shadow_chi: '🌑',
      yuan_qi: '✨',
      quintessence: '💎'
    };
    return icons[costType] || '⚡';
  };

  return (
    <div className="card" style={{ position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'linear-gradient(90deg, var(--gold) 0%, var(--gold-light) 100%)', opacity: 0.5 }}></div>
      
      <h3 className="panel-header" style={{ marginBottom: 'var(--spacing-md)', display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
        <span style={{ fontSize: '1.5rem' }}>⚔️</span>
        <span>Técnicas de Cultivo</span>
      </h3>
      
      <div className="grid grid-cols-2 gap-md">
        {skills.map((skill) => {
          const available = isSkillAvailable(skill);
          const elementColor = getElementColor(skill.element);
          
          return (
            <button
              key={skill.skill_id || skill.id}
              onClick={() => available && onSkillClick(skill.skill_id || skill.id)}
              disabled={isLoading || !available}
              className="card card-hover"
              style={{ 
                padding: 'var(--spacing-md)', 
                textAlign: 'left', 
                cursor: available ? 'pointer' : 'not-allowed', 
                position: 'relative', 
                transition: 'all var(--transition-base)',
                opacity: available ? 1 : 0.5,
                borderColor: available ? elementColor : 'var(--border)',
                borderWidth: '2px'
              }}
              title={skill.description || skill.desc}
            >
              {/* Tier Requirement Badge */}
              {skill.tier_requirement && (
                <div style={{ 
                  position: 'absolute', 
                  top: '4px', 
                  right: '4px', 
                  fontSize: '0.65rem', 
                  padding: '2px 6px', 
                  borderRadius: '8px', 
                  background: 'var(--bg-secondary)', 
                  color: 'var(--gold)',
                  fontWeight: 'bold'
                }}>
                  T{skill.tier_requirement}
                </div>
              )}
              
              <div style={{ fontSize: '2rem', marginBottom: 'var(--spacing-sm)' }}>
                {skill.icon || '⚔️'}
              </div>
              
              <div style={{ fontSize: '0.875rem', fontWeight: 'bold', color: elementColor, marginBottom: '4px' }}>
                {skill.name}
              </div>
              
              <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginBottom: 'var(--spacing-sm)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {skill.description || skill.desc}
              </div>
              
              {/* Cost & Cooldown */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--spacing-xs)', marginTop: '8px' }}>
                {skill.cost_type && skill.cost_amount && (
                  <div style={{ fontSize: '0.7rem', color: available ? 'var(--jade)' : 'var(--demon)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>{getCostIcon(skill.cost_type)}</span>
                    <span>{skill.cost_amount}</span>
                  </div>
                )}
                
                {skill.cooldown && skill.cooldown > 0 && (
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span>⏱️</span>
                    <span>{skill.cooldown}t</span>
                  </div>
                )}
                
                {skill.is_silent_art && (
                  <div style={{ fontSize: '0.7rem', color: 'var(--purple)', fontWeight: 'bold' }} title="Arte Silenciosa - Não detectável">
                    🤫
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default CombatInterface;
