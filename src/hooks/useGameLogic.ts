import { useState, useEffect, useCallback } from 'react';
import confetti from 'canvas-confetti';

export interface Difference {
    id: number;
    name: string;
    description?: string;
    modification?: string;
    bounding_box: { x1: number; y1: number; x2: number; y2: number } | number[];
    difficulty?: number;
    found: boolean;
}

export interface PuzzleData {
    puzzle_id: string;
    original_image: string;
    modified_image: string;
    total_differences: number;
    differences: Difference[];
}

export interface PuzzleManifest {
    total_puzzles: number;
    puzzles: {
        id: string;
        differences: number;
        path: string;
    }[];
}

// 기본 게임 데이터 (폴백용)
const DEFAULT_GAME_DATA = {
    "puzzle_id": "default",
    "original_image": "/images/A.png",
    "modified_image": "/images/B.png",
    "total_differences": 8,
    "time_limit": 60,
    "differences": [
        { "id": 1, "name": "분홍색종이", "bounding_box": { "x1": 320, "y1": 220, "x2": 380, "y2": 280 } },
        { "id": 2, "name": "선반블록", "bounding_box": { "x1": 890, "y1": 0, "x2": 930, "y2": 80 } },
        { "id": 3, "name": "의자색상", "bounding_box": { "x1": 340, "y1": 640, "x2": 420, "y2": 720 } },
        { "id": 4, "name": "고양이안경", "bounding_box": { "x1": 450, "y1": 500, "x2": 490, "y2": 540 } },
        { "id": 5, "name": "서랍손잡이", "bounding_box": { "x1": 830, "y1": 440, "x2": 870, "y2": 480 } },
        { "id": 6, "name": "책상화분", "bounding_box": { "x1": 520, "y1": 560, "x2": 560, "y2": 600 } },
        { "id": 7, "name": "침대이불", "bounding_box": { "x1": 240, "y1": 200, "x2": 320, "y2": 260 } },
        { "id": 8, "name": "사라진종이", "bounding_box": { "x1": 630, "y1": 160, "x2": 670, "y2": 200 } }
    ]
};

// bounding_box 형식 정규화 (배열 또는 객체 형식 모두 처리)
const normalizeBoundingBox = (box: { x1: number; y1: number; x2: number; y2: number } | number[]): { x1: number; y1: number; x2: number; y2: number } => {
    if (Array.isArray(box)) {
        return { x1: box[0], y1: box[1], x2: box[2], y2: box[3] };
    }
    return box;
};

