#!/bin/bash
# XTTS-v2 TTS 서버 시작 스크립트
# 실행 전: pip install -r requirements.txt

cd "$(dirname "$0")"

# .ttsCache 폴더 생성
mkdir -p .ttsCache

echo "🚀 XTTS-v2 TTS 서버 시작 (포트 5002)..."
uvicorn main:app --host 0.0.0.0 --port 5002
