#!/bin/bash

# Vultr 서버 자동 배포 스크립트 (서버에서 실행)

echo "🚀 Discord TTS Bot 자동 배포 시작..."

# 시스템 업데이트
echo "📦 시스템 업데이트 중..."
apt update && apt upgrade -y

# Node.js 20.x 설치
echo "📦 Node.js 20.x 설치 중..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs git

# 버전 확인
echo "✅ Node.js 버전:"
node -v
echo "✅ npm 버전:"
npm -v

# PM2 설치
echo "📦 PM2 설치 중..."
npm install -g pm2

# 봇 코드 클론
echo "📥 GitHub에서 코드 다운로드 중..."
cd /opt
git clone https://github.com/cactus87/roid.git tts-bot
cd tts-bot/juhee-bot

# 패키지 설치
echo "📦 npm 패키지 설치 중..."
npm install

# .env 파일 생성
echo "📝 .env 파일 생성 중..."
cat > .env << 'EOF'
TOKEN=YOUR_BOT_TOKEN_HERE
CLIENT_ID=1470053770334441649
NODE_ENV=production
PORT=3000
EOF

# 빌드
echo "🔨 TypeScript 빌드 중..."
npm run build

echo ""
echo "======================================"
echo "✅ 설치 완료!"
echo "======================================"
echo ""
echo "다음 단계:"
echo "1. Discord Bot Token 입력:"
echo "   nano /opt/tts-bot/juhee-bot/.env"
echo "   (TOKEN=YOUR_BOT_TOKEN_HERE를 실제 토큰으로 변경)"
echo ""
echo "2. 슬래시 커맨드 등록:"
echo "   cd /opt/tts-bot/juhee-bot"
echo "   npm run updateCommands"
echo ""
echo "3. 봇 시작:"
echo "   npm run start"
echo ""
echo "4. 로그 확인:"
echo "   pm2 logs juhee"
echo ""
echo "5. PM2 관리 명령어:"
echo "   pm2 list           # 프로세스 목록"
echo "   pm2 restart juhee  # 재시작"
echo "   pm2 stop juhee     # 중지"
echo "   pm2 startup        # 서버 재부팅 시 자동 시작"
echo "   pm2 save           # 현재 상태 저장"
echo ""
