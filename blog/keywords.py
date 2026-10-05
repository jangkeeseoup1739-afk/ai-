"""한국어 키워드 뽑기와 롱테일 제안.

형태소 분석기(konlpy 등)를 깔지 않아도 돌아가게 정규식으로 처리한다.
조사만 떼고 2글자 이상 명사처럼 생긴 토큰을 센다. 완벽하지는 않지만
"이 글이 어떤 키워드로 쓰였는지"를 보는 데는 충분하다.
"""
from __future__ import annotations

import re
from collections import Counter

# 자주 붙는 조사·어미. 긴 것부터 떼야 한다.
PARTICLES = sorted([
    "으로써", "으로서", "에서는", "에게는", "이라는", "라는", "까지", "부터", "에서",
    "에게", "한테", "으로", "로서", "로써", "이나", "이란", "라도", "이며", "하고",
    "보다", "처럼", "만큼", "조차", "마저", "이라", "으로의", "에는", "에도", "이다",
    "입니다", "했습니다", "합니다", "하는", "해서", "하고요", "은", "는", "이", "가",
    "을", "를", "의", "에", "도", "만", "와", "과", "로", "야", "여", "며", "랑",
], key=len, reverse=True)

STOPWORDS = {
    "그리고", "그래서", "하지만", "그런데", "그러나", "때문", "정말", "진짜", "조금",
    "다시", "이번", "저는", "제가", "우리", "여러분", "오늘", "어제", "내일", "요즘",
    "이거", "그거", "저거", "이런", "저런", "그런", "것을", "것이", "수가", "수는",
    "있는", "없는", "같은", "많은", "좋은", "대한", "위해", "통해", "하나", "먼저",
    "바로", "매우", "아주", "너무", "정도", "경우", "부분", "생각", "느낌", "시간",
    "사람", "사진", "이미지", "블로그", "포스팅", "안녕하세요", "감사합니다", "구독",
    "댓글", "공감", "클릭", "링크", "여기", "거기", "확인", "참고", "관련", "내용",
    "하시면", "하면", "되는", "된다", "한번", "다음", "마지막", "시작", "준비",
    "적당", "직접", "간단", "복잡", "가능", "필요", "중요", "다양", "충분", "정확",
}

# 조사가 붙은 한 글자 명사("잎이", "약을")는 떼면 한 글자만 남아 키워드로 못 쓴다.
TAIL_PARTICLES = ("이", "가", "을", "를", "은", "는", "의", "에", "도", "와", "과", "로")
# 용언이 활용된 꼴. 짧은 토큰("잡아", "치지")은 한 글자 어미로 걸러낸다.
TAIL_ENDINGS = ("고", "며", "서", "면", "데", "죠", "네", "야", "구", "지", "니",
                "아", "어", "게", "도", "자")
# 길이에 상관없이 걸러내는 활용 어미("않았습니다", "해봤는데").
VERB_TAILS = ("습니다", "니다", "세요", "어요", "아요", "였다", "했다", "한다", "된다",
              "겠다", "는데", "아서", "어서", "려고", "면서", "으며", "았다", "었다",
              "지만", "거나", "도록", "라고", "으로", "더라", "네요", "구나")

# 주제가 아니라 '검색 의도'를 나타내는 말. 주제 묶기에서는 뺀다.
GENERIC = {"방법", "총정리", "정리", "기준", "초보", "후기", "추천", "가격", "비용",
           "순서", "준비물", "주의사항", "비교", "차이", "장단점", "리뷰", "실패",
           "체크리스트", "키우", "만들", "하기", "보기", "쓰기", "먹기", "유지"}

_TOKEN = re.compile(r"[가-힣]{2,}|[A-Za-z]{3,}|\d+[가-힣A-Za-z]+")


