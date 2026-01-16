#!/usr/bin/env python3
"""
틀린그림찾기 문제 생성기 (AI Inpainting 기반)
Google Gemini API를 사용하여 원본 이미지에서 차이점이 있는 이미지를 생성합니다.
"""

import os
import sys
import json
import random
import base64
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image
import io

# ============================================================
# 설정
# ============================================================
try:
    from .config import GEMINI_API_KEY
except ImportError:
    import os
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Text 분석용 API
GEMINI_TEXT_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# 이미지 생성용 API (Gemini 3 Pro Image)
GEMINI_IMAGE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent"

# 생성할 차이점 개수 범위
MIN_DIFFERENCES = 10
MAX_DIFFERENCES = 10

# 입출력 경로
BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "IMG"

# 서버 구조(dist/puzzles)와 로컬 구조(public/puzzles) 모두 대응
if (BASE_DIR / "puzzles").exists():
    OUTPUT_DIR = BASE_DIR / "puzzles"
elif (BASE_DIR / "public" / "puzzles").exists():
    OUTPUT_DIR = BASE_DIR / "public" / "puzzles"
else:
    # 기본값 (없으면 생성)
    OUTPUT_DIR = BASE_DIR / "puzzles"

# ============================================================
# 유틸리티 함수
# ============================================================

def encode_image_to_base64(image_path: str) -> str:
    """이미지를 Base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def save_base64_image(base64_data: str, output_path: str):
    """Base64 이미지를 파일로 저장"""
    image_data = base64.b64decode(base64_data)
    with open(output_path, "wb") as f:
        f.write(image_data)

def get_image_dimensions(image_path: str) -> tuple:
    """이미지 크기 반환"""
    with Image.open(image_path) as img:
        return img.size

def resize_image_if_needed(image_path: str, max_size: int = 1024) -> str:
    """이미지가 너무 크면 리사이즈하고 임시 파일 경로 반환"""
    with Image.open(image_path) as img:
        width, height = img.size
        if width > max_size or height > max_size:
            ratio = min(max_size / width, max_size / height)
            new_size = (int(width * ratio), int(height * ratio))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # 임시 파일로 저장
            temp_path = str(image_path).replace(".png", "_resized.png").replace(".jpg", "_resized.jpg")
            resized.save(temp_path, "PNG")
            print(f"  📐 이미지 리사이즈: {width}x{height} → {new_size[0]}x{new_size[1]}")
            return temp_path
    return str(image_path)

# ============================================================
# Gemini API 호출
# ============================================================

def analyze_image_for_modifications(image_path: str) -> list:
    """
    Gemini를 사용하여 이미지를 분석하고 수정 가능한 영역을 찾습니다.
    """
    print("  🔍 이미지 분석 중...")
    
    image_base64 = encode_image_to_base64(image_path)
    width, height = get_image_dimensions(image_path)
    
    num_differences = random.randint(MIN_DIFFERENCES, MAX_DIFFERENCES)
    
    prompt = f"""이 이미지를 분석하고, 틀린그림찾기 게임을 위해 수정할 수 있는 {num_differences}개의 영역을 찾아주세요.

각 영역에 대해 다음 정보를 JSON 형식으로 제공해주세요:
- "area_name": 영역의 이름 (한글, 예: "빨간 사과", "파란 의자")
- "description": 현재 상태 설명
- "modification": 어떻게 수정할지 (색상 변경, 객체 추가/제거 등)
- "bounding_box": 이미지 내 위치 (x1, y1, x2, y2 - 0~{width}, 0~{height} 범위의 정수)
- "difficulty": 난이도 (1-5, 1=쉬움, 5=어려움)

- 수정이 자연스러워야 합니다
- 너무 작거나 눈에 띄지 않는 변경은 피하세요
- **중요: 각 수정 영역은 하나의 단일 객체나 단일 위치여야 합니다. (예: 타일 조각을 여러 군데 흩뿌리거나, 하나의 수정을 여러 파편으로 나누지 마세요.)**
- **절대 주의: 각 수정 영역(bounding_box)은 서로 겹쳐서는 안 됩니다. 충분한 거리를 두고 위치시켜 주세요.**
- 색상 변경, 작은 객체 추가/제거, 패턴 변경 등이 좋습니다
- bounding_box 값은 반드시 정수여야 합니다

