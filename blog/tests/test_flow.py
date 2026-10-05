"""끝에서 끝까지: 저장된 html 폴더로 리포트·계획·릴스 대본까지 나오는지 본다.

네트워크를 타지 않는다. 목록 받아오는 부분은 가짜 getter로 확인한다.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

TMP = Path(__file__).parent / "_tmp_flow"
# 실제 설정 파일(~/.config/blog)을 건드리지 않게 테스트 전용 경로로 돌린다
os.environ["BLOG_CONFIG"] = str(TMP / "config.json")

from blog import cli, fetch, plan, repurpose, stats   # noqa: E402
from blog.parse import parse_post                     # noqa: E402
from blog.tests import _fixtures as fx                # noqa: E402


def _make_html_dir() -> Path:
    html_dir = TMP / "posts"
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "1001.html").write_text(fx.long_post(), encoding="utf-8")
    (html_dir / "1002.html").write_text(fx.long_post("토마토"), encoding="utf-8")
    (html_dir / "1003.html").write_text(fx.thin_post(), encoding="utf-8")
    return html_dir


def test_diagnose_report() -> None:
    html_dir = _make_html_dir()
    out = TMP / "진단.md"
    assert cli.main(["diagnose", "--id", "myid", "--html-dir", str(html_dir),
                     "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "블로그 노출·유입 진단" in text
    # 통계 CSV가 없으면 '실제 유입'이 빠지고 번호가 당겨져야 한다
    heads = [l for l in text.splitlines() if l.startswith("## ")]
    assert [h.split(". ", 1)[1] for h in heads][:3] == [
        "블로그 전체 (채널 점수)", "무슨 블로그로 보이는가", "전체에서 가장 많이 깎인 항목"], heads
    assert [int(h[3:].split(".")[0]) for h in heads] == list(range(1, len(heads) + 1)), heads
    assert "글별 점검표" in text and "다음에 쓸 글" in text
    assert "오늘 다녀왔어요" in text              # 점수 낮은 글이 리포트에 들어가야 한다
    assert text.count("|") > 50                   # 표가 실제로 그려졌는지
    print(f"  진단 리포트 {len(text)}자 OK")


def test_diagnose_with_stats_csv() -> None:
    csv_path = TMP / "유입.csv"
    csv_path.write_text(
        "﻿유입분석 다운로드\n"
        "유입경로,조회수\n"
        "네이버 통합검색_모바일,120\n"
        "네이버 블로그검색,40\n"
        "이웃 새글,300\n", encoding="utf-8")
    inflow = stats.load(csv_path)
    assert inflow.total == 460, inflow.total
    assert inflow.top(1)[0][0] == "이웃 새글"
    assert inflow.search_share == 34.8, inflow.search_share

    out = TMP / "진단2.md"
    assert cli.main(["diagnose", "--id", "myid", "--html-dir", str(_make_html_dir()),
                     "--stats", str(csv_path), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "## 3. 실제 유입" in text
    assert "검색 유입 비중" in text and "34.8%" in text
    assert "검색 비중이 절반도 안 된다" in text    # 경고가 떠야 한다
    print(f"  통계 CSV 결합 OK (검색 {inflow.search_share}%)")


def test_post_and_repurpose() -> None:
    post_file = TMP / "one.html"
    post_file.write_text(fx.long_post(), encoding="utf-8")
    out = TMP / "글점검.md"
    assert cli.main(["post", "--html", str(post_file), "--out", str(out)]) == 0
    assert "핵심 키워드" in out.read_text(encoding="utf-8")

    script = repurpose.script(parse_post(fx.long_post(), "myid", "1"))
    assert "릴스 대본" in script and "상추" in script
    assert script.count("|") > 10
    assert "python -m reels all" in script
    print("  글 점검·릴스 대본 OK")


def test_plan_from_posts() -> None:
    out = TMP / "계획.md"
    assert cli.main(["plan", "--id", "myid", "--html-dir", str(_make_html_dir()),
                     "--weeks", "2", "--per-week", "3", "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "발행 계획" in text
    rows = [l for l in text.splitlines() if l.startswith("| ") and "/" in l[:8]]
    assert len(rows) == 6, len(rows)              # 2주 x 3편
    # 제목 틀이 모두 다른 유형으로 돌아가야 한다 (유사문서 방지)
    forms = {l.split("|")[3].strip() for l in rows}
    assert len(forms) >= 5, forms
    print(f"  발행 계획 {len(rows)}칸 OK")


def test_plan_slots_are_weekdays() -> None:
    slots = plan.build("상추", weeks=1, per_week=3)
    assert [s.when.weekday() for s in slots] == [0, 2, 4]
    assert all(s.title and s.must_have for s in slots)
    print("  발행 요일 OK")


def test_keywords_command() -> None:
    out = TMP / "키워드.md"
    assert cli.main(["keywords", "--id", "myid", "--html-dir", str(_make_html_dir()),
                     "--place", "수원", "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "키워드 지도" in text and "수원" in text
    print("  키워드 지도 OK")


def test_post_list_rss_then_fallback() -> None:
    rss = """<rss><channel>
    <item><title><![CDATA[상추 키우기]]></title>
    <link>https://blog.naver.com/myid/1001</link>
    <pubDate>Tue, 01 Sep 2026 10:30:00 +0900</pubDate>
    <description><![CDATA[<p>본문 미리보기</p>]]></description>
    <category>텃밭</category></item>
    </channel></rss>"""
    title_list = ('{"postList":[{"logNo":"1002","title":"%ED%86%A0%EB%A7%88%ED%86%A0",'
                  '"addDate":"2026-09-03 09:00:00"}]}')

    def getter(url: str) -> str:
        if "rss" in url:
            return rss
        if "PostTitleListAsync" in url:
            return title_list
        raise fetch.FetchError(url)

    refs = fetch.post_list("myid", limit=2, getter=getter)
    assert [r.log_no for r in refs] == ["1001", "1002"], refs
    assert refs[0].title == "상추 키우기"
    assert refs[0].published_at.year == 2026
    assert refs[0].tags == ["텃밭"]
    assert refs[1].title == "토마토"              # URL 인코딩이 풀려야 한다
    assert refs[1].url.endswith("/myid/1002")
    print("  글 목록(RSS + 대체 경로) OK")


def test_post_list_raises_when_blocked() -> None:
    def blocked(url: str) -> str:
        raise fetch.FetchError("CONNECT tunnel failed")

    try:
        fetch.post_list("myid", limit=5, getter=blocked)
    except fetch.FetchError as e:
        assert "CONNECT" in str(e)
        print("  막혔을 때 이유를 그대로 전달 OK")
    else:
        raise AssertionError("막혔는데도 성공했다")


def test_url_parsing() -> None:
    assert cli._blog_id_and_log_no("https://blog.naver.com/myid/223456") == ("myid", "223456")
    assert cli._blog_id_and_log_no(
        "https://m.blog.naver.com/PostView.naver?blogId=myid&logNo=999") == ("myid", "999")
    print("  주소 해석 OK")


def main() -> int:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    try:
        test_diagnose_report()
        test_diagnose_with_stats_csv()
        test_post_and_repurpose()
        test_plan_from_posts()
        test_plan_slots_are_weekdays()
        test_keywords_command()
        test_post_list_rss_then_fallback()
        test_post_list_raises_when_blocked()
        test_url_parsing()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
