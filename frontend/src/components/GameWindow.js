import React from 'react';

const GameWindow = ({ children }) => {
  return (
    <div className="container mx-auto mt-10 p-8 bg-cult-light text-cult-dark font-serif shadow-lg border-4 border-cult-gold rounded-lg"
         style={{ 
             backgroundImage: "url('/paper-texture.jpg')", // Usaremos uma textura de papel
             boxShadow: "0 0 20px rgba(255, 215, 0, 0.5)" // Um brilho dourado
         }}>
      <div className="overflow-y-auto h-96 p-4 border border-cult-secondary rounded">
        {children}
      </div>
    </div>
  );
};

export default GameWindow;
