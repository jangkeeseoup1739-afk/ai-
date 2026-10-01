"""환경 점검: 한 번 돌려서 붙여넣기 좋은 리포트를 낸다.

윈도우에서 실제로 되는지 확인하기 어려운 것들(초안 폴더 위치, gdigrab 녹화,
PowerShell)을 한 번에 훑는다. 실패해도 중간에 멈추지 않고 끝까지 간다.
"""
from __future__ import annotations

import os
import platform as pyplatform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import platforms

OK, WARN, FAIL, SKIP = "OK", "주의", "실패", "건너뜀"
MARK = {OK: "O", WARN: "!", FAIL: "X", SKIP: "-"}


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    lines: list[str] = field(default_factory=list)


def _run(cmd: list[str], timeout: float = 15.0) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except FileNotFoundError:
        return 127, "실행 파일 없음"
    except subprocess.TimeoutExpired:
        return 124, f"{timeout:.0f}초 안에 끝나지 않음"
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"


def _first_line(text: str) -> str:
    return text.splitlines()[0].strip() if text.strip() else ""


# --------------------------------------------------------------------------

def _version(mod: str) -> str:
    """설치된 버전을 찾는다. __version__ 이 없는 패키지도 메타데이터에서 읽는다."""
    try:
        from importlib.metadata import version

        return version(mod.replace("_", "-"))
    except Exception:
        pass
    try:
        return getattr(sys.modules[mod], "__version__", "(버전 확인 불가)")
    except Exception:
        return "(버전 확인 불가)"


def check_system() -> Check:
    lines = [
        f"OS: {pyplatform.platform()}",
        f"sys.platform: {sys.platform}",
        f"Python: {pyplatform.python_version()} ({sys.executable})",
    ]
    in_venv = sys.prefix != sys.base_prefix
    venv = os.environ.get("VIRTUAL_ENV") or (sys.prefix if in_venv else "")
    lines.append(f"가상환경: {venv or '(없음 - 시스템 파이썬)'}")
    if sys.version_info < (3, 10):
        return Check("시스템", FAIL, "Python 3.10 이상이 필요합니다", lines)
    return Check("시스템", OK, lines=lines)


def check_tools() -> Check:
    lines, missing = [], []
    for name, args in (("ffmpeg", ["-version"]), ("yt-dlp", ["--version"])):
        path = shutil.which(name)
        if not path:
            lines.append(f"{name}: 없음 (PATH에서 못 찾음)")
            missing.append(name)
            continue
        _, out = _run([path] + args, timeout=20)
        lines.append(f"{name}: {_first_line(out)[:70]}")
        lines.append(f"  {path}")
    if missing:
        if platforms.IS_WIN:
            hint = "winget install Gyan.FFmpeg / winget install yt-dlp.yt-dlp"
        elif platforms.IS_MAC:
            hint = "brew install ffmpeg yt-dlp"
        else:
            hint = "패키지 관리자로 설치하세요 (apt install ffmpeg 등)"
        return Check("외부 도구", FAIL, f"{', '.join(missing)} 없음 → {hint}", lines)
    return Check("외부 도구", OK, lines=lines)


def check_packages() -> Check:
    lines, bad = [], []
    for mod, label in (("pycapcut", "pycapcut"),
                       ("faster_whisper", "faster-whisper"),
                       ("pymediainfo", "pymediainfo")):
        try:
            __import__(mod)
            lines.append(f"{label}: {_version(mod)}")
        except Exception as exc:
            lines.append(f"{label}: 못 불러옴 — {type(exc).__name__}: {exc}")
            bad.append(label)
    try:
        import pymediainfo

        lines.append(f"libmediainfo 사용 가능: {pymediainfo.MediaInfo.can_parse()}")
    except Exception:
        pass
    if bad:
        return Check("파이썬 패키지", FAIL,
                     f"{', '.join(bad)} → pip install -r reels/requirements.txt", lines)
    return Check("파이썬 패키지", OK, lines=lines)


