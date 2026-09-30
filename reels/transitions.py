"""기존 캡컷 초안의 컷 경계에 장면 전환을 넣는다.

전환은 **앞쪽 컷**에 붙는다(pycapcut 규약). 이야기가 바뀌는 지점만 고르고,
같은 전환이 연달아 나오지 않도록 목록을 돌려가며 쓴다.
"""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .util import SEC_US

DEFAULT_DURATION = 0.3   # 초
MIN_SPACING_SEC = 3.0

# 뒤 문장이 이렇게 시작하면 이야기가 바뀐 것으로 본다. (표현, 이유, 우선순위)
MARKERS: list[tuple[re.Pattern, str, int]] = [
    (re.compile(r"^(자\s*)?(그럼|그러면|이제|이번엔|이번에는)"), "화제를 넘김", 0),
    (re.compile(r"^(다음은|다음으로|그다음|그 다음)"), "다음 순서로 넘어감", 0),
    (re.compile(r"^(마지막으로|정리하면|결론적으로|요약하면)"), "마무리로 넘어감", 0),
    (re.compile(r"^(두|세|네|다섯)\s*번째"), "목록의 다음 항목", 1),
    (re.compile(r"^(그런데|근데|하지만|반면|한편|그래도)"), "이야기가 꺾임", 1),
    (re.compile(r"^(그리고|또|게다가)"), "내용이 이어지며 바뀜", 2),
]

# 돌려 쓸 전환 목록 (pycapcut TransitionType 이름). 짧고 과하지 않은 것들.
DEFAULT_POOL = [
    "White_Flash",
    "Snap_Zoom",
    "Whip_Tear",
    "Lumin_Flash",
    "Zoom_to_Change",
    "Signal_Glitch_2",
]


@dataclass
class Point:
    """컷 경계 하나에 넣을 전환."""
    sentence_index: int      # 전환을 붙일 앞쪽 컷
    at_sec: float            # 그 컷이 끝나는 시각 = 전환이 일어나는 지점
    reason: str
    next_text: str
    priority: int = 9
    transition: str = ""


def _marker(text: str) -> tuple[str, int] | None:
    head = text.strip()
    for pattern, why, prio in MARKERS:
        if pattern.search(head):
            return why, prio
    return None


def find_points(sentences: list[dict], *, per_30s: float = 3.0,
                min_per_30s: float = 2.0, max_per_30s: float = 4.0,
                spacing: float = MIN_SPACING_SEC) -> list[Point]:
    """이야기가 바뀌는 경계를 골라 개수를 맞춘다."""
    if len(sentences) < 2:
        return []
    duration = max(s["end"] for s in sentences)
    scale = max(duration / 30.0, 1.0 / 30.0)
    budget = max(round(min_per_30s * scale),
                 min(round(per_30s * scale), round(max_per_30s * scale)))
    budget = max(1, int(budget))

    cands: list[Point] = []
    for i in range(len(sentences) - 1):      # 마지막 컷 뒤에는 전환을 못 붙인다
        got = _marker(sentences[i + 1]["text"])
        if not got:
            continue
        why, prio = got
        cands.append(Point(sentence_index=i, at_sec=sentences[i]["end"],
                           reason=why, next_text=sentences[i + 1]["text"],
                           priority=prio))

    chosen: list[Point] = []
    for p in sorted(cands, key=lambda c: (c.priority, c.at_sec)):
        if len(chosen) >= budget:
            break
        if any(abs(p.at_sec - c.at_sec) < spacing for c in chosen):
            continue
        chosen.append(p)
    chosen.sort(key=lambda p: p.at_sec)

    # 목록을 순서대로 돌려 쓰므로 같은 전환이 연달아 나오지 않는다
    pool = DEFAULT_POOL
    for n, p in enumerate(chosen):
        p.transition = pool[n % len(pool)]
    return chosen


def apply(content_path: Path, points: list[Point], *,
          duration: float = DEFAULT_DURATION, backup: bool = True,
          force: bool = False) -> int:
    import pycapcut as cc
    from pycapcut.video_segment import Transition

    if not points:
        raise SystemExit("넣을 전환이 없습니다.")
    content_path = Path(content_path)

    script = cc.ScriptFile.load_template(str(content_path))
    existing = script.imported_materials.get("transitions") or []
    if existing and not force:
        raise SystemExit(
            f"초안에 이미 전환 {len(existing)}개가 있습니다. "
            "캡컷에서 지우고 다시 실행하거나 --force 를 주세요."
        )

    video = next((t for t in script.imported_tracks
                  if t.track_type == cc.TrackType.video), None)
    if video is None or not getattr(video, "segments", None):
        raise SystemExit("초안에 영상 트랙이 없습니다.")
    segs = sorted(video.segments, key=lambda s: s.target_timerange.start)

    if backup:
        shutil.copy2(content_path, content_path.with_suffix(".json.bak"))

    dur_us = int(round(duration * SEC_US))
    added = 0
    for p in points:
        if not 0 <= p.sentence_index < len(segs) - 1:
            continue
        try:
            meta = getattr(cc.TransitionType, p.transition)
        except AttributeError:
            raise SystemExit(f"알 수 없는 전환 이름입니다: {p.transition}")
        seg = segs[p.sentence_index]
        # 전환 길이는 앞뒤 컷보다 짧아야 한다
        room = min(seg.target_timerange.duration,
                   segs[p.sentence_index + 1].target_timerange.duration)
        this_dur = max(int(0.1 * SEC_US), min(dur_us, int(room * 0.5)))

        tr = Transition(meta, this_dur)
        script.materials.transitions.append(tr)
        seg.raw_data.setdefault("extra_material_refs", []).append(tr.global_id)
        p.transition = f"{p.transition}@{this_dur / SEC_US:.2f}s"
        added += 1

    script.save()
    return added


def table(points: list[Point]) -> str:
    rows = ["| 시각 | 전환 | 넣은 이유 | 다음 문장 |",
            "|------|------|-----------|-----------|"]
    for p in points:
        nxt = (p.next_text[:20] + "…") if len(p.next_text) > 21 else p.next_text
        rows.append(f"| {p.at_sec:.2f}s | {p.transition} | {p.reason} | "
                    f"{nxt.replace('|', chr(92) + '|')} |")
    return "\n".join(rows)
