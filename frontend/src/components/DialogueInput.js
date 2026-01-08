import React, { useState } from 'react';

const DialogueInput = ({ onSend, isLoading = false }) => {
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    if (inputValue.trim() && !isLoading) {
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
    <div className="border-t-2 border-amber-500/30 p-4 bg-black/40">
      <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-3">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Descreva sua ação... (ex: 'explorar a floresta', 'meditar', 'atacar')"
          className="flex-1 px-5 py-3 bg-black/60 border border-purple-500/40 rounded-xl focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all font-body text-white placeholder-white/40 backdrop-blur-sm"
          disabled={isLoading}
        />
        <button
          type="submit"
          onClick={handleSend}
          disabled={isLoading || !inputValue.trim()}
          className="btn-celestial px-8 py-3 font-display disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '⏳ Aguarde' : '⚔️ Agir'}
        </button>
      </form>
    </div>
  );
};

export default DialogueInput;
