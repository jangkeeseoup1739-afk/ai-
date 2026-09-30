"""기존 캡컷 초안에 효과음 트랙을 얹는다.

문장 경계는 초안의 영상 트랙 컷에서, 문장 내용은 자막 트랙에서 읽는다.
소리는 로컬 폴더를 먼저 뒤지고, 없으면 Openverse(CC0/CC BY)에서 받아온다.
"""
from __future__ import annotations

import json
import re
import shutil
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from .util import SEC_US

OPENVERSE_API = "https://api.openverse.org/v1/audio/"
USER_AGENT = "reels-sfx/1.0 (personal video editing script)"
AUDIO_EXTS = (".wav", ".mp3", ".m4a", ".aiff", ".aif", ".ogg", ".flac", ".opus")

DEFAULT_SFX_DIR = Path("~/릴스효과음").expanduser()
DEFAULT_CACHE = Path("~/.cache/reels-sfx").expanduser()

LEAD_SEC = 0.05          # 문장 시작 이만큼 앞에서 소리를 낸다
MAX_SFX_SEC = 4.0        # 이보다 긴 소리는 쓰지 않는다
MIN_SPACING_SEC = 2.0    # 효과음끼리 최소 간격

# 파일명으로 로컬 소리를 찾을 때 쓰는 별칭
KIND_ALIASES: dict[str, list[str]] = {
    "whoosh": ["whoosh", "휙", "후쉬", "우슝"],
    "swoosh": ["swoosh", "스우시", "전환", "transition"],
    "pop": ["pop", "팝", "뿅"],
    "ding": ["ding", "딩", "벨", "bell", "종", "chime"],
    "click": ["click", "클릭", "딸깍", "탁"],
}
KIND_QUERIES: dict[str, list[str]] = {
    "whoosh": ["whoosh", "whoosh transition"],
    "swoosh": ["swoosh", "swoosh transition", "whoosh"],
    "pop": ["pop", "pop sound", "bubble pop"],
    "ding": ["ding", "bell ding", "chime"],
    "click": ["click", "button click", "mouse click"],
}

# 문장 분류 규칙
RE_NUMBER = re.compile(r"\d|[%＄$]|[일이삼사오육칠팔구십백천만억]\s*(?:배|개|초|분|원|퍼센트|명|번)")
RE_TWIST = re.compile(r"(근데|그런데|하지만|사실|알고\s*보니|반전|의외로|놀랍게도|문제는|함정)")
RE_LIST = re.compile(r"(첫째|첫\s*번째|첫번째|먼저|우선|하나는|1번|일단)")
RE_TOPIC = re.compile(r"(그리고|다음은|다음으로|이제|그럼|마지막으로|두\s*번째|세\s*번째|또)")
RE_CTA = re.compile(r"(댓글|구독|팔로우|좋아요|저장|공유|알림)")


@dataclass
class Pick:
    """문장 하나에 붙일 효과음 한 개."""
    sentence_index: int
    kind: str
    reason: str
    at_sec: float                 # 초안 타임라인상 재생 시작
    sentence_start: float
    text: str
    path: Path | None = None
    source: str = ""              # local / openverse
    meta: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# 초안 읽기
# --------------------------------------------------------------------------

def draft_content_path(draft_root: Path, name: str) -> Path:
    p = Path(draft_root).expanduser() / name / "draft_content.json"
    if not p.exists():
        raise SystemExit(f"초안을 찾을 수 없습니다: {p}")
    return p


