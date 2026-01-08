import React, { useState } from 'react';

const DialogueInput = ({ onSend, isLoading = false }) => {
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState(null);

  const handleSend = async () => {
    if (inputValue.trim() && !isLoading) {
      try {
        setError(null);
        await onSend(inputValue);
        setInputValue(''); // Só limpa se não houver erro
      } catch (err) {
        setError(err.message || 'Erro ao enviar ação');
        console.error('Erro no DialogueInput:', err);
      }
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t-2 border-imperial/30 p-5 bg-black/50 backdrop-blur-sm">
      {error && (
        <div className="glass-demon p-3 rounded-lg mb-3 border border-demon text-sm font-body text-slate-200">
          ⚠️ {error}
        </div>
      )}
      <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-3">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Descreva sua ação... (ex: 'explorar a floresta', 'meditar', 'atacar')"
          className="
            flex-1 px-6 py-4 
            glass-panel border border-mist-border 
            focus:border-imperial focus:outline-none focus:ring-2 focus:ring-imperial/50 
            rounded-xl transition-all font-body text-slate-200 text-lg
            placeholder-slate-500
          "
          disabled={isLoading}
        />
        <button
          type="submit"
          onClick={handleSend}
          disabled={isLoading || !inputValue.trim()}
          className="btn-gold px-8 py-4 font-display text-lg disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isLoading ? '⏳ Processando' : '⚔️ Agir'}
        </button>
      </form>
    </div>
  );
};

export default DialogueInput;
