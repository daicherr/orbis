import React from 'react';

const InventoryGrid = ({ inventory, itemsData }) => {
  if (!inventory || inventory.length === 0) {
    return (
      <div className="p-4 bg-cult-dark border-2 border-cult-gold rounded-lg mt-4">
        <h3 className="text-lg text-cult-gold mb-2 text-center">Inventário</h3>
        <p className="text-cult-light italic text-center">Vazio</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-cult-dark border-2 border-cult-gold rounded-lg mt-4">
      <h3 className="text-lg text-cult-gold mb-2 text-center">Inventário</h3>
      <div className="grid grid-cols-4 gap-2">
        {inventory.map((item, index) => {
          const itemDetails = itemsData[item.item_id] || { name: item.item_id };
          return (
            <div key={index} className="p-2 bg-cult-secondary rounded text-center" title={itemDetails.description}>
              <p className="text-cult-light text-sm truncate">{itemDetails.name}</p>
              <p className="text-cult-gold font-bold text-xs">x{item.quantity}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default InventoryGrid;
