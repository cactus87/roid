/**
 * @fileoverview Edge TTS 연동 (무료, API 키 불필요)
 * @description Microsoft Edge의 읽기 기능 API를 사용한 텍스트 음성 변환
 * @author forked from kevin1113dev's msTTS.ts, converted to Edge TTS
 */

import { MsEdgeTTS, OUTPUT_FORMAT } from "msedge-tts";
import { PassThrough, Readable } from "stream";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

import dotenv from "dotenv";
import { logger } from "./logger.js";

dotenv.config();

/** 기본 TTS 음성 */
const DEFAULT_VOICE: string = "SeoHyeonNeural";

type TtsCacheStats = {
  hits: number;
  misses: number;
  inflightWaits: number;
  errors: number;
};

declare global {
  // eslint-disable-next-line no-var
  var __juheeTtsCacheStats: TtsCacheStats | undefined;
}

function getTtsCacheStats(): TtsCacheStats {
  if (!globalThis.__juheeTtsCacheStats) {
    globalThis.__juheeTtsCacheStats = {
      hits: 0,
      misses: 0,
      inflightWaits: 0,
      errors: 0,
    };
  }
  return globalThis.__juheeTtsCacheStats;
}

function getShardIdForStats(): string {
  const shardId = process.env.SHARD_ID;
  if (shardId && shardId.trim().length > 0) return shardId.trim();

  const shards = process.env.SHARDS;
  if (shards && shards.trim().length > 0) {
    const first = shards.split(",")[0]?.trim();
    if (first) return first;
  }

  return "single";
}

function getStatsFilePath(): string {
  if (process.env.TTS_STATS_FILE && process.env.TTS_STATS_FILE.trim().length) {
    return path.resolve(process.env.TTS_STATS_FILE);
  }
  const shardId = getShardIdForStats();
  return path.join(TTS_CACHE_DIR, `tts-stats-${shardId}.json`);
}

let statsLoaded = false;
function loadPersistedStatsOnce() {
  if (statsLoaded) return;
  statsLoaded = true;

  try {
    ensureCacheDir();
    if (!cacheDirReady) return;

    const statsPath = getStatsFilePath();
    if (!fs.existsSync(statsPath)) return;

    const raw = fs.readFileSync(statsPath, "utf8");
    const parsed = JSON.parse(raw);
    const stats = getTtsCacheStats();
    stats.hits = Number(parsed?.hits ?? stats.hits) || 0;
    stats.misses = Number(parsed?.misses ?? stats.misses) || 0;
    stats.inflightWaits = Number(parsed?.inflightWaits ?? stats.inflightWaits) || 0;
    stats.errors = Number(parsed?.errors ?? stats.errors) || 0;
  } catch (e) {
    logger.warn("⚠️ TTS 캐시 통계 로드 실패:", e);
  }
}

let flushTimer: NodeJS.Timeout | null = null;
let lastFlushAt = 0;

async function flushStatsToDisk() {
  try {
    ensureCacheDir();
    if (!cacheDirReady) return;

    const stats = getTtsCacheStats();
    const statsPath = getStatsFilePath();
    const payload = {
      hits: stats.hits,
      misses: stats.misses,
      inflightWaits: stats.inflightWaits,
      errors: stats.errors,
      updatedAt: new Date().toISOString(),
      pid: process.pid,
    };

    const tmpPath = `${statsPath}.tmp-${process.pid}-${Date.now()}`;
    await fs.promises.writeFile(tmpPath, JSON.stringify(payload));
    await fs.promises.rename(tmpPath, statsPath);
    lastFlushAt = Date.now();
  } catch (e) {
    logger.warn("⚠️ TTS 캐시 통계 저장 실패:", e);
  }
}

function scheduleStatsFlush() {
  const MIN_INTERVAL_MS = 5000;
  const DEBOUNCE_MS = 1000;
  const now = Date.now();
  const waitMs = Math.max(DEBOUNCE_MS, MIN_INTERVAL_MS - (now - lastFlushAt));

  if (flushTimer) return;
  flushTimer = setTimeout(async () => {
    flushTimer = null;
    await flushStatsToDisk();
  }, waitMs);
}

/**
 * TTS 오디오 캐시 디렉토리
 */
const TTS_CACHE_DIR: string = process.env.TTS_CACHE_DIR
  ? path.resolve(process.env.TTS_CACHE_DIR)
  : path.join(process.cwd(), ".ttsCache");

/** 캐시 파일 최대 보관 기간 (일). 0 이하면 만료 체크 안 함 */
const TTS_CACHE_MAX_AGE_DAYS: number = (() => {
  const raw = process.env.TTS_CACHE_MAX_AGE_DAYS ?? "30";
  const parsed = parseInt(raw, 10);
  return Number.isFinite(parsed) ? parsed : 30;
})();

