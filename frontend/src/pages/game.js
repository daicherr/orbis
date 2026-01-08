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
import LoadingOverlay from '../components/LoadingOverlay';

export default function GamePage() {
	const { playerId, playerName, sendAction, isLoading: contextLoading, refreshFromStorage } = useGame();
	const [messages, setMessages] = useState([]);
	const [playerStats, setPlayerStats] = useState(null);
	const [npcsInScene, setNpcsInScene] = useState([]);
	const [selectedNpc, setSelectedNpc] = useState(null);
	const [inCombat, setInCombat] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [showCharacterSheet, setShowCharacterSheet] = useState(false);
	const [showQuestLog, setShowQuestLog] = useState(false);
	const [loadingType, setLoadingType] = useState('action');
	const [isInitializing, setIsInitializing] = useState(true);
	const messagesEndRef = useRef(null);

	// Helper para detectar tipo de loading baseado na ação
	const detectLoadingType = (action) => {
		const lowerAction = action.toLowerCase();
		const sleepKeywords = ['dormir', 'descansar', 'repousar', 'sleep', 'rest', 'recuperar energia'];
		if (sleepKeywords.some(kw => lowerAction.includes(kw))) {
			return 'sleep';
		}
		return 'action';
	};

	const playerSkills = [
		{ id: 'meteor_soul', name: 'Meteor Soul', element: 'shadow', icon: '⚔️', desc: 'Ignora armadura' },
		{ id: 'shadowstep', name: 'Shadowstep', element: 'shadow', icon: '👤', desc: 'Teleporte + Counter' },
		{ id: 'qi_burst', name: 'Qi Burst', element: 'qi', icon: '💫', desc: 'AOE de Yuan Qi' },
		{ id: 'silent_strike', name: 'Silent Strike', element: 'shadow', icon: '🗡️', desc: 'Ataque furtivo' },
		{ id: 'wall_of_northern_heavens', name: 'Wall of Northern', element: 'defense', icon: '🛡️', desc: 'Reflete 50% dano' },
		{ id: 'blood_essence_strike', name: 'Blood Essence', element: 'blood', icon: '🩸', desc: 'Usa HP como dano' },
	];

	// Atualizar playerId do localStorage ao montar
	useEffect(() => {
		if (refreshFromStorage) {
			refreshFromStorage();
		}
	}, []);

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
				setLoadingType('init');
				await handleSendWithType('olhar ao redor', 'init');
				setIsInitializing(false);
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

	// Versão interna que aceita tipo explícito
	const handleSendWithType = async (inputText, explicitType = null) => {
		if (!playerId) {
			setMessages(prev => [...prev, { type: 'error', text: '⚠️ Player não identificado. Recarregue a página.' }]);
			return;
		}

		if (inputText) {
			setMessages(prev => [...prev, { type: 'player', text: inputText }]);
		}
		setSelectedNpc(null);
		
		// Detectar tipo de loading
		const detectedType = explicitType || detectLoadingType(inputText);
		setLoadingType(detectedType);
		setIsLoading(true);

		try {
			const data = await sendAction(inputText);
			
			// Detectar se houve dawn tick na resposta
			if (data.action_result && data.action_result.includes('O sol nasce sobre Orbis')) {
				setLoadingType('dawn');
			}
			
			setMessages(prev => [...prev, { type: 'narrator', text: data.scene_description }]);
			return data;
		} catch (error) {
			console.error('Failed to send action:', error);
			setMessages(prev => [...prev, { type: 'error', text: `❌ Erro: ${error.message}` }]);
		} finally {
			setIsLoading(false);
		}
	};

	const handleSend = async (inputText) => {
		if (!playerId) {
			setMessages(prev => [...prev, { type: 'error', text: '⚠️ Player não identificado. Recarregue a página.' }]);
			return;
		}

		if (inputText) {
			setMessages(prev => [...prev, { type: 'player', text: inputText }]);
		}
		setSelectedNpc(null);
		
		// Detectar tipo de loading
		const detectedType = detectLoadingType(inputText);
		setLoadingType(detectedType);
		setIsLoading(true);

		try {
			const data = await sendAction(inputText);
			
			// Detectar se houve dawn tick
			if (data.action_result && data.action_result.includes('O sol nasce sobre Orbis')) {
				setLoadingType('dawn');
			}
			
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

			{/* === LOADING OVERLAY === */}
			<LoadingOverlay 
				isVisible={isLoading || isInitializing} 
				loadingType={loadingType} 
			/>

			{/* === MAIN GAME CONTAINER === */}
			<div className="game-container">
				
				{/* === TOP HEADER BAR === */}
				<div className="game-header">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-lg">
							<h1 className="game-title">✦ CÓDICE TRILUNA ✦</h1>
							<WorldClock />
						</div>
						{playerStats && (
							<div className="flex items-center gap-lg">
								<div style={{ textAlign: 'right' }}>
									<div className="glow-gold" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
										{playerStats.name}
									</div>
									<div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
										{getTierName(playerStats.cultivation_tier || 1)}
									</div>
								</div>
								{/* Cultivation Tier Badge */}
								<div className="badge badge-gold" style={{ 
									width: '48px', 
									height: '48px', 
									fontSize: '1.25rem',
									display: 'flex',
									alignItems: 'center',
									justifyContent: 'center',
									borderRadius: '50%',
									fontWeight: 700
								}}>
									{playerStats.cultivation_tier || 1}
								</div>
								{/* Header Buttons */}
								<button onClick={() => setShowCharacterSheet(true)} className="btn btn-secondary btn-sm">
									📜 Ficha
								</button>
								<button onClick={() => setShowQuestLog(true)} className="btn btn-ghost btn-sm">
									🎯 Missões
								</button>
							</div>
						)}
					</div>
				</div>

				{/* === MAIN 3-COLUMN LAYOUT === */}
				<div className="game-main">
					
					{/* === LEFT SIDEBAR (Player Stats) === */}
					<div className="game-sidebar">
						<PlayerHUD playerStats={playerStats} />

						{/* NPC Cards */}
						{npcsInScene.length > 0 && (
							<div className="panel">
								<h3 className="panel-header" style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
									<span>👥</span> Personagens
								</h3>
								<div className="flex flex-col gap-sm">
									{npcsInScene.map((npc) => (
										<div
											key={npc.id}
											onClick={() => setSelectedNpc(npc)}
											className={`npc-card ${npc.emotional_state === 'hostile' ? 'hostile' : npc.emotional_state === 'friendly' ? 'friendly' : ''}`}
										>
											<div className="npc-name">{npc.name}</div>
											<div className="npc-info">
												<span style={{ color: 'var(--purple)' }}>⚡ Tier {npc.cultivation_tier || 1}</span>
												<span style={{ color: 'var(--demon)' }}>❤️ {Math.round(npc.current_hp)}</span>
											</div>
										</div>
									))}
								</div>
							</div>
						)}
					</div>

					{/* === CENTER PANEL (Chat/Narrative) === */}
					<div className="game-center">
						{/* Decorative top border */}
						<div style={{ 
							height: '3px', 
							background: 'linear-gradient(90deg, transparent 0%, var(--gold) 20%, var(--gold) 80%, transparent 100%)',
							opacity: 0.5
						}} />

						{/* === MESSAGE AREA === */}
						<div className="chat-area">
							{messages.map((msg, idx) => {
								// Narrator message
								if (msg.type === 'narrator') {
									return (
										<div key={idx} className="chat-narrator">
											<div className="chat-narrator-label">
												<span>📜 Cronista do Crepúsculo</span>
											</div>
											<div className="chat-narrator-text">
												{msg.text.split('\n\n').map((paragraph, pIdx) => (
													<p key={pIdx}>{paragraph}</p>
												))}
											</div>
										</div>
									);
								}
								
								// Player message
								if (msg.type === 'player') {
									return (
										<div key={idx} className="chat-player">
											<div className="chat-player-label">
												🗣️ {playerStats?.name || 'Jogador'}
											</div>
											<div className="chat-player-text">{msg.text}</div>
										</div>
									);
								}
								
								// Action result
								if (msg.type === 'action') {
									return (
										<div key={idx} className="chat-action">
											<div className="chat-action-label">⚡ Resultado da Ação</div>
											<div className="chat-action-text">{msg.text}</div>
										</div>
									);
								}
								
								// Error
								if (msg.type === 'error') {
									return (
										<div key={idx} className="chat-error">
											<div className="chat-error-text">{msg.text}</div>
										</div>
									);
								}
								
								// System / Default
								return (
									<div key={idx} className="chat-system">
										<div className="chat-system-text">{msg.text}</div>
									</div>
								);
							})}
							
							{/* Loading indicator */}
							{isLoading && (
								<div className="chat-system" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--spacing-md)' }}>
									<div className="loading-spinner-small"></div>
									<span className="chat-system-text">O Cronista do Crepúsculo medita sobre o destino...</span>
								</div>
							)}
							<div ref={messagesEndRef} />
						</div>

						{/* === INPUT AREA === */}
						<DialogueInput onSend={handleSend} isLoading={isLoading} />
					</div>

					{/* === RIGHT SIDEBAR (Combat & Actions) === */}
					<div className="game-sidebar">
						
						{/* Combat Skills */}
						<CombatInterface 
							skills={playerSkills} 
							onSkillClick={handleAttack}
							isLoading={isLoading}
						/>

						{/* Quick Actions */}
						<div className="panel">
							<h3 className="panel-header" style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
								<span>⚡</span> Ações Rápidas
							</h3>
							<div className="flex flex-col gap-sm">
								<button
									onClick={() => handleSend('olhar ao redor')}
									disabled={isLoading}
									className="action-btn"
								>
									<span className="icon">👁️</span>
									<span>Observar Entorno</span>
								</button>
								<button
									onClick={() => handleSend('meditar e cultivar')}
									disabled={isLoading}
									className="action-btn"
									style={{ borderColor: 'var(--purple)' }}
								>
									<span className="icon">🧘</span>
									<span>Meditar</span>
								</button>
								<button
									onClick={() => handleSend('procurar por recursos')}
									disabled={isLoading}
									className="action-btn"
									style={{ borderColor: 'var(--jade)' }}
								>
									<span className="icon">🔍</span>
									<span>Buscar Recursos</span>
								</button>
								<button
									onClick={() => handleSend('descansar e recuperar energia')}
									disabled={isLoading}
									className="action-btn"
								>
									<span className="icon">💤</span>
									<span>Descansar</span>
								</button>
							</div>
						</div>

						{/* Combat Status Alert */}
						{inCombat && (
							<div className="combat-alert">
								<div className="icon">⚔️</div>
								<div className="title">Batalha!</div>
								<div className="subtitle">Escolha uma técnica para atacar</div>
							</div>
						)}
					</div>
				</div>

				{/* === MODALS === */}
				{selectedNpc && (
					<NpcInspector 
						npc={selectedNpc} 
						onClose={() => setSelectedNpc(null)}
					/>
				)}
				
				{showCharacterSheet && (
					<CharacterSheet 
						playerId={playerId} 
						onClose={() => setShowCharacterSheet(false)} 
					/>
				)}

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
