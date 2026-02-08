# 프로젝트: 디스코드 TTS 봇 (juhee-bot 포크)

## 프로젝트 개요
juhee-bot 포크 → 디스코드 음성채팅방 TTS 봇.
**현재**: Azure Speech SDK (유료) 사용 중.
Edge TTS 시도 후 복귀 (commit `3c6317c`).

## 기술 스택
- **TTS**: Azure Speech SDK (`microsoft-cognitiveservices-speech-sdk`)
- **출력**: `Ogg24Khz16BitMonoOpus` → `StreamType.OggOpus`
- **프레임워크**: discord.js v14 + @discordjs/voice
- **DB**: SQLite + Sequelize
- **언어**: TypeScript ESM (import 시 `.js` 확장자)

## 핵심 파일 구조
```
juhee-bot/
├── app/
│   ├── bot.ts            # 메인 봇 로직 + TTS 큐 시스템
│   ├── msTTS.ts          # Azure Speech SDK TTS 엔진
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

## 배포 (중요!)
`.cache/`가 `.gitignore`에 포함되어 있으므로 `git pull`만으로는 변경사항 반영 안 됨.

```bash
# 올바른 배포 명령어
ssh -i ~/.ssh/id_ed25519 root@141.164.59.237 \
  "cd /opt/tts-bot/juhee-bot && git pull && npm run build && pm2 reload juhee-bot"
```

## 빌드 & 실행
```bash
cd juhee-bot
npm install
npm run build          # TypeScript → .cache/app/
npm run updateCommands # 슬래시 커맨드 등록 (커맨드 변경 시 필수)
npm run start          # 빌드 + PM2 시작
```

## TTS 큐 시스템 (bot.ts)
연속 메시지를 순차적으로 재생하는 큐 시스템 구현됨.
- `processTTSQueue()`: while 루프, isPlayingTTS 플래그로 재진입 방지
- `getTTSStream()`: msTTS 콜백을 Promise로 래핑
- `waitForPlaybackEnd()`: Idle/error/30초 타임아웃 대기
- MessageCreate에서 모든 메시지를 큐에 push, 재생 중이어도 큐에 추가

## 슬래시 커맨드
| 커맨드 | 설명 |
|--------|------|
| `/들어와` | 음성 채널 참가 |
| `/나가` | 음성 채널 퇴장 |
| `/채널설정` | TTS 채널 지정 |
| `/채널해제` | TTS 채널 해제 |
| `/목소리` | 유저별 TTS 음성 선택 (한국어 10개) |
| `/피치` | 유저별 음높이 (x-low/low/medium/high/x-high) |
| `/속도` | 유저별 말하기 속도 (0-100) |
| `/닉네임읽기` | 닉네임 읽기 on/off + 앞/뒤 글자 수 |
| `/현재설정` | 현재 설정 확인 |
| `/음소거` / `/음소거해제` | 봇 음소거 |

## User DB 스키마
```
id: STRING (PK)          - Discord 유저 ID
ttsVoice: STRING          - 음성 이름
speed: INTEGER            - 속도 0~100
pitch: STRING             - 피치 (x-low/low/medium/high/x-high)
readNickname: BOOLEAN     - 닉네임 읽기 (default: true)
nicknamePrefix: INTEGER   - 앞 N글자 (default: 0)
nicknameSuffix: INTEGER   - 뒤 N글자 (default: 0)
```

## 환경변수 (.env)
```env
TOKEN=디스코드_봇_토큰
CLIENT_ID=디스코드_클라이언트_ID
SPEECH_KEY=Azure_Speech_API_키
SPEECH_REGION=Azure_리전
```

## 코딩 규칙
- TypeScript strict, ESM
- 한국어 주석
- 콜백 패턴: `msTTS(text, callback, voice, speed, pitch)`
- 캐시: SHA256 해시, `.ttsCache/*.ogg`, 캐시 키 `v: 3`
- 에러: try-catch + logger, 콜백에 null 전달

## 주의사항
- 커맨드 변경 시 반드시 `npm run updateCommands` 실행
- Sequelize `alter: true` 대신 `sync()` 사용
- 닉네임 자르기: prefix OR suffix (prefix 우선, 둘 다 0이면 전체 닉네임)
- uncaughtException에서 EBML/prism-media 에러는 비치명적 처리
