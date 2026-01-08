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
        setInventory(data || []);
      } catch (error) {
        console.error('Erro ao carregar inventário:', error);
        setInventory([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInventory();
  }, [playerId]);

  if (isLoading) {
    return (
      <div className="panel" style={{ padding: 'var(--spacing-lg)' }}>
        <h3 className="glow-gold text-center" style={{ marginBottom: 'var(--spacing-md)' }}>Inventário</h3>
        <div className="flex items-center justify-center gap-sm">
          <div className="spinner" style={{ width: '24px', height: '24px' }}></div>
          <span style={{ color: 'var(--jade)' }}>Carregando...</span>
        </div>
      </div>
    );
  }

  if (!inventory || inventory.length === 0) {
    return (
      <div className="panel card-gold" style={{ padding: 'var(--spacing-lg)' }}>
        <h3 className="glow-gold text-center" style={{ marginBottom: 'var(--spacing-md)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Inventário</h3>
        <p style={{ color: 'var(--text-tertiary)', fontStyle: 'italic', textAlign: 'center' }}>Nenhum item no inventário</p>
      </div>
    );
  }

  return (
    <div className="panel card-gold" style={{ padding: 'var(--spacing-lg)' }}>
      <h3 className="glow-gold text-center" style={{ marginBottom: 'var(--spacing-md)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Inventário</h3>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--spacing-sm)' }}>
        {inventory.map((item, index) => (
          <div 
            key={index} 
            className="panel card-hover text-center"
            style={{ 
              padding: 'var(--spacing-sm)',
              cursor: 'pointer',
              transition: 'all var(--transition-base)'
            }}
            title={item.description || item.name}
          >
            <div style={{ fontSize: '1.5rem', marginBottom: 'var(--spacing-xs)' }}>{item.icon || '📦'}</div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.name || item.item_id}
            </p>
            <p style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--gold)' }}>x{item.quantity}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InventoryGrid;