def check_draft_root(override: str = "") -> Check:
    lines, found = [], None
    cands = [Path(override).expanduser()] if override else platforms.draft_root_candidates()
    for p in cands:
        exists = p.is_dir()
        lines.append(f"{'[있음]' if exists else '[없음]'} {p}")
        if exists and found is None:
            found = p
    if found is None:
        return Check("캡컷 초안 폴더", FAIL,
                     "후보 중 어느 것도 없음 — 캡컷을 한 번 실행해 프로젝트를 만들거나 "
                     "--draft-root 로 지정하세요", lines)
    try:
        drafts = sorted(d.name for d in found.iterdir() if d.is_dir())
        lines.append(f"초안 {len(drafts)}개: " +
                     (", ".join(drafts[:8]) + (" ..." if len(drafts) > 8 else "")
                      if drafts else "(비어 있음)"))
    except Exception as exc:
        lines.append(f"폴더를 읽지 못함: {exc}")
    return Check("캡컷 초안 폴더", OK, str(found), lines)


def check_folders() -> Check:
    from . import broll, sfx, transcribe

    lines = []
    for label, p in (("효과음 폴더", sfx.DEFAULT_SFX_DIR),
                     ("효과음 캐시", sfx.DEFAULT_CACHE),
                     ("자료 화면 폴더", broll.DEFAULT_DIR),
                     ("받아쓰기 모델 캐시", transcribe.DEFAULT_CACHE)):
        p = Path(p).expanduser()
        if p.is_dir():
            n = sum(1 for _ in p.iterdir())
            lines.append(f"[있음] {label}: {p} ({n}개)")
        else:
            lines.append(f"[없음] {label}: {p} (필요할 때 자동 생성)")
    return Check("작업 폴더", OK, lines=lines)


def check_gpu() -> Check:
    try:
        import ctranslate2

        n = ctranslate2.get_cuda_device_count()
    except Exception as exc:
        return Check("GPU", SKIP, f"확인 불가 — {type(exc).__name__}", [])
    if n > 0:
        return Check("GPU", OK, f"CUDA 장치 {n}개 — 받아쓰기에 자동으로 씁니다")
    return Check("GPU", WARN, "CUDA 없음 — CPU로 받아쓰기 (느립니다)")


def check_monitors() -> Check:
    if platforms.IS_WIN:
        ps = ("Add-Type -AssemblyName System.Windows.Forms; "
              "[System.Windows.Forms.Screen]::AllScreens | ForEach-Object { "
              "\"$($_.DeviceName) $($_.Bounds.Width)x$($_.Bounds.Height) \" + "
              "\"at $($_.Bounds.X),$($_.Bounds.Y) primary=$($_.Primary)\" }")
        code, out = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps])
        if code != 0 or not out:
            return Check("모니터", WARN, "모니터 구성을 읽지 못했습니다", [out[:200]])
        lines = out.splitlines()
        if len(lines) > 1:
            return Check("모니터", WARN,
                         f"{len(lines)}대 — gdigrab이 전체를 잡으므로 "
                         "--rect x,y,w,h 로 한 화면만 지정하는 게 좋습니다", lines)
        return Check("모니터", OK, lines[0], lines)
    return Check("모니터", SKIP, "윈도우에서만 확인합니다")


def check_recording(enabled: bool = True) -> Check:
    if not enabled:
        return Check("화면 녹화", SKIP, "--no-record 로 건너뜀")
    if not platforms.can_record():
        return Check("화면 녹화", SKIP, f"{sys.platform}에서는 자동 녹화를 지원하지 않습니다")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg and not platforms.IS_MAC:
        return Check("화면 녹화", FAIL, "ffmpeg가 없어 시험할 수 없습니다")

    tmp = Path(tempfile.gettempdir()) / f"reels-doctor-test{platforms.RECORD_EXT}"
    tmp.unlink(missing_ok=True)
    cmd = platforms.record_cmd(tmp, 2.0, ffmpeg=ffmpeg or "ffmpeg")
    lines = ["실행: " + " ".join(cmd)]
    code, out = _run(cmd, timeout=40)
    try:
        if not tmp.exists() or tmp.stat().st_size == 0:
            lines.append(out[:400] or "(출력 없음)")
            return Check("화면 녹화", FAIL, "2초 시험 녹화에서 파일이 생기지 않았습니다", lines)
        size_mb = tmp.stat().st_size / 1e6
        lines.append(f"파일 생성됨: {size_mb:.1f}MB")
        try:
            import pymediainfo

            tr = pymediainfo.MediaInfo.parse(str(tmp)).video_tracks
            if tr:
                t = tr[0]
                lines.append(f"해상도 {t.width}x{t.height}, "
                             f"{(t.duration or 0) / 1000:.1f}초")
        except Exception as exc:
            lines.append(f"파일은 생겼지만 열어보지 못함: {exc}")
        return Check("화면 녹화", OK, "2초 시험 녹화 성공 (파일은 지웠습니다)", lines)
    finally:
        tmp.unlink(missing_ok=True)


