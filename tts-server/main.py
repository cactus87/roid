"""
로컬 Qwen3-TTS GGUF TTS 서버
FastAPI + Qwen3-TTS-GGUF (llama.cpp) + RTX GPU → OGG Opus 출력
"""

import os
import sys
import hashlib
import asyncio
from pathlib import Path

import numpy as np
import soundfile as sf
import ffmpeg

# ffmpeg 실행 파일 경로 명시
os.environ["PATH"] = r"C:\base_app\FFmpeg\bin" + os.pathsep + os.environ.get("PATH", "")

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

# GGUF 추론 엔진 (Qwen3-TTS-GGUF)
GGUF_PROJECT = Path(r"C:\ai\Qwen3-TTS-GGUF")
sys.path.insert(0, str(GGUF_PROJECT))
# GGUF venv의 site-packages 추가
sys.path.insert(0, str(GGUF_PROJECT / "venv" / "Lib" / "site-packages"))

os.chdir(GGUF_PROJECT)  # TTSEngine이 CWD 기준 model_dir 사용
from qwen3_tts_gguf.inference import TTSEngine, TTSConfig

# ── 초기 설정 ────────────────────────────────────────────────
CACHE_DIR = Path(r"C:\ai\tts-bot\tts-server\.ttsCache")
CACHE_DIR.mkdir(exist_ok=True)