JSON 배열로만 응답해주세요. 다른 텍스트 없이 JSON만 출력하세요. """

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_base64
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096
        }
    }
    
    response = requests.post(
        f"{GEMINI_TEXT_API_URL}?key={GEMINI_API_KEY}",
        headers=headers,
        json=payload,
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"  ❌ API 오류: {response.status_code}")
        print(response.text)
        return []
    
    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    
    # JSON 추출
    try:
        # ```json ... ``` 형식 처리
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        modifications = json.loads(text.strip())
        print(f"  ✅ {len(modifications)}개의 수정 영역 발견")
        return modifications
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 파싱 오류: {e}")
        print(f"  응답: {text[:500]}")
        return []

def generate_modified_image(image_path: str, modifications: list) -> tuple:
    """
    Gemini 이미지 생성 모델을 사용하여 수정된 이미지를 생성합니다.
    """
    print("  🎨 수정된 이미지 생성 중...")
    
    image_base64 = encode_image_to_base64(image_path)
    
    # 수정 지시사항 생성
    modification_instructions = "\n".join([
        f"{i+1}. {mod['area_name']}: {mod['modification']}"
        for i, mod in enumerate(modifications)
    ])
    
    prompt = f"""CRITICAL: This is for a spot-the-difference game. You MUST make these changes VERY VISIBLE and OBVIOUS.

REQUIRED CHANGES (YOU MUST IMPLEMENT ALL OF THESE):
{modification_instructions}

STRICT REQUIREMENTS:
- Make each change CLEARLY VISIBLE - this is a game, players need to see the differences!
- DO NOT make subtle changes - make them OBVIOUS
- **CRITICAL: DO NOT create fractured or multi-part modifications. Each modification must be a SINGLE, CONCENTRATED object or change. No scattered pieces, no multi-location tiles, no fragmented splinters.**
- ONLY change the specific items listed above
- Keep everything else EXACTLY the same
- If removing an object, completely remove it (not just make it transparent)
- If changing a color, make it a DISTINCTLY DIFFERENT color
- If adding something, make it clearly visible
- Maintain the same image size, quality, and overall composition

IMPORTANT: Players will compare this image with the original. The changes MUST be noticeable but not too easy.