def check_scroll(full: bool = False) -> Check:
    cmd = platforms.scroll_cmd()
    if not cmd:
        return Check("스크롤", SKIP, f"{sys.platform}에서는 지원하지 않습니다")
    if platforms.IS_WIN:
        probe = ("$w = New-Object -ComObject wscript.shell; "
                 "if ($w) { 'COM ok' } else { 'COM 실패' }")
        code, out = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", probe])
        lines = [f"PowerShell COM 시험: {out[:120] or '(출력 없음)'}"]
        if code != 0 or "ok" not in out:
            lines.append("실행 정책이 막고 있을 수 있습니다. --no-scroll 로 끌 수 있습니다.")
            return Check("스크롤", FAIL, "PowerShell에서 COM 객체를 못 만들었습니다", lines)
        if full:
            c2, o2 = _run(cmd)
            lines.append(f"실제 SendKeys 시험: {'성공' if c2 == 0 else '실패'} {o2[:100]}")
        else:
            lines.append("실제 키 전송은 건너뜀 (--full 로 시험 가능 — 활성 창에 ↓ 가 들어갑니다)")
        return Check("스크롤", OK, "PowerShell 사용 가능", lines)
    # macOS
    lines = ["맥은 손쉬운 사용 권한이 필요합니다."]
    if full:
        c2, o2 = _run(cmd)
        lines.append(f"osascript 시험: {'성공' if c2 == 0 else '실패'} {o2[:100]}")
        return Check("스크롤", OK if c2 == 0 else FAIL, lines=lines)
    lines.append("실제 키 전송은 건너뜀 (--full 로 시험)")
    return Check("스크롤", SKIP, lines=lines)


# --------------------------------------------------------------------------

def run(*, full: bool = False, record: bool = True, draft_root: str = "") -> list[Check]:
    return [
        check_system(),
        check_tools(),
        check_packages(),
        check_draft_root(draft_root),
        check_folders(),
        check_gpu(),
        check_monitors(),
        check_recording(record),
        check_scroll(full),
    ]


def report(checks: list[Check]) -> str:
    out = ["# reels doctor", ""]
    out.append("| | 항목 | 결과 |")
    out.append("|---|------|------|")
    for c in checks:
        out.append(f"| {MARK[c.status]} | {c.name} | {c.status}"
                   + (f" — {c.detail}" if c.detail else "") + " |")
    out += ["", "## 자세히", ""]
    for c in checks:
        out.append(f"### {MARK[c.status]} {c.name} — {c.status}")
        if c.detail:
            out.append(c.detail)
        out += [f"    {line}" for line in c.lines]
        out.append("")

    bad = [c for c in checks if c.status == FAIL]
    warn = [c for c in checks if c.status == WARN]
    out.append("## 요약")
    if bad:
        out.append(f"**{len(bad)}개 실패**: " + ", ".join(c.name for c in bad))
    if warn:
        out.append(f"{len(warn)}개 주의: " + ", ".join(c.name for c in warn))
    if not bad and not warn:
        out.append("전부 통과. 바로 편집을 돌려도 됩니다.")
    out.append("")
    out.append("이 리포트를 그대로 붙여넣으면 무엇이 막혔는지 바로 알 수 있습니다.")
    return "\n".join(out)