export const useGameLogic = () => {
    const [puzzleList, setPuzzleList] = useState<PuzzleManifest | null>(null);
    const [currentPuzzleIndex, setCurrentPuzzleIndex] = useState(0);
    const [puzzleData, setPuzzleData] = useState<PuzzleData | null>(null);
    const [differences, setDifferences] = useState<Difference[]>([]);
    const [timeLeft, setTimeLeft] = useState(60);
    const [score, setScore] = useState(0);
    const [gameState, setGameState] = useState<'idle' | 'loading' | 'playing' | 'won' | 'lost'>('idle');
    const [wrongEffect, setWrongEffect] = useState<{ x: number, y: number } | null>(null);
    const [originalImage, setOriginalImage] = useState('/images/A.png');
    const [modifiedImage, setModifiedImage] = useState('/images/B.png');

    // 퍼즐 목록 로드
    useEffect(() => {
        const loadManifest = async () => {
            try {
                const response = await fetch('api.php?action=list-puzzles');
                if (response.ok) {
                    const manifest = await response.json();

                    // 비공개(hidden) 퍼즐 제외
                    manifest.puzzles = manifest.puzzles.filter((p: any) => p.status !== 'hidden');

                    setPuzzleList(manifest);
                    console.log('퍼즐 목록 로드:', manifest);

                    // URL 파라미터 체크
                    const urlParams = new URLSearchParams(window.location.search);
                    const puzzleId = urlParams.get('puzzle');
                    if (puzzleId) {
                        await loadPuzzle(puzzleId);
                    }
                }
            } catch (error) {
                console.log('매니페스트 로드 실패, 기본 데이터 사용');
            }
        };
        loadManifest();
    }, []);

    // 타이머
    useEffect(() => {
        let timer: ReturnType<typeof setInterval>;
        if (gameState === 'playing' && timeLeft > 0) {
            timer = setInterval(() => {
                setTimeLeft(prev => {
                    if (prev <= 1) {
                        setGameState('lost');
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        }
        return () => clearInterval(timer);
    }, [gameState, timeLeft]);

    // 퍼즐 로드 함수
    const loadPuzzle = async (puzzleId: string) => {
        setGameState('loading');
        try {
            const response = await fetch(`api.php?action=get-puzzle&id=${puzzleId}`);
            if (!response.ok) throw new Error('퍼즐 로드 실패');

            const data = await response.json();
            setPuzzleData(data);

            // 이미지 경로 설정
            setOriginalImage(`puzzles/${puzzleId}/${data.original_image}`);
            setModifiedImage(`puzzles/${puzzleId}/${data.modified_image}`);

            // 차이점 데이터 정규화 (1024x1024 기준 좌표 사용)
            const normalizedDiffs = data.differences.map((d: any) => ({
                ...d,
                bounding_box: normalizeBoundingBox(d.bounding_box),
                found: false
            }));
            setDifferences(normalizedDiffs);

            // 차이점 개수에 따라 시간 설정 (차이점당 10초 + 기본 30초)
            const timeLimit = Math.max(60, data.total_differences * 10 + 30);
            setTimeLeft(timeLimit);
            setScore(0);
            setGameState('playing');

            console.log('퍼즐 로드 완료:', puzzleId, normalizedDiffs);
        } catch (error) {
            console.error('퍼즐 로드 오류:', error);
            // 기본 데이터로 폴백
            loadDefaultPuzzle();
        }
    };

    // 기본 퍼즐 로드
    const loadDefaultPuzzle = () => {
        setOriginalImage(DEFAULT_GAME_DATA.original_image);
        setModifiedImage(DEFAULT_GAME_DATA.modified_image);
        setDifferences(DEFAULT_GAME_DATA.differences.map(d => ({ ...d, found: false })));
        setTimeLeft(DEFAULT_GAME_DATA.time_limit);
        setScore(0);
        setGameState('playing');
    };

    // 게임 시작
    const startGame = async () => {
        if (puzzleList && puzzleList.puzzles.length > 0) {
            // 랜덤 퍼즐 선택
            const randomIndex = Math.floor(Math.random() * puzzleList.puzzles.length);
            setCurrentPuzzleIndex(randomIndex);
            await loadPuzzle(puzzleList.puzzles[randomIndex].id);
        } else {
            loadDefaultPuzzle();
        }
    };

    // 다음 퍼즐로 이동
    const nextPuzzle = async () => {
        if (puzzleList && puzzleList.puzzles.length > 0) {
            const nextIndex = (currentPuzzleIndex + 1) % puzzleList.puzzles.length;
            setCurrentPuzzleIndex(nextIndex);
            await loadPuzzle(puzzleList.puzzles[nextIndex].id);
        }
    };

    // 특정 퍼즐 선택
    const selectPuzzle = async (puzzleId: string) => {
        if (puzzleList) {
            const index = puzzleList.puzzles.findIndex(p => p.id === puzzleId);
            if (index !== -1) {
                setCurrentPuzzleIndex(index);
                await loadPuzzle(puzzleId);
            }
        }
    };

    const checkClick = useCallback((x: number, y: number) => {
        if (gameState !== 'playing') return;

        console.log('Click coordinates:', { x, y });

        const tolerance = 80; // increased tolerance for finer click detection
        const foundIdx = differences.findIndex(d => {
            const box = normalizeBoundingBox(d.bounding_box);
            const inBounds = !d.found &&
                x >= box.x1 - tolerance &&
                x <= box.x2 + tolerance &&
                y >= box.y1 - tolerance &&
                y <= box.y2 + tolerance;

            if (inBounds) {
                console.log('Found match:', d.name, box);
            }
            return inBounds;
        });

        if (foundIdx !== -1) {
            const newDiffs = [...differences];
            newDiffs[foundIdx].found = true;
            setDifferences(newDiffs);
            setScore(prev => prev + 100);

            playSuccessSound();

            if (newDiffs.every(d => d.found)) {
                setGameState('won');
                confetti({
                    particleCount: 150,
                    spread: 70,
                    origin: { y: 0.6 },
                    colors: ['#FFD700', '#FFA500', '#FF4500']
                });
            }
            return true;
        } else {
            console.log('No match. Available:', differences.filter(d => !d.found).map(d => d.name));
            setScore(prev => Math.max(0, prev - 10));
            setWrongEffect({ x, y });
            playErrorSound();
            setTimeout(() => setWrongEffect(null), 2000);
            return false;
        }
    }, [differences, gameState]);

    const playSuccessSound = () => {
        try {
            const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();

            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(440, audioCtx.currentTime);
            oscillator.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.1);

            gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);

            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            oscillator.start();
            oscillator.stop(audioCtx.currentTime + 0.2);
        } catch (e) { }
    };

    const playErrorSound = () => {
        try {
            const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();

            oscillator.type = 'sawtooth';
            oscillator.frequency.setValueAtTime(150, audioCtx.currentTime);
            oscillator.frequency.linearRampToValueAtTime(50, audioCtx.currentTime + 0.2);

            gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);

            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            oscillator.start();
            oscillator.stop(audioCtx.currentTime + 0.2);
        } catch (e) { }
    };

    const showAnswers = useCallback(() => {
        setDifferences(prev => prev.map(d => ({ ...d, found: true })));
    }, []);

    return {
        differences,
        timeLeft,
        score,
        gameState,
        startGame,
        checkClick,
        wrongEffect,
        showAnswers,
        // 새로운 기능들
        puzzleList,
        puzzleData,
        currentPuzzleIndex,
        nextPuzzle,
        selectPuzzle,
        originalImage,
        modifiedImage
    };
};
