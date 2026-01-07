import React from 'react';

const NpcInspector = ({ npc, onObserve, description, isObserving }) => {
  if (!npc) return null;

  return (
    <div className="p-4 bg-cult-dark border-2 border-cult-gold rounded-lg shadow-lg mt-4">
      <h3 className="text-xl font-bold text-cult-gold mb-2 text-center">{npc.name}</h3>
      <div className="text-center text-cult-light mb-4">
        <p>Rank: {npc.rank}</p>
        <p>Estado Emocional: <span className="italic capitalize">{npc.emotional_state}</span></p>
      </div>
      
      <button
        onClick={() => onObserve(npc)}
        disabled={isObserving}
        className="w-full bg-cult-gold text-cult-dark font-bold py-2 px-4 rounded hover:bg-yellow-600 transition duration-300 disabled:bg-gray-500"
      >
        {isObserving ? "Observando..." : "Observar com Percepção Espiritual"}
      </button>

      {description && (
        <div className="mt-4 p-3 bg-cult-secondary rounded">
          <p className="text-cult-light italic">{description}</p>
        </div>
      )}
    </div>
  );
};

export default NpcInspector;
