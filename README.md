# roid-bot

Discord 음성채팅방 TTS(Text-to-Speech) 봇.
로컬 GPU에서 Qwen3-TTS를 구동하여 무료로 고품질 음성을 생성합니다.

## 아키텍처

```
Discord 서버
    │ 채팅 메시지
    ▼
[VPS: roid-bot] (Node.js, discord.js v14)
    │ POST /tts (UTF-8)
    ▼
[로컬 PC: tts-server] (Python, FastAPI, 포트 5002)
    │ Qwen3-TTS-1.7B-VoiceDesign (CUDA)
    │ WAV → ffmpeg → OGG Opus
    ▼
Discord 음성 채널 재생
```

## 주요 기능

- **16종 음성 프리셋**: 기본 6종(여성/남성 A·B·C) + 캐릭터 10종(아이, 할머니, 락커, 조폭, 오타쿠, 애니 소녀/소년, 게임 영웅/악당, 나레이터)
- **음성 일관성**: voice_id별 고정 시드로 매번 동일한 음색 유지
- **개인 설정**: 유저별 목소리, 속도(0~100), 피치(5단계) 설정
- **닉네임 읽기**: 메시지 앞에 닉네임 읽기 (앞/뒤 글자 수 지정)
- **TTS 큐**: 연속 메시지를 순차적으로 재생
- **캐시**: SHA256 해시 기반 OGG 캐시로 동일 요청 즉시 응답

## 슬래시 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/들어와` | 음성 채널 참가 |
| `/나가` | 음성 채널 퇴장 |
| `/채널설정` | TTS 채널 지정 |
| `/채널해제` | TTS 채널 해제 |
| `/목소리` | TTS 음성 선택 (16종) |
| `/피치` | 음높이 변경 (x-low ~ x-high) |
| `/속도` | 말하기 속도 (0~100) |
| `/닉네임읽기` | 닉네임 읽기 on/off + 앞/뒤 글자 수 |
| `/현재설정` | 현재 설정 확인 |
| `/음소거` / `/음소거해제` | 봇 음소거 |

## 음성 프리셋

### 기본 음성

| ID | 설명 |
|----|------|
| `female_a` | 차분하고 또렷한 20대 여성 |
| `female_b` | 밝고 에너지 넘치는 20대 여성 |
| `female_c` | 전문적인 30대 뉴스 앵커 |
| `male_a` | 차분하고 깊은 30대 남성 |
| `male_b` | 편안하고 친근한 20대 남성 |
| `male_c` | 중후하고 무게감 있는 40대 남성 |

### 캐릭터 음성

| ID | 설명 |
|----|------|
| `child` | 아이 (5~7세) |
| `grandma` | 할머니 (70대) |
| `rocker` | 락커 |
| `gangster` | 조폭 |
| `otaku` | 오타쿠 |
| `anime_girl` | 애니메이션 소녀 |
| `anime_boy` | 애니메이션 소년 |
| `game_hero` | 게임 영웅 |
| `game_villain` | 게임 악당 |
| `narrator` | 나레이터 |

## 기술 스택

- **TTS 엔진**: Qwen3-TTS-1.7B-VoiceDesign (로컬 GPU)
- **TTS 서버**: Python, FastAPI, uvicorn
- **봇**: TypeScript ESM, discord.js v14, @discordjs/voice
- **DB**: SQLite + Sequelize
- **프로세스 관리**: PM2
- **네트워크**: Tailscale VPN (VPS ↔ 로컬 PC)

## 설치 및 실행

### TTS 서버 (로컬 PC, GPU 필요)

```bash
cd tts-server
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 5002
```

### 봇 (VPS)

```bash
cd juhee-bot
npm install
npm run build
npm run updateCommands  # 슬래시 커맨드 등록
npm run start           # PM2로 시작
```

### 환경변수 (juhee-bot/.env)

```env
TOKEN=디스코드_봇_토큰
CLIENT_ID=디스코드_클라이언트_ID
TTS_SERVER_URL=http://<TTS서버IP>:5002
```

## 배포

```bash
ssh -i ~/.ssh/id_ed25519 root@<VPS_IP> \
  "cd /opt/tts-bot/juhee-bot && git pull && npm run build && pm2 reload juhee-bot"
```

슬래시 커맨드 변경 시 `npm run updateCommands` 필수.

## 라이선스

저장소의 [LICENSE](./LICENSE) 파일 참조.
