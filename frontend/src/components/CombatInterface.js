import React, { useState } from 'react';

const CombatInterface = ({ skills, targets, onAttack }) => {
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [selectedTarget, setSelectedTarget] = useState(null);

  const handleAttack = () => {
    if (selectedSkill && selectedTarget) {
      onAttack(selectedSkill, selectedTarget);
      setSelectedSkill(null);
      setSelectedTarget(null);
    } else {
      alert("Selecione uma habilidade e um alvo.");
    }
  };

  return (
    <div className="mt-4 p-4 border-2 border-cult-red rounded-lg bg-cult-dark">
      <div className="grid grid-cols-2 gap-4">
        {/* Coluna de Habilidades */}
        <div>
          <h4 className="text-cult-gold font-bold mb-2">Habilidades</h4>
          {skills.map(skill => (
            <button
              key={skill.id}
              onClick={() => setSelectedSkill(skill.id)}
              className={`block w-full text-left p-2 rounded mb-1 ${selectedSkill === skill.id ? 'bg-cult-red text-white' : 'bg-cult-secondary text-cult-light hover:bg-cult-red'}`}
            >
              {skill.name}
            </button>
          ))}
        </div>
        
        {/* Coluna de Alvos */}
        <div>
          <h4 className="text-cult-gold font-bold mb-2">Alvos</h4>
          {targets.map(target => (
            <button
              key={target.id}
              onClick={() => setSelectedTarget(target.id)}
              className={`block w-full text-left p-2 rounded mb-1 ${selectedTarget === target.id ? 'bg-cult-red text-white' : 'bg-cult-secondary text-cult-light hover:bg-cult-red'}`}
            >
              {target.name}
            </button>
          ))}
        </div>
      </div>
      
      <button
        onClick={handleAttack}
        disabled={!selectedSkill || !selectedTarget}
        className="w-full mt-4 bg-cult-red text-white font-bold py-2 px-4 rounded hover:bg-red-700 transition duration-300 disabled:bg-gray-600"
      >
        Atacar
      </button>
    </div>
  );
};

export default CombatInterface;
