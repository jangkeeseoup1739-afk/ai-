"""3단계: 남긴 구간을 이어 붙인 타임라인 + 한 줄 12자 자막 SRT."""
from __future__ import annotations

from pathlib import Path

from .util import srt_timestamp

MIN_LINE_SEC = 0.35


def build_timeline(decisions: list[dict], gap: float = 0.0) -> list[dict]:
    """유지 구간만 순서대로 이어 붙인 새 타임라인을 계산한다.

    src_start/src_end 는 원본 위치, new_start/new_end 는 컷 후 위치.
    """
    cursor = 0.0
    out = []
    for d in decisions:
        if not d.get("keep"):
            continue
        dur = max(0.0, d["end"] - d["start"])
        if dur <= 0:
            continue
        out.append({
            "id": d["id"],
            "src_start": d["start"], "src_end": d["end"], "duration": dur,
            "new_start": cursor, "new_end": cursor + dur,
            "text": d.get("text_final") or d["text"],
        })
        cursor += dur + gap
    return out


def split_lines(text: str, max_chars: int = 12) -> list[str]:
    """띄어쓰기를 지키면서 max_chars 근처로 줄을 나눈다."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    cur = ""
    for w in words:
        while len(w) > max_chars:  # 한 어절이 너무 길면 강제로 자른다
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(w[:max_chars])
            w = w[max_chars:]
        candidate = f"{cur} {w}".strip()
        if cur and len(candidate) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    # 마지막 줄이 너무 짧으면 앞줄에 붙인다
    if len(lines) >= 2 and len(lines[-1]) <= max(2, max_chars // 4):
        merged = f"{lines[-2]} {lines[-1]}"
        if len(merged) <= max_chars + 4:
            lines[-2:] = [merged]
    return lines


def to_cues(timeline: list[dict], max_chars: int = 12) -> list[dict]:
    """구간 하나를 여러 자막 줄로 쪼개고 글자 수 비례로 시간을 배분한다."""
    cues: list[dict] = []
    for seg in timeline:
        lines = split_lines(seg["text"], max_chars)
        if not lines:
            continue
        weights = [max(1, len(l)) for l in lines]
        total = sum(weights)
        t = seg["new_start"]
        for line, w in zip(lines, weights):
            dur = max(MIN_LINE_SEC, seg["duration"] * w / total)
            end = min(t + dur, seg["new_end"])
            if end <= t:  # 구간이 너무 짧아 자리가 없으면 최소 길이라도 준다
                end = t + MIN_LINE_SEC
            cues.append({"start": t, "end": end, "text": line})
            t = end
    return cues


def to_srt(cues: list[dict]) -> str:
    blocks = []
    for i, c in enumerate(cues, 1):
        blocks.append(
            f"{i}\n{srt_timestamp(c['start'])} --> {srt_timestamp(c['end'])}\n{c['text']}\n"
        )
    return "\n".join(blocks)


def write_srt(timeline: list[dict], path: Path, max_chars: int = 12) -> Path:
    cues = to_cues(timeline, max_chars)
    Path(path).write_text(to_srt(cues), encoding="utf-8")
    return Path(path)
