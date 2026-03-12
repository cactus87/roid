# 프로젝트: 디스코드 TTS 봇 (juhee-bot 포크)

## 프로젝트 개요
juhee-bot 포크 → 디스코드 음성채팅방 TTS 봇.
**현재**: 로컬 Qwen3-TTS-1.7B-VoiceDesign (무료, 로컬 GPU).
Azure → XTTS-v2 → Qwen3-TTS 순으로 교체됨.

## 아키텍처

```
Discord 서버
    │ 채팅 메시지
    ▼
[VPS: juhee-bot] (Node.js, discord.js v14)
    │ POST /tts (application/x-www-form-urlencoded, UTF-8)
    │ text, voice_id, speed, pitch
    ▼
[로컬 PC: tts-server] (Python, FastAPI, 포트 5002)
    │ Qwen3-TTS-1.7B-VoiceDesign (CUDA)
    │ WAV → ffmpeg → OGG Opus
    ▼
[OGG 파일 응답]
    │
    ▼
[VPS: juhee-bot] → Discord 음성 채널 재생
```

## 기술 스택
- **TTS**: Qwen3-TTS-1.7B-VoiceDesign (`qwen-tts` 패키지)
- **TTS 서버**: FastAPI + uvicorn, 포트 5002 (로컬 PC)
- **출력**: WAV → ffmpeg libopus → OGG Opus
- **봇 프레임워크**: discord.js v14 + @discordjs/voice
- **DB**: SQLite + Sequelize
- **언어**: TypeScript ESM (import 시 `.js` 확장자)
- **Python 환경**: venv (Python 3.12), torch 2.10.0+cu130

## 핵심 파일 구조
```
tts-server/
├── main.py               # FastAPI + Qwen3-TTS 서버
├── requirements.txt      # Python 의존성
├── venv/                 # Python 가상환경
└── .ttsCache/            # OGG 캐시 (SHA256, v2: 접두사)

juhee-bot/
├── app/
│   ├── bot.ts            # 메인 봇 로직 + TTS 큐 시스템
│   ├── localTTS.ts       # TTS 서버 HTTP 클라이언트
│   ├── commands.ts       # 슬래시 커맨드 정의
│   ├── action.ts         # 음성채널 입/퇴장
│   ├── types.ts          # TTSQueueItem, GuildData 타입
│   ├── models/User.ts    # 유저 모델
│   ├── models/Server.ts  # 서버 모델
│   ├── config.ts         # 환경 변수 관리
│   ├── logger.ts         # 로깅
│   ├── dbObject.ts       # DB 관계 설정
│   └── dbFunction.ts     # DB 등록 함수
├── .cache/               # 빌드 출력 (.gitignore에 포함!)
├── package.json
└── tsconfig.json
```

## 핵심 심볼

### tts-server/main.py
| 심볼 | 타입 | 설명 |
|------|------|------|
| `VOICE_PRESETS` | `dict[str, str]` | voice_id → 영어 instruct 프롬프트 (16개: 기본 6 + 캐릭터 10) |
| `PITCH_SEMITONES` | `dict[str, int]` | pitch 이름 → 반음 수 |
| `tts_model` | `Qwen3TTSModel` | 모델 싱글턴 (서버 시작 시 로드) |
| `_tts_lock` | `asyncio.Lock` | GPU 직렬화용 Lock |
| `synthesize(request)` | `POST /tts` | TTS 합성 엔드포인트 |
| `list_voices()` | `GET /voices` | 사용 가능한 voice_id 목록 |
| `health()` | `GET /health` | 헬스 체크 |
| `speed_to_instruct(speed)` | `str` | speed(0~100) → instruct 접미사 |

### juhee-bot/app/localTTS.ts
| 심볼 | 타입 | 설명 |
|------|------|------|
| `localTTS(text, callback, voiceName, speed, pitch)` | `async fn` | TTS 서버 HTTP 클라이언트 |

### juhee-bot/app/bot.ts
| 심볼 | 타입 | 설명 |
|------|------|------|
| `processTTSQueue()` | `fn` | while 루프 기반 순차 TTS 재생 |
| `getTTSStream()` | `Promise` | localTTS 콜백을 Promise로 래핑 |
| `waitForPlaybackEnd()` | `Promise` | AudioPlayerStatus.Idle + 타임아웃 대기 |
| `guildDataMap` | `Map` | 길드별 TTS 큐 + 상태 |

