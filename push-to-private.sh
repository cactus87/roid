#!/bin/bash

# GitHub Private Repository 푸시 스크립트

cd c:/ai/tts-bot/juhee-bot

echo "🔐 GitHub Private Repository로 코드 푸시 중..."

# 1. 수정된 파일 커밋
echo "📝 변경사항 커밋 중..."

# .env 파일 제외 (.gitignore에 추가)
echo ".env" >> .gitignore

git add -A
git commit -m "feat: Azure Speech SDK → Edge TTS 무료 전환

- app/edgeTTS.ts 신규 생성 (msTTS.ts 대체)
- msedge-tts v2.0.4 사용 (API 키 불필요)
- 유저별 커스터마이징 기능 추가:
  - /목소리: 음성 선택 (한국어 10개)
  - /피치: 음높이 조절 (x-low ~ x-high)
  - /속도: 말하기 속도 (0-100)
  - /닉네임읽기: 닉네임 프리픽스 on/off
- User DB에 pitch, readNickname 컬럼 추가
- 캐시 키 버전 v:3으로 업그레이드
- WebSocket 타임아웃 처리 (15초)
- AudioPlayer 상태 관리 개선 (간헐적 재생 실패 수정)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 2. 원격 저장소 변경 (사용자 입력 필요)
echo ""
echo "⚠️  다음 명령어를 실행하여 원격 저장소를 변경하세요:"
echo ""
echo "git remote remove origin"
echo "git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
