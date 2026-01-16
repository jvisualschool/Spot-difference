/**
 * 틀린 그림 찾기 게임 로직
 * Resolution: 1024x1024
 */

// 게임 데이터
const gameData = {
  differences: [
    { id: 1, x1: 320, y1: 220, x2: 380, y2: 280, name: "분홍색종이", found: false, difficulty: "medium" },
    { id: 2, x1: 890, y1: 240, x2: 930, y2: 300, name: "선반블록", found: false, difficulty: "easy" },
    { id: 3, x1: 340, y1: 640, x2: 420, y2: 720, name: "의자색상", found: false, difficulty: "easy" },
    { id: 4, x1: 450, y1: 500, x2: 490, y2: 540, name: "고양이안경", found: false, difficulty: "hard" },
    { id: 5, x1: 830, y1: 440, x2: 870, y2: 480, name: "서랍손잡이", found: false, difficulty: "hard" },
    { id: 6, x1: 520, y1: 560, x2: 560, y2: 600, name: "책상화분", found: false, difficulty: "medium" },
    { id: 7, x1: 240, y1: 200, x2: 320, y2: 260, name: "침대이불", found: false, difficulty: "easy" },
    { id: 8, x1: 630, y1: 160, x2: 670, y2: 200, name: "사라진종이", found: false, difficulty: "medium" }
  ],
  config: {
    tolerance: 20,
    maxWrongClicks: 3,
    maxHints: 2,
    timeLimit: 120
  },
  state: {
    score: 0,
    wrongClicks: 0,
    hintsUsed: 0,
    startTime: null,
    endTime: null
  }
};

// 점수 계산
const scorePoints = {
  easy: 10,
  medium: 15,
  hard: 20
};

/**
 * 클릭 위치가 차이점 영역 내에 있는지 확인
 * @param {number} clickX - 클릭한 X 좌표
 * @param {number} clickY - 클릭한 Y 좌표
 * @returns {Object|null} - 발견한 차이점 정보 또는 null
 */
function checkClick(clickX, clickY) {
  const tolerance = gameData.config.tolerance;
  
  for (let diff of gameData.differences) {
    if (!diff.found) {
      // 허용 오차를 포함한 영역 체크
      if (clickX >= diff.x1 - tolerance && 
          clickX <= diff.x2 + tolerance && 
          clickY >= diff.y1 - tolerance && 
          clickY <= diff.y2 + tolerance) {
        
        diff.found = true;
        const points = scorePoints[diff.difficulty];
        gameData.state.score += points;
        
        return {
          success: true,
          difference: diff,
          points: points,
          message: `${diff.name} 발견! +${points}점`
        };
      }
    }
  }
  
  // 차이점을 찾지 못한 경우
  gameData.state.wrongClicks++;
  return {
    success: false,
    wrongClicks: gameData.state.wrongClicks,
    message: "틀렸습니다!"
  };
}

/**
 * 게임 진행률 계산
 * @returns {Object} - 진행률 정보
 */
function getProgress() {
  const found = gameData.differences.filter(d => d.found).length;
  const total = gameData.differences.length;
  
  return {
    found: found,
    total: total,
    percentage: Math.round((found / total) * 100),
    remaining: total - found
  };
}

/**
 * 힌트 제공
 * @returns {Object|null} - 힌트 정보
 */
function useHint() {
  if (gameData.state.hintsUsed >= gameData.config.maxHints) {
    return { success: false, message: "힌트를 모두 사용했습니다!" };
  }
  
  // 아직 찾지 못한 차이점 중 하나 선택
  const remaining = gameData.differences.filter(d => !d.found);
  if (remaining.length === 0) {
    return { success: false, message: "모든 차이점을 찾았습니다!" };
  }
  
  const hint = remaining[0];
  gameData.state.hintsUsed++;
  gameData.state.score -= 10; // 힌트 사용 패널티
  
  return {
    success: true,
    hint: {
      x: Math.round((hint.x1 + hint.x2) / 2),
      y: Math.round((hint.y1 + hint.y2) / 2),
      name: hint.name
    },
    penalty: 10,
    hintsRemaining: gameData.config.maxHints - gameData.state.hintsUsed
  };
}

/**
 * 게임 시작
 */
function startGame() {
  gameData.state.startTime = Date.now();
  gameData.state.score = 0;
  gameData.state.wrongClicks = 0;
  gameData.state.hintsUsed = 0;
  
  // 모든 차이점을 미발견 상태로 초기화
  gameData.differences.forEach(d => d.found = false);
  
  console.log("게임 시작!");
}

/**
 * 게임 종료 및 최종 점수 계산
 * @returns {Object} - 최종 결과
 */
function endGame() {
  gameData.state.endTime = Date.now();
  const elapsedSeconds = Math.floor((gameData.state.endTime - gameData.state.startTime) / 1000);
  
  // 시간 보너스 계산
  let timeBonus = 0;
  if (elapsedSeconds <= gameData.config.timeLimit) {
    const remainingTime = gameData.config.timeLimit - elapsedSeconds;
    timeBonus = Math.min(20, Math.floor(remainingTime / 6)); // 6초당 1점, 최대 20점
  }
  
  const finalScore = gameData.state.score + timeBonus;
  
  return {
    finalScore: finalScore,
    baseScore: gameData.state.score,
    timeBonus: timeBonus,
    elapsedTime: elapsedSeconds,
    wrongClicks: gameData.state.wrongClicks,
    hintsUsed: gameData.state.hintsUsed,
    allFound: gameData.differences.every(d => d.found)
  };
}

/**
 * 게임 상태 초기화
 */
function resetGame() {
  gameData.differences.forEach(d => d.found = false);
  gameData.state = {
    score: 0,
    wrongClicks: 0,
    hintsUsed: 0,
    startTime: null,
    endTime: null
  };
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    checkClick,
    getProgress,
    useHint,
    startGame,
    endGame,
    resetGame,
    gameData
  };
}
