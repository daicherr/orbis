import React from 'react';

const CombatInterface = ({ skills, onSkillClick, isLoading = false }) => {
  if (!skills || skills.length === 0) {
    return null;
  }

  return (
    <div className="card" style={{ position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'linear-gradient(90deg, var(--gold) 0%, var(--gold-light) 100%)', opacity: 0.5 }}></div>
      
      <h3 className="panel-header" style={{ marginBottom: 'var(--spacing-md)', display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
        <span style={{ fontSize: '1.5rem' }}>⚔️</span>
        <span>Técnicas de Cultivo</span>
      </h3>
      
      <div className="grid grid-cols-2 gap-md">
        {skills.map((skill) => (
          <button
            key={skill.id}
            onClick={() => onSkillClick(skill.id)}
            disabled={isLoading}
            className="card card-hover"
            style={{ padding: 'var(--spacing-md)', textAlign: 'left', cursor: 'pointer', position: 'relative', transition: 'all var(--transition-base)' }}
            title={skill.desc}
          >
            <div style={{ fontSize: '2rem', marginBottom: 'var(--spacing-sm)' }}>
              {skill.icon}
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 'bold', color: 'var(--text-primary)', marginBottom: '4px' }}>
              {skill.name}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {skill.desc}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default CombatInterface;
