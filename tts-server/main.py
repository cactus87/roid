"""
로컬 Qwen3-TTS VoiceDesign TTS 서버
FastAPI + Qwen3-TTS-1.7B-VoiceDesign + RTX GPU → OGG Opus 출력
speaker_wav 없이 텍스트 설명만으로 음성 생성
"""

import os
import hashlib
import asyncio
from pathlib import Path

import torch
import soundfile as sf
import numpy as np
import ffmpeg

# ffmpeg 실행 파일 경로 명시 (PATH에 없는 경우)
os.environ.setdefault("PATH", "")
os.environ["PATH"] = r"C:\base_app\FFmpeg\bin" + os.pathsep + os.environ["PATH"]
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse
from qwen_tts import Qwen3TTSModel

# ── 초기 설정 ────────────────────────────────────────────────
CACHE_DIR = Path(".ttsCache")
CACHE_DIR.mkdir(exist_ok=True)

# 음성 프리셋: voice_id → VoiceDesign instruct 프롬프트
VOICE_PRESETS: dict[str, str] = {
    "female_a": "A calm and clear female voice in her 20s, friendly and stable tone, moderate speaking pace",
    "female_b": "A bright and energetic female voice in her 20s, expressive and cheerful speech style",
    "female_c": "A female news anchor voice in her 30s, professional and precise pronunciation",
    "male_a":   "A calm and deep male voice in his 30s, trustworthy and gentle tone",
    "male_b":   "A relaxed and natural male voice in his 20s, friendly and casual speech style",
    "male_c":   "A deep and mature male voice in his 40s, clear and weighty narration style",
}

# 피치: 반음(semitone) 단위
PITCH_SEMITONES: dict[str, int] = {
    "x-low": -4,
    "low":   -2,
    "medium": 0,
    "high":   2,
    "x-high": 4,
}


def speed_to_instruct(speed: int) -> str:
    """speed(0~100) → VoiceDesign instruct 접미사"""
    if speed <= 30:
        return ", slow speaking pace"
    if speed >= 70:
        return ", fast speaking pace"
    return ""  # 기본 속도


# ── 모델 로드 ────────────────────────────────────────────────
print("🔄 Qwen3-TTS VoiceDesign 모델 로드 중... (첫 실행 시 HuggingFace에서 자동 다운로드)")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️  장치: {device}")

tts_model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    device_map="cuda" if torch.cuda.is_available() else "cpu",
    dtype=torch.bfloat16,
)
print("✅ 모델 로드 완료")

# ── FastAPI 앱 ───────────────────────────────────────────────
app = FastAPI(title="로컬 Qwen3-TTS VoiceDesign 서버")

# 동시 요청 직렬화용 Lock (GPU VRAM 경합 방지)
_tts_lock = asyncio.Lock()


@app.post("/tts")
async def synthesize(request: Request):
    """
    텍스트를 음성으로 변환하여 OGG Opus 파일로 반환.

    Parameters
    ----------
    text     : 변환할 텍스트
    voice_id : VOICE_PRESETS 키 (female_a / male_a 등)
    speed    : 0~100 (0=느림, 100=빠름) → VoiceDesign instruct 접미사로 변환
    pitch    : x-low / low / medium / high / x-high
    """
    # raw bytes로 읽어 UTF-8 강제 디코딩 (uvicorn 인코딩 오류 방지)
    raw = await request.body()
    from urllib.parse import parse_qs
    params = parse_qs(raw.decode("utf-8"))
    text     = params.get("text",     [""])[0]
    voice_id = params.get("voice_id", ["female_a"])[0]
    speed    = int(params.get("speed", ["30"])[0])
    pitch    = params.get("pitch",    ["medium"])[0]

    # 유효성 검사
    if voice_id not in VOICE_PRESETS:
        raise HTTPException(status_code=400, detail=f"알 수 없는 voice_id: {voice_id}. 사용 가능: {list(VOICE_PRESETS.keys())}")
    if pitch not in PITCH_SEMITONES:
        raise HTTPException(status_code=400, detail=f"알 수 없는 pitch: {pitch}")

    # 캐시 키 계산 (v2: XTTS 캐시와 분리)
    cache_key = hashlib.sha256(f"v2:{text}:{voice_id}:{speed}:{pitch}".encode()).hexdigest()
    ogg_path = CACHE_DIR / f"{cache_key}.ogg"

    if ogg_path.exists():
        return FileResponse(str(ogg_path), media_type="audio/ogg")

    wav_path = CACHE_DIR / f"{cache_key}.wav"

    # instruct 프롬프트 구성 (음성 프리셋 + 속도 접미사)
    instruct = VOICE_PRESETS[voice_id] + speed_to_instruct(speed)

    # GPU 직렬화: 동시에 여러 요청이 와도 순차 처리 (동기 호출)
    async with _tts_lock:
        result = tts_model.generate_voice_design(
            text=text,
            language="Auto",
            instruct=instruct,
        )

    wavs, sr = result  # wavs: List[np.ndarray], sr: int
    wav_np = wavs[0].astype(np.float32)  # 첫 번째 결과, 1D mono

    # soundfile로 임시 WAV 저장
    sf.write(str(wav_path), wav_np, sr, subtype='PCM_16')

    # ffmpeg: WAV → OGG Opus + pitch shift
    semitones = PITCH_SEMITONES[pitch]
    try:
        stream = ffmpeg.input(str(wav_path)).audio
        if semitones != 0:
            # asetrate로 pitch shift → aresample로 48kHz 복구 (sr은 모델 출력 샘플레이트)
            shifted_rate = int(sr * (2 ** (semitones / 12)))
            stream = stream.filter("asetrate", shifted_rate).filter("aresample", 48000)
        stream.output(str(ogg_path), codec="libopus").run(overwrite_output=True, quiet=True)
    finally:
        if wav_path.exists():
            wav_path.unlink()

    return FileResponse(str(ogg_path), media_type="audio/ogg")


@app.get("/voices")
async def list_voices():
    """사용 가능한 voice_id 목록 반환"""
    return {
        "voices": list(VOICE_PRESETS.keys()),
        "pitch_options": list(PITCH_SEMITONES.keys()),
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok", "device": device}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)
