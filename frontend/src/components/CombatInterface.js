import React from 'react';

const CombatInterface = ({ skills, onSkillClick, isLoading = false }) => {
  if (!skills || skills.length === 0) {
    return null;
  }

  return (
    <div className="glass-panel p-5 rounded-2xl border border-imperial/20 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-gold opacity-50"></div>
      <h3 className="font-title text-base text-gold-glow mb-4 uppercase tracking-wider flex items-center gap-2">
        <span className="text-2xl">⚔️</span>
        <span>Técnicas de Cultivo</span>
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-3">
        {skills.map((skill) => (
          <button
            key={skill.id}
            onClick={() => onSkillClick(skill.id)}
            disabled={isLoading}
            className="
              group relative p-4 
              bg-gradient-void hover:bg-gradient-to-r hover:from-purple-900 hover:to-indigo-900
              border border-mist-border hover:border-imperial 
              rounded-xl transition-all duration-300 
              hover:scale-105 hover:shadow-glow-purple
              disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100
              text-left
            "
            title={skill.desc}
          >
            <div className="text-3xl mb-2 filter drop-shadow-lg group-hover:scale-110 transition-transform">
              {skill.icon}
            </div>
            <div className="font-display text-sm font-bold leading-tight text-slate-200 group-hover:text-gold-glow transition-colors">
              {skill.name}
            </div>
            <div className="font-body text-xs text-slate-400 mt-1 line-clamp-1">
              {skill.desc}
            </div>
            <div className="absolute inset-0 bg-imperial/0 group-hover:bg-imperial/10 rounded-xl transition-all pointer-events-none"></div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default CombatInterface;