def read_sentences(content_path: Path) -> list[dict]:
    """영상 컷을 문장 단위로 보고, 그 구간에 걸친 자막을 본문으로 묶는다."""
    data = json.loads(Path(content_path).read_text(encoding="utf-8"))
    tracks = data.get("tracks", [])
    video = next((t for t in tracks if t.get("type") == "video"), None)
    texts = [t for t in tracks if t.get("type") == "text"]
    if not video or not video.get("segments"):
        raise SystemExit("초안에 영상 트랙이 없습니다.")

    cues = []
    materials = {m["id"]: m for m in data.get("materials", {}).get("texts", [])}
    for tr in texts:
        for seg in tr.get("segments", []):
            tr_rng = seg["target_timerange"]
            mat = materials.get(seg.get("material_id"), {})
            raw = mat.get("content", "")
            body = ""
            if raw:
                try:  # 캡컷은 본문을 JSON 문자열로 감싸 저장한다
                    body = json.loads(raw).get("text", "")
                except (json.JSONDecodeError, AttributeError):
                    body = raw
            cues.append({"start": tr_rng["start"] / SEC_US,
                         "end": (tr_rng["start"] + tr_rng["duration"]) / SEC_US,
                         "text": body})
    cues.sort(key=lambda c: c["start"])

    sentences = []
    segs = sorted(video["segments"], key=lambda s: s["target_timerange"]["start"])
    for i, seg in enumerate(segs):
        start = seg["target_timerange"]["start"] / SEC_US
        end = start + seg["target_timerange"]["duration"] / SEC_US
        body = " ".join(c["text"] for c in cues
                        if c["start"] < end - 1e-6 and c["end"] > start + 1e-6)
        sentences.append({"index": i, "start": start, "end": end,
                          "text": body.strip()})
    return sentences


# --------------------------------------------------------------------------
# 어디에 무슨 소리를 넣을지
# --------------------------------------------------------------------------

def _candidate(sentence: dict, is_first: bool, is_last: bool) -> tuple[str, str, int] | None:
    """(종류, 이유, 우선순위) — 우선순위가 낮을수록 먼저 지킨다."""
    text = sentence["text"]
    if is_first:
        return "whoosh", "첫 문장 — 시작을 끊어줌", 0
    if is_last:
        why = "마지막 문장 — 댓글 유도" if RE_CTA.search(text) else "마지막 문장 — 마무리"
        return "ding", why, 0
    if RE_TWIST.search(text):
        return "pop", "반전/전환 표현", 1
    if RE_NUMBER.search(text):
        return "pop", "숫자 강조", 1
    if RE_LIST.search(text):
        return "click", "목록 시작", 2
    if RE_TOPIC.search(text):
        return "swoosh", "주제가 바뀜", 3
    return None


def choose(sentences: list[dict], *, per_30s: float = 6.0,
           min_per_30s: float = 4.0, max_per_30s: float = 8.0,
           spacing: float = MIN_SPACING_SEC) -> list[Pick]:
    if not sentences:
        return []
    duration = max(s["end"] for s in sentences)
    scale = max(duration / 30.0, 1.0 / 30.0)
    budget = max(round(min_per_30s * scale), min(round(per_30s * scale),
                                                 round(max_per_30s * scale)))
    budget = max(1, int(budget))

    cands: list[tuple[int, Pick]] = []
    last = len(sentences) - 1
    for s in sentences:
        got = _candidate(s, s["index"] == 0, s["index"] == last)
        if not got:
            continue
        kind, why, prio = got
        cands.append((prio, Pick(
            sentence_index=s["index"], kind=kind, reason=why,
            at_sec=max(0.0, s["start"] - LEAD_SEC),
            sentence_start=s["start"], text=s["text"],
        )))

    # 우선순위 -> 시간 순으로 뽑되, 너무 붙어 있으면 건너뛴다
    chosen: list[Pick] = []
    for _, pick in sorted(cands, key=lambda c: (c[0], c[1].at_sec)):
        if len(chosen) >= budget:
            break
        if any(abs(pick.at_sec - c.at_sec) < spacing for c in chosen):
            continue
        chosen.append(pick)
    chosen.sort(key=lambda p: p.at_sec)
    return chosen


# --------------------------------------------------------------------------
# 소리 구하기
# --------------------------------------------------------------------------

def find_local(kind: str, sfx_dir: Path) -> Path | None:
    sfx_dir = Path(sfx_dir).expanduser()
    if not sfx_dir.is_dir():
        return None
    aliases = KIND_ALIASES.get(kind, [kind])
    for f in sorted(sfx_dir.iterdir()):
        if not f.is_file() or f.suffix.lower() not in AUDIO_EXTS:
            continue
        stem = f.stem.lower()
        if any(a.lower() in stem for a in aliases):
            return f
    return None


