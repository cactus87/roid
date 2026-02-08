/**
 * @fileoverview 환경 변수 중앙 관리
 * @description 모든 환경 변수를 한 곳에서 로드하고 검증
 */

import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { logger } from "./logger.js";

// __dirname 계산 (ESM 환경)
const __filename = fileURLToPath(import.meta.url);
const __dirname_local = path.dirname(__filename);

// .env 파일 명시적 경로 지정 (샤드 프로세스에서도 작동)
// 빌드 후 .cache/app/config.js → ../../.env
const envPath = path.join(__dirname_local, "../../.env");
const dotenvResult = dotenv.config({ path: envPath });

if (dotenvResult.error) {
  logger.error(`[config] .env 로드 실패: ${envPath}`, dotenvResult.error);
}

// Discord 설정 (필수)
export const DISCORD_TOKEN = process.env.TOKEN;
export const DISCORD_CLIENT_ID = process.env.CLIENT_ID;

// Azure Speech SDK 설정 (필수)
export const SPEECH_KEY = process.env.SPEECH_KEY;
export const SPEECH_REGION = process.env.SPEECH_REGION;

// Azure Language API 설정 (선택)
export const LANGUAGE_KEY = process.env.LANGUAGE_KEY;
export const LANGUAGE_ENDPOINT = process.env.LANGUAGE_ENDPOINT;

// Koreanbots 설정 (선택)
export const KOREANBOTS_TOKEN = process.env.KOREANBOTS_TOKEN;

// 환경 설정
export const NODE_ENV = process.env.NODE_ENV || "development";
export const PORT = parseInt(process.env.PORT || "3000", 10);

/**
 * 필수 환경 변수 검증
 * @throws {Error} 필수 환경 변수가 없으면 에러 발생
 */
export function validateConfig(): void {
  const errors: string[] = [];

  if (!DISCORD_TOKEN) {
    errors.push("TOKEN (Discord 봇 토큰)");
  }

  if (!DISCORD_CLIENT_ID) {
    errors.push("CLIENT_ID (Discord 클라이언트 ID)");
  }

  if (!SPEECH_KEY) {
    errors.push("SPEECH_KEY (Azure Speech API 키)");
  }

  if (!SPEECH_REGION) {
    errors.push("SPEECH_REGION (Azure Speech 리전)");
  }

  if (errors.length > 0) {
    const errorMessage = `필수 환경 변수가 설정되지 않았습니다:\n- ${errors.join("\n- ")}`;
    logger.error(`[config] ${errorMessage}`);
    throw new Error(errorMessage);
  }

  logger.info(`[config] 환경 변수 검증 완료 (SPEECH_REGION=${SPEECH_REGION})`);
}
