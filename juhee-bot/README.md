# 🎙️ Juhee Bot - Discord TTS Bot

Discord 음성 채널에서 채팅 메시지를 실시간으로 읽어주는 한국어 TTS 봇입니다.

## ✨ 주요 기능

- 🔊 **고품질 한국어 TTS** - Azure Speech SDK 기반 Neural 음성 (10종)
- 🎵 **유저별 맞춤 설정** - 음성, 속도, 피치, 닉네임 읽기 개인화
- ⚡ **실시간 큐 시스템** - 연속 메시지 순차 재생, 끊김 없는 경험
- 🤖 **자동 입퇴장** - 음성 채널 자동 참가, 빈 채널 즉시 퇴장
- 💾 **스마트 캐싱** - 동일 메시지 재사용으로 빠른 응답

## 🚀 빠른 시작

### 1. 사전 요구사항

- Node.js 18.0.0 이상
- Discord Bot Token
- Azure Speech API 키 (한국어 TTS 지원 리전)

### 2. 설치

```bash
# 저장소 클론
git clone https://github.com/your-repo/juhee-bot.git
cd juhee-bot

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env
# .env 파일에 TOKEN, CLIENT_ID, SPEECH_KEY, SPEECH_REGION 입력
```

### 3. 실행

```bash
# 개발 모드 (로컬)
npm run build
node .cache/app/bot.js

# 프로덕션 (PM2)
npm run start          # 빌드 + PM2 시작
npm run updateCommands # Discord에 슬래시 커맨드 등록
```

## 📋 슬래시 커맨드

### 기본 명령어

| 명령어 | 설명 |
|--------|------|
| `/들어와` | 음성 채널에 참가 |
| `/나가` | 음성 채널에서 퇴장 |
| `/채널설정 [채널]` | TTS 채널 지정 (텍스트/음성 채널) |
| `/채널해제` | TTS 채널 해제 |

### 음성 설정

| 명령어 | 설명 |
|--------|------|
| `/목소리 [목소리]` | TTS 음성 선택 (선히, 인준, 현수 등 10종) |
| `/속도 [0-100]` | 말하기 속도 조절 |
| `/피치 [x-low~x-high]` | 음높이 조절 |
| `/현재설정` | 현재 설정 확인 |

### 기타

| 명령어 | 설명 |
|--------|------|
| `/닉네임읽기 [on/off] [앞글자] [뒷글자]` | 닉네임 읽기 설정 |
| `/음소거` / `/음소거해제` | 봇 음소거 토글 |

## 🎤 지원 음성 (한국어 10종)

- **여성**: 선히, 지민, 서현, 순복, 유진
- **남성**: 인준, 현수, 봉진, 국민, 현수(다국어)

## 🛠️ 기술 스택

- **언어**: TypeScript (ESM)
- **프레임워크**: discord.js v14, @discordjs/voice
- **TTS**: Azure Speech SDK
- **DB**: SQLite + Sequelize
- **배포**: PM2
- **캐싱**: SHA256 기반 로컬 파일 캐시

## 📁 프로젝트 구조

```
juhee-bot/
├── app/
│   ├── bot.ts           # 메인 봇 로직 + TTS 큐 시스템
│   ├── msTTS.ts         # Azure Speech SDK TTS 엔진
│   ├── commands.ts      # 슬래시 커맨드 정의
│   ├── action.ts        # 음성 채널 액션
│   ├── types.ts         # TypeScript 타입 정의
│   ├── models/          # Sequelize 모델 (User, Server)
│   └── ...
├── .cache/              # TypeScript 빌드 출력
├── .ttsCache/           # TTS 캐시 파일
├── logs-prod/           # 프로덕션 로그
├── package.json
└── tsconfig.json
```

## 🔧 개발 & 배포

### 로컬 개발

```bash
npm run build          # TypeScript 빌드
node .cache/app/bot.js # 봇 실행
```

### 프로덕션 배포

```bash
# 서버에서 실행
git pull
npm run build
npm run updateCommands  # 커맨드 변경 시만
pm2 reload juhee-bot
```

**⚠️ 중요**: `.cache/`가 `.gitignore`에 포함되어 있으므로 배포 시 반드시 `npm run build` 실행 필요!

### PM2 명령어

```bash
pm2 status              # 상태 확인
pm2 logs juhee-bot      # 로그 실시간 보기
pm2 reload juhee-bot    # 재시작 (무중단)
pm2 stop juhee-bot      # 중지
```

## 🎯 주요 기능 상세

### TTS 큐 시스템

- **순차 재생**: while 루프 기반 큐 처리, 재생 중 메시지도 큐에 추가
- **재진입 방지**: `isPlayingTTS` 플래그로 중복 처리 방지
- **에러 복구**: AudioPlayer 에러 감지 + 30초 타임아웃으로 멈춤 방지
- **비치명적 에러 처리**: EBML/prism-media 에러는 프로세스 유지

### 자동 입퇴장

- **자동 참가**: 사용자가 음성 채널에 있으면 메시지 수신 시 자동 참가
- **타임아웃**: 240분(4시간) 동안 메시지 없으면 자동 퇴장 (메시지마다 리셋)
- **빈 채널 감지**: 봇만 남으면 즉시 퇴장

### 캐싱 시스템

- **캐시 키**: `SHA256(음성+속도+피치+텍스트)` - 버전 v3
- **저장 위치**: `.ttsCache/*.ogg`
- **통계**: 히트/미스/생성 로그 기록

## 🐛 트러블슈팅

### Q: 슬래시 커맨드가 안 보여요
**A**: `npm run updateCommands` 실행 후 Discord 앱 재시작. 글로벌 커맨드는 최대 1시간 소요.

### Q: 음성 채널이 `/채널설정`에 안 떠요
**A**: 2026년 2월 9일 업데이트로 해결됨. 봇 권한에 "채널 보기", "연결", "말하기" 있는지 확인.

### Q: 채팅해도 TTS가 안 나와요
**A**:
1. 사용자가 음성 채널에 들어가 있는지 확인
2. `/채널설정`으로 올바른 채널 설정 확인
3. 서버 로그 확인: `pm2 logs juhee-bot`

### Q: 배포했는데 코드 변경이 안 됐어요
**A**: `.cache/` 디렉토리가 `.gitignore`에 있습니다. 반드시 `npm run build` 실행!

## 📜 라이선스

ISC

## 🙏 크레딧

- **원작**: [kevin1113dev/juhee-bot](https://github.com/kevin1113-github/juhee-bot)
- **포크 개선**: TTS 큐 시스템, 자동 입퇴장, 음성 채널 지원 추가

---

**문의**: 이슈 트래커로 버그 리포트 & 기능 제안 환영합니다!
