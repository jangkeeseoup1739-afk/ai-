"""다음 4주에 무엇을 쓸지 정해 준다.

주제 하나를 잡고 검색 의도별로 글을 깔아 주제 묶음(스마트블록)을 만드는 순서.
글 유형을 돌려 쓰는 이유는 같은 형태가 반복되면 유사문서로 묶이기 때문이다.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from . import keywords as kw

# (유형, 제목 틀, 글에 꼭 들어가야 하는 것)
FORMS: list[tuple[str, str, str]] = [
    ("방법", "{kw} 방법 총정리 (처음 하는 사람 기준)", "순서 1-2-3, 단계별 사진, 걸린 시간"),
    ("후기", "{kw} 직접 해본 후기 ({year}년 {month}월)", "실제 사진, 쓴 돈, 아쉬운 점"),
    ("비교", "{kw} A vs B 뭐가 나은지 비교", "표 1개, 기준 3개, 결론 한 줄"),
    ("실패", "{kw} 하다 실패한 이유 3가지", "실패 장면 사진, 다시 하면 이렇게"),
    ("목록", "{kw} 체크리스트 {n}가지", "번호 목록, 각 항목 2~3줄"),
    ("가격", "{kw} 가격·비용 얼마 드는지", "실제 영수증·견적, 합계 숫자"),
    ("질문", "{kw} 자주 묻는 질문 정리", "질문을 소제목으로, 답은 3줄 안"),
]


@dataclass
class Slot:
    when: date
    keyword: str
    form: str
    title: str
    must_have: str

    def row(self) -> str:
        return (f"| {self.when:%m/%d} ({'월화수목금토일'[self.when.weekday()]}) "
                f"| {self.keyword} | {self.form} | {self.title} | {self.must_have} |")


def build(main_keyword: str, weeks: int = 4, per_week: int = 3,
          start: date | None = None, place: str = "",
          existing_titles: list[str] | None = None) -> list[Slot]:
    start = start or date.today()
    existing = [t for t in (existing_titles or [])]
    tails = kw.longtail(main_keyword, year=start.year, place=place)
    # 네이버는 평일 오전~점심 유입이 가장 많다. 월·수·금을 기본으로 깐다.
    weekdays = [0, 2, 4, 1, 3, 5, 6][:max(1, min(per_week, 7))]

    slots: list[Slot] = []
    i = 0
    for w in range(weeks):
        monday = start + timedelta(days=(7 - start.weekday()) % 7 + w * 7)
        for wd in sorted(weekdays):
            target = tails[i % len(tails)] if tails else main_keyword
            form, tpl, must = FORMS[i % len(FORMS)]
            title = tpl.format(kw=target, year=monday.year, month=monday.month,
                               n=5 + (i % 3) * 2)
            if any(title == t for t in existing):
                title += " - 다시 정리"
            slots.append(Slot(monday + timedelta(days=wd), target, form, title, must))
            i += 1
    return slots


def render(main_keyword: str, slots: list[Slot], place: str = "") -> str:
    out = [f"# 발행 계획 - 주력 주제 `{main_keyword}`", ""]
    out.append("원칙 3가지")
    out.append("1. 한 주제 안에서만 키워드를 늘린다. 주제가 흩어지면 채널 점수가 안 쌓인다.")
    out.append("2. 발행 간격을 비우지 않는다. 주 3회를 4주만 지켜도 노출이 달라진다.")
    out.append("3. 쓴 글은 2주 뒤에 다시 열어 사진·분량·소제목을 보강한다(수정도 점수에 들어간다).")
    out.append("")
    out.append("| 날짜 | 노리는 키워드 | 유형 | 제목안 | 꼭 들어갈 것 |")
    out.append("|---|---|---|---|---|")
    out += [s.row() for s in slots]
    out.append("")
    out.append("## 글마다 지킬 형식")
    out.append("- 제목 15~35자, 맨 앞에 노리는 키워드 그대로.")
    out.append("- 첫 3줄: 인사말 없이 핵심 키워드 + 결론 한 줄.")
    out.append("- 공백 뺀 1700자 이상, 소제목 3개 이상, 직접 찍은 사진 5장 이상, 짧은 영상 1개.")
    out.append("- 태그 5~10개(하나는 제목 키워드와 똑같이), 같은 주제 내 글 1~2개 링크.")
    out.append("- 발행 시간은 평일 오전 9~11시.")
    return "\n".join(out)
