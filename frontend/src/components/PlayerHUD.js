import React from 'react';

const StatBar = ({ label, value, maxValue, colorClass }) => (
  <div className="mb-2">
    <div className="flex justify-between text-sm font-bold text-cult-light">
      <span>{label}</span>
      <span>{Math.round(value)} / {maxValue}</span>
    </div>
    <div className="w-full bg-cult-secondary rounded-full h-2.5">
      <div 
        className={`${colorClass} h-2.5 rounded-full`} 
        style={{ width: `${(value / maxValue) * 100}%` }}
      ></div>
    </div>
  </div>
);

const PlayerHUD = ({ playerStats }) => {
  if (!playerStats) {
    return <div>Carregando status...</div>;
  }

  return (
    <div className="p-4 bg-cult-dark border-2 border-cult-gold rounded-lg shadow-lg">
      <h3 className="text-lg font-bold text-cult-gold mb-3 text-center">{playerStats.name}</h3>
      
      {/* Tríade Energética */}
      <StatBar label="HP" value={playerStats.current_hp} maxValue={playerStats.max_hp} colorClass="bg-red-600" />
      <StatBar label="Quintessência" value={playerStats.quintessential_essence} maxValue={100} colorClass="bg-yellow-500" />
      <StatBar label="Chi das Sombras" value={playerStats.shadow_chi} maxValue={100} colorClass="bg-purple-600" />
      <StatBar label="Yuan Qi" value={playerStats.yuan_qi} maxValue={100} colorClass="bg-blue-500" />
      
    </div>
  );
};

export default PlayerHUD;
