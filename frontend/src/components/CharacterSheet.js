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
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gradient-to-br from-purple-900 to-indigo-900 p-8 rounded-lg shadow-2xl">
          <p className="text-white">Carregando dados do cultivador...</p>
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

  const renderStatsTab = () => (
    <div className="space-y-4">
      {/* Cultivation Tier */}
      <div className="bg-gradient-to-r from-yellow-900 to-amber-800 p-4 rounded-lg border border-yellow-600">
        <h3 className="text-xl font-bold text-yellow-300 mb-2">Cultivation Tier</h3>
        <p className="text-3xl font-bold text-white">Tier {cultivation_tier}</p>
      </div>

      {/* Health Bar */}
      <div className="bg-gray-800 p-4 rounded-lg">
        <div className="flex justify-between mb-2">
          <span className="text-red-400 font-semibold">HP</span>
          <span className="text-white">{current_hp} / {max_hp}</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-4">
          <div 
            className="bg-gradient-to-r from-red-500 to-red-700 h-4 rounded-full transition-all"
            style={{ width: `${(current_hp / max_hp) * 100}%` }}
          />
        </div>
      </div>

      {/* Energy Bars (Tri-Vector System) */}
      <div className="space-y-3">
        {/* Quintessential Essence */}
        <div className="bg-gray-800 p-3 rounded-lg">
          <div className="flex justify-between mb-1">
            <span className="text-orange-400 text-sm font-semibold">Quintessential Essence</span>
            <span className="text-white text-sm">{quintessential_essence} / {max_quintessential_essence}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-orange-500 to-red-600 h-2 rounded-full"
              style={{ width: `${(quintessential_essence / max_quintessential_essence) * 100}%` }}
            />
          </div>
        </div>

        {/* Shadow Chi */}
        <div className="bg-gray-800 p-3 rounded-lg">
          <div className="flex justify-between mb-1">
            <span className="text-purple-400 text-sm font-semibold">Shadow Chi</span>
            <span className="text-white text-sm">{shadow_chi} / {max_shadow_chi}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-purple-500 to-indigo-600 h-2 rounded-full"
              style={{ width: `${(shadow_chi / max_shadow_chi) * 100}%` }}
            />
          </div>
        </div>

        {/* Yuan Qi */}
        <div className="bg-gray-800 p-3 rounded-lg">
          <div className="flex justify-between mb-1">
            <span className="text-cyan-400 text-sm font-semibold">Yuan Qi</span>
            <span className="text-white text-sm">{yuan_qi} / {max_yuan_qi}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-cyan-500 to-blue-600 h-2 rounded-full"
              style={{ width: `${(yuan_qi / max_yuan_qi) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Gold */}
      <div className="bg-gradient-to-r from-yellow-900 to-yellow-800 p-3 rounded-lg border border-yellow-600">
        <div className="flex justify-between items-center">
          <span className="text-yellow-300 font-semibold">🪙 Gold Tael</span>
          <span className="text-white text-xl font-bold">{gold}</span>
        </div>
      </div>
    </div>
  );

  const renderBackstoryTab = () => (
    <div className="space-y-4">
      {/* Appearance */}
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-lg font-bold text-purple-300 mb-2">Aparência</h3>
        <p className="text-gray-300">{appearance || 'Não especificada'}</p>
      </div>

      {/* Constitution */}
      <div className="bg-gradient-to-r from-indigo-900 to-purple-900 p-4 rounded-lg border border-purple-500">
        <h3 className="text-lg font-bold text-purple-300 mb-2">Constituição</h3>
        <p className="text-white text-xl font-semibold">{constitution_type}</p>
      </div>

      {/* Origin */}
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-lg font-bold text-blue-300 mb-2">Local de Origem</h3>
        <p className="text-gray-300">{origin_location}</p>
      </div>

      {/* Backstory */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-4 rounded-lg border border-gray-700">
        <h3 className="text-lg font-bold text-yellow-300 mb-3">História</h3>
        <p className="text-gray-300 leading-relaxed">{backstory}</p>
      </div>
    </div>
  );

  const renderInventoryTab = () => (
    <div className="space-y-4">
      {/* Skills */}
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-lg font-bold text-cyan-300 mb-3">Habilidades Aprendidas</h3>
        {learned_skills && learned_skills.length > 0 ? (
          <div className="grid grid-cols-2 gap-2">
            {learned_skills.map((skill, idx) => (
              <div key={idx} className="bg-gray-700 p-2 rounded border border-cyan-600">
                <p className="text-white text-sm font-semibold">{skill}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 italic">Nenhuma habilidade aprendida ainda</p>
        )}
      </div>

      {/* Inventory Items */}
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-lg font-bold text-yellow-300 mb-3">Inventário</h3>
        {inventory && inventory.length > 0 ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {inventory.map((item, idx) => (
              <div key={idx} className="bg-gray-700 p-3 rounded flex justify-between items-center border border-gray-600">
                <div>
                  <p className="text-white font-semibold">{item.item_id.replace(/_/g, ' ').toUpperCase()}</p>
                  <p className="text-gray-400 text-xs">
                    Tier {item.tier} | {item.category}
                    {item.quantity > 1 && ` | x${item.quantity}`}
                  </p>
                </div>
                {item.buy_price && (
                  <span className="text-yellow-400 text-sm">🪙 {item.buy_price}</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 italic">Inventário vazio</p>
        )}
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-br from-gray-900 to-indigo-900 rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden border-2 border-purple-500">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-800 to-indigo-800 p-4 border-b border-purple-500">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-white">{name}</h2>
            <button
              onClick={onClose}
              className="text-white hover:text-red-400 text-2xl font-bold transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700 bg-gray-800">
          <button
            onClick={() => setActiveTab('stats')}
            className={`flex-1 py-3 font-semibold transition-colors ${
              activeTab === 'stats'
                ? 'bg-purple-700 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            📊 Stats
          </button>
          <button
            onClick={() => setActiveTab('backstory')}
            className={`flex-1 py-3 font-semibold transition-colors ${
              activeTab === 'backstory'
                ? 'bg-purple-700 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            📜 História
          </button>
          <button
            onClick={() => setActiveTab('inventory')}
            className={`flex-1 py-3 font-semibold transition-colors ${
              activeTab === 'inventory'
                ? 'bg-purple-700 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            🎒 Inventário
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {activeTab === 'stats' && renderStatsTab()}
          {activeTab === 'backstory' && renderBackstoryTab()}
          {activeTab === 'inventory' && renderInventoryTab()}
        </div>
      </div>
    </div>
  );
}
