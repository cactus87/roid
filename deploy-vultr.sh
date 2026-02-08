#!/bin/bash

# Vultr VPS Discord TTS Bot 배포 스크립트

echo "🚀 Discord TTS Bot 배포 시작..."

# 1. 시스템 업데이트
echo "📦 시스템 업데이트 중..."
apt update && apt upgrade -y

# 2. Node.js 20.x 설치
echo "📦 Node.js 20.x 설치 중..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 3. Git 설치
echo "📦 Git 설치 중..."
apt install -y git

# 4. PM2 전역 설치
echo "📦 PM2 설치 중..."
npm install -g pm2

# 5. 작업 디렉토리 생성
echo "📁 작업 디렉토리 생성 중..."
mkdir -p /opt/discord-bots
cd /opt/discord-bots

# 6. 레포지토리 클론
echo "📥 봇 코드 다운로드 중..."
git clone https://github.com/kevin1113-github/juhee-bot.git
cd juhee-bot

# 7. Edge TTS 교체 버전으로 수정된 파일 적용 안내
echo ""
echo "⚠️  수동 작업 필요:"
echo "1. 로컬에서 수정한 파일들을 서버로 복사해야 합니다:"
echo "   - app/edgeTTS.ts (새 파일)"
echo "   - app/bot.ts"
echo "   - app/commands.ts"
echo "   - app/models/User.ts"
echo "   - package.json"
echo "   - .env.example"
echo ""
echo "2. 또는 수정된 코드를 GitHub에 푸시한 후:"
echo "   git pull origin main"
echo ""

# 8. 의존성 설치
echo "📦 npm 패키지 설치 중..."
npm install

# 9. .env 파일 생성
echo "📝 .env 파일 생성 중..."
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
echo "nano /opt/discord-bots/juhee-bot/.env"
echo "TOKEN=실제_봇_토큰 으로 변경하세요"
echo ""

# 10. 빌드
echo "🔨 TypeScript 빌드 중..."
npm run build

# 11. 슬래시 커맨드 등록
echo "📝 Discord 슬래시 커맨드 등록 중..."
echo "⚠️  .env 파일에 TOKEN 입력 후 실행하세요:"
echo "npm run updateCommands"
echo ""

# 12. PM2로 봇 시작 (주석 처리 - 수동 실행)
echo "🎯 봇 시작 준비 완료!"
echo ""
echo "다음 명령어로 봇을 시작하세요:"
echo "  cd /opt/discord-bots/juhee-bot"
echo "  npm run start"
echo ""
echo "PM2 프로세스 관리:"
echo "  pm2 list          # 실행 중인 프로세스 확인"
echo "  pm2 logs juhee    # 로그 확인"
echo "  pm2 restart juhee # 재시작"
echo "  pm2 stop juhee    # 중지"
echo "  pm2 startup       # 서버 재부팅 시 자동 시작 설정"
echo "  pm2 save          # 현재 프로세스 목록 저장"
echo ""

echo "✅ 배포 스크립트 실행 완료!"
