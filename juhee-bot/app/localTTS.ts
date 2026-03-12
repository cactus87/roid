/**
 * @fileoverview 로컬 XTTS-v2 TTS 클라이언트
 * @description 로컬 Python FastAPI 서버에 HTTP 요청으로 TTS 생성
 */

import { PassThrough } from "stream";
import { logger } from "./logger.js";
import { TTS_SERVER_URL } from "./config.js";

/**
 * 로컬 TTS 서버에서 음성 합성 스트림을 가져옴
 *
 * @param textData   - 변환할 텍스트
 * @param callback   - (stream: PassThrough | null) => void
 * @param voiceName  - voice_id (female_a, male_a 등, 기본값: female_a)
 * @param speed      - 0~100 속도 (기본값: 30)
 * @param pitch      - x-low / low / medium / high / x-high (기본값: medium)
 */
async function localTTS(
  textData: string,
  callback: (stream: PassThrough | null) => void,
  voiceName: string = "female_a",
  speed: number = 30,
  pitch?: string
): Promise<void> {
  try {
    const params = new URLSearchParams({
      text: textData,
      voice_id: voiceName,
      speed: String(speed),
      pitch: pitch ?? "medium",
    });

    const res = await fetch(`${TTS_SERVER_URL}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
    });

    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(`TTS 서버 응답 오류 [${res.status}]: ${errText}`);
    }

    const buffer = Buffer.from(await res.arrayBuffer());
    const stream = new PassThrough();
    stream.end(buffer);
    callback(stream);
  } catch (e) {
    logger.error("❌ localTTS 실패:", e);
    callback(null);
  }
}

export default localTTS;