# 음성 프리셋: voice_id → VoiceDesign instruct 프롬프트
VOICE_PRESETS: dict[str, str] = {
    # 기본 음성
    "female_a": "A calm and clear female voice in her 20s, friendly and stable tone, moderate speaking pace",
    "female_b": "A bright and energetic female voice in her 20s, expressive and cheerful speech style",
    "female_c": "A female news anchor voice in her 30s, professional and precise pronunciation",
    "male_a":   "A calm and deep male voice in his 30s, trustworthy and gentle tone",
    "male_b":   "A relaxed and natural male voice in his 20s, friendly and casual speech style",
    "male_c":   "A deep and mature male voice in his 40s, clear and weighty narration style",
    # 캐릭터 음성
    "child":        "A cute and cheerful child voice around 7 years old, high-pitched and bright tone, playful and innocent speech style",
    "grandma":      "A warm and gentle elderly woman voice in her 70s, soft and caring tone, slow and deliberate pace, slightly low pitch",
    "rocker":       "A strong and bold male voice in his 30s, confident and intense tone, powerful projection, rock singer style with clear enunciation",
    "gangster":     "A deep and firm male voice in his 40s, sharp and commanding tone, moderate pace with strong emphasis, clear and powerful projection",
    "otaku":        "A slightly high-pitched young male voice in his 20s, fast-paced and enthusiastic, energetic and passionate speech style",
    "anime_girl":   "A high-pitched cute female voice in her teens, cheerful and sweet intonation, bubbly and expressive tone, bright and lively delivery",
    "anime_boy":    "A bright and confident young male voice in his late teens, heroic and determined tone, energetic and clear delivery",
    "game_hero":    "A strong and commanding male voice in his 30s, noble and courageous tone, clear and powerful projection, confident and resolute delivery",
    "game_villain":    "A low-pitched and elegant male voice in his 40s, cold and calm tone, smooth and controlled delivery, sophisticated and composed",
    "narrator":        "A rich and resonant male voice in his 50s, authoritative and captivating storytelling tone, measured pace, documentary narrator style",
    # 추가 캐릭터
    "angry_auntie":    "A sharp and stern middle-aged female voice in her 50s, high-pitched and firm tone, fast speaking pace with strong emphasis, scolding speech style",
    "foreigner":       "A warm and friendly male voice in his 30s with a distinct accent, slightly uneven rhythm, clear but non-native pronunciation",
    "robot":           "A flat and steady male voice with no emotional inflection, even pace, high clarity, precise and uniform delivery",
    "human_theater_m": "A warm and emotional male narrator in his 50s, slow and thoughtful pace, empathetic and sincere tone, documentary storytelling style",
    "human_theater_f": "A warm and gentle female narrator in her 40s, soft and emotional delivery, slow and contemplative pace, sincere storytelling style",
    "starcraft_dragon":"A deep and commanding male voice in his 50s, slow and majestic delivery, resonant and powerful projection, ancient authority",
    "homeshopping":    "An enthusiastic and energetic female voice in her 30s, fast speaking pace, bright and persuasive tone, confident product presentation style",
    "drill_sergeant":  "A firm and authoritative male voice in his 40s, clear and sharp delivery, commanding and strict tone, strong projection with discipline",
    "drunk_boss":      "A cheerful and relaxed middle-aged male voice in his 40s, slow and casual speech, warm and friendly tone, easygoing delivery",
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
    return ""


# ── GGUF 엔진 로드 ───────────────────────────────────────────
print("🔄 Qwen3-TTS GGUF 엔진 초기화 중...")
tts_engine = TTSEngine(model_dir="model-design", onnx_provider="CUDA", verbose=True)
print("✅ GGUF 엔진 로드 완료")

# ── FastAPI 앱 ───────────────────────────────────────────────
app = FastAPI(title="로컬 Qwen3-TTS GGUF 서버")

# 동시 요청 직렬화용 Lock
_tts_lock = asyncio.Lock()


@app.post("/tts")
async def synthesize(request: Request):
    """
    텍스트를 음성으로 변환하여 OGG Opus 파일로 반환.

    Parameters
    ----------
    text     : 변환할 텍스트
    voice_id : VOICE_PRESETS 키
    speed    : 0~100
    pitch    : x-low / low / medium / high / x-high
    """
    # raw bytes로 읽어 UTF-8 강제 디코딩
    raw = await request.body()
    from urllib.parse import parse_qs
    params = parse_qs(raw.decode("utf-8"))
    text     = params.get("text",     [""])[0]
    voice_id = params.get("voice_id", ["female_a"])[0]
    speed    = int(params.get("speed", ["30"])[0])
    pitch    = params.get("pitch",    ["medium"])[0]

    if voice_id not in VOICE_PRESETS:
        raise HTTPException(status_code=400, detail=f"알 수 없는 voice_id: {voice_id}")
    if pitch not in PITCH_SEMITONES:
        raise HTTPException(status_code=400, detail=f"알 수 없는 pitch: {pitch}")

    # 캐시 키
    cache_key = hashlib.sha256(f"v4:{text}:{voice_id}:{speed}:{pitch}".encode()).hexdigest()
    ogg_path = CACHE_DIR / f"{cache_key}.ogg"

    if ogg_path.exists():
        return FileResponse(str(ogg_path), media_type="audio/ogg")

    wav_path = CACHE_DIR / f"{cache_key}.wav"

    # instruct 프롬프트 구성
    instruct = VOICE_PRESETS[voice_id] + speed_to_instruct(speed)

    # voice_id별 고정 시드 → 일관된 음색 유지
    voice_seed = hash(voice_id) & 0x7FFFFFFF

    config = TTSConfig(
        temperature=0.7,        # 공식 기본 0.9, 낮출수록 안정적이나 기계적
        sub_temperature=0.5,    # 낮추면 속도 떨림/전자음 감소
        top_k=50,               # 공식 기본값
        sub_top_k=50,
        top_p=1.0,              # 공식 기본값
        sub_top_p=1.0,
        min_p=0.05,             # 저확률 노이즈/전자음 필터링
        repeat_penalty=1.05,    # 공식 기본값
        seed=voice_seed,
        sub_seed=voice_seed,
        max_steps=300,          # 공식 기본값
        streaming=False,
    )

    # GPU 직렬화 (요청마다 새 스트림 → 동시 요청 간 상태 충돌 방지)
    async with _tts_lock:
        stream = tts_engine.create_stream()
        result = stream.design(text=text, instruct=instruct, config=config)
        stream.join()

    # WAV 저장 (GGUF 출력 샘플레이트 고정 24000Hz)
    wav_np = result.audio.astype(np.float32)
    sr = 24000
    sf.write(str(wav_path), wav_np, sr, subtype='PCM_16')

    # ffmpeg: WAV → OGG Opus + pitch shift
    semitones = PITCH_SEMITONES[pitch]
    try:
        stream = ffmpeg.input(str(wav_path)).audio
        if semitones != 0:
            shifted_rate = int(sr * (2 ** (semitones / 12)))
            stream = stream.filter("asetrate", shifted_rate).filter("aresample", 48000)
        stream.output(str(ogg_path), codec="libopus").run(overwrite_output=True, quiet=True)
    finally:
        if wav_path.exists():
            wav_path.unlink()

    return FileResponse(str(ogg_path), media_type="audio/ogg")


@app.get("/voices")
async def list_voices():
    return {"voices": list(VOICE_PRESETS.keys()), "pitch_options": list(PITCH_SEMITONES.keys())}


@app.get("/health")
async def health():
    return {"status": "ok", "engine": "gguf"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)