Generate the edited image with ALL the changes listed above."""

    headers = {"Content-Type": "application/json"}
    
    # Gemini 이미지 생성 모델 사용
    payload = {
        "contents": [{
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_base64
                    }
                },
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"]
        }
    }
    
    response = requests.post(
        f"{GEMINI_IMAGE_API_URL}?key={GEMINI_API_KEY}",
        headers=headers,
        json=payload,
        timeout=180
    )
    
    if response.status_code != 200:
        print(f"  ❌ 이미지 생성 API 오류: {response.status_code}")
        error_detail = response.text[:500]
        print(f"  오류 상세: {error_detail}")
        
        # 모델이 없는 경우 대체 모델 시도
        if "not found" in error_detail.lower():
            return try_alternative_image_generation(image_path, modifications)
        return None, None
    
    result = response.json()
    
    # 디버깅: 전체 응답 구조 확인
    print(f"  📋 API 응답 키: {list(result.keys())}")
    
    # 응답에서 이미지 추출
    try:
        if "candidates" not in result:
            print(f"  ❌ candidates 없음. 응답: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
            return None, None
            
        parts = result["candidates"][0]["content"]["parts"]
        print(f"  📋 응답 parts 개수: {len(parts)}")
        
        for i, part in enumerate(parts):
            print(f"  📋 Part {i} 키: {list(part.keys())}")
            # inline_data 또는 inlineData (camelCase) 둘 다 처리
            if "inline_data" in part or "inlineData" in part:
                inline_data = part.get("inline_data") or part.get("inlineData")
                image_data = inline_data.get("data") or inline_data.get("bytesBase64Encoded")
                mime_type = inline_data.get("mime_type") or inline_data.get("mimeType", "image/png")
                print(f"  ✅ 수정된 이미지 생성 완료 ({mime_type})")
                return image_data, mime_type
        
        # 이미지가 없으면 텍스트 응답 확인
        for part in parts:
            if "text" in part:
                print(f"  ⚠️ 텍스트 응답만 받음: {part['text'][:500]}")
        
        return None, None
    except (KeyError, IndexError) as e:
        print(f"  ❌ 응답 파싱 오류: {e}")
        print(f"  응답: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
        return None, None

def try_alternative_image_generation(image_path: str, modifications: list) -> tuple:
    """
    대체 이미지 생성 방법을 시도합니다 (Imagen 3 사용).
    """
    print("  🔄 대체 모델로 재시도 중 (Imagen 3)...")
    
    image_base64 = encode_image_to_base64(image_path)
    
    modification_instructions = "\n".join([
        f"{i+1}. {mod['area_name']}: {mod['modification']}"
        for i, mod in enumerate(modifications)
    ])
    
    prompt = f"""Edit this image with these changes:
{modification_instructions}
Keep everything else exactly the same."""

    headers = {"Content-Type": "application/json"}
    
    # Imagen 3 API 시도
    imagen_url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"
    
    payload = {
        "instances": [{
            "prompt": prompt,
            "image": {
                "bytesBase64Encoded": image_base64
            }
        }],
        "parameters": {
            "sampleCount": 1
        }
    }
    
    response = requests.post(
        f"{imagen_url}?key={GEMINI_API_KEY}",
        headers=headers,
        json=payload,
        timeout=180
    )
    
    if response.status_code != 200:
        print(f"  ❌ Imagen API도 실패: {response.status_code}")
        return None, None
    
    result = response.json()
    
    try:
        predictions = result.get("predictions", [])
        if predictions:
            image_data = predictions[0].get("bytesBase64Encoded")
            if image_data:
                print("  ✅ Imagen으로 이미지 생성 완료")
                return image_data, "image/png"
    except Exception as e:
        print(f"  ❌ Imagen 응답 파싱 오류: {e}")
    
    return None, None

# ============================================================
# 메인 생성 함수
# ============================================================

def generate_puzzle_for_image(image_path: Path) -> dict:
    """
    하나의 원본 이미지에서 틀린그림찾기 퍼즐을 생성합니다.
    """
    print(f"\n{'='*60}")
    print(f"📷 처리 중: {image_path.name}")
    print(f"{'='*60}")
    
    # 이미지 리사이즈 (필요시)
    processed_path = resize_image_if_needed(str(image_path))
    
    # 1단계: 이미지 분석 및 수정 영역 찾기
    modifications = analyze_image_for_modifications(processed_path)
    
    if not modifications:
        print("  ⚠️ 수정 영역을 찾지 못했습니다.")
        return None
    
    # 2단계: 수정된 이미지 생성
    modified_image_data, mime_type = generate_modified_image(processed_path, modifications)
    
    if not modified_image_data:
        print("  ⚠️ 이미지 생성에 실패했습니다.")
        return None
    
    # 3단계: 파일 저장
    puzzle_id = image_path.stem
    
    # 재생성 시(original.png인 경우) 부모 폴더명을 ID로 사용
    if puzzle_id == "original" and image_path.parent.name.startswith("i"):
        puzzle_id = image_path.parent.name
        
    puzzle_dir = OUTPUT_DIR / puzzle_id
    puzzle_dir.mkdir(parents=True, exist_ok=True)
    
    # 원본 이미지 복사 (JPG로 저장, 1MB 이하 유지)
    original_output = puzzle_dir / "original.jpg"
    with Image.open(processed_path) as img:
        img.convert("RGB").save(original_output, "JPEG", quality=85, optimize=True)
        # 파일 크기 체크 및 재조정 (1MB 미만 보장)
        while os.path.getsize(original_output) > 1024 * 1024:
            quality = int(os.path.getsize(original_output) / (1024 * 1024) * 80)
            img.convert("RGB").save(original_output, "JPEG", quality=max(10, quality), optimize=True)
            if quality < 10: break
    
    # 수정된 이미지 저장
    modified_output = puzzle_dir / "modified.jpg"
    image_data = base64.b64decode(modified_image_data)
    with Image.open(io.BytesIO(image_data)) as m_img:
        m_img.convert("RGB").save(modified_output, "JPEG", quality=85, optimize=True)
        while os.path.getsize(modified_output) > 1024 * 1024:
            quality = int(os.path.getsize(modified_output) / (1024 * 1024) * 80)
            m_img.convert("RGB").save(modified_output, "JPEG", quality=max(10, quality), optimize=True)
            if quality < 10: break
    
    # 정답 JSON 생성
    answer_data = {
        "puzzle_id": puzzle_id,
        "created_at": datetime.now().isoformat(),
        "original_image": "original.jpg",
        "modified_image": "modified.jpg",
        "total_differences": len(modifications),
        "differences": [
            {
                "id": i + 1,
                "name": mod["area_name"],
                "description": mod["description"],
                "modification": mod["modification"],
                "bounding_box": mod["bounding_box"],
                "difficulty": mod.get("difficulty", 3)
            }
            for i, mod in enumerate(modifications)
        ]
    }
    
    answer_path = puzzle_dir / "answer.json"
    with open(answer_path, "w", encoding="utf-8") as f:
        json.dump(answer_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n  ✅ 퍼즐 생성 완료!")
    print(f"     📁 저장 위치: {puzzle_dir}")
    print(f"     🔢 차이점 개수: {len(modifications)}")
    
    # 차이점 목록 출력
    print(f"\n  📋 차이점 목록:")
    for mod in modifications:
        print(f"     - {mod['area_name']}: {mod['modification']}")
    
    # 검수 페이지 생성
    generate_review_page(puzzle_dir, answer_data)
    
    return answer_data

def generate_review_page(puzzle_dir: Path, answer_data: dict):
    """검수용 HTML 페이지 생성"""
    puzzle_id = answer_data["puzzle_id"]
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>퍼즐 검수 - {puzzle_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .puzzle-id {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2em;
        }}
        .images-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .image-wrapper {{
            position: relative;
            border: 3px solid #ddd;
            border-radius: 10px;
            overflow: hidden;
            background: #f9f9f9;
        }}
        .image-wrapper h2 {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            margin: 0;
            text-align: center;
            font-size: 1.3em;
        }}
        .image-container {{
            position: relative;
            display: inline-block;
            width: 100%;
        }}
        .image-container img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .image-container canvas {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }}
        .differences-list {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .differences-list h2 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        .difference-item {{
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .difference-item h3 {{
            color: #667eea;
            margin-bottom: 5px;
        }}
        .difference-item p {{
            color: #666;
            margin: 5px 0;
        }}
        .difficulty {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        .difficulty-1, .difficulty-2 {{ background: #4ade80; color: white; }}
        .difficulty-3 {{ background: #fbbf24; color: white; }}
        .difficulty-4, .difficulty-5 {{ background: #ef4444; color: white; }}
        .actions {{
            text-align: center;
            padding: 20px;
        }}
        .btn {{
            padding: 15px 40px;
            margin: 0 10px;
            font-size: 1.1em;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }}
        .btn-approve {{
            background: #10b981;
            color: white;
        }}
        .btn-approve:hover {{
            background: #059669;
            transform: translateY(-2px);
        }}
        .btn-regenerate {{
            background: #ef4444;
            color: white;
        }}
        .btn-regenerate:hover {{
            background: #dc2626;
            transform: translateY(-2px);
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            margin-bottom: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            color: white;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 퍼즐 검수</h1>
        <div class="puzzle-id">Puzzle ID: {puzzle_id}</div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{answer_data['total_differences']}</div>
                <div class="stat-label">차이점 개수</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{answer_data['created_at'][:10]}</div>
                <div class="stat-label">생성 날짜</div>
            </div>
        </div>
        
        <div class="images-container">
            <div class="image-wrapper">
                <h2>원본 이미지</h2>
                <div class="image-container" id="original-container">
                    <img src="original.png" alt="Original" id="original-img">
                    <canvas id="original-canvas"></canvas>
                </div>
            </div>
            <div class="image-wrapper">
                <h2>수정된 이미지</h2>
                <div class="image-container" id="modified-container">
                    <img src="{answer_data['modified_image']}" alt="Modified" id="modified-img">
                    <canvas id="modified-canvas"></canvas>
                </div>
            </div>
        </div>
        
        <div class="differences-list">
            <h2>📋 차이점 목록</h2>
            {''.join([f'''
            <div class="difference-item">
                <h3>{diff['id']}. {diff['name']}</h3>
                <p><strong>설명:</strong> {diff['description']}</p>
                <p><strong>수정사항:</strong> {diff['modification']}</p>
                <p><strong>위치:</strong> {diff['bounding_box']}</p>
                <p><span class="difficulty difficulty-{diff['difficulty']}">난이도: {diff['difficulty']}</span></p>
            </div>
            ''' for diff in answer_data['differences']])}
        </div>
        
        <div class="actions">
            <button class="btn btn-approve" onclick="approve()">✅ 승인</button>
            <button class="btn btn-regenerate" onclick="regenerate()">🔄 재생성</button>
        </div>
    </div>
    
    <script>
        const differences = {json.dumps(answer_data['differences'], ensure_ascii=False)};
        
        function drawBoundingBoxes() {{
            const originalImg = document.getElementById('original-img');
            const modifiedImg = document.getElementById('modified-img');
            const originalCanvas = document.getElementById('original-canvas');
            const modifiedCanvas = document.getElementById('modified-canvas');
            
            // 이미지 로드 후 캔버스 설정
            originalImg.onload = function() {{
                originalCanvas.width = originalImg.width;
                originalCanvas.height = originalImg.height;
                modifiedCanvas.width = modifiedImg.width;
                modifiedCanvas.height = modifiedImg.height;
                
                const ctx1 = originalCanvas.getContext('2d');
                const ctx2 = modifiedCanvas.getContext('2d');
                
                differences.forEach((diff, index) => {{
                    const box = diff.bounding_box;
                    const [x1, y1, x2, y2] = box;
                    const width = x2 - x1;
                    const height = y2 - y1;
                    
                    // 스케일 계산
                    const scaleX = originalImg.width / 1024;
                    const scaleY = originalImg.height / 1024;
                    
                    // 빨간 사각형 그리기
                    [ctx1, ctx2].forEach(ctx => {{
                        ctx.strokeStyle = '#ff0000';
                        ctx.lineWidth = 3;
                        ctx.strokeRect(x1 * scaleX, y1 * scaleY, width * scaleX, height * scaleY);
                        
                        // 번호 표시
                        ctx.fillStyle = '#ff0000';
                        ctx.font = 'bold 20px Arial';
                        ctx.fillText(diff.id, x1 * scaleX + 5, y1 * scaleY + 25);
                    }});
                }});
            }};
            
            modifiedImg.onload = originalImg.onload;
        }}
        
        function approve() {{
            alert('✅ 퍼즐이 승인되었습니다!\\n게임에서 사용할 수 있습니다.');
        }}
        
        function regenerate() {{
            if (confirm('🔄 이 퍼즐을 재생성하시겠습니까?')) {{
                alert('재생성 기능은 Python 스크립트를 다시 실행해야 합니다.\\n\\n명령어:\\npython3 generator/generate_puzzle.py IMG/{puzzle_id}.png');
            }}
        }}
        
        // 페이지 로드 시 bounding box 그리기
        drawBoundingBoxes();
    </script>
</body>
</html>"""
    
    review_path = puzzle_dir / "review.html"
    with open(review_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n  📄 검수 페이지 생성: {review_path}")
    print(f"     🌐 브라우저에서 열기: file://{review_path.absolute()}")


def generate_all_puzzles():
    """
    IMG 폴더의 모든 이미지에 대해 퍼즐을 생성합니다.
    """
    print("\n" + "="*60)
    print("🎮 틀린그림찾기 문제 생성기")
    print("="*60)
    
    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 입력 이미지 찾기
    image_files = list(INPUT_DIR.glob("*.png")) + list(INPUT_DIR.glob("*.jpg"))
    image_files = [f for f in image_files if not f.name.startswith(".") and "_resized" not in f.name]
    
    if not image_files:
        print(f"❌ {INPUT_DIR}에서 이미지를 찾을 수 없습니다.")
        return
    
    print(f"\n📂 입력 폴더: {INPUT_DIR}")
    print(f"📂 출력 폴더: {OUTPUT_DIR}")
    print(f"🖼️  발견된 이미지: {len(image_files)}개")
    
    # 각 이미지에 대해 퍼즐 생성
    results = []
    for image_path in sorted(image_files):
        try:
            result = generate_puzzle_for_image(image_path)
            if result:
                results.append(result)
        except Exception as e:
            print(f"  ❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    # 전체 결과 요약
    print("\n" + "="*60)
    print("📊 생성 결과 요약")
    print("="*60)
    print(f"✅ 성공: {len(results)}/{len(image_files)}개")
    
    # 전체 퍼즐 목록 JSON 생성
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "total_puzzles": len(results),
        "puzzles": [
            {
                "id": r["puzzle_id"],
                "differences": r["total_differences"],
                "path": f"puzzles/{r['puzzle_id']}"
            }
            for r in results
        ]
    }
    
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 매니페스트 저장: {manifest_path}")
    print("\n✨ 완료!")

# ============================================================
# 메인
# ============================================================

if __name__ == "__main__":
    # 특정 이미지만 처리하려면 인자로 전달
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
        if image_path.exists():
            generate_puzzle_for_image(image_path)
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {image_path}")
    else:
        generate_all_puzzles()
