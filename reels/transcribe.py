"""1단계: 영상에서 음성을 뽑아 whisper.cpp로 받아쓰기."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .util import SEC_US, ensure_dir, ffmpeg_bin, run, whisper_bin

DEFAULT_MODEL = Path("~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin").expanduser()


def extract_audio(src: Path, wav: Path) -> Path:
    """whisper.cpp가 요구하는 16kHz mono 16bit wav로 변환."""
    run([ffmpeg_bin(), "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", wav])
    return wav


def run_whisper(wav: Path, model: Path, lang: str, prefix: Path,
                threads: int = 0, beam: int = 5) -> Path:
    if not Path(model).exists():
        raise SystemExit(
            f"whisper 모델이 없습니다: {model}\n"
            "  curl -L -o ~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin \\\n"
            "    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/"
            "ggml-large-v3-turbo-q5_0.bin"
        )
    cmd = [whisper_bin(), "-m", model, "-f", wav, "-l", lang,
           "-oj", "-of", prefix, "-pp", "-bs", beam]
    if threads:
        cmd += ["-t", threads]
    run(cmd)
    out = Path(str(prefix) + ".json")
    if not out.exists():
        raise SystemExit(f"whisper 출력 JSON을 찾을 수 없습니다: {out}")
    return out


def load_whisper_json(path: Path) -> list[dict]:
    """whisper.cpp -oj 결과를 {id,start,end,text} 리스트로 정규화 (초 단위)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    segments = []
    for i, item in enumerate(data.get("transcription", [])):
        off = item.get("offsets") or {}
        text = (item.get("text") or "").strip()
        if not text:
            continue
        segments.append({
            "id": i,
            "start": off.get("from", 0) / 1000.0,   # ms -> s
            "end": off.get("to", 0) / 1000.0,
            "text": text,
        })
    return segments


def transcribe(src: Path, workdir: Path, model: Path = DEFAULT_MODEL,
               lang: str = "ko", threads: int = 0, beam: int = 5) -> list[dict]:
    src = Path(src).expanduser()
    if not src.exists():
        raise SystemExit(f"입력 영상이 없습니다: {src}")
    work = ensure_dir(workdir)
    wav = work / "audio.wav"
    extract_audio(src, wav)
    js = run_whisper(wav, Path(model).expanduser(), lang, work / "whisper", threads, beam)
    segments = load_whisper_json(js)
    (work / "segments.json").write_text(
        json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    return segments
