"""2단계: NG 반복 / 군말 / 말하다 끊긴 부분 판정.

판정 결과는 decisions.json 으로 떨어지고, 사람이 직접 고쳐서 다시 넣을 수 있다.
문맥 기반 오타 교정은 규칙으로는 한계가 있어 --llm 옵션(Claude API)을 따로 둔다.
"""
from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

# 단독으로 나오면 대사가 아니라 군말/구령인 토큰
FILLERS = {
    "음", "엄", "어", "아", "에", "흠", "허", "으",
    "그", "저", "저기", "뭐", "머", "자", "이제",
    "다시", "컷", "잠깐", "잠시만", "스톱", "노", "엔지", "ng",
}

# 문장이 끝났다고 볼 수 있는 어미
FINAL_ENDING = re.compile(
    r"(습니다|세요|예요|에요|네요|는데요|거든요|더라고요|"
    r"다|요|죠|까|네|군|자|래|라|니|야|지|음|함|삼)[\.\!\?…~]*$"
)

PUNCT = re.compile(r"[\s\.,!?…~\-·\"'“”‘’()\[\]]+")
REPEAT_CHAR = re.compile(r"(.)\1{1,}")


def normalize(text: str) -> str:
    """비교용 정규화: 공백/문장부호 제거 + 늘어진 글자 축약."""
    t = PUNCT.sub("", text).lower()
    return REPEAT_CHAR.sub(r"\1", t)


def tokens(text: str) -> list[str]:
    return [PUNCT.sub("", t).lower() for t in text.split() if PUNCT.sub("", t)]


def _is_filler_token(tok: str) -> bool:
    return REPEAT_CHAR.sub(r"\1", tok) in FILLERS


def is_filler_only(text: str) -> bool:
    toks = tokens(text)
    return bool(toks) and all(_is_filler_token(t) for t in toks)


def strip_leading_fillers(text: str) -> str:
    """대사 앞에 붙은 군말만 떼어낸다 (뒤쪽 내용은 건드리지 않음)."""
    parts = text.split()
    while parts and _is_filler_token(PUNCT.sub("", parts[0]).lower()):
        parts.pop(0)
    return " ".join(parts).strip() or text.strip()


def similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _looks_cut_off(text: str, norm: str) -> bool:
    if text.rstrip().endswith(("...", "…", "-", "—")):
        return True
    if len(norm) <= 3 and not FINAL_ENDING.search(text.strip()):
        return True
    return False


def decide(segments: list[dict], *, ng_threshold: float = 0.75,
           ng_window: int = 4, ng_max_gap: float = 20.0,
           prefix_threshold: float = 0.8,
           typo_map: dict[str, str] | None = None) -> list[dict]:
    """각 세그먼트에 keep/drop 과 이유를 붙여 돌려준다."""
    typo_map = typo_map or {}
    n = len(segments)
    norms = [normalize(s["text"]) for s in segments]
    out = [{
        "id": s["id"], "start": s["start"], "end": s["end"],
        "text": s["text"], "text_final": s["text"].strip(),
        "keep": True, "reason": "",
    } for s in segments]

    def drop(i: int, reason: str) -> None:
        out[i]["keep"] = False
        out[i]["reason"] = reason

    # 1) 군말만으로 이루어진 구간
    for i, seg in enumerate(segments):
        if is_filler_only(seg["text"]):
            drop(i, f"군말/구령만 있는 구간 (\"{seg['text'].strip()}\")")

    # 2) 말하다 끊긴 부분 / 하다 만 도입부
    for i in range(n):
        if not out[i]["keep"]:
            continue
        nxt = next((k for k in range(i + 1, n) if out[k]["keep"]), None)
        if nxt is not None:
            a, b = norms[i], norms[nxt]
            head = b[:len(a)]
            if a and len(a) < len(b) * 0.8 and similar(a, head) >= prefix_threshold:
                drop(i, f"말하다 끊긴 도입부 — 다음 #{segments[nxt]['id']}에서 "
                        f"같은 말을 끝까지 다시 함")
                continue
        if _looks_cut_off(segments[i]["text"], norms[i]):
            drop(i, "문장이 끝나지 않고 끊김")

    # 3) 같은 말 반복(NG) -> 마지막 테이크만 남김
    for i in range(n):
        if not out[i]["keep"]:
            continue
        for j in range(i + 1, min(n, i + 1 + ng_window)):
            if not out[j]["keep"]:
                continue
            if segments[j]["start"] - segments[i]["end"] > ng_max_gap:
                break
            ratio = similar(norms[i], norms[j])
            if ratio >= ng_threshold:
                drop(i, f"같은 말 반복(NG) — 뒤 테이크 #{segments[j]['id']}와 "
                        f"{int(ratio * 100)}% 일치, 마지막 것만 유지")
                break

    # 4) 살아남은 대사 다듬기: 앞쪽 군말 제거 + 오타 치환
    for item in out:
        if not item["keep"]:
            continue
        t = strip_leading_fillers(item["text"])
        for wrong, right in typo_map.items():
            t = t.replace(wrong, right)
        if t != item["text"].strip():
            item["note"] = "앞 군말 제거/오타 교정"
        item["text_final"] = t

    return out


