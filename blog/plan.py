"""다음 4주에 무엇을 쓸지 정해 준다.

주제 하나를 잡고 검색 의도별로 글을 깔아 주제 묶음(스마트블록)을 만드는 순서.
글 유형을 돌려 쓰는 이유는 같은 형태가 반복되면 유사문서로 묶이기 때문이다.
유형마다 노리는 키워드가 따로 있어서, 4주를 돌면 세부 키워드가 12개 깔린다.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

# (유형, 노리는 키워드에 붙일 말, 제목 틀, 글에 꼭 들어가야 하는 것)
Form = tuple[str, str, str, str]

FORMS: list[Form] = [
    ("방법", "방법", "{kw} 방법 총정리 (처음 하는 사람 기준)",
     "순서 1-2-3, 단계별 사진, 걸린 시간"),
    ("후기", "후기", "{kw} 직접 해본 후기 ({year}년 {month}월)",
     "실제 사진, 쓴 돈, 아쉬운 점"),
    ("비교", "비교", "{kw} A vs B 뭐가 나은지 비교",
     "표 1개, 기준 3개, 결론 한 줄"),
    ("실패", "실패 이유", "{kw} 하다 실패한 이유 3가지",
     "실패 장면 사진, 다시 하면 이렇게"),
    ("목록", "체크리스트", "{kw} 체크리스트 {n}가지",
     "번호 목록, 각 항목 2~3줄"),
    ("가격", "가격", "{kw} 가격·비용 얼마 드는지",
     "실제 영수증·견적, 합계 숫자"),
    ("질문", "자주 묻는 질문", "{kw} 자주 묻는 질문 정리",
     "질문을 소제목으로, 답은 3줄 안"),
]

# 부동산·지역 영업(중개·분양·임대)용. 중개사만 쓸 수 있는 것(현장·숫자·사례)을 강제한다.
ESTATE_FORMS: list[Form] = [
    ("시세", "시세", "{kw} 시세 지금 얼마인가 ({year}년 {month}월 기준)",
     "실제 매물 3건 표, 평당가, 전달 대비 변화"),
    ("현장", "", "{kw} 직접 가서 보고 왔습니다",
     "건물 외관·내부·주차장 사진, 역에서 걸어서 몇 분, 아쉬운 점"),
    ("공실", "공실", "{kw} 공실 많다는데 실제로 돌아보니",
     "층별 공실 현황, 비어 있는 이유, 사진"),
    ("임대료", "임대료", "{kw} 임대료 얼마에 나가나",
     "최근 계약 사례 3건, 평당 임대료, 권리금 유무"),
    ("조건", "입주 조건", "{kw} 입주 가능 업종과 조건 정리",
     "업종 목록, 안 되는 경우, 확인 방법"),
    ("비교", "비교", "{kw} vs 인근 단지 비교",
     "표 1개(평당가·전용률·주차·공실), 결론 한 줄"),
    ("비용", "실투자금", "{kw} 실제로 드는 돈 전부 (취득세·대출·관리비)",
     "숫자 표 1개, 합계, 월 부담액"),
    ("주의", "계약 전 확인", "{kw} 계약 전 꼭 확인할 {n}가지",
     "실제 계약서 조항, 놓쳐서 생긴 사례"),
    ("상담", "자주 묻는 질문", "{kw} 문의 중 가장 많은 질문 {n}가지",
     "실제 받은 질문 그대로, 답은 3줄 안"),
    ("대출", "대출", "{kw} 대출 얼마나 나오나 (한도·금리)",
     "실제 승인 사례, 은행별 차이, 월 이자"),
    ("정책", "제도 변경", "{kw}, 제도 바뀌고 현장은 이렇게 달라졌다",
     "발표 요약은 30%만, 나머지는 내 손님 사례와 해석"),
    ("전망", "전망", "{kw} 지금 들어가도 되나",
     "공실·거래량 숫자, 내 판단과 근거, 반대 의견도"),
]

PRESETS: dict[str, list[Form]] = {"기본": FORMS, "부동산": ESTATE_FORMS}


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
          existing_titles: list[str] | None = None,
          preset: str = "기본") -> list[Slot]:
    start = start or date.today()
    existing = list(existing_titles or [])
    forms = PRESETS.get(preset, FORMS)
    base = " ".join(x for x in (place, main_keyword) if x).strip()
    # 네이버는 평일 오전~점심 유입이 가장 많다. 월·수·금을 기본으로 깐다.
    weekdays = sorted([0, 2, 4, 1, 3, 5, 6][:max(1, min(per_week, 7))])

    slots: list[Slot] = []
    i = 0
    for w in range(weeks):
        monday = start + timedelta(days=(7 - start.weekday()) % 7 + w * 7)
        for wd in weekdays:
            form, tail, tpl, must = forms[i % len(forms)]
            when = monday + timedelta(days=wd)
            title = tpl.format(kw=base, year=when.year, month=when.month,
                               n=5 + (i % 3) * 2)
            if title in existing:
                title += " - 다시 정리"
            keyword = " ".join(x for x in (base, tail) if x)
            slots.append(Slot(when, keyword, form, title, must))
            i += 1
    return slots


def render(main_keyword: str, slots: list[Slot], place: str = "") -> str:
    base = " ".join(x for x in (place, main_keyword) if x).strip()
    out = [f"# 발행 계획 - 주력 주제 `{base}`", ""]
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
