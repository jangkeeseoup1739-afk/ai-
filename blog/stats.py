"""블로그 통계에서 내려받은 표(CSV)를 읽어 유입 현황을 정리한다.

네이버 블로그 > 통계 > 유입분석 / 검색 유입 화면에서 내려받은 파일을
CSV로 저장해 넣으면 된다(엑셀에서 '다른 이름으로 저장 > CSV UTF-8').
열 이름이 화면마다 달라서 이름에 들어간 말로 찾는다.
"""
from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

KEY_COLS = ("검색어", "키워드", "유입경로", "경로", "keyword", "referrer")
NUM_COLS = ("조회", "유입", "건수", "횟수", "수", "count", "pv")
SEARCH_HINTS = ("검색", "search", "naver.com/search", "google", "daum", "bing")


@dataclass
class Inflow:
    rows: list[tuple[str, float]] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(v for _, v in self.rows)

    def top(self, n: int = 20) -> list[tuple[str, float]]:
        return sorted(self.rows, key=lambda r: r[1], reverse=True)[:n]

    @property
    def search_share(self) -> float:
        """검색으로 들어온 비중(%). 이 값이 낮으면 노출이 아니라 지인 유입이다."""
        if not self.total:
            return 0.0
        s = sum(v for k, v in self.rows
                if any(h in k.lower() for h in SEARCH_HINTS))
        return round(s / self.total * 100, 1)


def _pick(header: list[str], hints: tuple[str, ...], skip: int | None = None
          ) -> int | None:
    # 힌트 순서가 우선순위다. "유입경로"는 경로 열이면서 "유입"도 품고 있어서
    # 이미 고른 열(skip)은 건너뛴다.
    for hint in hints:
        for i, h in enumerate(header):
            if i == skip:
                continue
            if hint.lower() in (h or "").lower():
                return i
    return None


def load(path: str | Path) -> Inflow:
    text = Path(path).expanduser().read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            decoded = text.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        decoded = text.decode("utf-8", "replace")

    reader = list(csv.reader(io.StringIO(decoded)))
    header_i = 0
    for i, row in enumerate(reader[:10]):  # 위쪽에 안내 줄이 붙어 오는 경우가 있다
        if _pick(row, KEY_COLS) is not None:
            header_i = i
            break
    if not reader:
        return Inflow()
    header = reader[header_i]
    ki = _pick(header, KEY_COLS) or 0
    vi = _pick(header, NUM_COLS, skip=ki)

    agg: Counter[str] = Counter()
    for row in reader[header_i + 1:]:
        if len(row) <= ki or not row[ki].strip():
            continue
        key = row[ki].strip()
        val = 1.0
        if vi is not None and len(row) > vi:
            raw = row[vi].replace(",", "").strip()
            try:
                val = float(raw)
            except ValueError:
                val = 1.0
        agg[key] += val
    return Inflow(rows=list(agg.items()))
