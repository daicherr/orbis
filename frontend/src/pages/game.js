import React, { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import WorldClock from '../components/WorldClock';
import CharacterSheet from '../components/CharacterSheet';
import QuestLog from '../components/QuestLog';
import PlayerHUD from '../components/PlayerHUD';
import DialogueInput from '../components/DialogueInput';
import CombatInterface from '../components/CombatInterface';
import NpcInspector from '../components/NpcInspector';

export default function GamePage() {
	const [messages, setMessages] = useState([]);
	const [playerId, setPlayerId] = useState(null);
	const [playerStats, setPlayerStats] = useState(null);
	const [npcsInScene, setNpcsInScene] = useState([]);
	const [selectedNpc, setSelectedNpc] = useState(null);
	const [inCombat, setInCombat] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [showCharacterSheet, setShowCharacterSheet] = useState(false);
	const [showQuestLog, setShowQuestLog] = useState(false);
	const messagesEndRef = useRef(null);

	const playerSkills = [
		{ id: 'meteor_soul', name: 'Meteor Soul', element: 'shadow', icon: '⚔️', desc: 'Ignora armadura' },
		{ id: 'shadowstep', name: 'Shadowstep', element: 'shadow', icon: '👤', desc: 'Teleporte + Counter' },
		{ id: 'qi_burst', name: 'Qi Burst', element: 'qi', icon: '💫', desc: 'AOE de Yuan Qi' },
		{ id: 'silent_strike', name: 'Silent Strike', element: 'shadow', icon: '🗡️', desc: 'Ataque furtivo' },
		{ id: 'wall_of_northern_heavens', name: 'Wall of Northern', element: 'defense', icon: '🛡️', desc: 'Reflete 50% dano' },
		{ id: 'blood_essence_strike', name: 'Blood Essence', element: 'blood', icon: '🩸', desc: 'Usa HP como dano' },
	];

	useEffect(() => {
		const initOrLoadPlayer = async () => {
			const storedId = window.localStorage.getItem('playerId');
			const storedName = window.localStorage.getItem('playerName');
			if (storedId && storedName) {
				setPlayerId(Number(storedId));
				setPlayerStats(prev => prev || { name: storedName });
				setMessages([{ type: 'system', text: `✨ Bem-vindo de volta, ${storedName}. Sua jornada continua...` }]);
				handleSend('olhar ao redor', Number(storedId));
				return;
			}

			// Se não tem player salvo, redireciona para tela de criação
			window.location.href = '/';
		};
		initOrLoadPlayer();
	}, []);

	useEffect(() => {
		const hostileNpcs = npcsInScene.some(npc => npc.emotional_state === 'hostile');
		setInCombat(hostileNpcs);
	}, [npcsInScene]);

	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	}, [messages]);

	const handleSend = async (inputText, pId = playerId) => {
		if (!pId) {
			setMessages(prev => [...prev, { type: 'error', text: '⚠️ Ainda criando o jogador...' }]);
			return;
		}

		if (inputText) {
			setMessages(prev => [...prev, { type: 'player', text: inputText }]);
			setInputText('');
		}
		setSelectedNpc(null);
		setObservedDesc('');
		setIsLoading(true);

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
				setMessages(prev => [...prev, { type: 'action', text: data.action_result }]);
			}
			setPlayerStats(data.player_state);
			setNpcsInScene(data.npcs_in_scene || []);
		} catch (error) {
			console.error('Failed to send action:', error);
			setMessages(prev => [...prev, { type: 'error', text: `❌ Erro: ${error.message}` }]);
		} finally {
			setIsLoading(false);
		}
	};

	const handleAttack = (skillId) => {
		const target = npcsInScene.find(npc => npc.emotional_state === 'hostile');
		if (target) {
			const skill = playerSkills.find(s => s.id === skillId);
			const inputText = `Eu ataco ${target.name} usando ${skill?.name || skillId}`;
			handleSend(inputText);
		} else {
			handleSend(`usar ${playerSkills.find(s => s.id === skillId)?.name || skillId}`);
		}
	};

	const getTierName = (tier) => {
		const tiers = {
			1: "Fundação",
			2: "Despertar",
			3: "Ascensão",
			4: "Transcendência",
			5: "Soberania",
			6: "Divindade",
			7: "Imortalidade",
			8: "Ancestral",
			9: "Criação"
		};
		return tiers[tier] || `Tier ${tier}`;
	};

	return (
		<>
			<Head>
				<title>Códice Triluna - Cultivation RPG</title>
				<meta name="viewport" content="width=device-width, initial-scale=1.0" />
			</Head>

			<div className="h-screen celestial-bg flex flex-col overflow-hidden">
				{/* Header Celestial */}
				<div className="mystic-glass-gold m-4 p-4 rounded-2xl border-t-2 border-amber-500/50">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-6">
							<h1 className="font-title text-2xl text-celestial-gold text-mystic-glow">
								Códice Triluna
							</h1>
							<WorldClock />
						</div>
						{playerStats && (
							<div className="flex items-center gap-4">
								<div className="text-right">
									<div className="font-display text-base font-semibold text-celestial-gold">{playerStats.name}</div>
									<div className="font-body text-xs text-white/70">{getTierName(playerStats.cultivation_tier || 1)}</div>
								</div>
								<div className="w-14 h-14 rounded-full bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-600 flex items-center justify-center text-xl font-bold shadow-glow-purple border-2 border-purple-400/30">
									{playerStats.cultivation_tier || 1}
								</div>
								{/* [SPRINT 5] Character Sheet Button */}
								<button
									onClick={() => setShowCharacterSheet(true)}
									className="btn-celestial px-5 py-2.5 font-display text-sm"
								>
									<span className="flex items-center gap-2">
										<span>📜</span>
										<span>Ficha</span>
									</span>
								</button>
								{/* [SPRINT 6] Quest Log Button */}
								<button
									onClick={() => setShowQuestLog(true)}
									className="px-5 py-2.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 rounded-xl font-display text-sm text-white font-semibold transition-all shadow-glow-gold border border-amber-400/30"
								>
									<span className="flex items-center gap-2">
										<span>🎯</span>
										<span>Missões</span>
									</span>
								</button>
							</div>
						)}
					</div>
				</div>

				{/* Main Layout */}
				<div className="flex-1 grid grid-cols-12 gap-4 px-4 pb-4 overflow-hidden">
					{/* Sidebar Esquerda - PlayerHUD Component */}
					<div className="col-span-2 overflow-y-auto custom-scrollbar">
						<PlayerHUD playerStats={playerStats} />
								{/* HP */}
								<div className="mystic-glass p-4 rounded-xl border border-red-500/30">
									<div className="flex justify-between text-xs mb-2 font-semibold text-white/90">
										<span className="flex items-center gap-1">
											<span className="text-red-400">❤️</span>
											<span className="font-mono">HP</span>
										</span>
										<span className="font-mono text-red-300">{Math.round(playerStats.current_hp)}/{Math.round(playerStats.max_hp)}</span>
									</div>
									<div className="h-2.5 bg-black/40 rounded-full overflow-hidden border border-red-900/50">
										<div 
											className="h-full bg-gradient-to-r from-red-600 via-red-500 to-pink-500 transition-all duration-300 shadow-glow-purple"
											style={{ width: `${getEnergyPercentage(playerStats.current_hp, playerStats.max_hp)}%` }}
										/>
									</div>
								</div>

								{/* Energias da Tríade */}
								<div className="mystic-glass p-4 rounded-xl border border-purple-500/30">
									<h3 className="font-title text-sm text-celestial-gold mb-3 uppercase tracking-wider">Tríade Energética</h3>
									<div className="space-y-3">
										<div>
											<div className="flex justify-between text-xs mb-1.5">
												<span className="text-orange-300 font-body">💎 Quintessência</span>
												<span className="font-mono text-orange-200">{Math.round(playerStats.quintessential_essence)}</span>
											</div>
											<div className="h-2 bg-black/40 rounded-full overflow-hidden border border-orange-900/50">
												<div 
													className="h-full bg-gradient-to-r from-orange-600 to-yellow-500 transition-all duration-300"
													style={{ width: `${getEnergyPercentage(playerStats.quintessential_essence, playerStats.max_quintessential_essence || 100)}%` }}
												/>
											</div>
										</div>
										<div>
											<div className="flex justify-between text-xs mb-1.5">
												<span className="text-purple-300 font-body">🌙 Shadow Chi</span>
												<span className="font-mono text-purple-200">{Math.round(playerStats.shadow_chi)}</span>
											</div>
											<div className="h-2 bg-black/40 rounded-full overflow-hidden border border-purple-900/50">
												<div 
													className="h-full bg-gradient-to-r from-purple-600 to-violet-500 transition-all duration-300 shadow-glow-purple"
													style={{ width: `${getEnergyPercentage(playerStats.shadow_chi, playerStats.max_shadow_chi || 100)}%` }}
												/>
											</div>
										</div>
										<div>
											<div className="flex justify-between text-xs mb-1.5">
												<span className="text-blue-300 font-body">⚡ Yuan Qi</span>
												<span className="font-mono text-blue-200">{Math.round(playerStats.yuan_qi)}</span>
											</div>
											<div className="h-2 bg-black/40 rounded-full overflow-hidden border border-blue-900/50">
												<div 
													className="h-full bg-gradient-to-r from-blue-600 to-cyan-500 transition-all duration-300"
													style={{ width: `${getEnergyPercentage(playerStats.yuan_qi, playerStats.max_yuan_qi || 100)}%` }}
												/>
											</div>
										</div>
									</div>
								</div>

								{/* Stats */}
								<div className="mystic-glass p-4 rounded-xl border border-amber-500/30">
									<h3 className="font-title text-sm text-celestial-gold mb-3 uppercase tracking-wider">Atributos</h3>
									<div className="grid grid-cols-2 gap-3 text-center">
										<div className="bg-black/30 rounded-lg p-2 border border-blue-500/20">
											<div className="font-mono text-lg font-bold text-blue-300">{playerStats.rank || 1}</div>
											<div className="font-body text-xs text-white/60">Rank</div>
										</div>
										<div className="bg-black/30 rounded-lg p-2 border border-green-500/20">
											<div className="font-mono text-lg font-bold text-green-300">{Math.round(playerStats.xp || 0)}</div>
											<div className="font-body text-xs text-white/60">XP</div>
										</div>
										<div className="bg-black/30 rounded-lg p-2 border border-red-500/20">
											<div className="font-mono text-lg font-bold text-red-300">{Math.round(playerStats.corruption || 0)}%</div>
											<div className="font-body text-xs text-white/60">Corrupção</div>
										</div>
										<div className="bg-black/30 rounded-lg p-2 border border-purple-500/20">
											<div className="font-mono text-lg font-bold text-purple-300">{Math.round(playerStats.willpower || 50)}</div>
											<div className="font-body text-xs text-white/60">Vontade</div>
										</div>
									</div>
								</div>

						{/* NPCs */}
						{npcsInScene.length > 0 && (
							<div className="mystic-glass p-4 rounded-xl border border-indigo-500/30 mt-4">
								<h3 className="font-title text-sm text-celestial-gold mb-3 uppercase tracking-wider">Personagens</h3>
								<div className="space-y-2">
									{npcsInScene.map((npc) => (
										<div
											key={npc.id}
											onClick={() => setSelectedNpc(npc)}
											className={`p-3 rounded-lg cursor-pointer transition-all hover:scale-105 border ${
												npc.emotional_state === 'hostile' 
													? 'bg-red-900/30 hover:bg-red-800/40 border-red-500/50 shadow-glow-purple' 
													: npc.emotional_state === 'friendly' 
													? 'bg-green-900/30 hover:bg-green-800/40 border-green-500/50' 
													: 'bg-white/5 hover:bg-white/10 border-white/10'
											}`}
										>
											<div className="font-display text-sm font-semibold text-white">{npc.name}</div>
											<div className="font-mono text-xs text-white/60 mt-1">
												Tier {npc.cultivation_tier || 1} • {Math.round(npc.current_hp)} HP
											</div>
										</div>
									))}
								</div>
							</div>
						)}
					</div>

					{/* Chat Principal - PAINEL CENTRAL */}
					<div className="col-span-7 flex flex-col mystic-glass rounded-2xl overflow-hidden border border-purple-500/30">
						{/* Area de Mensagens */}
						<div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
							{messages.map((msg, idx) => (
								<div
									key={idx}
									className={`animate-fade-in ${
										msg.type === 'player' ? 'ml-auto max-w-md bg-gradient-to-br from-violet-900/40 to-indigo-900/40 backdrop-blur-sm p-4 rounded-xl border border-violet-500/30' : 
										msg.type === 'narrator' ? 'bg-black/30 backdrop-blur-sm p-5 rounded-xl border border-amber-500/20' : 
										msg.type === 'action' ? 'bg-blue-900/30 backdrop-blur-sm p-4 rounded-xl border border-blue-500/30' : 
										msg.type === 'error' ? 'bg-red-900/30 backdrop-blur-sm p-4 rounded-xl border border-red-500/50' : 
										'bg-purple-900/20 backdrop-blur-sm p-4 rounded-xl border border-purple-500/20'
									}`}
								>
									{msg.type === 'narrator' ? (
										<div className="prose prose-invert max-w-none">
											{msg.text.split('\n\n').map((paragraph, pIdx) => (
												<p key={pIdx} className="mb-4 leading-relaxed text-base font-body text-white/90 first-letter:text-2xl first-letter:text-celestial-gold first-letter:font-display first-letter:mr-1">
													{paragraph}
												</p>
											))}
										</div>
									) : (
										<div className="text-base leading-relaxed font-body text-white/85">{msg.text}</div>
									)}
								</div>
							))}
							{isLoading && (
								<div className="flex items-center gap-3 text-celestial-jade font-body">
									<div className="spinner border-celestial-jade"></div>
									<span>Processando<span className="loading-dots"></span></span>
								</div>
							)}
							<div ref={messagesEndRef} />
						</div>

						{/* DialogueInput Component */}
						<DialogueInput onSend={handleSend} isLoading={isLoading} />
					</div>

					{/* Sidebar Direita - CombatInterface Component */}
					<div className="col-span-3 space-y-4 overflow-y-auto custom-scrollbar">
						<CombatInterface 
							skills={playerSkills} 
							onSkillClick={handleAttack}
							isLoading={isLoading}
						/>

						{/* Quick Actions */}
						<div className="mystic-glass p-5 rounded-2xl border border-indigo-500/30">
							<h3 className="font-title text-sm text-celestial-gold mb-4 uppercase tracking-wider">Ações Rápidas</h3>
							<div className="space-y-2">
								<button
									onClick={() => handleSend('olhar ao redor')}
									disabled={isLoading}
									className="w-full px-4 py-3 bg-gradient-to-r from-slate-800/60 to-slate-700/60 hover:from-slate-700/80 hover:to-slate-600/80 border border-white/10 hover:border-white/20 rounded-lg text-sm font-body transition-all disabled:opacity-50 flex items-center gap-2"
								>
									<span className="text-lg">👁️</span>
									<span>Observar Entorno</span>
								</button>
								<button
									onClick={() => handleSend('meditar e cultivar')}
									disabled={isLoading}
									className="w-full px-4 py-3 bg-gradient-to-r from-purple-900/40 to-violet-900/40 hover:from-purple-800/60 hover:to-violet-800/60 border border-purple-500/20 hover:border-purple-400/40 rounded-lg text-sm font-body transition-all disabled:opacity-50 flex items-center gap-2"
								>
									<span className="text-lg">🧘</span>
									<span>Meditar e Cultivar</span>
								</button>
								<button
									onClick={() => handleSend('procurar por recursos')}
									disabled={isLoading}
									className="w-full px-4 py-3 bg-gradient-to-r from-green-900/40 to-emerald-900/40 hover:from-green-800/60 hover:to-emerald-800/60 border border-green-500/20 hover:border-green-400/40 rounded-lg text-sm font-body transition-all disabled:opacity-50 flex items-center gap-2"
								>
									<span className="text-lg">🔍</span>
									<span>Procurar Recursos</span>
								</button>
								<button
									onClick={() => handleSend('descansar e recuperar energia')}
									disabled={isLoading}
									className="w-full px-4 py-3 bg-gradient-to-r from-blue-900/40 to-cyan-900/40 hover:from-blue-800/60 hover:to-cyan-800/60 border border-blue-500/20 hover:border-blue-400/40 rounded-lg text-sm font-body transition-all disabled:opacity-50 flex items-center gap-2"
								>
									<span className="text-lg">💤</span>
									<span>Descansar</span>
								</button>
							</div>
						</div>

						{/* Combate Status */}
						{inCombat && (
							<div className="mystic-glass-gold p-5 rounded-2xl border-2 border-red-500/70 animate-pulse-border shadow-glow-purple">
								<div className="text-center">
									<div className="text-4xl mb-3 animate-bounce">⚔️</div>
									<div className="font-title text-base font-bold text-red-300 tracking-wider">EM COMBATE!</div>
									<div className="font-body text-xs text-white/70 mt-2">Selecione uma técnica para atacar</div>
								</div>
							</div>
						)}
					</div>
				</div>

				{/* NpcInspector Component */}
				{selectedNpc && (
					<NpcInspector 
						npc={selectedNpc} 
						onClose={() => setSelectedNpc(null)}
					/>
				)}
				
				{/* [SPRINT 5] Character Sheet Modal */}
				{showCharacterSheet && (
					<CharacterSheet 
						playerId={playerId} 
						onClose={() => setShowCharacterSheet(false)} 
					/>
				)}

				{/* [SPRINT 6] Quest Log Modal */}
				{showQuestLog && (
					<QuestLog
						playerId={playerId}
						isOpen={showQuestLog}
						onClose={() => setShowQuestLog(false)}
					/>
				)}
			</div>
		</>
	);
}
