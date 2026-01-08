import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useGame } from '../contexts/GameContext';
import CharacterCreationWizard from '../components/CharacterCreationWizard';
import CharacterSelector from '../components/CharacterSelector';

export default function Home() {
  const router = useRouter();
  const { playerId } = useGame();
  const [showWizard, setShowWizard] = useState(false);
  const [showSelector, setShowSelector] = useState(false);

  const handleWizardComplete = async (player) => {
    try {
      // O player já vem criado do CharacterCreationWizard
      // Salvar no localStorage
      window.localStorage.setItem('playerId', String(player.id));
      window.localStorage.setItem('playerName', player.name);
      
      // Redirecionar para o jogo
      router.push('/game');
    } catch (error) {
      console.error('Erro ao processar jogador:', error);
      alert(`Erro ao processar personagem: ${error.message}`);
    }
  };

  const handleSelectCharacter = (character) => {
    // Salvar personagem selecionado
    window.localStorage.setItem('playerId', String(character.id));
    window.localStorage.setItem('playerName', character.name);
    router.push('/game');
  };

  const handleContinue = () => {
    if (playerId) {
      router.push('/game');
    }
  };

  // Se wizard está ativo, mostrar só ele
  if (showWizard) {
    return <CharacterCreationWizard onComplete={handleWizardComplete} />;
  }

  // Se selector está ativo, mostrar seleção
  if (showSelector) {
    return (
      <CharacterSelector 
        onSelect={handleSelectCharacter}
        onCreateNew={() => setShowWizard(true)}
      />
    );
  }

  return (
    <>
      <Head>
        <title>Códice Triluna - RPG de Cultivo Imortal</title>
      </Head>

      <div className="page-wrapper">
        <div className="card card-gold" style={{ maxWidth: '720px', width: '100%' }}>
          <div className="text-center">
            <h1>✦ CÓDICE TRILUNA ✦</h1>
            <p style={{ fontSize: '1.25rem', color: 'var(--text-secondary)', fontStyle: 'italic', marginBottom: '32px' }}>
              A Jornada do Cultivador Imortal
            </p>
            <div className="divider-gold"></div>
          </div>

          <div className="flex flex-col gap-md mt-xl">
            <button
              onClick={() => setShowSelector(true)}
              className="btn btn-primary btn-lg btn-block"
            >
              <span style={{ fontSize: '1.5rem' }}>⚔️</span>
              <span>Selecionar Cultivador</span>
            </button>

            <button
              onClick={() => setShowWizard(true)}
              className="btn btn-secondary btn-lg btn-block"
            >
              <span style={{ fontSize: '1.5rem' }}>✨</span>
              <span>Criar Novo Personagem</span>
            </button>

            {playerId && (
              <button
                onClick={handleContinue}
                className="btn btn-ghost btn-lg btn-block"
              >
                <span style={{ fontSize: '1.5rem' }}>📖</span>
                <span>Continuar Última Jornada</span>
              </button>
            )}
          </div>

          <div className="mt-xl" style={{ paddingTop: 'var(--spacing-lg)', borderTop: '1px solid var(--border-accent)' }}>
            <div className="flex flex-col gap-sm" style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
              <div className="flex gap-sm">
                <span style={{ fontSize: '1.25rem' }}>🌟</span>
                <p><strong className="glow-gold">Sistema de Cultivo:</strong> 9 Tiers de Transcendência</p>
              </div>
              <div className="flex gap-sm">
                <span style={{ fontSize: '1.25rem' }}>⚡</span>
                <p><strong className="glow-jade">Tríade Energética:</strong> Quintessência, Shadow Chi, Yuan Qi</p>
              </div>
              <div className="flex gap-sm">
                <span style={{ fontSize: '1.25rem' }}>🗡️</span>
                <p><strong style={{ color: 'var(--purple)' }}>Artes Silenciosas:</strong> Northern Blade Techniques</p>
              </div>
              <div className="flex gap-sm">
                <span style={{ fontSize: '1.25rem' }}>🧬</span>
                <p><strong className="glow-demon">Constituições:</strong> Mortal, Godfiend, Taboo</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
