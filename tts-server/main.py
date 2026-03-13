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
    "child":        "A cute and innocent child voice around 5-7 years old, high-pitched with a lisp, cheerful and playful tone, slightly clumsy pronunciation",
    "grandma":      "A warm and gentle elderly woman voice in her 70s, soft and caring tone, slow and deliberate pace, slightly raspy with age",
    "rocker":       "A raspy and powerful male rock singer voice in his 30s, aggressive and intense tone, raw vocal texture with slight growl, loud and rebellious attitude",
    "gangster":     "A deep and intimidating male voice in his 40s, sharp and commanding tone, moderate pace with strong emphasis, clear and powerful projection",
    "otaku":        "A nasally and excitable young male voice in his 20s, fast-paced and enthusiastic, high energy with awkward social tone, nerdy and passionate",
    "anime_girl":   "A very high-pitched cute female voice in her teens, exaggerated cheerful intonation, sweet and bubbly with dramatic emotional shifts, kawaii style",
    "anime_boy":    "A bright and confident young male voice in his late teens, heroic and determined tone, energetic with dramatic flair, shounen protagonist style",
    "game_hero":    "A strong and commanding male voice in his 30s, noble and courageous tone, clear and powerful projection, epic fantasy hero with unwavering resolve",
    "game_villain":    "A sinister and elegant male voice in his 40s, cold and calculating tone, smooth yet threatening delivery, dark charisma with subtle menace",
    "narrator":        "A rich and resonant male voice in his 50s, authoritative and captivating storytelling tone, measured pace with dramatic emphasis, documentary narrator style",
    # 추가 캐릭터
    "angry_auntie":    "An aggressive and sharp middle-aged Korean woman in her 50s, loud and scolding tone, fast and nagging speech, high-pitched complaints with strong emphasis",
    "foreigner":       "A non-native Korean speaker with a strong Southeast Asian accent, broken rhythm, uncertain intonation, friendly but clearly struggling with pronunciation",
    "robot":           "Monotone, synthetic, robotic voice with no emotional inflection, metallic tint, steady pace, high clarity, non-human delivery with artificial cadence",
    "human_theater_m": "A warm and emotional male documentary narrator in his 50s, slow and thoughtful pace, deeply empathetic tone, Korean human interest story style with heartfelt gravitas",
    "human_theater_f": "A warm and gentle female documentary narrator in her 40s, soft and emotional delivery, slow contemplative pace, Korean human interest story style with tender compassion",
    "starcraft_dragon":"A deep, ancient and commanding dragon voice, slow and majestic delivery, resonant and powerful projection, otherworldly authority with a hint of menace",
    "homeshopping":    "An enthusiastic and urgent female home shopping host in her 30s, rapid high-energy delivery, dramatic emphasis on deals, bright and persuasive tone",
    "drill_sergeant":  "A loud and authoritative military drill instructor, sharp staccato delivery, commanding and strict tone, powerful projection with intense discipline",
    "drunk_boss":      "A cheerful and slightly slurred middle-aged male voice, loose and rambling speech, warm but unfocused delivery, happy-drunk energy with occasional chuckling",
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
    cache_key = hashlib.sha256(f"v3:{text}:{voice_id}:{speed}:{pitch}".encode()).hexdigest()
    ogg_path = CACHE_DIR / f"{cache_key}.ogg"

    if ogg_path.exists():
        return FileResponse(str(ogg_path), media_type="audio/ogg")

    wav_path = CACHE_DIR / f"{cache_key}.wav"

    # instruct 프롬프트 구성
    instruct = VOICE_PRESETS[voice_id] + speed_to_instruct(speed)

    # voice_id별 고정 시드 → 일관된 음색 유지
    voice_seed = hash(voice_id) & 0x7FFFFFFF

    config = TTSConfig(
        temperature=0.3,        # 낮출수록 안정적 (늘어짐/소리지름 방지)
        sub_temperature=0.3,
        top_k=15,               # 후보 토큰 제한 → 이상한 음성 억제
        sub_top_k=15,
        top_p=0.85,
        sub_top_p=0.85,
        repeat_penalty=1.15,    # 반복 패턴 억제
        seed=voice_seed,
        sub_seed=voice_seed,
        max_steps=400,
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
