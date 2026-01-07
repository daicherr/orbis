import React, { useState } from 'react';

const DialogueInput = ({ onSend }) => {
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    if (inputValue.trim()) {
      onSend(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div className="mt-4 flex">
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={handleKeyPress}
        className="flex-grow bg-cult-light border border-cult-gold text-cult-dark p-2 rounded-l-md focus:outline-none focus:ring-2 focus:ring-cult-gold"
        placeholder="O que você faz?"
      />
      <button
        onClick={handleSend}
        className="bg-cult-gold text-cult-dark font-bold py-2 px-4 rounded-r-md hover:bg-yellow-600 transition duration-300"
      >
        Enviar
      </button>
    </div>
  );
};

export default DialogueInput;
