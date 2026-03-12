# Qwen3-TTS VoiceDesign 서버

로컬 GPU로 한국어 TTS를 생성하는 FastAPI 서버.
`speaker_wav` 없이 영어 텍스트 설명(instruct)만으로 음성 스타일 제어.

## 요구사항
- Python 3.12
- CUDA 지원 GPU (RTX 권장)
- FFmpeg (`C:\base_app\FFmpeg\bin` 또는 PATH에 추가)

## 설치

```bash
# 가상환경 생성
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# torch GPU 버전으로 교체 (qwen-tts가 CPU 버전을 끌어올 수 있음)
pip install --force-reinstall torch==2.10.0+cu130 --index-url https://download.pytorch.org/whl/cu130

# flash-attn (선택사항, 미리 빌드된 whl 필요)
# pip install flash_attn-*.whl
```

## 실행

```bash
cd tts-server
venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 5002
```

첫 실행 시 HuggingFace에서 모델 자동 다운로드 (~3GB).

## API

### POST /tts
텍스트를 OGG Opus로 변환.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `text` | string | 필수 | 합성할 텍스트 |
| `voice_id` | string | `female_a` | 음성 프리셋 |
| `speed` | int | `30` | 속도 0~100 |
| `pitch` | string | `medium` | 음높이 |

**voice_id 목록**

| voice_id | 설명 |
|----------|------|
| `female_a` | 여성 A (기본) |
| `female_b` | 여성 B (밝음) |
| `female_c` | 여성 C (뉴스) |
| `male_a` | 남성 A (기본) |
| `male_b` | 남성 B (친근) |
| `male_c` | 남성 C (내레이터) |

**pitch 목록**: `x-low` / `low` / `medium` / `high` / `x-high`

### GET /voices
사용 가능한 voice_id 및 pitch 목록 반환.

### GET /health
서버 상태 및 GPU 사용 여부 반환.

## 테스트

```bash
# TTS 합성
curl -X POST http://localhost:5002/tts \
  --data-urlencode "text=안녕하세요 반갑습니다" \
  -d "voice_id=female_a&speed=30&pitch=medium" \
  --output test.ogg

# 재생
"C:\base_app\FFmpeg\bin\ffplay.exe" -nodisp -autoexit test.ogg

# 헬스 체크
curl http://localhost:5002/health
```

## VPS 연결

로컬 PC에서 실행하고 VPS 봇이 접근할 수 있도록 포트 5002를 외부에 오픈하거나 Cloudflare Tunnel 사용.

```env
# juhee-bot/.env (VPS)
TTS_SERVER_URL=http://<로컬PC공인IP>:5002
```

## 주의사항
- **instruct는 반드시 영어**: 한국어 instruct 사용 시 외계어 출력
- **이중 모델 로드 금지**: 서버 실행 중 동일 모델을 다른 프로세스에서 로드하면 VRAM 오류
- **Form 파라미터 직접 사용 금지**: uvicorn의 `Form(...)` 파싱이 한국어를 깨뜨림 → `Request.body()` 직접 파싱
- 캐시 키 접두사 `v2:` (XTTS-v2 캐시와 분리)
