import { useState, useEffect } from 'react';

export default function CharacterSelector({ onSelect, onCreateNew }) {
  const [characters, setCharacters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  useEffect(() => {
    loadCharacters();
  }, []);

  const loadCharacters = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/player/list/all');
      if (response.ok) {
        const data = await response.json();
        setCharacters(data);
      }
    } catch (error) {
      console.error('❌ Erro ao carregar personagens:', error);
    }
    setLoading(false);
  };

  const handleDelete = async (characterId) => {
    try {
      const response = await fetch(`http://localhost:8000/player/${characterId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        await loadCharacters(); // Recarregar lista
        setDeleteConfirm(null);
      }
    } catch (error) {
      console.error('❌ Erro ao deletar personagem:', error);
      alert('Erro ao deletar personagem');
    }
  };

  const getRankColor = (rank) => {
    const colors = {
      'Mortal': 'var(--text-secondary)',
      'Foundation': 'var(--jade)',
      'Core': 'var(--gold)',
      'Nascent': 'var(--demon)'
    };
    return colors[rank] || 'var(--text-primary)';
  };

  if (loading) {
    return (
      <div className="page-wrapper">
        <div className="card card-gold" style={{ maxWidth: '600px', textAlign: 'center', padding: 'var(--spacing-2xl)' }}>
          <div className="spinner"></div>
          <p style={{ marginTop: 'var(--spacing-md)' }}>Carregando cultivadores...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <div className="card card-gold" style={{ maxWidth: '900px', width: '100%' }}>
        <div className="text-center">
          <h1 className="glow-gold">Selecione Seu Cultivador</h1>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--spacing-xl)' }}>
            Escolha um personagem ou crie um novo
          </p>
        </div>

        <div className="divider-gold" style={{ margin: 'var(--spacing-xl) 0' }}></div>

        {/* Lista de Personagens */}
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 'var(--spacing-md)' }}>
          {characters.map((char) => (
            <div key={char.id} className="card card-hover" style={{ position: 'relative' }}>
              {/* Botão Delete */}
              {deleteConfirm === char.id ? (
                <div style={{ 
                  position: 'absolute', 
                  top: 'var(--spacing-xs)', 
                  right: 'var(--spacing-xs)', 
                  display: 'flex', 
                  gap: 'var(--spacing-xs)' 
                }}>
                  <button
                    onClick={() => handleDelete(char.id)}
                    className="btn-demon"
                    style={{ fontSize: '0.75rem', padding: '4px 8px' }}
                  >
                    Confirmar
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(null)}
                    className="btn-ghost"
                    style={{ fontSize: '0.75rem', padding: '4px 8px' }}
                  >
                    Cancelar
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setDeleteConfirm(char.id)}
                  style={{
                    position: 'absolute',
                    top: 'var(--spacing-xs)',
                    right: 'var(--spacing-xs)',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--demon)',
                    fontSize: '1.25rem',
                    cursor: 'pointer',
                    opacity: 0.6,
                    transition: 'opacity var(--transition-fast)'
                  }}
                  onMouseEnter={(e) => e.target.style.opacity = '1'}
                  onMouseLeave={(e) => e.target.style.opacity = '0.6'}
                >
                  ✕
                </button>
              )}

              {/* Card Content */}
              <div onClick={() => onSelect(char)} style={{ cursor: 'pointer' }}>
                <h3 className="glow-gold" style={{ fontSize: '1.5rem', marginBottom: 'var(--spacing-sm)' }}>
                  {char.name}
                </h3>
                
                <div className="flex gap-sm" style={{ marginBottom: 'var(--spacing-md)' }}>
                  <span className="badge badge-gold">{char.constitution_type}</span>
                  <span 
                    className="badge" 
                    style={{ 
                      background: `${getRankColor(char.rank)}22`,
                      borderColor: getRankColor(char.rank),
                      color: getRankColor(char.rank)
                    }}
                  >
                    {char.rank}
                  </span>
                </div>

                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  <p>📍 {char.current_location}</p>
                  <p>💰 {char.gold} Gold</p>
                  <p>⚡ Level {char.level}</p>
                </div>
              </div>
            </div>
          ))}

          {/* Card "Criar Novo" */}
          <div 
            className="card card-jade card-hover" 
            onClick={onCreateNew}
            style={{ 
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '200px',
              textAlign: 'center'
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: 'var(--spacing-md)' }}>✨</div>
            <h3 className="glow-jade">Novo Cultivador</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: 'var(--spacing-sm)' }}>
              Iniciar nova jornada
            </p>
          </div>
        </div>

        {characters.length === 0 && (
          <div className="text-center" style={{ padding: 'var(--spacing-2xl)' }}>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--spacing-lg)' }}>
              Nenhum personagem criado ainda
            </p>
            <button onClick={onCreateNew} className="btn-primary">
              Criar Primeiro Cultivador
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
