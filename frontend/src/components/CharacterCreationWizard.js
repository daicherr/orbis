import { useState } from 'react';

export default function CharacterCreationWizard({ onComplete }) {
  const [step, setStep] = useState(1);
  const [characterData, setCharacterData] = useState({
    name: '',
    appearance: '',
    constitution: '',
    origin_location: '',
    backstory: '',
    session_zero_answers: []
  });

  const [sessionZeroQuestions, setSessionZeroQuestions] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  // Constituições baseadas no GDD
  const constitutions = [
    {
      id: 'mortal',
      name: 'Mortal',
      tier: 'Comum',
      description: 'Corpo humano comum sem vantagens especiais. Cresce através de esforço puro e técnicas de cultivo.',
      pros: ['Sem restrições', 'Livre para desenvolver qualquer caminho', 'Sem desvantagens iniciais'],
      cons: ['Sem bônus especiais', 'Crescimento mais lento', 'Requer mais recursos'],
      icon: '👤',
      color: 'from-gray-400 to-gray-600'
    },
    {
      id: 'godfiend',
      name: 'Godfiend',
      tier: 'Lendário',
      description: 'Linhagem de sangue divino ou demoníaco. 7 tipos únicos: Black Sand, Eon Sea, Phoenix, etc.',
      pros: ['Crescimento acelerado (+50%)', 'Habilidades únicas de linhagem', 'Resistências elementais'],
      cons: ['Atrai inimigos poderosos', 'Requer mais comida (2x)', 'Tribulações mais difíceis'],
      icon: '🔥',
      color: 'from-purple-500 to-red-600'
    },
    {
      id: 'taboo',
      name: 'Taboo Body',
      tier: 'Amaldiçoado',
      description: 'Corpo amaldiçoado pelo céu. Heavenly Scourge atrai raios durante breakthroughs.',
      pros: ['Poder massivo se sobreviver', 'Imune a venenos', 'Mental muito forte'],
      cons: ['Raios atacam durante breakthrough', 'Rejeitado pela sociedade', 'Mortalidade alta'],
      icon: '⚡',
      color: 'from-yellow-400 to-red-700'
    }
  ];

  const locations = [
    { id: 'floresta_assombrada', name: 'Floresta Assombrada', type: 'wilderness', danger: 'Médio', icon: '🌲' },
    { id: 'vila_tranquila', name: 'Vila Tranquila', type: 'settlement', danger: 'Baixo', icon: '🏘️' },
    { id: 'templo_nuvens', name: 'Templo das Nuvens', type: 'sacred', danger: 'Baixo', icon: '⛩️' },
    { id: 'cavernas_profundas', name: 'Cavernas Profundas', type: 'dungeon', danger: 'Alto', icon: '🕳️' },
    { id: 'cidade_imperial', name: 'Cidade Imperial', type: 'settlement', danger: 'Médio', icon: '🏯' }
  ];

  const handleNext = async () => {
    if (step === 3 && !sessionZeroQuestions.length) {
      // Buscar perguntas do Session Zero
      await fetchSessionZeroQuestions();
    }
    setStep(step + 1);
  };

  const fetchSessionZeroQuestions = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/character/session-zero', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: characterData.name,
          constitution: characterData.constitution,
          origin_location: characterData.origin_location
        })
      });
      
      if (!response.ok) {
        throw new Error('Erro ao buscar Session Zero');
      }
      
      const data = await response.json();
      setSessionZeroQuestions(data.questions || []);
    } catch (error) {
      console.error('Erro ao buscar Session Zero:', error);
      setSessionZeroQuestions([
        'Qual foi o momento que definiu sua jornada no cultivo?',
        'Quem foi seu mentor ou inspiração?',
        'Qual é seu maior medo?'
      ]);
    }
    setLoading(false);
  };

  const handleSessionZeroAnswer = () => {
    if (!currentAnswer.trim()) return;
    
    const newAnswers = [...characterData.session_zero_answers, currentAnswer];
    setCharacterData({ ...characterData, session_zero_answers: newAnswers });
    setCurrentAnswer('');
    
    if (newAnswers.length >= sessionZeroQuestions.length) {
      // Completou todas as perguntas
      handleFinalSubmit(newAnswers);
    }
  };

  const handleFinalSubmit = async (answers) => {
    setLoading(true);
    
    // Enviar apenas os campos que o backend espera
    const finalData = {
      name: characterData.name,
      appearance: characterData.appearance,
      constitution: characterData.constitution,
      origin_location: characterData.origin_location,
      session_zero_answers: answers
    };
    
    console.log('📤 Enviando para backend:', finalData);
    
    try {
      const response = await fetch('http://localhost:8000/player/create-full', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(finalData)
      });
      
      console.log('📥 Status da resposta:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ Erro do backend:', errorData);
        throw new Error(JSON.stringify(errorData.detail || errorData));
      }
      
      const player = await response.json();
      console.log('✅ Personagem criado:', player);
      onComplete(player);
    } catch (error) {
      console.error('❌ Erro ao criar personagem:', error);
      alert(`Erro ao criar personagem:\n${error.message}`);
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="flex flex-col gap-lg">
      <div>
        <h2 className="glow-gold" style={{ fontSize: '2rem', marginBottom: 'var(--spacing-sm)' }}>Nome do Cultivador</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--spacing-md)' }}>Escolha um nome digno de uma lenda</p>
        <input
          type="text"
          value={characterData.name}
          onChange={(e) => setCharacterData({ ...characterData, name: e.target.value })}
          placeholder="Ex: Zhang Wei, Lin Feng, Xiao Yan..."
          className="input"
          style={{ fontSize: '1rem' }}
        />
      </div>
      
      <div>
        <h3 className="glow-gold" style={{ fontSize: '1.25rem', marginBottom: 'var(--spacing-sm)' }}>Aparência (Opcional)</h3>
        <textarea
          value={characterData.appearance}
          onChange={(e) => setCharacterData({ ...characterData, appearance: e.target.value })}
          placeholder="Descreva a aparência do seu personagem..."
          className="input"
          style={{ minHeight: '100px' }}
        />
      </div>
      
      <button
        onClick={handleNext}
        disabled={!characterData.name}
        className="btn btn-primary btn-lg btn-block"
      >
        Continuar →
      </button>
    </div>
  );

  const renderStep2 = () => (
    <div className="flex flex-col gap-lg">
      <div>
        <h2 className="glow-gold" style={{ fontSize: '2rem', marginBottom: 'var(--spacing-sm)' }}>Constituição</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--spacing-md)' }}>Escolha o tipo de corpo que define seu destino</p>
      </div>
      
      <div className="flex flex-col gap-md">
        {constitutions.map((const_type) => (
          <div
            key={const_type.id}
            onClick={() => setCharacterData({ ...characterData, constitution: const_type.id })}
            className={`card card-hover ${characterData.constitution === const_type.id ? 'card-gold' : ''}`}
            style={{ cursor: 'pointer', transition: 'all var(--transition-base)' }}
          >
            <div className="flex items-center gap-md" style={{ marginBottom: 'var(--spacing-sm)' }}>
              <span style={{ fontSize: '2rem' }}>{const_type.icon}</span>
              <div>
                <h3 className="glow-gold" style={{ fontSize: '1.25rem' }}>{const_type.name}</h3>
                <span className="badge badge-gold">{const_type.tier}</span>
              </div>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: 'var(--spacing-md)' }}>{const_type.description}</p>
            
            <div className="grid grid-cols-2 gap-sm" style={{ fontSize: '0.75rem' }}>
              <div>
                <p style={{ color: 'var(--jade)', fontWeight: 'bold', marginBottom: '4px' }}>Vantagens:</p>
                <ul style={{ paddingLeft: '12px' }}>
                  {const_type.pros.map((pro, i) => (
                    <li key={i} style={{ color: 'var(--text-secondary)', marginBottom: '2px' }}>• {pro}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p style={{ color: 'var(--demon)', fontWeight: 'bold', marginBottom: '4px' }}>Desvantagens:</p>
                <ul style={{ paddingLeft: '12px' }}>
                  {const_type.cons.map((con, i) => (
                    <li key={i} style={{ color: 'var(--text-secondary)', marginBottom: '2px' }}>• {con}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="flex gap-md">
        <button
          onClick={() => setStep(step - 1)}
          className="btn btn-ghost flex-1"
        >
          ← Voltar
        </button>
        <button
          onClick={handleNext}
          disabled={!characterData.constitution}
          className="btn btn-primary flex-1"
        >
          Continuar →
        </button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="flex flex-col gap-lg">
      <div>
        <h2 className="glow-gold" style={{ fontSize: '2rem', marginBottom: 'var(--spacing-sm)' }}>Localização Inicial</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--spacing-md)' }}>Onde sua jornada começa?</p>
      </div>
      
      <div className="grid grid-cols-2 gap-md">
        {locations.map((loc) => (
          <div
            key={loc.id}
            onClick={() => setCharacterData({ ...characterData, origin_location: loc.id })}
            className={`card card-hover ${characterData.origin_location === loc.id ? 'card-gold' : ''}`}
            style={{ cursor: 'pointer', transition: 'all var(--transition-base)' }}
          >
            <div className="flex items-center gap-md" style={{ marginBottom: 'var(--spacing-sm)' }}>
              <span style={{ fontSize: '2rem' }}>{loc.icon}</span>
              <div>
                <h3 className="glow-gold" style={{ fontSize: '1.125rem' }}>{loc.name}</h3>
                <span className="badge badge-jade" style={{ fontSize: '0.625rem' }}>{loc.type}</span>
              </div>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Perigo: <span style={{ color: loc.danger === 'Alto' ? 'var(--demon)' : loc.danger === 'Médio' ? 'var(--gold)' : 'var(--jade)' }}>{loc.danger}</span>
            </p>
          </div>
        ))}
      </div>
      
      <div className="flex gap-md">
        <button
          onClick={() => setStep(step - 1)}
          className="btn btn-ghost flex-1"
        >
          ← Voltar
        </button>
        <button
          onClick={handleNext}
          disabled={!characterData.origin_location}
          className="btn btn-primary flex-1"
        >
          Continuar →
        </button>
      </div>
    </div>
  );

  const renderStep4 = () => {
    const currentQuestionIndex = characterData.session_zero_answers.length;
    const currentQuestion = sessionZeroQuestions[currentQuestionIndex];
    
    return (
      <div className="flex flex-col gap-lg">
        <div>
          <h2 className="glow-gold" style={{ fontSize: '2rem', marginBottom: 'var(--spacing-sm)' }}>Session Zero</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--spacing-md)' }}>O Mestre deseja conhecer sua história...</p>
        </div>
        
        {loading ? (
          <div className="text-center" style={{ padding: 'var(--spacing-xl)' }}>
            <div style={{ fontSize: '3rem', marginBottom: 'var(--spacing-md)', animation: 'spin 1s linear infinite' }}>⚡</div>
            <p style={{ color: 'var(--text-secondary)' }}>Carregando perguntas...</p>
          </div>
        ) : (
          <>
            <div className="panel card-jade">
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: 'var(--spacing-sm)' }}>
                Pergunta {currentQuestionIndex + 1} de {sessionZeroQuestions.length}
              </p>
              <p className="glow-gold" style={{ fontSize: '1.125rem', marginBottom: 'var(--spacing-md)' }}>{currentQuestion}</p>
              
              <textarea
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                placeholder="Sua resposta..."
                className="input"
                style={{ minHeight: '120px', marginBottom: 'var(--spacing-md)' }}
              />
              
              <button
                onClick={handleSessionZeroAnswer}
                disabled={!currentAnswer.trim() || loading}
                className="btn btn-primary btn-block"
              >
                {currentQuestionIndex < sessionZeroQuestions.length - 1 ? 'Próxima →' : '✨ Finalizar Criação'}
              </button>
            </div>
            
            {characterData.session_zero_answers.length > 0 && (
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                <p style={{ marginBottom: 'var(--spacing-sm)' }}>Respostas anteriores:</p>
                <div className="flex flex-col gap-sm">
                  {characterData.session_zero_answers.map((answer, i) => (
                    <div key={i} className="panel" style={{ padding: 'var(--spacing-sm)' }}>
                      <p className="glow-gold" style={{ fontSize: '0.75rem', marginBottom: '4px' }}>{sessionZeroQuestions[i]}</p>
                      <p style={{ color: 'var(--text-secondary)' }}>{answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
        
        <button
          onClick={() => setStep(step - 1)}
          disabled={loading}
          className="btn btn-ghost btn-block"
        >
          ← Voltar
        </button>
      </div>
    );
  };

  return (
    <div className="page-wrapper">
      <div className="card card-gold" style={{ maxWidth: '900px', width: '100%' }}>
        {/* Progress Bar */}
        <div style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div className="flex gap-sm" style={{ marginBottom: 'var(--spacing-sm)' }}>
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                style={{
                  flex: 1,
                  height: '4px',
                  borderRadius: '999px',
                  background: s <= step ? 'linear-gradient(90deg, var(--gold) 0%, var(--gold-light) 100%)' : 'var(--bg-tertiary)',
                  transition: 'all var(--transition-base)'
                }}
              />
            ))}
          </div>
          <p className="text-center" style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Etapa {step} de 4
          </p>
        </div>
        
        {/* Step Content */}
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}
        {step === 4 && renderStep4()}
      </div>
    </div>
  );
}
