"""채점: 좋은 글은 만점, 빈약한 글은 고칠 것이 나오고, 블로그 전체 항목도 잡힌다."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from blog import score                   # noqa: E402
from blog.parse import parse_post        # noqa: E402
from blog.tests import _fixtures as fx   # noqa: E402


def test_good_post_scores_full() -> None:
    d = score.score_post(parse_post(fx.long_post(), "myid", "1"))
    assert d.keyword == "상추", d.keyword
    assert d.score == d.total == 100, [(c.name, c.earned) for c in d.checks]
    assert d.fixes == []
    print(f"  잘 쓴 글 {d.score}/{d.total} OK")


def test_thin_post_lists_fixes() -> None:
    d = score.score_post(parse_post(fx.thin_post(), "myid", "2"))
    assert d.score < 45, d.score
    names = [c.name for c in d.fixes]
    for expected in ("본문 분량", "이미지", "소제목 구조", "태그"):
        assert expected in names, names
    assert all(c.fix for c in d.fixes)          # 고칠 방법이 비어 있으면 리포트가 무의미하다
    assert d.fixes[0].weight - d.fixes[0].earned >= d.fixes[-1].weight - d.fixes[-1].earned
    print(f"  빈약한 글 {d.score}/{d.total}, 고칠 것 {len(d.fixes)}개 OK")


def test_repeat_rate_is_length_aware() -> None:
    # 긴 키워드도 "1500자에 5~15회"면 통과해야 한다 (밀도 기준이면 떨어졌다)
    body = ["지식산업센터 공실을 직접 보고 왔습니다. " + "현장 이야기를 적습니다. " * 12] * 8
    d = score.score_post(parse_post(fx.post_html("주안 지식산업센터 공실 정리", body)),
                         keyword="지식산업센터")
    c = next(c for c in d.checks if c.name == "키워드 반복")
    assert c.ok, c.got
    print(f"  긴 키워드 반복 기준 OK ({c.got})")


def test_ad_phrases_and_density_bounds() -> None:
    body = ["최저가 문의 주세요. 카톡 주세요. 상담 가능합니다."] * 5
    d = score.score_post(parse_post(fx.post_html("최저가 문의", body), "myid", "3"))
    ad = next(c for c in d.checks if c.name == "광고성 문구 과다 아님")
    assert not ad.ok and "최저가" in ad.got
    print(f"  광고 문구 적발 OK ({ad.got})")


def test_keyword_stuffing_in_title() -> None:
    d = score.score_post(
        parse_post(fx.post_html("상추 상추 상추 키우기", ["상추 " * 50]), "myid", "4"),
        keyword="상추")
    rep = next(c for c in d.checks if c.name == "제목 키워드 반복 과다 아님")
    dens = next(c for c in d.checks if c.name == "키워드 반복")
    assert not rep.ok and not dens.ok
    print("  제목 키워드 남용·밀도 과다 적발 OK")


def test_blog_level() -> None:
    posts = [parse_post(fx.long_post(), "myid", str(i)) for i in range(3)]
    posts.append(parse_post(fx.thin_post(), "myid", "9"))
    bd = score.score_blog("myid", posts)
    by_name = {c.name: c for c in bd.checks}

    # 같은 글 3편이 들어갔으므로 자기잠식과 유사문서가 모두 걸려야 한다
    assert not by_name["같은 키워드 중복 아님"].ok, by_name["같은 키워드 중복 아님"].got
    assert not by_name["유사문서 위험 낮음"].ok
    assert bd.similar_pairs and bd.similar_pairs[0][2] > 0.5
    assert bd.clusters and bd.clusters[0][0] == "상추"
    assert bd.weakest and bd.weakest[0][1] > 0
    assert 0 < bd.avg_score < 100
    print(f"  블로그 전체 OK (평균 {bd.avg_score}, 겹친 쌍 {len(bd.similar_pairs)})")


def test_similarity_edges() -> None:
    assert score.similarity("", "") == 0.0
    assert score.similarity("같은 글" * 50, "같은 글" * 50) > 0.9
    assert score.similarity("상추 키우기" * 50, "고양이 간식" * 50) < 0.1
    print("  유사도 경계 OK")


def main() -> int:
    test_good_post_scores_full()
    test_thin_post_lists_fixes()
    test_repeat_rate_is_length_aware()
    test_ad_phrases_and_density_bounds()
    test_keyword_stuffing_in_title()
    test_blog_level()
    test_similarity_edges()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
