import React, { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import { useGame } from '../contexts/GameContext';
import WorldClock from '../components/WorldClock';
import CharacterSheet from '../components/CharacterSheet';
import QuestLog from '../components/QuestLog';
import PlayerHUD from '../components/PlayerHUD';
import DialogueInput from '../components/DialogueInput';
import CombatInterface from '../components/CombatInterface';
import NpcInspector from '../components/NpcInspector';

export default function GamePage() {
	const { playerId, playerName, sendAction, isLoading: contextLoading } = useGame();
	const [messages, setMessages] = useState([]);
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
		const initGame = async () => {
			// Se não tem playerId do contexto, redireciona
			if (!contextLoading && !playerId) {
				window.location.href = '/';
				return;
			}

			if (playerId && playerName) {
				setPlayerStats(prev => prev || { name: playerName });
				setMessages([{ type: 'system', text: `✨ Bem-vindo de volta, ${playerName}. Sua jornada continua...` }]);
				handleSend('olhar ao redor');
			}
		};
		initGame();
	}, [playerId, playerName, contextLoading]);

	useEffect(() => {
		const hostileNpcs = npcsInScene.some(npc => npc.emotional_state === 'hostile');
		setInCombat(hostileNpcs);
	}, [npcsInScene]);

	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	}, [messages]);

	const handleSend = async (inputText, pId = playerId) => {
		if (!pId) {) => {
		if (!playerId) {
			setMessages(prev => [...prev, { type: 'error', text: '⚠️ Player não identificado. Recarregue a página.' }]);
			return;
		}

		if (inputText) {
			setMessages(prev => [...prev, { type: 'player', text: inputText }]);
		}
		setSelectedNpc(null);
		setIsLoading(true);

		try {
			const data = await sendAction(inputTextype: 'narrator', text: data.scene_description }]);
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

			{/* === MAIN HUD CONTAINER (AAA Game Style) === */}
			<div className="h-screen w-screen nebula-void overflow-hidden flex flex-col">
				{/* === TOP BAR (Ornate Header with Mystical Glow) === */}
				<div className="glass-gold m-6 p-5 rounded-2xl border-ornate-gold relative">
					<div className="flex items-center justify-between relative z-10">
						<div className="flex items-center gap-8">
							<h1 className="font-title text-3xl text-gold-glow tracking-wider">
								✦ CÓDICE TRILUNA ✦
							</h1>
							<WorldClock />
						</div>
						{playerStats && (
							<div className="flex items-center gap-6">
								<div className="text-right">
									<div className="font-display text-xl font-bold text-gold-glow drop-shadow-lg">{playerStats.name}</div>
									<div className="font-body text-sm text-slate-300 tracking-wide">{getTierName(playerStats.cultivation_tier || 1)}</div>
								</div>
								{/* Avatar with Pulsing Glow */}
								<div className="relative">
									<div className="w-16 h-16 rounded-full bg-gradient-void flex items-center justify-center text-2xl font-bold shadow-mystic border-2 border-imperial animate-pulse-glow">
										{playerStats.cultivation_tier || 1}
									</div>
									<div className="absolute -inset-1 bg-gradient-gold rounded-full opacity-20 blur-md -z-10"></div>
								</div>
								{/* Action Buttons */}
								<button
									onClick={() => setShowCharacterSheet(true)}
									className="btn-gold"
								>
									📜 Ficha
								</button>
								<button
									onClick={() => setShowQuestLog(true)}
									className="btn-action"
								>
									🎯 Missões
								</button>
							</div>
						)}
					</div>
				</div>

				{/* === MAIN GAME AREA (3-Column Grid) === */}
				<div className="flex-1 grid grid-cols-12 gap-6 px-6 pb-6 overflow-hidden">
					
					{/* === LEFT SIDEBAR (Player HUD) === */}
					<div className="col-span-3 overflow-y-auto scrollbar-xianxia space-y-4">
						<PlayerHUD playerStats={playerStats} />

						{/* === NPC CARDS (AAA Style with Glow on Hover) === */}
						{npcsInScene.length > 0 && (
							<div className="glass-jade p-5 rounded-2xl">
								<h3 className="font-title text-base text-jade-glow mb-4 uppercase tracking-wider flex items-center gap-2">
									<span>👥</span> Personagens
								</h3>
								<div className="space-y-3">
									{npcsInScene.map((npc) => (
										<div
											key={npc.id}
											onClick={() => setSelectedNpc(npc)}
											className={`
												p-4 rounded-xl cursor-pointer 
												transition-all duration-300 
												hover:scale-105 hover:shadow-mystic
												border-2 relative overflow-hidden
												${npc.emotional_state === 'hostile' 
													? 'glass-demon animate-pulse-glow' 
													: npc.emotional_state === 'friendly' 
													? 'glass-jade' 
													: 'glass-panel border-mist-border'
												}
											`}
										>
											{/* Hostile Indicator Animation */}
											{npc.emotional_state === 'hostile' && (
												<div className="absolute -top-1 -right-1 w-3 h-3 bg-demon rounded-full animate-ping"></div>
											)}
											<div className="font-display text-base font-bold text-white drop-shadow-lg">{npc.name}</div>
											<div className="font-mono text-sm text-slate-300 mt-2 flex items-center gap-3">
												<span className="text-imperial">⚡ Tier {npc.cultivation_tier || 1}</span>
												<span className="text-red-400">❤️ {Math.round(npc.current_hp)}</span>
											</div>
										</div>
									))}
								</div>
							</div>
						)}
					</div>

					{/* === CENTER PANEL (Narrative Chat - Storytelling Focus) === */}
					<div className="col-span-6 flex flex-col glass-panel rounded-2xl overflow-hidden border-2 border-void-200/30 relative">
						{/* Decorative Top Border */}
						<div className="absolute top-0 left-0 right-0 h-1 bg-gradient-gold opacity-40"></div>

						{/* === MESSAGE AREA (Scrollable Narrative Log) === */}
						<div className="flex-1 overflow-y-auto p-6 space-y-5 scrollbar-xianxia">
							{messages.map((msg, idx) => (
								<div
									key={idx}
									className={`
										${msg.type === 'player' 
											? 'ml-auto max-w-2xl glass-panel p-5 rounded-2xl border-l-4 border-imperial' 
											: msg.type === 'narrator' 
											? 'glass-gold p-6 rounded-2xl border-ornate-gold' 
											: msg.type === 'action' 
											? 'glass-jade p-5 rounded-2xl border-l-4 border-jade' 
											: msg.type === 'error' 
											? 'glass-demon p-5 rounded-2xl border-l-4 border-demon' 
											: 'glass-panel p-5 rounded-2xl border-mist-border'
										}
										transition-all duration-300 hover:scale-[1.01]
									`}
								>
									{msg.type === 'narrator' ? (
										<div className="prose prose-invert max-w-none">
											{msg.text.split('\n\n').map((paragraph, pIdx) => (
												<p 
													key={pIdx} 
													className="
														mb-4 leading-relaxed text-lg font-body text-slate-100
														first-letter:text-4xl first-letter:text-gold-glow 
														first-letter:font-title first-letter:float-left 
														first-letter:mr-2 first-letter:leading-none
													"
												>
													{paragraph}
												</p>
											))}
										</div>
									) : (
										<div className="text-lg leading-relaxed font-body text-slate-200">
											{msg.text}
										</div>
									)}
								</div>
							))}
							{isLoading && (
								<div className="flex items-center gap-4 text-jade font-body text-lg glass-panel p-4 rounded-xl w-fit">
									<div className="w-6 h-6 border-4 border-jade/20 border-t-jade rounded-full animate-spin"></div>
									<span className="text-jade-glow">A história se desenrola...</span>
								</div>
							)}
							<div ref={messagesEndRef} />
						</div>

						{/* === INPUT AREA (Epic Text Input) === */}
						<DialogueInput onSend={handleSend} isLoading={isLoading} />
					</div>

					{/* === RIGHT SIDEBAR (Combat Skills & Actions) === */}
					<div className="col-span-3 space-y-4 overflow-y-auto scrollbar-xianxia">
						
						{/* === COMBAT SKILLS (Epic Button Grid) === */}
						<CombatInterface 
							skills={playerSkills} 
							onSkillClick={handleAttack}
							isLoading={isLoading}
						/>

						{/* === QUICK ACTIONS (Contextual Buttons) === */}
						<div className="glass-panel p-5 rounded-2xl border border-imperial/20 relative overflow-hidden">
							<div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-gold opacity-50"></div>
							<h3 className="font-title text-base text-gold-glow mb-4 uppercase tracking-wider flex items-center gap-2">
								⚡ Ações Rápidas
							</h3>
							<div className="space-y-3">
								<button
									onClick={() => handleSend('olhar ao redor')}
									disabled={isLoading}
									className="
										w-full px-5 py-4 
										bg-gradient-void hover:bg-gradient-to-r hover:from-void-200 hover:to-void-100
										border border-mist-border hover:border-mist-glow
										rounded-xl text-base font-body text-slate-200
										transition-all duration-300 hover:scale-105 hover:shadow-mystic
										disabled:opacity-40 disabled:cursor-not-allowed
										flex items-center gap-3
									"
								>
									<span className="text-2xl">👁️</span>
									<span className="font-semibold">Observar Entorno</span>
								</button>
								<button
									onClick={() => handleSend('meditar e cultivar')}
									disabled={isLoading}
									className="
										w-full px-5 py-4 
										bg-gradient-to-r from-purple-900/50 to-violet-900/50 
										hover:from-purple-800 hover:to-violet-800
										border border-purple-500/30 hover:border-purple-400
										rounded-xl text-base font-body text-slate-200
										transition-all duration-300 hover:scale-105 hover:shadow-glow-purple
										disabled:opacity-40 disabled:cursor-not-allowed
										flex items-center gap-3
									"
								>
									<span className="text-2xl">🧘</span>
									<span className="font-semibold">Meditar</span>
								</button>
								<button
									onClick={() => handleSend('procurar por recursos')}
									disabled={isLoading}
									className="
										w-full px-5 py-4 
										bg-gradient-jade hover:shadow-glow-jade
										border border-jade/30 hover:border-jade
										rounded-xl text-base font-body text-void font-bold
										transition-all duration-300 hover:scale-105
										disabled:opacity-40 disabled:cursor-not-allowed
										flex items-center gap-3
									"
								>
									<span className="text-2xl">🔍</span>
									<span>Buscar Recursos</span>
								</button>
								<button
									onClick={() => handleSend('descansar e recuperar energia')}
									disabled={isLoading}
									className="
										w-full px-5 py-4 
										bg-gradient-to-r from-cyan-900/50 to-blue-900/50 
										hover:from-cyan-800 hover:to-blue-800
										border border-cyan-500/30 hover:border-cyan-400
										rounded-xl text-base font-body text-slate-200
										transition-all duration-300 hover:scale-105
										disabled:opacity-40 disabled:cursor-not-allowed
										flex items-center gap-3
									"
								>
									<span className="text-2xl">💤</span>
									<span className="font-semibold">Descansar</span>
								</button>
							</div>
						</div>

						{/* === COMBAT STATUS (Warning Indicator) === */}
						{inCombat && (
							<div className="glass-demon p-6 rounded-2xl border-2 border-demon animate-pulse-glow relative overflow-hidden">
								<div className="absolute inset-0 bg-gradient-demon opacity-10 animate-pulse"></div>
								<div className="text-center relative z-10">
									<div className="text-5xl mb-4 animate-bounce drop-shadow-lg">⚔️</div>
									<div className="font-title text-xl font-bold text-demon-100 tracking-wider uppercase">
										Batalha!
									</div>
									<div className="font-body text-sm text-slate-300 mt-3">
										Escolha uma técnica para atacar
									</div>
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
