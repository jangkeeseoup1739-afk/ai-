"""공용 유틸: 외부 실행파일 탐색, 명령 실행, 시간 변환."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

SEC_US = 1_000_000  # 1초 = 마이크로초


def which_first(*names: str) -> str | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def ffmpeg_bin() -> str:
    p = which_first("ffmpeg")
    if p:
        return p
    try:  # 테스트/개발 환경용 폴백 (pip install imageio-ffmpeg)
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    import sys

    if sys.platform == "win32":
        raise SystemExit("ffmpeg를 찾을 수 없습니다.  winget install Gyan.FFmpeg")
    raise SystemExit("ffmpeg를 찾을 수 없습니다.  brew install ffmpeg")


def run(cmd: list[str], quiet: bool = False) -> None:
    if not quiet:
        print("$ " + " ".join(str(c) for c in cmd), file=sys.stderr)
    subprocess.run([str(c) for c in cmd], check=True)


def srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ensure_dir(p: str | Path) -> Path:
    path = Path(p).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path
