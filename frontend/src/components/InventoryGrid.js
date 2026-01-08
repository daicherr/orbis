import React, { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';

const InventoryGrid = () => {
  const { playerId, loadInventory } = useGame();
  const [inventory, setInventory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchInventory = async () => {
      if (!playerId) return;
      
      setIsLoading(true);
      try {
        const data = await loadInventory();
        setInventory(data);
      } catch (error) {
        console.error('Erro ao carregar inventário:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInventory();
  }, [playerId]);

  if (isLoading) {
    return (
      <div className="glass-panel p-6 rounded-xl">
        <h3 className="text-lg text-gold-glow mb-4 text-center font-title">Inventário</h3>
        <div className="flex items-center justify-center gap-2 text-jade">
          <div className="w-6 h-6 border-4 border-jade/20 border-t-jade rounded-full animate-spin"></div>
          <span className="font-body">Carregando...</span>
        </div>
      </div>
    );
  }

  if (!inventory || inventory.length === 0) {
    return (
      <div className="glass-panel p-6 rounded-xl border border-imperial/20">
        <h3 className="text-lg text-gold-glow mb-4 text-center font-title uppercase tracking-wider">Inventário</h3>
        <p className="text-slate-400 italic text-center font-body">Nenhum item no inventário</p>
      </div>
    );
  }

  return (
    <div className="glass-panel p-6 rounded-xl border border-imperial/20">
      <h3 className="text-lg text-gold-glow mb-4 text-center font-title uppercase tracking-wider">Inventário</h3>
      <div className="grid grid-cols-4 gap-3">
        {inventory.map((item, index) => (
          <div 
            key={index} 
            className="
              glass-panel p-3 rounded-lg text-center 
              border border-mist-border hover:border-imperial 
              transition-all duration-300 hover:scale-105 hover:shadow-mystic
              cursor-pointer group
            "
            title={item.description || item.name}
          >
            <div className="text-2xl mb-2">{item.icon || '📦'}</div>
            <p className="text-slate-200 text-sm font-body truncate group-hover:text-gold-glow">
              {item.name || item.item_id}
            </p>
            <p className="text-imperial font-bold text-xs mt-1">x{item.quantity}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InventoryGrid;
