import React, { useState, useEffect } from 'react';
import GameWindow from '../components/GameWindow';
import DialogueInput from '../components/DialogueInput';
import PlayerHUD from '../components/PlayerHUD';
import NpcInspector from '../components/NpcInspector';
import CombatInterface from '../components/CombatInterface';

export default function GamePage() {
	const [messages, setMessages] = useState([]);
	const [playerId, setPlayerId] = useState(null);
	const [playerStats, setPlayerStats] = useState(null);
	const [npcsInScene, setNpcsInScene] = useState([]);
	const [selectedNpc, setSelectedNpc] = useState(null);
	const [observedDesc, setObservedDesc] = useState("");
	const [isObserving, setIsObserving] = useState(false);
	const [inCombat, setInCombat] = useState(false);

	const playerSkills = [
		{ id: 'meteor_soul', name: 'Meteor Soul' },
		{ id: 'shadowstep', name: 'Shadowstep' },
	];

	useEffect(() => {
		const initOrLoadPlayer = async () => {
			const storedId = window.localStorage.getItem('playerId');
			const storedName = window.localStorage.getItem('playerName');
			if (storedId && storedName) {
				setPlayerId(Number(storedId));
				setPlayerStats(prev => prev || { name: storedName });
				setMessages([{ type: 'narrator', text: `Bem-vindo de volta, ${storedName}.` }]);
				handleSend('olhar ao redor', Number(storedId));
				return;
			}

			const playerName = 'Viajante';
			try {
				const response = await fetch('http://localhost:8000/player/create?name=' + playerName, {
					method: 'POST',
				});
				const data = await response.json();
				setPlayerId(data.id);
				setPlayerStats(data);
				window.localStorage.setItem('playerId', String(data.id));
				window.localStorage.setItem('playerName', data.name);
				setMessages([{ type: 'narrator', text: `Bem-vindo, ${data.name}.` }]);
				handleSend('olhar ao redor', data.id);
			} catch (error) {
				console.error('Failed to create player:', error);
				setMessages([{ type: 'error', text: 'Erro: Não foi possível conectar ao servidor do jogo.' }]);
			}
		};
		initOrLoadPlayer();
	}, []);

	useEffect(() => {
		const hostileNpcs = npcsInScene.some(npc => npc.emotional_state === 'hostile');
		setInCombat(hostileNpcs);
	}, [npcsInScene]);

	const handleSend = async (inputText, pId = playerId) => {
		if (!pId) {
			setMessages(prev => [...prev, { type: 'error', text: 'Ainda criando o jogador...' }]);
			return;
		}

		if (inputText) {
			setMessages(prev => [...prev, { type: 'player', text: `> ${inputText}` }]);
		}
		setSelectedNpc(null);
		setObservedDesc('');

		try {
			const response = await fetch(
				`http://localhost:8000/game/turn?player_id=${pId}&player_input=${encodeURIComponent(inputText)}`,
				{ method: 'POST' }
			);

			if (!response.ok) {
				const errData = await response.json();
				throw new Error(errData.detail || 'Ocorreu um erro no servidor.');
			}

			const data = await response.json();
			setMessages(prev => [...prev, { type: 'narrator', text: data.scene_description }]);
			if (data.action_result) {
				setMessages(prev => [...prev, { type: 'narrator', text: data.action_result }]);
			}
			setPlayerStats(data.player_state);
			setNpcsInScene(data.npcs_in_scene || []);
		} catch (error) {
			console.error('Failed to send action:', error);
			setMessages(prev => [...prev, { type: 'error', text: `Erro: ${error.message}` }]);
		}
	};

	const handleAttack = (skillId, targetId) => {
		const target = npcsInScene.find(npc => npc.id === targetId);
		if (target) {
			const inputText = `Eu ataco ${target.name} usando ${skillId}`;
			handleSend(inputText);
		}
	};

	const handleObserveNpc = async (npc) => {
		if (!npc) return;
		setSelectedNpc(npc);
		setIsObserving(true);
		setObservedDesc('');
		try {
			const response = await fetch(`http://localhost:8000/npc/${npc.id}/observe`, { method: 'POST' });
			const data = await response.json();
			setObservedDesc(data.description);
		} catch (error) {
			console.error('Failed to observe NPC:', error);
			setObservedDesc('Sua percepção falha em discernir os detalhes.');
		} finally {
			setIsObserving(false);
		}
	};

	return (
		<main className="flex min-h-screen flex-col items-center p-6 md:p-12 bg-cult-dark">
			<h1 className="text-4xl md:text-5xl font-bold text-cult-gold mb-8 font-serif">Códice Triluna</h1>
			<div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-7xl">
				<div className="md:col-span-1">
					<PlayerHUD playerStats={playerStats} />
					<div className="mt-4 p-4 bg-cult-dark border-2 border-cult-gold rounded-lg">
						<h3 className="text-lg text-cult-gold mb-2">Presentes na Cena:</h3>
						{npcsInScene.length > 0 ? npcsInScene.map(npc => (
							<button
								key={npc.id}
								onClick={() => handleObserveNpc(npc)}
								className="block w-full text-left p-2 rounded hover:bg-cult-secondary text-cult-light mb-1"
							>
								{npc.name}
							</button>
						)) : <p className="text-cult-light italic">Ninguém à vista.</p>}
					</div>
					<NpcInspector npc={selectedNpc} onObserve={handleObserveNpc} description={observedDesc} isObserving={isObserving} />
				</div>
				<div className="md:col-span-2 flex flex-col">
					<GameWindow>
						{messages.map((msg, index) => (
							<p
								key={index}
								className={`mb-2 ${
									msg.type === 'player' ? 'text-cult-gold italic' :
									msg.type === 'error' ? 'text-cult-red font-bold' :
									'text-cult-light'
								}`}
							>
								{msg.text}
							</p>
						))}
					</GameWindow>
					{inCombat ? (
						<CombatInterface
							skills={playerSkills}
							targets={npcsInScene.filter(n => n.emotional_state === 'hostile')}
							onAttack={handleAttack}
						/>
					) : (
						<DialogueInput onSend={handleSend} />
					)}
				</div>
			</div>
		</main>
	);
}

