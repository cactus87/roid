# 프로젝트: 디스코드 TTS 봇 (juhee-bot 포크)

## 프로젝트 개요
juhee-bot 포크 → 디스코드 음성채팅방 TTS 봇.
Azure Speech SDK(유료) → **Edge TTS(무료)** 교체 완료.

## 완료된 작업 (Edge TTS 교체)
- `app/msTTS.ts` 삭제 → `app/edgeTTS.ts` 생성
- `msedge-tts` v2.0.4 사용, Azure 패키지 제거
- 출력: `WEBM_24KHZ_16BIT_MONO_OPUS` → `StreamType.WebmOpus`
- 캐시: `.webm` 확장자, 캐시 키 `v: 2`
- bot.ts: import 변경, `createAudioResourceFromStream()` 으로 리네임

## 다음 작업: 유저별 음성 커스터마이징 강화

### 새로운 슬래시 커맨드 추가

| 커맨드 | 설명 | 파라미터 |
|--------|------|----------|
| `/목소리` | 유저별 TTS 음성 선택 | 목소리(choice): 한국어 10개 음성 |
| `/피치` | 유저별 음높이 설정 | 값(string): `x-low`, `low`, `medium`, `high`, `x-high` 또는 Hz값(`+50Hz`) |
| `/속도` | 유저별 말하기 속도 | 값(integer): 0~100 (현재와 동일) |
| `/닉네임읽기` | TTS 재생 시 "닉네임: 메시지" 형태로 읽기 on/off | 활성화(boolean) |
| `/현재설정` | 현재 목소리+피치+속도+닉네임읽기 상태 표시 | (기존 커맨드 확장) |

### DB 스키마 변경 (User 모델)

현재 User 모델:
```
id: STRING (PK)
ttsVoice: STRING (nullable)
speed: INTEGER (nullable)
```

추가할 컬럼:
```
pitch: STRING (nullable)     — 피치값 (기본: "medium")
readNickname: BOOLEAN (nullable) — 닉네임 읽기 (기본: true)
```

### 수정 대상 파일

| 파일 | 변경 내용 |
|------|----------|
| `app/models/User.ts` | `pitch`, `readNickname` 컬럼 추가 |
| `app/commands.ts` | `/목소리`, `/피치`, `/닉네임읽기` 커맨드 추가. 기존 `/목소리설정`→`/목소리`, `/속도설정`→`/속도`로 리네임 |
| `app/bot.ts` | 새 커맨드 핸들러 추가, TTS 호출 시 pitch 전달, 닉네임 프리픽스 로직 |
| `app/edgeTTS.ts` | `pitch` 파라미터 추가 (ProsodyOptions에 pitch 전달) |

### edgeTTS 함수 시그니처 변경

현재:
```typescript
async function edgeTTS(textData, callback, voiceName, speed)
```

변경 후:
```typescript
async function edgeTTS(textData, callback, voiceName, speed, pitch?)
```

msedge-tts ProsodyOptions:
```typescript
tts.toStream(text, {
  rate: "+30%",       // 속도
  pitch: "+50Hz",     // 피치 (새로 추가)
});
```

### 피치 지원 값 (msedge-tts)
- 프리셋: `x-low`, `low`, `medium`, `high`, `x-high`, `default`
- 상대값: `+50Hz`, `-20Hz`, `+2st`, `-1st`, `+10%`, `-10%`
- 슬래시 커맨드에서는 프리셋 5개를 choice로 제공

### 닉네임 읽기 로직
bot.ts MessageCreate에서:
```
if (user.readNickname) {
  parsedText = `${displayName}, ${parsedText}`
}
```

## 기술 스택
- TTS: `msedge-tts` v2.0.4 (무료, API 키 불필요)
- 프레임워크: discord.js v14 + @discordjs/voice
- DB: SQLite + Sequelize
- 언어: TypeScript ESM (import 시 `.js` 확장자)

## 핵심 파일 구조
```
juhee-bot/
├── app/
│   ├── bot.ts            # 메인 봇 로직
│   ├── commands.ts       # 슬래시 커맨드 정의
│   ├── action.ts         # 음성채널 입/퇴장
│   ├── edgeTTS.ts        # Edge TTS 엔진 (무료)
│   ├── models/User.ts    # 유저 모델 (voice, speed, pitch, readNickname)
│   ├── models/Server.ts  # 서버 모델
│   ├── dbObject.ts       # DB 관계 설정
│   └── dbFunction.ts     # DB 등록 함수
├── package.json
└── tsconfig.json
```

## 코딩 규칙
- TypeScript strict, ESM
- 한국어 주석
- 콜백 패턴: `edgeTTS(text, callback, voice, speed, pitch)`
- 캐시: SHA256 해시, `.ttsCache/*.webm`
- 에러: try-catch + logger, 콜백에 null 전달

## 빌드 & 실행
```bash
cd juhee-bot
npm install
npm run build          # TypeScript → .cache/app/
npm run updateCommands # 슬래시 커맨드 등록 (커맨드 변경 시 필수)
npm run start          # 빌드 + PM2 시작
```

## 환경변수 (.env)
```env
TOKEN=디스코드_봇_토큰
CLIENT_ID=디스코드_클라이언트_ID
# Edge TTS는 API 키 불필요
```

## 주의사항
- `toStream()`은 동기 반환, `setMetadata()`는 async
- 캐시 키에 pitch 추가 시 `v: 3`으로 버전 올려야 기존 캐시와 충돌 방지
- 커맨드 이름 변경 시 반드시 `npm run updateCommands` 실행
- Sequelize `alter: true` 대신 수동 마이그레이션 또는 `sync()` 사용