def _get_json(url: str, timeout: float = 20.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_openverse(query: str, *, page_size: int = 20,
                     timeout: float = 20.0) -> list[dict]:
    params = {"q": query, "license": "cc0,by", "page_size": str(page_size)}
    url = OPENVERSE_API + "?" + urllib.parse.urlencode(params)
    try:
        data = _get_json(url, timeout)
    except Exception as exc:  # 네트워크/레이트리밋 등
        raise RuntimeError(f"Openverse 검색 실패 ({query}): {exc}") from exc
    return data.get("results") or []


def _audio_url(result: dict) -> str | None:
    if result.get("url"):
        return result["url"]
    for alt in result.get("alt_files") or []:
        if alt.get("url"):
            return alt["url"]
    return None


def _duration_sec(result: dict) -> float | None:
    d = result.get("duration")          # Openverse는 밀리초로 준다
    return None if d is None else d / 1000.0


def download(url: str, dest: Path, timeout: float = 30.0) -> Path:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=timeout) as resp, \
            open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)
    return dest


def _playable(path: Path) -> float | None:
    """pymediainfo로 실제 오디오인지 확인하고 길이(초)를 돌려준다."""
    try:
        import pymediainfo

        info = pymediainfo.MediaInfo.parse(str(path))
        for tr in info.audio_tracks:
            if tr.duration:
                return float(tr.duration) / 1000.0
        return None
    except Exception:
        return None


def fetch_openverse(kind: str, cache: Path, *, max_sec: float = MAX_SFX_SEC,
                    tries: int = 5) -> tuple[Path, dict]:
    cache = Path(cache).expanduser()
    cache.mkdir(parents=True, exist_ok=True)
    errors = []
    for query in KIND_QUERIES.get(kind, [kind]):
        try:
            results = search_openverse(query)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        checked = 0
        for r in results:
            if checked >= tries:
                break
            dur = _duration_sec(r)
            if dur is None or dur > max_sec or dur <= 0:
                continue
            url = _audio_url(r)
            if not url:
                continue
            checked += 1
            ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
            if ext not in AUDIO_EXTS:
                ext = ".mp3"
            dest = cache / f"{kind}-{r.get('id', 'x')}{ext}"
            try:
                if not dest.exists():
                    download(url, dest)
            except Exception as exc:
                errors.append(f"{query}: 내려받기 실패 {exc}")
                continue
            real = _playable(dest)
            if real is None or real > max_sec + 0.5:
                dest.unlink(missing_ok=True)
                continue
            meta = {
                "title": r.get("title") or "(제목 없음)",
                "creator": r.get("creator") or "(작자 미상)",
                "creator_url": r.get("creator_url") or "",
                "license": (r.get("license") or "").lower(),
                "license_version": r.get("license_version") or "",
                "license_url": r.get("license_url") or "",
                "landing": r.get("foreign_landing_url") or "",
                "provider": r.get("provider") or "",
                "duration": real,
                "query": query,
            }
            return dest, meta
    raise RuntimeError(
        f"'{kind}' 소리를 구하지 못했습니다. "
        + ("; ".join(errors) if errors else "조건에 맞는 결과가 없습니다.")
    )


def resolve(picks: list[Pick], *, sfx_dir: Path = DEFAULT_SFX_DIR,
            cache: Path = DEFAULT_CACHE, allow_download: bool = True,
            max_sec: float = MAX_SFX_SEC) -> list[Pick]:
    """종류별로 한 번만 구해서 같은 종류는 같은 파일을 쓴다."""
    resolved: dict[str, tuple[Path, str, dict]] = {}
    failures: list[str] = []
    for p in picks:
        if p.kind not in resolved:
            local = find_local(p.kind, sfx_dir)
            if local:
                dur = _playable(local)
                resolved[p.kind] = (local, "local", {"duration": dur,
                                                     "title": local.name})
            elif allow_download:
                try:
                    path, meta = fetch_openverse(p.kind, cache, max_sec=max_sec)
                    resolved[p.kind] = (path, "openverse", meta)
                except RuntimeError as exc:
                    failures.append(str(exc))
                    resolved[p.kind] = (None, "", {})  # type: ignore[assignment]
            else:
                failures.append(f"'{p.kind}' 로컬 파일 없음 (다운로드 꺼짐)")
                resolved[p.kind] = (None, "", {})  # type: ignore[assignment]
        path, source, meta = resolved[p.kind]
        p.path, p.source, p.meta = path, source, meta
    if failures:
        for f in dict.fromkeys(failures):
            print(f"  ! {f}")
    return picks


