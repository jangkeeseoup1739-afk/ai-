"""블로그 글 하나를 30초 릴스 대본으로 바꾼다.

릴스·쇼츠에서 블로그로 들어오는 길을 만드는 용도다. 검색 노출만으로는
처음 한두 달이 비니까, 같은 내용을 영상으로 한 번 더 내보낸다.
대본이 나오면 이 레포의 릴스 편집 파이프라인에 그대로 넣을 수 있다.
"""
from __future__ import annotations

import re

from . import keywords as kw
from .parse import Post

_SENT = re.compile(r"[^.!?\n]+[.!?\n]?")


def sentences(text: str) -> list[str]:
    out = []
    for s in _SENT.findall(text or ""):
        s = " ".join(s.split())
        if 10 <= len(s) <= 120:
            out.append(s)
    return out


def _score_sentence(s: str, keyword: str) -> int:
    score = 0
    if keyword and keyword in s:
        score += 3
    if re.search(r"\d", s):
        score += 2            # 숫자가 든 문장이 영상에서 가장 잘 붙는다
    if any(w in s for w in ("이유", "결론", "하면", "안 되는", "주의", "꼭", "먼저")):
        score += 2
    if 20 <= len(s) <= 70:
        score += 1
    return score


def script(post: Post, keyword: str | None = None, seconds: int = 30) -> str:
    k = keyword or kw.main_keyword(post.title, post.body)
    sents = sentences(post.body)
    ranked = sorted(sents, key=lambda s: _score_sentence(s, k), reverse=True)
    picked: list[str] = []
    for s in ranked:
        if len(picked) >= 4:
            break
        if all(kw_ratio(s, p) < 0.6 for p in picked):
            picked.append(s)
    order = [s for s in sents if s in picked]  # 원문 흐름대로 되돌린다

    hook = f"{k}, 이것만 알면 됩니다"
    if order and re.search(r"\d", order[0]):
        hook = f"{k} 하면서 {re.search(r'[0-9]+', order[0]).group()}가지 실수했습니다"

    lines = [f"# 릴스 대본 ({seconds}초) - {post.title}", "",
             f"노리는 키워드: `{k}`", "",
             "| 초 | 말할 것 | 화면 |", "|---|---|---|",
             f"| 0-3 | {hook} | 얼굴 or 결과물 클로즈업 |"]
    per = max(4, (seconds - 8) // max(1, len(order) or 1))
    t = 3
    for i, s in enumerate(order, 1):
        lines.append(f"| {t}-{t + per} | {s} | 과정 사진 {i} |")
        t += per
    lines.append(f"| {t}-{seconds} | 자세한 순서는 프로필 링크 블로그에 정리해 뒀습니다 "
                 "| 블로그 화면 녹화 |")
    lines += ["",
              "## 올릴 때",
              f"- 캡션 첫 줄에 `{k}` 를 그대로 넣고, 블로그 글 링크를 프로필에 둔다.",
              "- 해시태그: " + " ".join("#" + t.replace(" ", "")
                                         for t in ([k] + kw.longtail(k)[:4])),
              "- 이 표를 그대로 촬영한 뒤 `python -m reels all --input 촬영본.mp4` 로 편집한다.",
              ]
    return "\n".join(lines)


def kw_ratio(a: str, b: str) -> float:
    ta, tb = set(kw.tokenize(a)), set(kw.tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))
