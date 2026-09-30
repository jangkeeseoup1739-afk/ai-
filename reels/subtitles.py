"""3단계: 남긴 구간을 이어 붙인 타임라인 + 한 줄 12자 자막 SRT."""
from __future__ import annotations

from pathlib import Path

from .util import srt_timestamp

MIN_LINE_SEC = 0.35


MAX_SILENCE = 0.4


def build_timeline(decisions: list[dict],
                   max_silence: float = MAX_SILENCE) -> list[dict]:
    """유지 구간을 이어 붙인 새 타임라인을 계산한다.

    구간 사이 침묵은 `max_silence`까지만 남기고 나머지는 덜어낸다. 남길 침묵은
    빈자리로 두지 않고 앞뒤 컷의 소재 범위를 넓혀서 채운다 — 그래야 영상에
    검은 구멍이 생기지 않고, 말끝이 잘리지도 않는다.

    NG나 군말을 들어낸 자리는 침묵을 남기지 않는다(하드컷).

    src_start/src_end 는 원본 위치, new_start/new_end 는 컷 후 위치.
    """
    kept = [i for i, d in enumerate(decisions)
            if d.get("keep") and d["end"] > d["start"]]

    def bridge(a: int, b: int) -> float:
        """a와 b 사이에 남겨도 되는 침묵의 길이."""
        if any(not decisions[k].get("keep") for k in range(a + 1, b)):
            return 0.0  # 사이에서 뭘 들어냈으면 붙여버린다
        raw = decisions[b]["start"] - decisions[a]["end"]
        return min(max(raw, 0.0), max_silence)

    cursor = 0.0
    out = []
    for n, i in enumerate(kept):
        d = decisions[i]
        # 남길 침묵은 앞 컷의 꼬리와 뒤 컷의 머리가 절반씩 나눠 갖는다
        lead = bridge(kept[n - 1], i) / 2 if n > 0 else 0.0
        tail = bridge(i, kept[n + 1]) / 2 if n < len(kept) - 1 else 0.0
        src_start = max(0.0, d["start"] - lead)
        src_end = d["end"] + tail
        dur = src_end - src_start
        out.append({
            "id": d["id"],
            "src_start": src_start, "src_end": src_end, "duration": dur,
            "new_start": cursor, "new_end": cursor + dur,
            "text": d.get("text_final") or d["text"],
        })
        cursor += dur
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
