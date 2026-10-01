"""윈도우/맥 차이를 한곳에 모은다.

캡컷 초안 폴더 위치, 화면 녹화 명령, 스크롤 방법이 운영체제마다 다르다.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

# 녹화 파일 확장자 (gdigrab은 mp4, screencapture는 mov)
RECORD_EXT = ".mp4" if IS_WIN else ".mov"
VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v")


def _win_draft_roots() -> list[Path]:
    roots = []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots.append(Path(local) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft")
    home = Path.home()
    roots += [
        home / "AppData" / "Local" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
        # 캡컷에서 초안 위치를 바꾼 경우 흔히 쓰이는 이름
        home / "Documents" / "CapCut Drafts",
        home / "CapCut Drafts",
    ]
    return roots


def _mac_draft_roots() -> list[Path]:
    home = Path.home()
    return [
        home / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
        home / "Movies" / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft",
    ]


def draft_root_candidates() -> list[Path]:
    if IS_WIN:
        return _win_draft_roots()
    if IS_MAC:
        return _mac_draft_roots()
    return [Path.home() / "CapCut Drafts"]


def default_draft_root() -> Path:
    """실제로 존재하는 첫 후보. 없으면 첫 후보를 그대로 돌려준다(오류 메시지용)."""
    cands = draft_root_candidates()
    for p in cands:
        if p.is_dir():
            return p
    return cands[0]


def draft_root_help() -> str:
    lines = ["캡컷 초안 폴더를 찾지 못했습니다. 찾아본 곳:"]
    lines += [f"  - {p}" for p in draft_root_candidates()]
    lines.append("캡컷을 한 번 실행해 프로젝트를 만들거나, --draft-root 로 직접 지정하세요.")
    if IS_WIN:
        lines.append("캡컷 설정에서 초안 위치를 바꿨다면 그 경로를 주면 됩니다.")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# 브라우저 / 화면 녹화 / 스크롤
# --------------------------------------------------------------------------

def open_browser_cmd(url: str) -> list[str]:
    """크롬으로 연다. 없으면 기본 브라우저로 떨어진다."""
    if IS_WIN:
        # start 는 cmd 내장 명령이고, 첫 따옴표 인자를 창 제목으로 먹으므로 "" 를 넣는다
        return ["cmd", "/c", "start", "", "chrome", url]
    if IS_MAC:
        return ["open", "-a", "Google Chrome", "--new", url]
    return ["xdg-open", url]


def record_cmd(dest: Path, seconds: float, *, rect: str = "",
               ffmpeg: str = "ffmpeg", framerate: int = 30) -> list[str]:
    """화면을 녹화하는 명령. rect 는 "x,y,w,h" 형식."""
    if IS_WIN:
        cmd = [ffmpeg, "-y", "-v", "error", "-f", "gdigrab",
               "-framerate", str(framerate), "-t", f"{seconds:.2f}"]
        if rect:
            x, y, w, h = [p.strip() for p in rect.split(",")]
            cmd += ["-offset_x", x, "-offset_y", y, "-video_size", f"{w}x{h}"]
        cmd += ["-i", "desktop", "-pix_fmt", "yuv420p", "-c:v", "libx264",
                "-preset", "ultrafast", str(dest)]
        return cmd
    if IS_MAC:
        cmd = ["screencapture", "-v", "-V", f"{seconds:.0f}", "-x"]
        if rect:
            cmd += ["-R", rect]
        cmd.append(str(dest))
        return cmd
    # 리눅스 (테스트/개발용)
    cmd = [ffmpeg, "-y", "-v", "error", "-f", "x11grab",
           "-framerate", str(framerate), "-t", f"{seconds:.2f}"]
    if rect:
        x, y, w, h = [p.strip() for p in rect.split(",")]
        cmd += ["-video_size", f"{w}x{h}"]
        cmd += ["-i", f":0.0+{x},{y}"]
    else:
        cmd += ["-i", ":0.0"]
    cmd += ["-pix_fmt", "yuv420p", str(dest)]
    return cmd


_WIN_SCROLL = (
    "$w = New-Object -ComObject wscript.shell; "
    "$null = $w.AppActivate('Chrome'); "
    "$w.SendKeys('{DOWN}')"
)
_MAC_SCROLL = 'tell application "System Events" to key code 125'


def scroll_cmd() -> list[str]:
    """활성 창을 한 칸 아래로 스크롤하는 명령."""
    if IS_WIN:
        return ["powershell", "-NoProfile", "-NonInteractive", "-Command", _WIN_SCROLL]
    if IS_MAC:
        return ["osascript", "-e", _MAC_SCROLL]
    return []


def scroll_permission_hint() -> str:
    if IS_WIN:
        return ("스크롤이 안 되면 크롬 창이 맨 앞에 있는지 확인하세요. "
                "PowerShell 실행 정책이 막으면 --no-scroll 로 끄면 됩니다.")
    if IS_MAC:
        return ("스크롤에는 손쉬운 사용 권한이 필요합니다 "
                "(시스템 설정 → 개인정보 보호 및 보안 → 손쉬운 사용).")
    return ""


def record_permission_hint() -> str:
    if IS_WIN:
        return "gdigrab은 별도 권한이 필요 없지만, 녹화될 화면에 개인정보가 없는지 확인하세요."
    if IS_MAC:
        return ("화면 기록 권한이 필요합니다 "
                "(시스템 설정 → 개인정보 보호 및 보안 → 화면 기록).")
    return ""


def can_record() -> bool:
    return IS_WIN or IS_MAC


def find_recording(directory: Path, stem: str) -> Path | None:
    """확장자를 가리지 않고 녹화 파일을 찾는다 (직접 녹화한 경우 대비)."""
    directory = Path(directory)
    for ext in VIDEO_EXTS:
        p = directory / (stem + ext)
        if p.exists():
            return p
    hits = sorted(q for q in directory.glob(stem + ".*")
                  if q.suffix.lower() in VIDEO_EXTS)
    return hits[0] if hits else None


def run_quiet(cmd: list[str], timeout: float = 5.0) -> bool:
    try:
        subprocess.run(cmd, check=False, capture_output=True, timeout=timeout)
        return True
    except Exception:
        return False
