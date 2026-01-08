import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import CharacterCreationWizard from '../components/CharacterCreationWizard';

export default function Home() {
  const router = useRouter();
  const [showWizard, setShowWizard] = useState(false);
  const [hasSavedCharacter, setHasSavedCharacter] = useState(false);

  // Checa localStorage apenas no cliente (após montar)
  useEffect(() => {
    const storedId = window.localStorage.getItem('playerId');
    setHasSavedCharacter(!!storedId);
  }, []);

  const handleWizardComplete = (player) => {
    window.localStorage.setItem('playerId', String(player.id));
    window.localStorage.setItem('playerName', player.name);
    router.push('/game');
  };

  const handleContinue = () => {
    const storedId = window.localStorage.getItem('playerId');
    if (storedId) {
      router.push('/game');
    }
  };

  // Se wizard está ativo, mostrar só ele
  if (showWizard) {
    return <CharacterCreationWizard onComplete={handleWizardComplete} />;
  }

  return (
    <>
      <Head>
        <title>Códice Triluna - Início da Jornada</title>
      </Head>

      <div className="min-h-screen celestial-bg flex items-center justify-center p-4">
        <div className="mystic-glass-gold p-10 max-w-lg w-full rounded-2xl">
          <div className="text-center mb-10">
            <h1 className="font-title text-6xl md:text-7xl text-celestial-gold text-mystic-glow mb-4">
              Códice Triluna
            </h1>
            <p className="font-display text-xl text-white/70 italic">
              A Jornada do Cultivador Imortal
            </p>
            <div className="mt-4 h-px bg-gradient-to-r from-transparent via-amber-500/50 to-transparent"></div>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => setShowWizard(true)}
              className="btn-celestial w-full py-4 text-lg font-semibold group"
            >
              <span className="flex items-center justify-center gap-2">
                <span className="text-2xl group-hover:scale-110 transition-transform">✨</span>
                <span className="font-display">Novo Cultivador</span>
              </span>
            </button>

            {hasSavedCharacter && (
              <button
                onClick={handleContinue}
                className="w-full py-4 bg-gradient-to-r from-amber-600/20 to-yellow-600/20 hover:from-amber-500/30 hover:to-yellow-500/30 rounded-xl font-display text-lg transition-all duration-300 border border-amber-500/40 hover:border-amber-400 shadow-glow-gold"
              >
                <span className="flex items-center justify-center gap-2">
                  <span className="text-2xl">📖</span>
                  <span>Continuar Jornada</span>
                </span>
              </button>
            )}
          </div>

          <div className="mt-10 pt-8 border-t-2 border-amber-500/30">
            <div className="font-body text-sm text-white/70 space-y-2">
              <div className="flex items-start gap-3">
                <span className="text-lg">🌟</span>
                <p><span className="text-celestial-gold font-semibold">Sistema de Cultivo:</span> 9 Tiers de Transcendência</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-lg">⚡</span>
                <p><span className="text-celestial-jade font-semibold">Tríade Energética:</span> Quintessência, Shadow Chi, Yuan Qi</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-lg">🗡️</span>
                <p><span className="text-purple-300 font-semibold">Artes Silenciosas:</span> Northern Blade Techniques</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-lg">🧬</span>
                <p><span className="text-red-300 font-semibold">Constituições:</span> Mortal, Godfiend, Taboo</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
