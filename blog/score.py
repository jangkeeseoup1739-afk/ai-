"""노출 점검: 글 하나와 블로그 전체를 항목별로 채점한다.

기준은 네이버 검색이 공개한 방향(C-Rank = 주제를 꾸준히 깊게,
D.I.A.+ = 검색 의도에 대한 실제 답, 스마트블록 = 주제 묶음 노출)을
글에서 확인할 수 있는 형태로 옮긴 것이다. 점수는 절대 등수가 아니라
"고칠 곳 찾기"용이다.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import timedelta

from . import keywords as kw
from .parse import Post

# 권장값 (글 하나 기준)
MIN_CHARS = 1500          # 공백 뺀 글자 수
GOOD_CHARS = 1700
MIN_IMAGES = 5
MIN_HEADINGS = 3
TAG_RANGE = (5, 10)
TITLE_RANGE = (15, 35)
DENSITY_RANGE = (0.5, 2.0)

AD_PHRASES = ["최저가", "문의 주세요", "전화 주세요", "카톡 주세요", "상담 가능",
              "무료 상담", "협찬", "원고료", "제공받아", "체험단", "구매 링크",
              "쿠팡 파트너스", "수수료를 받을 수 있습니다"]


@dataclass
class Check:
    name: str
    weight: int
    earned: int
    got: str          # 지금 상태
    fix: str = ""     # 고치는 방법 (만점이면 빈 칸)

    @property
    def ok(self) -> bool:
        return self.earned >= self.weight


def _partial(value: float, target: float, weight: int) -> int:
    if target <= 0:
        return weight
    return int(round(min(1.0, value / target) * weight))


@dataclass
class PostDiagnosis:
    post: Post
    keyword: str
    checks: list[Check] = field(default_factory=list)

    @property
    def score(self) -> int:
        return sum(c.earned for c in self.checks)

    @property
    def total(self) -> int:
        return sum(c.weight for c in self.checks)

    @property
    def fixes(self) -> list[Check]:
        return sorted((c for c in self.checks if not c.ok),
                      key=lambda c: c.weight - c.earned, reverse=True)


def score_post(post: Post, keyword: str | None = None) -> PostDiagnosis:
    k = keyword or kw.main_keyword(post.title, post.body)
    ks = k or "없음"   # 제목에 검색어로 쓸 명사가 아예 없는 경우
    title, body = post.title, post.body
    checks: list[Check] = []
    add = checks.append

    # 1. 제목 ------------------------------------------------------------
    tlen = len(title)
    lo, hi = TITLE_RANGE
    add(Check("제목 길이", 8, 8 if lo <= tlen <= hi else (4 if tlen else 0),
              f"{tlen}자",
              "" if lo <= tlen <= hi else
              f"{lo}~{hi}자로. 짧으면 롱테일 수식어(지역·연도·대상)를 붙이고, "
              "길면 검색어가 아닌 감상 표현을 덜어낸다."))

    in_title = kw.count_in(title, k) if k else 0
    add(Check("제목에 핵심 키워드", 10, 10 if in_title else 0,
              f"'{ks}' {in_title}회",
              "" if in_title else
              (f"검색창에 실제로 칠 말('{k}' 같은)을 제목 앞쪽에 그대로 넣는다." if k else
               "제목에 검색할 수 있는 명사가 없다. 감상('오늘 다녀왔어요') 대신 "
               "검색창에 칠 말(지역+대상+행동)을 그대로 쓴다.")))

    add(Check("제목 키워드 반복 과다 아님", 5, 5 if in_title <= 2 else 0,
              f"'{ks}' {in_title}회",
              "" if in_title <= 2 else "같은 말을 제목에서 3번 이상 쓰면 어뷰징으로 본다. 1~2회로."))

    # 2. 검색 의도에 대한 답 (D.I.A.+) -----------------------------------
    head = post.first_paragraph[:300]
    add(Check("첫 문단에 키워드+결론", 10,
              10 if (k and kw.count_in(head, k)) else 0,
              f"첫 문단 {len(head)}자, 키워드 {kw.count_in(head, k) if k else 0}회",
              "" if (k and kw.count_in(head, k)) else
              "첫 3줄에 핵심 키워드와 '결론 한 줄'을 먼저 쓴다. "
              "인사말로 시작하면 이탈이 늘고 체류시간이 떨어진다."))

    chars = post.char_count
    add(Check("본문 분량", 15, _partial(chars, GOOD_CHARS, 15), f"{chars}자(공백 제외)",
              "" if chars >= MIN_CHARS else
              f"{MIN_CHARS}자 이상으로. 지금보다 {max(0, MIN_CHARS - chars)}자 더 필요하다. "
              "직접 겪은 과정·숫자·실패한 이유를 넣어 늘린다(같은 말 반복은 역효과)."))

    d = kw.density(body, k)
    dlo, dhi = DENSITY_RANGE
    add(Check("키워드 밀도", 12,
              12 if dlo <= d <= dhi else (6 if d else 0),
              f"{d}% ('{ks}' {kw.count_in(body, k) if k else 0}회)",
              "" if dlo <= d <= dhi else
              ((f"밀도가 낮다. 본문에 '{k}'를 {dlo}~{dhi}% 수준으로(대략 "
                f"{max(1, int(chars * dlo / 100 / max(1, len(k))))}회 이상) "
                "자연스럽게 넣는다." if k else
                "노리는 키워드 자체가 없다. 먼저 제목을 검색어로 바꾸고, "
                "그 말을 본문에도 쓴다.")
               if d < dlo else
               "밀도가 높다. 같은 키워드 반복을 줄이고 유사어로 바꾼다.")))

    # 3. 체류시간을 만드는 구성 -------------------------------------------
    add(Check("이미지", 10, _partial(post.images, MIN_IMAGES, 10), f"{post.images}장",
              "" if post.images >= MIN_IMAGES else
              f"직접 찍은 사진 {MIN_IMAGES}장 이상. 퍼온 이미지는 유사문서로 묶일 수 있다."))

    add(Check("동영상", 5, 5 if post.videos else 0, f"{post.videos}개",
              "" if post.videos else
              "15~30초짜리 짧은 영상 1개만 넣어도 체류시간이 확 올라간다. "
              "릴스 편집 결과물을 그대로 올리면 된다."))

    add(Check("소제목 구조", 8, _partial(len(post.headings), MIN_HEADINGS, 8),
              f"{len(post.headings)}개",
              "" if len(post.headings) >= MIN_HEADINGS else
              f"소제목을 {MIN_HEADINGS}개 이상 넣어 단락을 나눈다. "
              "스마트블록은 '질문-답' 구조를 잘 집어간다."))

    # 4. 태그·링크 --------------------------------------------------------
    n_tags = len(post.tags)
    tag_has_kw = any(k and k in t for t in post.tags)
    tag_score = 0
    if TAG_RANGE[0] <= n_tags <= TAG_RANGE[1]:
        tag_score += 4
    elif n_tags:
        tag_score += 2
    if tag_has_kw:
        tag_score += 3
    add(Check("태그", 7, tag_score, f"{n_tags}개" + (", 핵심 키워드 포함" if tag_has_kw else ""),
              "" if tag_score == 7 else
              f"태그 {TAG_RANGE[0]}~{TAG_RANGE[1]}개, 그중 하나는 핵심 키워드와 똑같이. "
              "관련 없는 인기 태그를 달면 감점된다."))

    add(Check("내 글끼리 연결", 5, 5 if post.internal_links else 0,
              f"내부 {post.internal_links} / 외부 {post.external_links}",
              "" if post.internal_links else
              "같은 주제의 내 글 1~2개를 본문에 링크한다. 주제 묶음이 생겨 C-Rank에 유리하고 "
              "한 명이 두 글을 읽게 된다."))

    found_ads = [p for p in AD_PHRASES if p in body]
    add(Check("광고성 문구 과다 아님", 5, 5 if len(found_ads) <= 1 else 0,
              ", ".join(found_ads) or "없음",
              "" if len(found_ads) <= 1 else
              "홍보 문구가 많으면 상업성 글로 분류돼 노출이 깎인다. "
              "대가성 표기는 한 번만 남기고 나머지는 정리한다."))
    return PostDiagnosis(post=post, keyword=k, checks=checks)


# --------------------------------------------------------------------------
# 블로그 전체


def _shingles(text: str, n: int = 12) -> set[str]:
    flat = re.sub(r"\s+", "", text)
    return {flat[i:i + n] for i in range(0, max(0, len(flat) - n), n // 2 or 1)}


def similarity(a: str, b: str) -> float:
    sa, sb = _shingles(a), _shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


@dataclass
class BlogDiagnosis:
    blog_id: str
    posts: list[Post]
    diagnoses: list[PostDiagnosis]
    checks: list[Check] = field(default_factory=list)
    clusters: list[tuple[str, int]] = field(default_factory=list)
    cannibal: list[tuple[str, list[str]]] = field(default_factory=list)
    similar_pairs: list[tuple[str, str, float]] = field(default_factory=list)

    @property
    def avg_score(self) -> float:
        if not self.diagnoses:
            return 0.0
        return round(sum(d.score for d in self.diagnoses) / len(self.diagnoses), 1)

    @property
    def weakest(self) -> list[tuple[str, int, int]]:
        """항목별로 모든 글에서 깎인 점수 합계. 많이 깎인 것부터."""
        lost: Counter[str] = Counter()
        full: Counter[str] = Counter()
        for d in self.diagnoses:
            for c in d.checks:
                lost[c.name] += c.weight - c.earned
                full[c.name] += c.weight
        return [(n, lost[n], full[n]) for n, _ in lost.most_common() if lost[n]]


def score_blog(blog_id: str, posts: list[Post]) -> BlogDiagnosis:
    diags = [score_post(p) for p in posts]
    checks: list[Check] = []
    add = checks.append

    # 발행 주기 -----------------------------------------------------------
    dated = sorted([p for p in posts if p.published_at],
                   key=lambda p: p.published_at)
    if len(dated) >= 2:
        span = (dated[-1].published_at - dated[0].published_at) or timedelta(days=1)
        weeks = max(1.0, span.days / 7)
        per_week = round(len(dated) / weeks, 1)
        gaps = [(b.published_at - a.published_at).days
                for a, b in zip(dated, dated[1:])]
        long_gaps = sum(1 for g in gaps if g >= 7)
        add(Check("발행 주기", 20,
                  20 if per_week >= 2 else (12 if per_week >= 1 else 4),
                  f"주 {per_week}회, 7일 이상 쉰 구간 {long_gaps}번",
                  "" if per_week >= 2 else
                  "주 2~3회로 올린다. C-Rank는 '꾸준함'을 채널 점수로 본다. "
                  "일주일 넘게 비면 그동안 쌓인 점수가 내려간다."))
    else:
        add(Check("발행 주기", 20, 0, "글 수가 적어 판단 불가",
                  "최근 4주 동안 최소 8편은 있어야 주기를 평가할 수 있다."))

    # 주제 집중도 ---------------------------------------------------------
    clusters = kw.cluster([(p.title, p.body) for p in posts])
    n = max(1, len(posts))
    top_share = (clusters[0][1] / n) if clusters else 0
    add(Check("주제 집중도", 25,
              25 if top_share >= 0.5 else (15 if top_share >= 0.3 else 5),
              (f"1위 주제 '{clusters[0][0]}'가 {clusters[0][1]}/{n}편 "
               f"({int(top_share * 100)}%)" if clusters else "반복 주제 없음"),
              "" if top_share >= 0.5 else
              "한 주제가 전체의 절반을 넘게 만든다. 주제가 흩어지면 C-Rank가 "
              "'이 블로그는 무슨 블로그'인지 못 잡아 어떤 키워드에서도 밀린다. "
              "큰 주제 1개 + 곁주제 1개로 좁히고, 그 안에서 세부 키워드를 늘린다."))

    # 자기잠식 (같은 키워드로 여러 글) -------------------------------------
    by_kw: dict[str, list[str]] = {}
    for d in diags:
        by_kw.setdefault(d.keyword, []).append(d.post.title)
    cannibal = [(k, v) for k, v in by_kw.items() if len(v) >= 3 and k]
    add(Check("같은 키워드 중복 아님", 15, 15 if not cannibal else 5,
              ", ".join(f"{k}({len(v)}편)" for k, v in cannibal) or "없음",
              "" if not cannibal else
              "같은 키워드로 3편 이상이면 내 글끼리 순위를 나눠 먹는다. "
              "가장 잘 쓴 한 편으로 내용을 합치고, 나머지는 다른 세부 키워드로 제목을 바꾼다."))

    # 유사문서 위험 -------------------------------------------------------
    similar: list[tuple[str, str, float]] = []
    for i, a in enumerate(posts):
        for b in posts[i + 1:]:
            s = similarity(a.body, b.body)
            if s >= 0.25:
                similar.append((a.title, b.title, round(s, 2)))
    similar.sort(key=lambda x: x[2], reverse=True)
    add(Check("유사문서 위험 낮음", 15, 15 if not similar else 5,
              f"겹치는 글 {len(similar)}쌍" if similar else "없음",
              "" if not similar else
              "본문이 많이 겹치면 유사문서로 묶여 한 편만 노출된다. "
              "공통 인사말·안내 문구 템플릿을 지우고 사례·숫자를 글마다 다르게 쓴다."))

    # 평균 글 품질 --------------------------------------------------------
    avg = sum(d.score for d in diags) / max(1, len(diags))
    add(Check("글 평균 점수", 25, int(round(avg / 100 * 25)), f"{round(avg, 1)}/100",
              "" if avg >= 80 else "글 단위 점검표에서 깎인 항목부터 고친다."))

    return BlogDiagnosis(blog_id=blog_id, posts=posts, diagnoses=diags,
                         checks=checks, clusters=clusters, cannibal=cannibal,
                         similar_pairs=similar[:10])