/** 동일 요청 동시 합성 중복 방지 */
const inFlightSynthesis: Map<string, Promise<Buffer>> = new Map();

let cacheDirReady = false;

function ensureCacheDir() {
  if (cacheDirReady) return;
  try {
    fs.mkdirSync(TTS_CACHE_DIR, { recursive: true });
    cacheDirReady = true;
  } catch (e) {
    logger.warn("⚠️ TTS 캐시 디렉토리 생성 실패:", e);
  }
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function bufferToStream(buffer: Buffer): PassThrough {
  const stream = new PassThrough();
  stream.end(buffer);
  return stream;
}

function fileToStream(filePath: string): PassThrough {
  const stream = new PassThrough();
  const rs = fs.createReadStream(filePath);
  rs.on("error", (e) => stream.destroy(e));
  rs.pipe(stream);
  return stream;
}

function sha256Hex(input: string): string {
  return crypto.createHash("sha256").update(input).digest("hex");
}

async function isCacheValid(filePath: string): Promise<boolean> {
  try {
    const stat = await fs.promises.stat(filePath);
    if (TTS_CACHE_MAX_AGE_DAYS <= 0) return true;
    const maxAgeMs = TTS_CACHE_MAX_AGE_DAYS * 24 * 60 * 60 * 1000;
    const ageMs = Date.now() - stat.mtimeMs;
    if (ageMs <= maxAgeMs) return true;
    await fs.promises.unlink(filePath).catch(() => undefined);
    return false;
  } catch {
    return false;
  }
}

async function writeCacheAtomic(filePath: string, data: Buffer) {
  try {
    ensureCacheDir();
    if (!cacheDirReady) return;
    if (fs.existsSync(filePath)) return;

    const tmpPath = `${filePath}.tmp-${process.pid}-${Date.now()}`;
    await fs.promises.writeFile(tmpPath, data);
    await fs.promises.rename(tmpPath, filePath);
  } catch (e) {
    logger.warn("⚠️ TTS 캐시 저장 실패:", e);
  }
}

/**
 * Edge TTS로 텍스트를 음성 버퍼로 합성 (재시도 포함)
 */
async function synthesizeWithRetry(
  voice: string,
  textData: string,
  speed: number,
  pitch: string | undefined,
  maxRetries: number
): Promise<Buffer> {
  let attempt = 0;

  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      const tts = new MsEdgeTTS();
      await tts.setMetadata(voice, OUTPUT_FORMAT.WEBM_24KHZ_16BIT_MONO_OPUS);

      const prosodyOptions: { rate: string; pitch?: string } = {
        rate: `+${speed ?? 30}%`,
      };
      if (pitch && pitch !== "medium") {
        prosodyOptions.pitch = pitch;
      }

      const { audioStream } = tts.toStream(textData, prosodyOptions);

      const chunks: Buffer[] = [];
      const buffer = await new Promise<Buffer>((resolve, reject) => {
        let settled = false;
        const settle = (fn: () => void) => {
          if (!settled) { settled = true; fn(); }
        };

        // 15초 타임아웃 (Edge TTS WebSocket 응답이 안 올 때 대비)
        const timeout = setTimeout(() => {
          settle(() => {
            try { tts.close(); } catch { /* ignore */ }
            if (chunks.length > 0) {
              resolve(Buffer.concat(chunks));
            } else {
              reject(new Error("Edge TTS timeout: no audio data received"));
            }
          });
        }, 15000);

        audioStream.on("data", (chunk: Buffer) => {
          chunks.push(chunk);
        });
        audioStream.on("end", () => {
          clearTimeout(timeout);
          settle(() => resolve(Buffer.concat(chunks)));
        });
        audioStream.on("close", () => {
          clearTimeout(timeout);
          settle(() => resolve(Buffer.concat(chunks)));
        });
        audioStream.on("error", (err: Error) => {
          clearTimeout(timeout);
          settle(() => reject(err));
        });
      });

      try { tts.close(); } catch { /* ignore */ }

      if (buffer.length === 0) {
        throw new Error("Empty audio buffer from Edge TTS");
      }

      return buffer;
    } catch (e: any) {
      const message = e?.message?.toString?.() ?? String(e);

      if (attempt < maxRetries) {
        attempt += 1;
        logger.debug(`⚠️ TTS 재시도 (${attempt}/${maxRetries})`);
        await delay(1000 * attempt);
        continue;
      }

      logger.error("❌ TTS 합성 오류:", message);
      throw e;
    }
  }
}

