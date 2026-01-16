# 🧩 틀린그림찾기 (Spot the Difference) - Nano Banana Pro

![Banner](https://img.shields.io/badge/AI-Nano_Banana_Pro-yellow?style=for-the-badge&logo=google-gemini)
![Tech](https://img.shields.io/badge/Tech-React_%7C_PHP_%7C_MySQL-blue?style=for-the-badge)

**Nano Banana Pro**를 활용한 지능형 틀린그림찾기 퍼즐 생성 및 게임 플랫폼입니다. 사용자가 이미지를 업로드하면 AI가 자연스러운 차이점을 생성하고, 관리자가 이를 검수하여 즉시 게임으로 배포할 수 있습니다.

---

## 🚀 주요 기능 (Key Features)

### 1. Nano Banana Pro AI 엔진
- **자동 이미지 분석:** 업로드된 이미지를 분석하여 수정하기 적합한 영역(Bounding Box)을 추출합니다.
- **이미지 변형 생성:** Gemini API를 통해 색상 변경, 객체 추가/삭제 등 자연스러운 틀린그림을 생성합니다.
- **파편화 방지:** 단일 객체 위주의 명확한 수정을 보장하며, 정답 영역이 겹치지 않도록 설계되었습니다.

### 2. 관리자 대시보드 (Admin Dashboard)
- **퍼즐 관리:** 생성된 퍼즐의 상태(공개, 대기, 비공개)를 제어하고 추천 퍼즐(별표)을 지정합니다.
- **실시간 검수 도구:** AI가 생성한 정답 영역(Bbox)을 마우스 드래그로 수정하거나 삭제할 수 있습니다.
- **재생성 기능:** AI 결과가 마음에 들지 않을 경우, 즉시 새로운 차이점을 재생성합니다.

### 3. 게임 플레이 (Game Experience)
- **반응형 웹 UI:** 모바일과 PC 모두에서 최적화된 게임 환경을 제공합니다.
- **복셀 아트 스타일:** 세련된 다크 모드 기반의 프리미엄 UI 디자인을 적용했습니다.
- **실시간 정답 확인:** 클릭 시 정답 여부를 즉각적으로 피드백합니다.

---

## 🛠 기술 스택 (Tech Stack)

### **Frontend**
- **React (Vite):** 핵심 게임 로직 및 UI 컴포넌트
- **Vanilla HTML/CSS/JS:** 관리자 대시보드 및 검수 페이지
- **Lucide Icons:** 현대적인 벡터 아이콘 시스템

### **Backend**
- **PHP 8.x:** 데이터베이스 통신 및 파일 시스템 API 역할
- **MySQL:** 퍼즐 메타데이터 및 정답 정보 저장
- **Python 3:** Gemini API를 이용한 이미지 생성 처리

### **AI & Cloud**
- **Google Gemini API:** 고성능 멀티모달 모델을 통한 이미지 변형 및 분석
- **Apache (Bitnami):** 안정적인 서버 호스팅 환경

---

## 📂 프로젝트 구조 (Project Structure)

```text
.
├── src/                # React 게임 소스 코드
├── public/             # 정적 자산 및 퍼즐 리소스
│   └── puzzles/        # 생성된 퍼즐 데이터 (이미지, answer.json)
├── generator/          # AI 퍼즐 생성 엔진 (Python)
├── IMG/                # 업로드된 원본 이미지 저장소
├── api.php             # 메인 백엔드 API
├── index.html          # 메인 퍼즐 선택 페이지
├── admin_dashboard.html # 관리자 대시보드
└── game.html           # React 게임 진입점
```

---

## 📝 설치 및 실행 (Installation)

1. **서버 환경 구성:** PHP와 MySQL이 설치된 Apache 서버(예: Bitnami)가 필요합니다.
2. **Python 의존성 설치:**
   ```bash
   pip install pillow google-generativeai requests
   ```
3. **API 키 설정:** `generator/generate_puzzle.py` 파일 상단에 `GEMINI_API_KEY`를 설정합니다.
4. **빌드 및 배포:**
   ```bash
   npm install
   npm run build
   # 빌드된 dist 폴더의 내용을 서버로 전송
   ```

---

## 👨‍💻 Developer
- **작성자:** Jinho Jung
- **개발 연도:** 2026

---
&copy; 2026 Nano Banana Pro | Jinho Jung | All rights reserved.