## 배포 (중요!)
`.cache/`가 `.gitignore`에 포함되어 있으므로 `git pull`만으로는 변경사항 반영 안 됨.

```bash
# VPS 배포
ssh -i ~/.ssh/id_ed25519 root@141.164.59.237 \
  "cd /opt/tts-bot/juhee-bot && git pull && npm run build && pm2 reload juhee-bot"
```

## 빌드 & 실행

### 봇 (VPS)
```bash
cd juhee-bot
npm install
npm run build          # TypeScript → .cache/app/
npm run updateCommands # 슬래시 커맨드 등록 (커맨드 변경 시 필수)
npm run start          # 빌드 + PM2 시작
```

### TTS 서버 (로컬 PC)
```bash
cd tts-server
venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 5002
```

## TTS 큐 시스템 (bot.ts)
연속 메시지를 순차적으로 재생하는 큐 시스템.
- `processTTSQueue()`: while 루프, isPlayingTTS 플래그로 재진입 방지
- `getTTSStream()`: localTTS 콜백을 Promise로 래핑
- `waitForPlaybackEnd()`: Idle/error/240분 타임아웃 대기
- MessageCreate에서 모든 메시지를 큐에 push, 재생 중이어도 큐에 추가

## 슬래시 커맨드
| 커맨드 | 설명 |
|--------|------|
| `/들어와` | 음성 채널 참가 |
| `/나가` | 음성 채널 퇴장 |
| `/채널설정` | TTS 채널 지정 |
| `/채널해제` | TTS 채널 해제 |
| `/목소리` | 유저별 TTS 음성 선택 (기본 6종 + 캐릭터 10종: child/grandma/rocker/gangster/otaku/anime_girl/anime_boy/game_hero/game_villain/narrator) |
| `/피치` | 유저별 음높이 (x-low/low/medium/high/x-high) |
| `/속도` | 유저별 말하기 속도 (0-100) |
| `/닉네임읽기` | 닉네임 읽기 on/off + 앞/뒤 글자 수 |
| `/현재설정` | 현재 설정 확인 |
| `/음소거` / `/음소거해제` | 봇 음소거 |

## User DB 스키마
```
id: STRING (PK)          - Discord 유저 ID
ttsVoice: STRING          - 음성 이름 (female_a 등)
speed: INTEGER            - 속도 0~100
pitch: STRING             - 피치 (x-low/low/medium/high/x-high)
readNickname: BOOLEAN     - 닉네임 읽기 (default: true)
nicknamePrefix: INTEGER   - 앞 N글자 (default: 0)
nicknameSuffix: INTEGER   - 뒤 N글자 (default: 0)
```

## 환경변수

### juhee-bot/.env (VPS)
```env
TOKEN=디스코드_봇_토큰
CLIENT_ID=디스코드_클라이언트_ID
TTS_SERVER_URL=http://<로컬PC공인IP>:5002
```

## 코딩 규칙
- TypeScript strict, ESM
- 한국어 주석
- TTS 클라이언트: `localTTS(text, callback, voice, speed, pitch)`
- 캐시: SHA256 해시, `.ttsCache/*.ogg`, 캐시 키 접두사 `v2:`
- 에러: try-catch + logger, 콜백에 null 전달

## 주의사항 (중요!)
- **uvicorn Form 인코딩 버그**: `Form(...)` 파라미터로 한국어 받으면 latin-1로 깨짐
  → 반드시 `Request` 객체로 raw bytes 받아 `decode("utf-8")` 직접 파싱
- **instruct 프롬프트는 영어만**: 한국어 instruct → 외계어 출력
- **instruct에 rough/raspy/slow/pauses 등 극단적 묘사 주의**: 잡음·늘어짐 유발, 깔끔한 톤 위주로 작성
- **이중 모델 로드 금지**: 서버 실행 중 동일 모델 다른 프로세스로 로드 시 VRAM 오류
- **디버그/테스트는 API 호출만**: curl 등 HTTP 요청으로만 테스트
- 커맨드 변경 시 반드시 `npm run updateCommands` 실행
- Sequelize `alter: true` 대신 `sync()` 사용
- 닉네임 자르기: prefix OR suffix (prefix 우선, 둘 다 0이면 전체 닉네임)
- uncaughtException에서 EBML/prism-media 에러는 비치명적 처리
