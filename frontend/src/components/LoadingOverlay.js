import React, { useState, useEffect } from 'react';

/**
 * LoadingOverlay - Overlay estilizado durante carregamento
 * Triggers:
 * - Session init (início do jogo)
 * - Sleep/rest actions (dormir, descansar)
 * - World tick transition (amanhecer)
 * 
 * Props:
 * - isVisible: boolean - Controla visibilidade do overlay
 * - loadingType: 'init' | 'sleep' | 'dawn' | 'action' - Tipo de loading para mensagens customizadas
 * - message: string (opcional) - Mensagem customizada
 */

const LOADING_MESSAGES = {
  init: [
    "Despertando as energias do mundo...",
    "Alinhando os meridianos do destino...",
    "O Qi flui através dos reinos...",
    "Ancestrais observam sua jornada...",
  ],
  sleep: [
    "As estrelas giram no firmamento...",
    "Sonhos de cultivo permeiam sua mente...",
    "O corpo refina a essência absorvida...",
    "Horas passam como folhas ao vento...",
  ],
  dawn: [
    "O sol nasce sobre Orbis...",
    "As facções despertam e se movem...",
    "O mundo evolui enquanto você observa...",
    "A aurora traz novos desafios...",
  ],
  action: [
    "Processando o fluxo do destino...",
    "O karma se manifesta...",
    "Consequências se desdobram...",
    "O Dao responde às suas ações...",
  ]
};

const LoadingOverlay = ({ isVisible, loadingType = 'action', message = null }) => {
  const [currentMessage, setCurrentMessage] = useState('');
  const [dots, setDots] = useState('');

  // Selecionar mensagem aleatória baseada no tipo
  useEffect(() => {
    if (isVisible) {
      const messages = LOADING_MESSAGES[loadingType] || LOADING_MESSAGES.action;
      const randomIndex = Math.floor(Math.random() * messages.length);
      setCurrentMessage(message || messages[randomIndex]);
    }
  }, [isVisible, loadingType, message]);

  // Animação dos pontos
  useEffect(() => {
    if (!isVisible) return;

    const interval = setInterval(() => {
      setDots(prev => {
        if (prev.length >= 3) return '';
        return prev + '.';
      });
    }, 400);

    return () => clearInterval(interval);
  }, [isVisible]);

  if (!isVisible) return null;

  // Ícone baseado no tipo
  const getIcon = () => {
    switch (loadingType) {
      case 'init': return '☯️';
      case 'sleep': return '🌙';
      case 'dawn': return '🌅';
      default: return '✧';
    }
  };

  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-content">
        {/* Círculo de Qi animado */}
        <div className="qi-circle">
          <div className="qi-inner">
            <span className="qi-icon">{getIcon()}</span>
          </div>
          <div className="qi-ring qi-ring-1"></div>
          <div className="qi-ring qi-ring-2"></div>
          <div className="qi-ring qi-ring-3"></div>
        </div>
        
        {/* Mensagem */}
        <p className="loading-message">
          {currentMessage}<span className="loading-dots">{dots}</span>
        </p>
      </div>

      <style jsx>{`
        .loading-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(10, 10, 15, 0.92);
          backdrop-filter: blur(8px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .loading-content {
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2rem;
        }

        .qi-circle {
          position: relative;
          width: 120px;
          height: 120px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .qi-inner {
          position: absolute;
          width: 60px;
          height: 60px;
          background: radial-gradient(circle, var(--primary-gold) 0%, transparent 70%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          animation: pulse 2s ease-in-out infinite;
        }

        .qi-icon {
          font-size: 2rem;
          animation: float 3s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 0.8; }
          50% { transform: scale(1.1); opacity: 1; }
        }

        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }

        .qi-ring {
          position: absolute;
          border: 2px solid;
          border-radius: 50%;
          animation: expand 2s ease-out infinite;
        }

        .qi-ring-1 {
          width: 80px;
          height: 80px;
          border-color: var(--primary-gold);
          animation-delay: 0s;
        }

        .qi-ring-2 {
          width: 100px;
          height: 100px;
          border-color: var(--secondary-crimson);
          animation-delay: 0.4s;
        }

        .qi-ring-3 {
          width: 120px;
          height: 120px;
          border-color: var(--accent-jade);
          animation-delay: 0.8s;
        }

        @keyframes expand {
          0% {
            transform: scale(0.5);
            opacity: 1;
          }
          100% {
            transform: scale(1.5);
            opacity: 0;
          }
        }

        .loading-message {
          font-size: 1.25rem;
          color: var(--text-secondary);
          font-style: italic;
          letter-spacing: 0.05em;
          max-width: 300px;
        }

        .loading-dots {
          display: inline-block;
          width: 1.5em;
          text-align: left;
        }
      `}</style>
    </div>
  );
};

export default LoadingOverlay;
