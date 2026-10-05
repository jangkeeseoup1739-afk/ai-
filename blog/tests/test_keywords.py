"""조사 떼기·키워드 세기·롱테일·주제 묶기."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from blog import keywords as kw        # noqa: E402


def test_strip_particle() -> None:
    assert kw.strip_particle("상추를") == "상추"
    assert kw.strip_particle("텃밭에서") == "텃밭"
    assert kw.strip_particle("비료로") == "비료"
    # 2글자가 안 남으면 떼지 않는다
    assert kw.strip_particle("물을") == "물을"
    print("  조사 떼기 OK")


def test_tokenize_drops_stopwords() -> None:
    toks = kw.tokenize("안녕하세요 오늘은 상추를 심었습니다 그리고 물을 줬어요")
    assert "상추" in toks
    assert "안녕하세요" not in toks and "그리고" not in toks
    print(f"  불용어 제거 OK {toks}")


def test_density_and_count() -> None:
    text = "상추 심기. " * 10
    assert kw.count_in(text, "상추") == 10
    d = kw.density(text, "상추")
    assert 10 < d < 50, d          # 공백 뺀 글자 수 기준
    assert kw.density("", "상추") == 0.0
    print(f"  밀도 계산 OK ({d}%)")


def test_main_keyword_prefers_body_repeats() -> None:
    title = "베란다 상추 키우는 방법"
    body = "상추 " * 20 + "베란다 " * 2
    assert kw.main_keyword(title, body) == "상추"
    assert kw.main_keyword("", "") == ""
    print("  핵심 키워드 추정 OK")


def test_longtail() -> None:
    tails = kw.longtail("상추", year=2026, place="수원")
    assert "수원 상추" == tails[0]
    assert any(t == "상추 후기" for t in tails)
    assert any("2026" in t for t in tails)
    assert kw.longtail("") == []
    print(f"  롱테일 {len(tails)}개 OK")


def test_cluster_counts_documents_not_words() -> None:
    docs = [("상추 키우기", "상추 " * 5 + "물주기"),
            ("상추 수확", "상추 " * 5 + "벌레"),
            ("고양이 간식", "고양이 " * 5)]
    clusters = dict(kw.cluster(docs))
    assert clusters.get("상추") == 2, clusters
    assert "고양이" not in clusters      # 한 편에만 나온 말은 빠진다
    print(f"  주제 묶기 OK {clusters}")


def main() -> int:
    test_strip_particle()
    test_tokenize_drops_stopwords()
    test_density_and_count()
    test_main_keyword_prefers_body_repeats()
    test_longtail()
    test_cluster_counts_documents_not_words()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
