import React, { useState } from 'react';

const DialogueInput = ({ onSend, isLoading = false }) => {
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState(null);

  const handleSend = async () => {
    if (inputValue.trim() && !isLoading) {
      try {
        setError(null);
        await onSend(inputValue);
        setInputValue('');
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

  const quickActions = [
    { text: 'Olhar ao redor', icon: '👁️' },
    { text: 'Falar com', icon: '💬' },
    { text: 'Atacar', icon: '⚔️' },
    { text: 'Meditar', icon: '🧘' },
  ];

  return (
    <div style={{ 
      borderTop: '2px solid var(--gold)', 
      padding: 'var(--spacing-lg)', 
      background: 'var(--bg-secondary)' 
    }}>
      {error && (
        <div className="card-demon" style={{ padding: 'var(--spacing-sm)', marginBottom: 'var(--spacing-md)', fontSize: '0.875rem' }}>
          ⚠️ {error}
        </div>
      )}
      
      {/* Quick Action Pills */}
      <div className="flex gap-sm" style={{ marginBottom: 'var(--spacing-md)', flexWrap: 'wrap' }}>
        {quickActions.map((action, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setInputValue(action.text + ' ')}
            disabled={isLoading}
            className="btn-pill"
          >
            <span>{action.icon}</span>
            <span>{action.text}</span>
          </button>
        ))}
      </div>

      {/* Main Input Area */}
      <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-md">
        <div style={{ flex: 1, position: 'relative' }}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="O que você deseja fazer? (Descreva sua ação em linguagem natural...)"
            disabled={isLoading}
            className="input"
            style={{ fontSize: '1rem', width: '100%' }}
          />
        </div>
        
        <button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          className="btn btn-primary"
          style={{ whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}
        >
          {isLoading ? (
            <>
              <div className="loading-spinner-small"></div>
              <span>Aguarde...</span>
            </>
          ) : (
            <>
              <span style={{ fontSize: '1.25rem' }}>⚔️</span>
              <span>Agir</span>
            </>
          )}
        </button>
      </form>
      
      {/* Helper Text */}
      <div style={{ marginTop: 'var(--spacing-sm)', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
        💡 Dica: Seja descritivo! <span style={{ color: 'var(--text-secondary)' }}>"Examino cuidadosamente o pergaminho antigo"</span> é melhor que <span style={{ color: 'var(--text-secondary)' }}>"olhar"</span>
      </div>
    </div>
  );
};

export default DialogueInput;
