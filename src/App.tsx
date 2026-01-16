import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Play,
    RotateCcw,
    Trophy,
    Clock,
    Target,
    AlertCircle,
    Github,
    Award,
    Search,
    Home,
    X
} from 'lucide-react';
import GameBoard from './components/GameBoard';
import { useGameLogic } from './hooks/useGameLogic';

const App: React.FC = () => {
    const {
        differences,
        timeLeft,
        score,
        gameState,
        startGame,
        checkClick,
        wrongEffect,
        showAnswers,
        puzzleList,
        puzzleData,
        nextPuzzle,
        originalImage,
        modifiedImage
    } = useGameLogic();

    const foundCount = differences.filter(d => d.found).length;
    const totalCount = differences.length;

    return (
        <div className="min-h-screen py-12 px-4 flex flex-col items-center justify-center bg-[#0c0c0e] text-white">
            {/* HUD Header */}
            <AnimatePresence>
                {gameState === 'playing' && (
                    <motion.div
                        initial={{ y: -20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: -20, opacity: 0 }}
                        className="hud-container"
                    >
                        <a
                            href="./index.html"
                            className="hud-item"
                            style={{ cursor: 'pointer', minWidth: 'auto', textDecoration: 'none' }}
                        >
                            <Home style={{ width: '20px', height: '20px', color: '#94a3b8' }} />
                        </a>
                        <div className="hud-divider" />
                        <div className="hud-item">
                            <Clock className={`w-5 h-5 ${timeLeft < 20 ? 'text-red-500 animate-pulse' : 'text-blue-400'}`} />
                            <span className={`text-xl font-bold font-mono ${timeLeft < 20 ? 'text-red-500' : ''}`}>
                                {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
                            </span>
                        </div>
                        <div className="hud-divider" />
                        <div className="hud-item">
                            <Target className="w-5 h-5 text-yellow-500" />
                            <span className="text-xl font-bold">{foundCount} / {totalCount}</span>
                        </div>
                        <div className="hud-divider" />
                        <div className="hud-item">
                            <Trophy className="w-5 h-5 text-green-400" />
                            <span className="text-xl font-bold">{score.toLocaleString()}</span>
                        </div>
                        <div className="hud-divider" />
                        <div
                            className="hud-item"
                            onClick={showAnswers}
                            style={{ cursor: 'pointer', minWidth: 'auto' }}
                        >
                            <Search style={{ width: '20px', height: '20px', color: '#fbbf24' }} />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Game Area */}
            <main className="game-main">
                {gameState === 'idle' ? (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="landing-container"
                    >
                        <div className="landing-icon pulse-animation">
                            <Award className="w-12 h-12 text-white" />
                        </div>
                        <h1 className="landing-title">
                            틀린그림찾기 <span className="font-normal opacity-80">Spot the Difference</span>
                        </h1>
                        <p className="landing-description">
                            {puzzleList ? `${puzzleList.total_puzzles}개의 퍼즐이 준비되어 있습니다.` : 'AI가 생성한 퍼즐에서 차이점을 찾아보세요!'}<br />
                            제한 시간 안에 모든 차이점을 찾아내세요.
                        </p>
                        <div className="flex flex-col gap-3 w-full">
                            <button
                                onClick={startGame}
                                className="landing-button"
                            >
                                <Play className="w-6 h-6 fill-current" />
                                <span>GAME START</span>
                            </button>
                            <a
                                href="./index.html"
                                className="text-gray-500 hover:text-white transition-colors text-sm font-bold flex items-center justify-center gap-2"
                                style={{ textDecoration: 'none' }}
                            >
                                <Home className="w-4 h-4" /> SELECT ANOTHER PUZZLE
                            </a>
                        </div>
                    </motion.div>
                ) : (
                    <GameBoard
                        originalSrc={originalImage}
                        modifiedSrc={modifiedImage}
                        differences={differences}
                        onImageClick={checkClick}
                        gameState={gameState}
                        wrongEffect={wrongEffect}
                    />
                )}
            </main>

            {/* Modals */}
            <AnimatePresence>
                {gameState === 'won' && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4"
                    >
                        <motion.div
                            initial={{ scale: 0.8, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            className="glass max-w-md w-full p-12 flex flex-col items-center text-center shadow-2xl"
                        >
                            <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mb-6 shadow-lg shadow-green-500/30">
                                <Trophy className="w-10 h-10 text-white" />
                            </div>
                            <h2 className="text-4xl font-black mb-2">VICTORY!</h2>
                            <p className="text-gray-400 mb-8">모든 차이점을 찾아냈습니다!</p>

                            <div className="grid grid-cols-2 gap-4 w-full mb-8">
                                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                    <div className="text-gray-500 text-xs uppercase font-bold mb-1">SCORE</div>
                                    <div className="text-2xl font-black text-yellow-400">{score.toLocaleString()}</div>
                                </div>
                                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                    <div className="text-gray-500 text-xs uppercase font-bold mb-1">TIME LEFT</div>
                                    <div className="text-2xl font-black text-blue-400">{timeLeft}s</div>
                                </div>
                            </div>

                            <div className="flex gap-3 w-full">
                                <button
                                    onClick={startGame}
                                    className="flex-1 py-4 bg-white text-black font-bold rounded-xl hover:bg-yellow-400 transition-colors flex items-center justify-center gap-2"
                                >
                                    <RotateCcw className="w-5 h-5" /> REPLAY
                                </button>
                                {puzzleList && puzzleList.total_puzzles > 1 && (
                                    <button
                                        onClick={nextPuzzle}
                                        className="flex-1 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold rounded-xl hover:from-purple-600 hover:to-pink-600 transition-colors flex items-center justify-center gap-2"
                                    >
                                        NEXT PUZZLE
                                    </button>
                                )}
                            </div>
                            <a
                                href="./index.html"
                                className="mt-4 text-gray-400 hover:text-white text-sm font-bold flex items-center gap-2"
                            >
                                <Home className="w-4 h-4" /> BACK TO MENU
                            </a>
                        </motion.div>
                    </motion.div>
                )}

                {gameState === 'lost' && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        style={{
                            position: 'fixed',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            zIndex: 50,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backgroundColor: 'rgba(0, 0, 0, 0.85)',
                            backdropFilter: 'blur(10px)',
                            padding: '1rem',
                        }}
                    >
                        <motion.div
                            initial={{ scale: 0.8, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            style={{
                                maxWidth: '400px',
                                width: '100%',
                                padding: '3rem',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                textAlign: 'center',
                                background: 'rgba(255, 255, 255, 0.05)',
                                borderRadius: '1.5rem',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                backdropFilter: 'blur(20px)',
                            }}
                        >
                            <div style={{
                                width: '80px',
                                height: '80px',
                                backgroundColor: '#ef4444',
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                marginBottom: '1.5rem',
                                boxShadow: '0 20px 40px rgba(239, 68, 68, 0.3)',
                            }}>
                                <AlertCircle style={{ width: '40px', height: '40px', color: 'white' }} />
                            </div>
                            <h2 style={{ fontSize: '2.5rem', fontWeight: 900, marginBottom: '0.5rem' }}>TIME OVER</h2>
                            <p style={{ color: '#9ca3af', marginBottom: '2rem' }}>시간이 다 되었습니다. 다시 시도해보세요!</p>

                            <button
                                onClick={startGame}
                                style={{
                                    width: '100%',
                                    padding: '1rem',
                                    backgroundColor: 'white',
                                    color: 'black',
                                    fontWeight: 'bold',
                                    borderRadius: '0.75rem',
                                    border: 'none',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '0.5rem',
                                    fontSize: '1rem',
                                }}
                            >
                                <RotateCcw style={{ width: '20px', height: '20px' }} /> TRY AGAIN
                            </button>
                            <a
                                href="./index.html"
                                style={{
                                    marginTop: '1.5rem',
                                    color: '#6b7280',
                                    fontSize: '0.875rem',
                                    fontWeight: 'bold',
                                    textDecoration: 'none',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem'
                                }}
                                className="hover:text-white"
                            >
                                <Home style={{ width: '16px', height: '16px' }} /> BACK TO MENU
                            </a>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Footer */}
            <footer style={{
                marginTop: '4rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.8rem',
                opacity: 0.6,
                padding: '4rem 0',
                borderTop: '1px solid rgba(255,255,255,0.1)',
                width: '100%',
                maxWidth: '800px'
            }}>
                <div style={{
                    fontSize: '0.7rem',
                    letterSpacing: '0.2em',
                    textTransform: 'uppercase',
                    color: '#f59e0b',
                    fontWeight: 700
                }}>
                    <a href="https://deepmind.google/technologies/gemini/" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>Nano Banana Pro</a> •
                    <a href="https://www.php.net/" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>PHP</a> •
                    <a href="https://www.mysql.com/" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>MySQL</a> •
                    <a href="https://react.dev/" target="_blank" style={{ color: 'inherit', textDecoration: 'none' }}>React</a>
                </div>
                <div style={{ fontSize: '1.2rem', fontWeight: 900, color: 'white' }}>
                    틀린그림찾기 Spot the Difference
                </div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
                    <a href="mailto:jvisualschool@gmail.com" style={{ color: 'inherit', textDecoration: 'none' }}>Jinho Jung</a>
                </div>
                <p style={{
                    fontSize: '0.8rem',
                    color: '#6b7280',
                }}>
                    &copy; 2026 All rights reserved.
                </p>
            </footer>
        </div>
    );
};

export default App;
