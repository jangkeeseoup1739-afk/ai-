"""글 HTML에서 제목·본문·사진·태그를 제대로 뽑는지 본다."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from blog.parse import parse_post            # noqa: E402
from blog.tests import _fixtures as fx       # noqa: E402


def test_full_post() -> None:
    p = parse_post(fx.long_post(), "myid", "222")
    assert "상추" in p.title, p.title
    assert ": 네이버 블로그" not in p.title
    assert p.images == 7, p.images
    assert p.videos == 1, p.videos
    assert len(p.headings) >= 3, p.headings
    assert "텃밭" in p.tags, p.tags
    assert p.char_count > 1500, p.char_count
    assert p.published_at and p.published_at.year == 2026
    assert p.internal_links == 1 and p.external_links == 1
    assert p.url.endswith("/myid/222")
    print(f"  제목·본문·사진·태그 OK ({p.char_count}자, 사진 {p.images})")


def test_first_paragraph_skips_short_lines() -> None:
    p = parse_post(fx.post_html("제목", ["짧음", "여기가 실제 첫 문단이고 결론이 들어 있습니다."]))
    assert p.first_paragraph.startswith("여기가"), p.first_paragraph
    print("  첫 문단 추출 OK")


def test_old_editor() -> None:
    html = ('<html><body><title>구 에디터 글 : 네이버 블로그</title>'
            '<div id="postViewArea">' + "<p>본문입니다. " * 60 +
            '</p><img class="_photoImage" src="a.jpg"></div></body></html>')
    p = parse_post(html, "myid", "1")
    assert "구 에디터 글" in p.title, p.title
    assert p.images == 1
    assert p.char_count > 100
    print("  구 에디터 OK")


def test_no_body_falls_back() -> None:
    p = parse_post("<html><body>본문 영역을 못 찾는 경우</body></html>")
    assert p.images == 0 and p.videos == 0
    assert p.char_count >= 0
    print("  본문 못 찾아도 터지지 않음 OK")


def main() -> int:
    test_full_post()
    test_first_paragraph_skips_short_lines()
    test_old_editor()
    test_no_body_falls_back()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
