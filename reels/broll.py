"""배경 자료 화면: 보여줄 화면을 고르고, 녹화하고, 초안에 올린다.

세 단계로 나뉜다.
  plan   - 자료 화면이 필요한 문장 3~5곳을 골라 목록을 보여준다 (사람 확인용)
  record - 크롬으로 열고 screencapture로 녹화한다 (macOS 전용)
  place  - 녹화분을 세로로 잘라 "자료 화면" 트랙에 올린다

로그인·결제·개인정보가 보이는 주소는 계획 단계에서 막고, 녹화도 거부한다.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .util import SEC_US, ffmpeg_bin, run

DEFAULT_DIR = Path("~/릴스자료").expanduser()
TRACK_NAME = "자료 화면"
MIN_CLIP = 3.0
MAX_CLIP = 5.0
MIN_PICKS = 3
MAX_PICKS = 5

# 자료 화면 트랙이 차지할 영역 (세로 캔버스의 위쪽 절반)
HALF_W, HALF_H = 1080, 960
UPPER_HALF_Y = 0.5   # 캡컷 좌표에서 위쪽 절반의 중심

RE_URL = re.compile(r"https?://[^\s]+")
RE_DOMAIN = re.compile(
    r"\b([a-zA-Z0-9][a-zA-Z0-9-]{1,30}\.(?:com|net|org|io|dev|ai|app|co\.kr|kr)"
    r"(?:/[^\s,)\]]*)?)")
RE_NUMBER = re.compile(r"\d|[%＄$]|[일이삼사오육칠팔구십백천만억]\s*(?:배|개|초|분|원|퍼센트|명|번)")
RE_RESULT = re.compile(r"(결과|화면|완성|초안|파일|폴더|여기\s*보|보시면|이렇게\s*나)")

# 말로만 언급되는 서비스 -> 보여줄 주소
KNOWN_SITES: dict[str, str] = {
    "유튜브": "https://www.youtube.com",
    "youtube": "https://www.youtube.com",
    "구글": "https://www.google.com",
    "깃허브": "https://github.com",
    "github": "https://github.com",
    "노션": "https://www.notion.so",
    "notion": "https://www.notion.so",
    "인스타": "https://www.instagram.com",
    "캡컷": "https://www.capcut.com",
    "capcut": "https://www.capcut.com",
    "openverse": "https://openverse.org",
    "허깅페이스": "https://huggingface.co",
    "홈브루": "https://brew.sh",
    "homebrew": "https://brew.sh",
}

# 이런 주소는 찍지 않는다
BLOCKED = re.compile(
    r"(/login|/signin|/sign-in|/logout|/account|/checkout|/payment|/billing"
    r"|/cart|/order|/invoice|/password|/settings/|/admin|/wallet|/bank"
    r"|mail\.|banking|pay\.)", re.I)
BLOCKED_WORDS = re.compile(r"(로그인|결제|카드번호|계좌|비밀번호|주민등록|여권)")


@dataclass
class Shot:
    """자료 화면 한 컷."""
    sentence_index: int
    at_sec: float               # 초안 타임라인상 시작
    duration: float             # 녹화/배치 길이
    text: str
    kind: str                   # url / site / number / result
    reason: str
    url: str = ""
    file: str = ""
    blocked: bool = False
    block_reason: str = ""
    priority: int = 9
    note: str = field(default="")


# --------------------------------------------------------------------------
# plan
# --------------------------------------------------------------------------

def _detect(text: str) -> tuple[str, str, str, int] | None:
    """(kind, reason, url, priority)"""
    m = RE_URL.search(text)
    if m:
        return "url", f"주소를 직접 말함 ({m.group(0)})", m.group(0), 0
    m = RE_DOMAIN.search(text)
    if m:
        return "url", f"주소를 직접 말함 ({m.group(1)})", "https://" + m.group(1), 0
    low = text.lower()
    for name, url in KNOWN_SITES.items():
        if name in low:
            return "site", f"'{name}' 언급", url, 0
    if RE_NUMBER.search(text):
        return "number", "숫자를 말함 — 화면으로 보여주면 좋음", "", 1
    if RE_RESULT.search(text):
        return "result", "결과물을 가리킴", "", 2
    return None


def plan(sentences: list[dict], *, max_picks: int = MAX_PICKS,
         min_picks: int = MIN_PICKS, out_dir: Path = DEFAULT_DIR) -> list[Shot]:
    cands: list[Shot] = []
    for s in sentences:
        got = _detect(s["text"])
        if not got:
            continue
        kind, why, url, prio = got
        dur = max(MIN_CLIP, min(MAX_CLIP, s["end"] - s["start"]))
        shot = Shot(sentence_index=s["index"], at_sec=s["start"], duration=dur,
                    text=s["text"], kind=kind, reason=why, url=url,
                    priority=prio)
        if BLOCKED.search(url) or BLOCKED.search(s["text"]):
            shot.blocked = True
            shot.block_reason = "로그인·결제 화면으로 보임"
        if BLOCKED_WORDS.search(s["text"]):
            shot.blocked = True
            shot.block_reason = "개인정보가 보일 수 있는 내용"
        if not url:
            shot.note = "보여줄 주소를 직접 채워 넣어야 함"
        shot.file = f"{shot.sentence_index:02d}-{kind}.mov"
        cands.append(shot)

    picked = sorted([c for c in cands if not c.blocked],
                    key=lambda c: (c.priority, c.at_sec))[:max_picks]
    picked.sort(key=lambda c: c.at_sec)
    blocked = [c for c in cands if c.blocked]
    if len(picked) < min_picks:
        for c in picked:
            c.note = (c.note + " / 후보가 적음").strip(" /")
    return picked + blocked


def save_plan(shots: list[Shot], out_dir: Path = DEFAULT_DIR) -> Path:
    out_dir = Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "plan.json"
    path.write_text(json.dumps([asdict(s) for s in shots],
                               ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_plan(path: Path) -> list[Shot]:
    data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    return [Shot(**d) for d in data]


def table(shots: list[Shot]) -> str:
    rows = ["| 시각 | 길이 | 보여줄 화면 | 고른 이유 | 문장 |",
            "|------|------|-------------|-----------|------|"]
    for s in shots:
        txt = (s.text[:20] + "…") if len(s.text) > 21 else s.text
        what = s.url or "(주소를 채워주세요)"
        if s.blocked:
            what = f"**건너뜀** — {s.block_reason}"
        note = f" _{s.note}_" if s.note and not s.blocked else ""
        rows.append(f"| {s.at_sec:.1f}s | {s.duration:.0f}초 | {what}{note} | "
                    f"{s.reason} | {txt.replace('|', chr(92) + '|')} |")
    return "\n".join(rows)


# --------------------------------------------------------------------------
# record (macOS 전용)
# --------------------------------------------------------------------------

def record_commands(shot: Shot, out_dir: Path, *, settle: float = 2.5,
                    rect: str = "") -> list[list[str]]:
    """실제로 실행할 명령들을 그대로 돌려준다 (검토·dry-run용)."""
    dest = Path(out_dir).expanduser() / shot.file
    cap = ["screencapture", "-v", "-V", f"{shot.duration:.0f}", "-x"]
    if rect:
        cap += ["-R", rect]
    cap.append(str(dest))
    return [["open", "-a", "Google Chrome", "--new", shot.url], cap]


def record(shots: list[Shot], out_dir: Path = DEFAULT_DIR, *,
           settle: float = 2.5, rect: str = "", scroll: bool = True,
           dry_run: bool = False) -> list[Shot]:
    """크롬으로 열고 녹화한다. 녹화 중 천천히 아래로 스크롤한다."""
    import sys

    out_dir = Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    done = []
    for shot in shots:
        if shot.blocked:
            print(f"  · 건너뜀 {shot.at_sec:.1f}s — {shot.block_reason}")
            continue
        if not shot.url:
            print(f"  · 건너뜀 {shot.at_sec:.1f}s — 보여줄 주소가 비어 있음")
            continue
        if BLOCKED.search(shot.url):
            print(f"  · 건너뜀 {shot.url} — 로그인·결제 화면")
            continue
        open_cmd, cap_cmd = record_commands(shot, out_dir, settle=settle, rect=rect)
        if dry_run:
            print("$ " + " ".join(open_cmd))
            print(f"$ sleep {settle}")
            print("$ " + " ".join(cap_cmd))
            continue
        if sys.platform != "darwin":
            raise SystemExit("녹화는 macOS에서만 됩니다. --dry-run 으로 명령만 보세요.")
        run(open_cmd)
        time.sleep(settle)
        proc = subprocess.Popen(cap_cmd)
        if scroll:
            _scroll_while(proc, shot.duration)
        proc.wait()
        dest = out_dir / shot.file
        if not dest.exists():
            print(f"  ! 녹화 파일이 없습니다: {dest} (화면 기록 권한 확인)")
            continue
        done.append(shot)
        print(f"  · 녹화됨 {dest.name} ({shot.duration:.0f}초)")
    return done


def _scroll_while(proc: subprocess.Popen, seconds: float,
                  step: float = 0.7) -> None:
    """녹화가 도는 동안 아래 화살표를 눌러 천천히 스크롤한다."""
    end = time.time() + seconds
    while time.time() < end and proc.poll() is None:
        try:
            subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to key code 125'],
                check=False, capture_output=True, timeout=3)
        except Exception:
            return      # 손쉬운 사용 권한이 없으면 조용히 스크롤만 포기
        time.sleep(step)


# --------------------------------------------------------------------------
# place
# --------------------------------------------------------------------------

def to_vertical(src: Path, dest: Path, *, mode: str = "cover",
                crop_x: float = 0.5) -> Path:
    """녹화분을 자료 화면 영역(1080x960)에 맞게 자른다."""
    src, dest = Path(src), Path(dest)
    if mode == "cover":
        vf = (f"scale={HALF_W}:{HALF_H}:force_original_aspect_ratio=increase,"
              f"crop={HALF_W}:{HALF_H}:(iw-ow)*{crop_x:.3f}:(ih-oh)/2")
    elif mode == "fit":
        vf = (f"scale={HALF_W}:{HALF_H}:force_original_aspect_ratio=decrease,"
              f"pad={HALF_W}:{HALF_H}:(ow-iw)/2:(oh-ih)/2:black")
    else:
        raise SystemExit(f"crop-mode는 cover 또는 fit 입니다: {mode}")
    run([ffmpeg_bin(), "-y", "-v", "error", "-i", src, "-vf", vf,
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", dest])
    return dest


def place(content_path: Path, shots: list[Shot], src_dir: Path = DEFAULT_DIR, *,
          crop_mode: str = "cover", crop_x: float = 0.5,
          track_name: str = TRACK_NAME, backup: bool = True) -> int:
    import pycapcut as cc

    src_dir = Path(src_dir).expanduser()
    content_path = Path(content_path)

    usable = []
    for s in shots:
        if s.blocked:
            continue
        raw = src_dir / s.file
        if not raw.exists():
            print(f"  · 없음 {raw.name} — 건너뜁니다")
            continue
        vert = src_dir / (Path(s.file).stem + "_vert.mp4")
        if not vert.exists():
            to_vertical(raw, vert, mode=crop_mode, crop_x=crop_x)
        usable.append((s, vert))
    if not usable:
        raise SystemExit(f"{src_dir} 에 쓸 녹화 파일이 없습니다. 먼저 record 를 도세요.")

    script = cc.ScriptFile.load_template(str(content_path))
    if any(getattr(t, "name", None) == track_name for t in script.imported_tracks):
        raise SystemExit(f"'{track_name}' 트랙이 이미 있습니다. 캡컷에서 지우고 다시 실행하세요.")
    if backup:
        shutil.copy2(content_path, content_path.with_suffix(".json.bak"))

    # 본 영상 위, 자막 아래
    script.add_track(cc.TrackType.video, track_name, relative_index=100)
    added = 0
    for s, vert in usable:
        material = cc.VideoMaterial(str(vert))
        script.add_material(material)
        dur = min(int(round(s.duration * SEC_US)), material.duration)
        if dur <= 0:
            continue
        script.add_segment(
            cc.VideoSegment(
                material,
                target_timerange=cc.trange(int(round(s.at_sec * SEC_US)), dur),
                source_timerange=cc.trange(0, dur),
                clip_settings=cc.ClipSettings(transform_y=UPPER_HALF_Y),
            ),
            track_name,
        )
        added += 1
    script.save()
    return added