def strip_particle(word: str) -> str:
    if not re.fullmatch(r"[가-힣]+|\d+[가-힣]+", word):
        return word
    for p in PARTICLES:
        if word.endswith(p) and len(word) - len(p) >= 2:
            rest = word[: -len(p)]
            # "손으로" -> "로"를 떼면 "손으"가 남는다. 이런 꼴은 버린다.
            return rest if not rest.endswith(("으", "하")) else word
    return word


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    for raw in _TOKEN.findall(text or ""):
        w = strip_particle(raw)
        if len(w) < 2 or w in STOPWORDS:
            continue
        if re.fullmatch(r"[가-힣]{2}", w) and w.endswith(TAIL_PARTICLES):
            continue
        if len(w) <= 3 and w.endswith(TAIL_ENDINGS):
            continue
        if w.endswith(VERB_TAILS):
            continue
        out.append(w.lower() if re.fullmatch(r"[A-Za-z]+", w) else w)
    return out


def top_keywords(text: str, n: int = 15) -> list[tuple[str, int]]:
    return Counter(tokenize(text)).most_common(n)


def count_in(text: str, keyword: str) -> int:
    """키워드가 글에 몇 번 나오는지. 조사가 붙은 형태도 센다."""
    if not keyword:
        return 0
    return len(re.findall(re.escape(keyword), text or ""))


def density(text: str, keyword: str) -> float:
    """키워드 밀도(%). 공백 뺀 글자 수 기준."""
    chars = len(re.sub(r"\s+", "", text or ""))
    if not chars or not keyword:
        return 0.0
    return round(count_in(text, keyword) * len(keyword) / chars * 100, 2)


def main_keyword(title: str, body: str = "") -> str:
    """이 글이 노리는 키워드로 보이는 말 하나.

    제목에 있는 토큰 중 본문에서 가장 많이 반복된 것을 고른다.
    제목이 곧 노리는 키워드라는 네이버 검색의 전제를 따른다.
    """
    cand = tokenize(title)
    if not cand:
        return ""
    if not body:
        return max(cand, key=len)
    counts = Counter(tokenize(body))
    return max(cand, key=lambda w: (counts.get(w, 0), len(w)))


# 검색 의도를 붙여 롱테일을 만드는 수식어. 앞/뒤 붙이는 자리를 나눠 둔다.
INTENT_SUFFIX = ["후기", "추천", "방법", "가격", "비용", "순서", "준비물", "주의사항",
                 "비교", "차이", "장단점", "실패 이유", "초보", "총정리", "체크리스트"]
INTENT_PREFIX = ["처음", "혼자", "집에서", "직접", "하루만에", "무료로"]


def longtail(keyword: str, year: int | None = None, place: str = "") -> list[str]:
    """핵심 키워드 하나에서 노려볼 롱테일 조합을 만든다."""
    if not keyword:
        return []
    out = [f"{keyword} {s}" for s in INTENT_SUFFIX]
    out += [f"{p} {keyword}" for p in INTENT_PREFIX]
    if year:
        out.append(f"{year} {keyword}")
        out.append(f"{keyword} {year} 기준")
    if place:
        out.insert(0, f"{place} {keyword}")
        out.insert(1, f"{place} {keyword} 추천")
    return out


def cluster(titles_bodies: list[tuple[str, str]], min_posts: int = 2
            ) -> list[tuple[str, int]]:
    """글 전체에서 반복되는 주제 키워드. C-Rank가 보는 '주제 집중도'용.

    한 글 안에서 몇 번 나왔는지는 보지 않고, 몇 개의 글에 걸쳐 나왔는지를 센다.
    """
    doc_freq: Counter[str] = Counter()
    in_title: Counter[str] = Counter()
    total: Counter[str] = Counter()
    for title, body in titles_bodies:
        body_counts = Counter(tokenize(body))
        title_words = set(tokenize(title))
        in_title.update(title_words)
        total.update(body_counts)
        cand = title_words | {w for w, c in body_counts.items() if c >= 3}
        doc_freq.update(cand - GENERIC)
    # 같은 수의 글에 걸렸다면 제목에 쓰인 말, 그다음 많이 쓰인 말을 주제로 본다.
    ranked = sorted(doc_freq.items(),
                    key=lambda kv: (kv[1], in_title[kv[0]], total[kv[0]]),
                    reverse=True)
    return [(w, c) for w, c in ranked[:30] if c >= min_posts]
