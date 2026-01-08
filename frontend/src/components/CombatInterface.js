import React from 'react';

const CombatInterface = ({ skills, onSkillClick, isLoading = false }) => {
  if (!skills || skills.length === 0) {
    return null;
  }

  return (
    <div className="mystic-glass p-5 rounded-2xl border border-purple-500/30">
      <h3 className="font-title text-sm text-celestial-gold mb-4 uppercase tracking-wider flex items-center gap-2">
        <span className="text-lg">⚔️</span>
        <span>Técnicas de Cultivo</span>
      </h3>
      <div className="grid grid-cols-2 gap-3">
        {skills.map((skill) => (
          <button
            key={skill.id}
            onClick={() => onSkillClick(skill.id)}
            disabled={isLoading}
            className="group relative p-4 bg-gradient-to-br from-purple-900/40 to-indigo-900/40 hover:from-purple-800/60 hover:to-indigo-800/60 border border-purple-500/40 hover:border-purple-400/70 rounded-xl transition-all hover:scale-105 shadow-lg hover:shadow-glow-purple disabled:opacity-50 disabled:cursor-not-allowed"
            title={skill.desc}
          >
            <div className="text-3xl mb-2 filter drop-shadow-lg">{skill.icon}</div>
            <div className="font-display text-xs font-semibold leading-tight text-white/90">{skill.name}</div>
            <div className="absolute inset-0 bg-purple-400/0 group-hover:bg-purple-400/10 rounded-xl transition-all pointer-events-none"></div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default CombatInterface;
