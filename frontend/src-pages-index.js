import { useState, useEffect } from 'react';
import PlayerHUD from '@/components/PlayerHUD';
import NpcInspector from '@/components/NpcInspector';
import CombatInterface from '@/components/CombatInterface';
import InventoryGrid from '@/components/InventoryGrid';

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [playerStats, setPlayerStats] = useState(null);
  const [selectedNpc, setSelectedNpc] = useState(null);
  const [observedDesc, setObservedDesc] = useState("");
  const [isObserving, setIsObserving] = useState(false);
  const [inCombat, setInCombat] = useState(false);
  const [itemsData, setItemsData] = useState({});

  // Mock de habilidades do jogador
  const playerAbilities = [
      { id: 'fireball', name: 'Fireball' },
      { id: 'iceblast', name: 'Ice Blast' },
      { id: 'lightningstrike', name: 'Lightning Strike' },
      { id: 'shadowstep', name: 'Shadowstep' }
  ];

  useEffect(() => {
    // Carrega os dados dos itens para o frontend
    const fetchItemsData = async () => {
        try {
            const response = await fetch('/items.json');
            const itemsArray = await response.json();
            const itemsMap = itemsArray.reduce((acc, item) => {
                acc[item.id] = item;
                return acc;
            }, {});
            setItemsData(itemsMap);
        } catch (error) {
            console.error("Failed to fetch items data:", error);
        }
    };

    fetchItemsData();

    // Mock de dados do jogador
    const mockPlayerStats = {
      health: 100,
      mana: 50,
      stamina: 75,
      experience: 1200,
      level: 5,
      inventory: [
        { id: 'potion', quantity: 2 },
        { id: 'elixir', quantity: 1 }
      ],
      abilities: playerAbilities
    };

    setPlayerStats(mockPlayerStats);
  }, []);

  const handleObserveNpc = (npc) => {
    setSelectedNpc(npc);
    setIsObserving(true);
    setObservedDesc(npc.description);
  };

  const handleCloseNpcInspector = () => {
    setIsObserving(false);
    setSelectedNpc(null);
    setObservedDesc("");
  };

  const handleCombatStart = () => {
    setInCombat(true);
  };

  const handleCombatEnd = () => {
    setInCombat(false);
  };

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-7xl">
        <div className="md:col-span-1">
          <PlayerHUD playerStats={playerStats} />
          <InventoryGrid inventory={playerStats?.inventory} itemsData={itemsData} />
          <div className="mt-4 p-4 bg-cult-dark border-2 border-cult-gold rounded-lg">
            <h3 className="text-lg text-cult-gold mb-2">Presentes na Cena:</h3>
            { /* Mapeia os NPCs ou objetos da cena aqui */ }
            {false ? (
              /* Substitua false pela condição real para exibir NPCs/objetos */
              ["NPC 1", "NPC 2"].map((npc, index) => (
                <button key={index} className="w-full text-left p-2 hover:bg-cult-gold hover:text-cult-dark rounded-lg transition-all">
                  {npc}
                </button>
              ))
            ) : <p className="text-cult-light italic">Ninguém à vista.</p>}
          </div>
          <NpcInspector npc={selectedNpc} onObserve={handleObserveNpc} description={observedDesc} isObserving={isObserving} />
        </div>
        <div className="md:col-span-2 flex flex-col">
          {inCombat ? (
            <CombatInterface onCombatEnd={handleCombatEnd} />
          ) : (
            <div className="p-4 bg-cult-dark border-2 border-cult-gold rounded-lg">
              <h2 className="text-xl text-cult-gold mb-4">Bem-vindo ao Aventure-se!</h2>
              <p className="text-cult-light mb-4">Explore, lute e descubra os mistérios que este mundo tem a oferecer.</p>
              <button onClick={handleCombatStart} className="px-4 py-2 bg-cult-gold text-cult-dark rounded-lg hover:bg-cult-light transition-all">
                Iniciar Combate (Mock)
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}