def apply_llm(decisions: list[dict], model: str = "claude-sonnet-5-5") -> list[dict]:
    """ANTHROPIC_API_KEY가 있으면 문맥 기반으로 판정과 오타를 다듬는다."""
    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY가 없어 --llm을 쓸 수 없습니다.")
    from anthropic import Anthropic

    payload = [{"id": d["id"], "text": d["text"], "keep": d["keep"],
                "reason": d["reason"]} for d in decisions]
    prompt = (
        "다음은 한국어 영상 촬영본의 whisper 받아쓰기와 규칙 기반 1차 판정이다.\n"
        "문맥을 보고 각 구간을 최종 판정하라.\n"
        "- 같은 말을 여러 번 한 NG는 마지막 것만 keep=true\n"
        "- '음/어/다시' 같은 군말, 말하다 끊긴 구간은 keep=false\n"
        "- keep=true인 구간의 text는 문맥에 맞게 오타만 고치고 말투는 유지\n"
        "- reason은 한국어 한 문장\n"
        "JSON 배열만 출력: [{\"id\":0,\"keep\":true,\"text\":\"...\",\"reason\":\"...\"}]\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=1)
    )
    client = Anthropic()
    msg = client.messages.create(
        model=model, max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(b.text for b in msg.content if b.type == "text").strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    verdicts = {v["id"]: v for v in json.loads(raw)}
    for d in decisions:
        v = verdicts.get(d["id"])
        if not v:
            continue
        d["keep"] = bool(v.get("keep", d["keep"]))
        d["reason"] = v.get("reason", d["reason"])
        if d["keep"] and v.get("text"):
            d["text_final"] = v["text"].strip()
    return decisions


def report(decisions: list[dict]) -> str:
    kept = [d for d in decisions if d["keep"]]
    dropped = [d for d in decisions if not d["keep"]]
    kept_dur = sum(d["end"] - d["start"] for d in kept)
    total_dur = sum(d["end"] - d["start"] for d in decisions)

    lines = ["# 러프컷 판정 결과", ""]
    lines.append(f"- 전체 {len(decisions)}구간 / {total_dur:.1f}초")
    lines.append(f"- 유지 {len(kept)}구간 / {kept_dur:.1f}초")
    lines.append(f"- 제거 {len(dropped)}구간 / {total_dur - kept_dur:.1f}초")
    lines += ["", "## 뺀 부분과 이유", ""]
    if dropped:
        lines.append("| # | 구간 | 내용 | 뺀 이유 |")
        lines.append("|---|------|------|---------|")
        for d in dropped:
            txt = d["text"].strip().replace("|", "\\|")
            lines.append(f"| {d['id']} | {d['start']:.1f}–{d['end']:.1f}s | {txt} | {d['reason']} |")
    else:
        lines.append("_뺀 구간 없음_")
    lines += ["", "## 남긴 부분", ""]
    lines.append("| # | 구간 | 자막으로 쓸 대사 |")
    lines.append("|---|------|------------------|")
    for d in kept:
        txt = d["text_final"].replace("|", "\\|")
        note = f"  _({d['note']})_" if d.get("note") else ""
        lines.append(f"| {d['id']} | {d['start']:.1f}–{d['end']:.1f}s | {txt}{note} |")
    return "\n".join(lines) + "\n"


def save(decisions: list[dict], workdir: Path) -> tuple[Path, Path]:
    work = Path(workdir)
    dj = work / "decisions.json"
    rp = work / "report.md"
    dj.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    rp.write_text(report(decisions), encoding="utf-8")
    return dj, rp
