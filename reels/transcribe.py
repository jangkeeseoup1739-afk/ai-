"""1단계: faster-whisper로 받아쓰기.

faster-whisper는 영상 파일을 그대로 읽으므로 ffmpeg로 음성을 따로 뽑지 않는다.
모델은 처음 한 번만 자동으로 내려받아 캐시에 둔다.
"""
from __future__ import annotations

import json
from pathlib import Path

from .util import ensure_dir

DEFAULT_MODEL = "large-v3-turbo"
DEFAULT_CACHE = Path("~/.cache/reels-whisper").expanduser()


def _pick_compute(device: str) -> tuple[str, str]:
    """쓸 수 있는 장치와 연산 정밀도를 고른다."""
    if device != "auto":
        return device, ("float16" if device == "cuda" else "int8")
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def transcribe(src: Path, workdir: Path, model: str = DEFAULT_MODEL,
               lang: str = "ko", beam: int = 5, device: str = "auto",
               cache: Path = DEFAULT_CACHE, vad: bool = True) -> list[dict]:
    """{id, start, end, text} 목록을 돌려주고 segments.json 으로도 남긴다."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit(
            "faster-whisper가 없습니다.\n"
            "  pip install faster-whisper"
        )

    src = Path(src).expanduser()
    if not src.exists():
        raise SystemExit(f"입력 영상이 없습니다: {src}")
    work = ensure_dir(workdir)

    device, compute = _pick_compute(device)
    print(f"      모델 {model} / {device} / {compute}", flush=True)

    whisper = WhisperModel(model, device=device, compute_type=compute,
                           download_root=str(Path(cache).expanduser()))
    # vad_filter가 긴 무음을 미리 잘라내 헛인식을 줄인다
    result, info = whisper.transcribe(
        str(src), language=lang, beam_size=beam, vad_filter=vad,
        condition_on_previous_text=False,
    )

    segments = []
    for i, seg in enumerate(result):          # 제너레이터라 여기서 실제로 돈다
        text = (seg.text or "").strip()
        if not text:
            continue
        segments.append({"id": len(segments), "start": float(seg.start),
                         "end": float(seg.end), "text": text})
        if i % 10 == 0:
            print(f"      {seg.end:6.1f}초까지 받아쓰는 중...", flush=True)

    (work / "segments.json").write_text(
        json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    dur = getattr(info, "duration", 0.0) or 0.0
    print(f"      {len(segments)}구간 / 영상 {dur:.1f}초", flush=True)
    return segments


def load_segments(path: Path) -> list[dict]:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
