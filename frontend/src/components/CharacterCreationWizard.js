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
          origin: characterData.origin_location
        })
      });
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
    
    // Compilar backstory das respostas
    const backstory = sessionZeroQuestions
      .map((q, i) => `${q}\n${answers[i]}`)
      .join('\n\n');
    
    const finalData = {
      ...characterData,
      backstory,
      session_zero_answers: answers
    };
    
    try {
      const response = await fetch('http://localhost:8000/player/create-full', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(finalData)
      });
      
      const player = await response.json();
      onComplete(player);
    } catch (error) {
      console.error('Erro ao criar personagem:', error);
      alert('Erro ao criar personagem. Tente novamente.');
    }
    
    setLoading(false);
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gold mb-2">Nome do Cultivador</h2>
        <p className="text-secondary mb-4">Escolha um nome digno de uma lenda</p>
        <input
          type="text"
          value={characterData.name}
          onChange={(e) => setCharacterData({ ...characterData, name: e.target.value })}
          placeholder="Ex: Zhang Wei, Lin Feng, Xiao Yan..."
          className="w-full bg-black/50 border-2 border-gold/30 rounded-lg px-4 py-3 text-white focus:border-gold outline-none"
        />
      </div>
      
      <div>
        <h3 className="text-lg font-bold text-gold mb-2">Aparência (Opcional)</h3>
        <textarea
          value={characterData.appearance}
          onChange={(e) => setCharacterData({ ...characterData, appearance: e.target.value })}
          placeholder="Descreva a aparência do seu personagem..."
          className="w-full bg-black/50 border-2 border-gold/30 rounded-lg px-4 py-3 text-white focus:border-gold outline-none h-24 resize-none"
        />
      </div>
      
      <button
        onClick={handleNext}
        disabled={!characterData.name}
        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 rounded-lg transition-all"
      >
        Continuar →
      </button>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gold mb-2">Constituição</h2>
        <p className="text-secondary mb-4">Escolha o tipo de corpo que define seu destino</p>
      </div>
      
      <div className="grid grid-cols-1 gap-4">
        {constitutions.map((const_type) => (
          <div
            key={const_type.id}
            onClick={() => setCharacterData({ ...characterData, constitution: const_type.id })}
            className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
              characterData.constitution === const_type.id
                ? 'border-gold bg-gradient-to-br ' + const_type.color + ' bg-opacity-20'
                : 'border-gray-600 bg-black/30 hover:border-gold/50'
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">{const_type.icon}</span>
              <div>
                <h3 className="text-lg font-bold text-gold">{const_type.name}</h3>
                <span className="text-xs text-secondary">{const_type.tier}</span>
              </div>
            </div>
            <p className="text-sm text-gray-300 mb-3">{const_type.description}</p>
            
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="text-green-400 font-bold mb-1">Vantagens:</p>
                <ul className="space-y-1">
                  {const_type.pros.map((pro, i) => (
                    <li key={i} className="text-gray-300">• {pro}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-red-400 font-bold mb-1">Desvantagens:</p>
                <ul className="space-y-1">
                  {const_type.cons.map((con, i) => (
                    <li key={i} className="text-gray-300">• {con}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="flex gap-3">
        <button
          onClick={() => setStep(step - 1)}
          className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 rounded-lg transition-all"
        >
          ← Voltar
        </button>
        <button
          onClick={handleNext}
          disabled={!characterData.constitution}
          className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 rounded-lg transition-all"
        >
          Continuar →
        </button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gold mb-2">Localização Inicial</h2>
        <p className="text-secondary mb-4">Onde sua jornada começa?</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {locations.map((loc) => (
          <div
            key={loc.id}
            onClick={() => setCharacterData({ ...characterData, origin_location: loc.id })}
            className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
              characterData.origin_location === loc.id
                ? 'border-gold bg-gradient-to-br from-purple-900 to-blue-900 bg-opacity-50'
                : 'border-gray-600 bg-black/30 hover:border-gold/50'
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">{loc.icon}</span>
              <div>
                <h3 className="text-lg font-bold text-gold">{loc.name}</h3>
                <span className="text-xs text-secondary">{loc.type}</span>
              </div>
            </div>
            <p className="text-sm text-gray-300">
              Perigo: <span className={
                loc.danger === 'Alto' ? 'text-red-400' :
                loc.danger === 'Médio' ? 'text-yellow-400' :
                'text-green-400'
              }>{loc.danger}</span>
            </p>
          </div>
        ))}
      </div>
      
      <div className="flex gap-3">
        <button
          onClick={() => setStep(step - 1)}
          className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 rounded-lg transition-all"
        >
          ← Voltar
        </button>
        <button
          onClick={handleNext}
          disabled={!characterData.origin_location}
          className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 rounded-lg transition-all"
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
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gold mb-2">Session Zero</h2>
          <p className="text-secondary mb-4">O Mestre deseja conhecer sua história...</p>
        </div>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin text-4xl mb-4">⚡</div>
            <p className="text-secondary">Carregando perguntas...</p>
          </div>
        ) : (
          <>
            <div className="bg-black/50 border-2 border-purple-500/30 rounded-lg p-6">
              <p className="text-sm text-secondary mb-2">
                Pergunta {currentQuestionIndex + 1} de {sessionZeroQuestions.length}
              </p>
              <p className="text-lg text-gold font-medium mb-4">{currentQuestion}</p>
              
              <textarea
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                placeholder="Sua resposta..."
                className="w-full bg-black/50 border-2 border-gold/30 rounded-lg px-4 py-3 text-white focus:border-gold outline-none h-32 resize-none"
              />
              
              <button
                onClick={handleSessionZeroAnswer}
                disabled={!currentAnswer.trim() || loading}
                className="mt-4 w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 rounded-lg transition-all"
              >
                {currentQuestionIndex < sessionZeroQuestions.length - 1 ? 'Próxima →' : '✨ Finalizar Criação'}
              </button>
            </div>
            
            {characterData.session_zero_answers.length > 0 && (
              <div className="text-sm text-secondary">
                <p className="mb-2">Respostas anteriores:</p>
                {characterData.session_zero_answers.map((answer, i) => (
                  <div key={i} className="bg-black/30 rounded p-2 mb-2">
                    <p className="text-gold text-xs">{sessionZeroQuestions[i]}</p>
                    <p className="text-gray-300">{answer}</p>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
        
        <button
          onClick={() => setStep(step - 1)}
          disabled={loading}
          className="w-full bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 rounded-lg transition-all"
        >
          ← Voltar
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen animated-bg flex items-center justify-center p-4">
      <div className="glass-card max-w-3xl w-full p-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={`flex-1 h-2 rounded-full mx-1 transition-all ${
                  s <= step ? 'bg-gradient-to-r from-purple-500 to-blue-500' : 'bg-gray-700'
                }`}
              />
            ))}
          </div>
          <p className="text-center text-sm text-secondary">
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