/**
 * Edge TTS를 사용하여 텍스트를 음성으로 변환
 *
 * @param textData - 변환할 텍스트
 * @param callback - 오디오 스트림을 받을 콜백 함수
 * @param voiceName - 사용할 음성 이름 (기본값: SeoHyeonNeural)
 * @param speed - 속도 조절 (0-100, 기본값: 30)
 * @param pitch - 피치 조절 (x-low, low, medium, high, x-high 또는 Hz값)
 *
 * @remarks
 * - 언어 자동 감지 (한국어, 일본어, 영어)
 * - 오류 발생 시 최대 2번 재시도
 * - WebM Opus 형식으로 출력
 */
async function edgeTTS(
  textData: string,
  callback: Function,
  voiceName: string = DEFAULT_VOICE,
  speed: number = 30,
  pitch?: string,
) {
  const MAX_RETRIES = 2;
  const stats = getTtsCacheStats();

  try {
    loadPersistedStatsOnce();
    ensureCacheDir();

    // Edge TTS는 매우 짧은 텍스트에서 빈 버퍼를 반환할 수 있음 (최소 길이 보장)
    let processedText = textData.trim();
    if (processedText.length < 2) {
      processedText = processedText + " "; // 공백 추가
      logger.debug(`⚠️ TTS 텍스트 너무 짧음 ("${textData}") - 공백 추가`);
    }

    let language: string;
    let voice: string;
    const detectedLanguage = (voiceName == 'HyunsuMultilingualNeural') ? 'ko' : quickLanguageDetect(processedText);

    switch (detectedLanguage) {
      case "ko":
        language = "ko-KR";
        voice = language + "-" + (voiceName ?? DEFAULT_VOICE);
        break;
      case "ja":
        language = "ja-JP";
        voice = language + "-AoiNeural";
        break;
      case "en":
        language = "en-US";
        voice = language + "-AnaNeural";
        break;
      default:
        language = "ko-KR";
        voice = language + "-" + (voiceName ?? DEFAULT_VOICE);
        break;
    }

    const cacheKey = sha256Hex(
      JSON.stringify({
        v: 3,
        format: "Webm24Khz16BitMonoOpus",
        language,
        voice,
        speed,
        pitch: pitch ?? "medium",
        textData: processedText
      })
    );
    const cacheFilePath = path.join(TTS_CACHE_DIR, `${cacheKey}.webm`);

    // 캐시 히트
    if (cacheDirReady && (await isCacheValid(cacheFilePath))) {
      logger.debug(`💾 TTS 캐시 히트: ${cacheKey}`);
      stats.hits += 1;
      scheduleStatsFlush();
      if (typeof callback === "function") {
        try {
          callback(fileToStream(cacheFilePath));
        } catch (callbackError) {
          logger.error("❌ TTS 캐시 스트림 콜백 실패:", callbackError);
        }
      }
      return;
    }

    // 동일 키 동시 요청은 한 번만 합성
    let synthesisPromise = inFlightSynthesis.get(cacheKey);
    if (!synthesisPromise) {
      stats.misses += 1;
      scheduleStatsFlush();
      synthesisPromise = (async () => {
        const buffer = await synthesizeWithRetry(
          voice,
          processedText,
          speed,
          pitch,
          MAX_RETRIES
        );
        await writeCacheAtomic(cacheFilePath, buffer);
        return buffer;
      })();
      inFlightSynthesis.set(cacheKey, synthesisPromise);
    } else {
      stats.inflightWaits += 1;
      scheduleStatsFlush();
    }

    try {
      const buffer = await synthesisPromise;
      if (typeof callback === "function") {
        try {
          callback(bufferToStream(buffer));
        } catch (callbackError) {
          logger.error("❌ TTS 스트림 콜백 실패:", callbackError);
        }
      }
    } catch (e) {
      stats.errors += 1;
      scheduleStatsFlush();
      throw e;
    } finally {
      if (inFlightSynthesis.get(cacheKey) === synthesisPromise) {
        inFlightSynthesis.delete(cacheKey);
      }
    }

    return;
  } catch (error) {
    logger.error("❌ TTS 초기화 실패:", error);
    stats.errors += 1;
    scheduleStatsFlush();

    if (typeof callback === "function") {
      try {
        callback(null);
      } catch (callbackError) {
        logger.error("❌ 최종 실패 콜백 오류:", callbackError);
      }
    }
  }
}

/**
 * 빠른 로컬 언어 감지
 * API 호출 없이 정규식으로 언어 판별
 *
 * @param text - 감지할 텍스트
 * @returns 언어 코드 ('ko', 'ja', 'en')
 */
function quickLanguageDetect(text: string): string {
  const koreanRegex = /[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]/;
  const japaneseRegex = /[ひらがなカタカナ]/;
  const englishRegex = /^[a-zA-Z\s\d\.,!?]+$/;

  if (koreanRegex.test(text)) return "ko";
  if (japaneseRegex.test(text)) return "ja";
  if (englishRegex.test(text)) return "en";
  return "ko";
}

export default edgeTTS;
