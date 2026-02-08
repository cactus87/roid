#!/bin/bash

# Vultr VPS 자동 배포 스크립트 (서버에서 실행)

echo "🚀 Discord TTS Bot 배포 시작..."

# 1. 시스템 업데이트
apt update && apt upgrade -y

# 2. Node.js 20.x 설치
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs git

# 3. PM2 설치
npm install -g pm2

# 4. 봇 코드 클론 (Private Repository)
cd /opt
git clone https://github.com/cactus87/roid.git tts-bot
cd tts-bot

# 5. 의존성 설치
cd juhee-bot
npm install

# 6. .env 파일 생성
cat > .env << 'EOF'
# Discord Bot Configuration
TOKEN=YOUR_BOT_TOKEN_HERE
CLIENT_ID=1470053770334441649

# Edge TTS - API 키 불필요 (무료)

# Node Environment
NODE_ENV=production

# Server Configuration
PORT=3000
EOF

echo ""
echo "⚠️  .env 파일 수정 필요:"
echo "nano /opt/tts-bot/juhee-bot/.env"
echo "TOKEN=실제_봇_토큰 입력 후 저장 (Ctrl+O, Enter, Ctrl+X)"
echo ""

# 7. 빌드
npm run build

echo ""
echo "✅ 배포 준비 완료!"
echo ""
echo "다음 명령어를 실행하세요:"
echo "1. TOKEN 입력: nano /opt/tts-bot/juhee-bot/.env"
echo "2. 커맨드 등록: cd /opt/tts-bot/juhee-bot && npm run updateCommands"
echo "3. 봇 시작: npm run start"
echo ""
