"""진단 결과를 마크다운 리포트로 쓴다. 그대로 읽고 바로 고칠 수 있게."""
from __future__ import annotations

from datetime import datetime

from . import keywords as kw
from .score import BlogDiagnosis, PostDiagnosis
from .stats import Inflow

MARK = {True: "O", False: "X"}


def _bar(earned: int, weight: int, width: int = 10) -> str:
    filled = int(round(earned / weight * width)) if weight else width
    return "#" * filled + "." * (width - filled)


def post_section(d: PostDiagnosis, detail: bool = True) -> str:
    p = d.post
    lines = [f"### [{d.score}/{d.total}] {p.title or '(제목 없음)'}"]
    meta = [f"핵심 키워드 `{d.keyword or '없음'}`", f"{p.char_count}자",
            f"사진 {p.images}", f"영상 {p.videos}", f"소제목 {len(p.headings)}",
            f"태그 {len(p.tags)}"]
    if p.published_at:
        meta.insert(0, p.published_at.strftime("%Y-%m-%d"))
    lines.append(" · ".join(meta))
    if p.url:
        lines.append(f"{p.url}")
    lines.append("")
    if detail:
        lines += ["| | 항목 | 점수 | 지금 | 고칠 것 |", "|---|---|---|---|---|"]
        for c in d.checks:
            lines.append(f"| {MARK[c.ok]} | {c.name} | {c.earned}/{c.weight} "
                         f"| {c.got} | {c.fix or '-'} |")
    else:
        for c in d.fixes[:3]:
            lines.append(f"- **{c.name}** ({c.earned}/{c.weight}) {c.got} -> {c.fix}")
    lines.append("")
    return "\n".join(lines)


def render(bd: BlogDiagnosis, inflow: Inflow | None = None,
           detail_posts: int = 5) -> str:
    n = len(bd.posts)
    out: list[str] = []
    step = iter(range(1, 99))           # 통계 CSV가 없으면 번호가 비지 않게 센다

    def head(title: str) -> str:
        return f"## {next(step)}. {title}"

    out.append(f"# {bd.blog_id} 블로그 노출·유입 진단")
    out.append(f"뽑은 날짜 {datetime.now().strftime('%Y-%m-%d')} · 분석한 글 {n}편 "
               f"· 글 평균 {bd.avg_score}/100")
    out.append("")

    # 1. 블로그 전체
    out.append(head("블로그 전체 (채널 점수)"))
    out.append("같은 글이라도 채널이 약하면 아예 안 걸린다. 여기가 먼저다.")
    out.append("")
    out.append("| | 항목 | 점수 | | 지금 | 고칠 것 |")
    out.append("|---|---|---|---|---|---|")
    for c in bd.checks:
        out.append(f"| {MARK[c.ok]} | {c.name} | {c.earned}/{c.weight} "
                   f"| `{_bar(c.earned, c.weight)}` | {c.got} | {c.fix or '-'} |")
    out.append("")

    # 2. 주제
    out.append(head("무슨 블로그로 보이는가"))
    if bd.clusters:
        out.append("몇 편의 글에 걸쳐 나온 말 (= 검색이 이 블로그의 전문 분야로 읽는 것)")
        out.append("")
        out.append("| 주제어 | 걸친 글 | 비중 |")
        out.append("|---|---|---|")
        for word, cnt in bd.clusters[:12]:
            out.append(f"| {word} | {cnt}편 | {int(cnt / max(1, n) * 100)}% |")
    else:
        out.append("글 사이에 반복되는 주제어가 없다. 검색이 이 블로그의 분야를 못 잡는 상태다.")
    out.append("")

    # 3. 유입 (통계 CSV가 있을 때만)
    if inflow and inflow.rows:
        out.append(head("실제 유입"))
        out.append(f"합계 {int(inflow.total)} · 검색 유입 비중 **{inflow.search_share}%**")
        if inflow.search_share < 50:
            out.append("")
            out.append("> 검색 비중이 절반도 안 된다. 글이 아니라 노출이 문제라는 뜻이다. "
                       "아래 키워드 작업이 1순위다.")
        out.append("")
        out.append("| 유입 경로·검색어 | 수 |")
        out.append("|---|---|")
        for k, v in inflow.top(20):
            out.append(f"| {k} | {int(v)} |")
        out.append("")

    # 4. 많이 깎인 항목
    out.append(head("전체에서 가장 많이 깎인 항목"))
    out.append("한 번 손보면 모든 글이 같이 올라가는 순서다.")
    out.append("")
    out.append("| 항목 | 깎인 점수 | 만점 |")
    out.append("|---|---|---|")
    for name, lost, full in bd.weakest[:8]:
        out.append(f"| {name} | -{lost} | {full} |")
    out.append("")

    # 5. 중복·유사
    if bd.cannibal or bd.similar_pairs:
        out.append(head("내 글끼리 부딪히는 곳"))
        for k, titles in bd.cannibal:
            out.append(f"- `{k}` 로 {len(titles)}편: " + ", ".join(titles[:4]))
        for a, b, s in bd.similar_pairs:
            out.append(f"- 본문 {int(s * 100)}% 겹침: \"{a}\" <-> \"{b}\"")
        out.append("")

    # 6. 글별
    out.append(head("글별 점검표"))
    ranked = sorted(bd.diagnoses, key=lambda d: d.score)
    out.append(f"점수가 낮은 {min(detail_posts, len(ranked))}편은 항목 전체, "
               "나머지는 고칠 것만 적었다.")
    out.append("")
    for i, d in enumerate(ranked):
        out.append(post_section(d, detail=i < detail_posts))

    # 7. 다음에 쓸 것
    out.append(head("다음에 쓸 글 (롱테일 후보)"))
    if bd.clusters:
        main = bd.clusters[0][0]
        out.append(f"주력 주제 `{main}` 에서 바로 쓸 수 있는 제목 후보:")
        out.append("")
        for t in kw.longtail(main, year=datetime.now().year)[:12]:
            out.append(f"- {t}")
    else:
        out.append("주력 주제가 아직 없다. 가장 자신 있는 주제 하나를 정하고 "
                   "`python -m blog plan --keyword <주제>` 로 4주 계획을 먼저 받는다.")
    out.append("")
    return "\n".join(out)