# --------------------------------------------------------------------------
# 초안에 얹기
# --------------------------------------------------------------------------

def attach(content_path: Path, picks: list[Pick], *, volume: float = 0.5,
           track_name: str = "효과음", backup: bool = True) -> int:
    import pycapcut as cc

    usable = [p for p in picks if p.path]
    if not usable:
        raise SystemExit("쓸 수 있는 효과음이 하나도 없습니다.")

    content_path = Path(content_path)
    if backup:
        shutil.copy2(content_path, content_path.with_suffix(".json.bak"))

    script = cc.ScriptFile.load_template(str(content_path))
    if any(getattr(t, "name", None) == track_name for t in script.imported_tracks):
        raise SystemExit(
            f"'{track_name}' 트랙이 이미 있습니다. 캡컷에서 지우고 다시 실행하거나 "
            "--track-name 으로 다른 이름을 주세요."
        )
    script.add_track(cc.TrackType.audio, track_name)

    materials: dict[str, object] = {}
    added = 0
    for p in usable:
        key = str(p.path)
        if key not in materials:
            materials[key] = cc.AudioMaterial(key)
            script.add_material(materials[key])
        mat = materials[key]
        dur = min(mat.duration, int(round(MAX_SFX_SEC * SEC_US)))
        if dur <= 0:
            continue
        start = int(round(p.at_sec * SEC_US))
        script.add_segment(
            cc.AudioSegment(mat,
                            target_timerange=cc.trange(start, dur),
                            source_timerange=cc.trange(0, dur),
                            volume=volume),
            track_name,
        )
        added += 1
    script.save()
    return added


# --------------------------------------------------------------------------
# 보고
# --------------------------------------------------------------------------

def table(picks: list[Pick]) -> str:
    rows = ["| 시각 | 종류 | 넣은 이유 | 문장 | 출처 |",
            "|------|------|-----------|------|------|"]
    for p in picks:
        txt = (p.text[:22] + "…") if len(p.text) > 23 else p.text
        txt = txt.replace("|", "\\|") or "—"
        if p.source == "local":
            src = f"내 폴더: {Path(p.path).name}" if p.path else "— (못 구함)"
        elif p.source == "openverse":
            lic = (p.meta.get("license") or "").upper()
            src = f"Openverse {lic} — {p.meta.get('title', '')}"
        else:
            src = "— (못 구함)"
        rows.append(f"| {p.at_sec:.2f}s | {p.kind} | {p.reason} | {txt} | {src} |")
    return "\n".join(rows)


def attribution(picks: list[Pick]) -> str:
    """CC BY 소리에 대한 캡션용 출처 문구. CC0만 썼으면 빈 문자열."""
    seen: dict[str, dict] = {}
    for p in picks:
        if p.source != "openverse":
            continue
        lic = (p.meta.get("license") or "").lower()
        if lic != "by":
            continue
        key = p.meta.get("landing") or p.meta.get("title", "")
        seen.setdefault(key, p.meta)
    if not seen:
        return ""
    ver = lambda m: m.get("license_version") or "4.0"  # noqa: E731
    lines = ["효과음 출처"]
    for m in seen.values():
        line = f"· {m.get('title')} — {m.get('creator')} (CC BY {ver(m)})"
        if m.get("landing"):
            line += f" {m['landing']}"
        lines.append(line)
    return "\n".join(lines)
