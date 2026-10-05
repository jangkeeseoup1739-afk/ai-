"""글 HTML에서 노출 점검에 필요한 것만 뽑아낸다.

스마트에디터 ONE(se-*), 구 에디터(postViewArea) 양쪽을 다 본다.
네이버가 클래스 이름을 조금씩 바꾸므로 한 가지 패턴에 기대지 않고
여러 패턴을 모아서 세고, 하나도 안 걸리면 0으로 둔다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .fetch import strip_tags, unescape

# 본문 영역을 잡는 패턴 (앞쪽부터 먼저 맞는 것을 쓴다)
_BODY_PATTERNS = [
    r'(?is)<div[^>]*class="[^"]*se-main-container[^"]*"[^>]*>(.*?)(?:<div[^>]*class="[^"]*se-module-sticker|<div[^>]*id="postMenu|</body>)',
    r'(?is)<div[^>]*id="postViewArea"[^>]*>(.*?)</div>\s*(?:<div[^>]*class="post_footer|</body>)',
    r'(?is)<div[^>]*class="[^"]*post_ct[^"]*"[^>]*>(.*?)</body>',
]

_IMG_PATTERNS = [
    r'(?i)<img[^>]+class="[^"]*se-image-resource',
    r'(?i)<img[^>]+class="[^"]*_photoImage',
    r'(?i)<img[^>]+class="[^"]*se_mediaImage',
    r'(?i)<div[^>]*class="[^"]*se-module-image\b',
]
_VIDEO_PATTERNS = [
    r'(?i)class="[^"]*se-module-video',
    r'(?i)class="[^"]*se-video\b',
    r'(?i)<iframe[^>]+(?:youtube|youtu\.be|naver\.com/embed|serviceapi\.nmv)',
    r'(?i)data-module="[^"]*v2_video',
]
_MAP_PATTERNS = [
    r'(?i)class="[^"]*se-module-map',
    r'(?i)class="[^"]*se-map\b',
    r'(?i)class="[^"]*__se_map',
]
_HEADING_PATTERNS = [
    r'(?is)<div[^>]*class="[^"]*se-module-text[^"]*se-title-text[^"]*"[^>]*>(.*?)</div>',
    r'(?is)<div[^>]*class="[^"]*se-section-sectionTitle[^"]*"[^>]*>(.*?)</div>',
    r'(?is)<div[^>]*class="[^"]*se-section-quotation[^"]*"[^>]*>(.*?)</div>',
    r'(?is)<h([1-4])[^>]*>(.*?)</h\1>',
]
_TAG_PATTERNS = [
    r'(?is)<div[^>]*class="[^"]*(?:post_tag|wrap_tag|tag_area)[^"]*"[^>]*>(.*?)</div>',
    r'(?is)<ul[^>]*class="[^"]*(?:tag|post_tag)[^"]*"[^>]*>(.*?)</ul>',
]


@dataclass
class Post:
    log_no: str = ""
    url: str = ""
    title: str = ""
    body: str = ""
    published_at: datetime | None = None
    images: int = 0
    videos: int = 0
    maps: int = 0
    headings: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    internal_links: int = 0
    external_links: int = 0

    @property
    def char_count(self) -> int:
        """공백을 뺀 글자 수. 네이버 글자 수 세기와 기준을 맞춘다."""
        return len(re.sub(r"\s+", "", self.body))

    @property
    def first_paragraph(self) -> str:
        for chunk in self.body.split("\n"):
            if len(chunk.strip()) >= 20:
                return chunk.strip()
        return self.body[:200]


def _meta(html: str, prop: str) -> str:
    m = (re.search(rf'(?i)<meta[^>]+property="{prop}"[^>]+content="([^"]*)"', html)
         or re.search(rf'(?i)<meta[^>]+content="([^"]*)"[^>]+property="{prop}"', html))
    return unescape(m.group(1)).strip() if m else ""


def _title(html: str, body_html: str) -> str:
    for pat in (r'(?is)<div[^>]*class="[^"]*se-title-text[^"]*"[^>]*>(.*?)</div>',
                r'(?is)<div[^>]*class="[^"]*pcol1[^"]*itemSubjectBoldfont[^"]*"[^>]*>(.*?)</div>',
                r'(?is)<h3[^>]*class="[^"]*se_textarea[^"]*"[^>]*>(.*?)</h3>'):
        m = re.search(pat, html)
        if m:
            t = " ".join(strip_tags(m.group(1)).split())
            if t:
                return t
    og = _meta(html, "og:title")
    if og:
        return re.sub(r"\s*:\s*네이버 블로그\s*$", "", og).strip()
    m = re.search(r"(?is)<title>(.*?)</title>", html)
    return " ".join(strip_tags(m.group(1)).split()) if m else ""


def _published_at(html: str) -> datetime | None:
    pats = [
        r'(?is)class="[^"]*(?:se_publishDate|blog_date|date)[^"]*"[^>]*>\s*([\d]{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?(?:\s*\d{1,2}:\d{2})?)',
        r'(?i)"publishDate"\s*:\s*"([^"]+)"',
        r'(?i)<meta[^>]+property="og:createdate"[^>]+content="([^"]+)"',
    ]
    for pat in pats:
        m = re.search(pat, html)
        if not m:
            continue
        raw = m.group(1).strip().rstrip(".")
        raw = re.sub(r"\s+", " ", raw)
        for fmt in ("%Y. %m. %d. %H:%M", "%Y. %m. %d %H:%M", "%Y. %m. %d.",
                    "%Y. %m. %d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                    "%Y%m%d%H%M%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def _count(html: str, patterns: list[str]) -> int:
    return max((len(re.findall(p, html)) for p in patterns), default=0)


def _headings(body_html: str) -> list[str]:
    out: list[str] = []
    for pat in _HEADING_PATTERNS:
        for m in re.finditer(pat, body_html):
            raw = m.group(m.lastindex or 1)
            text = " ".join(strip_tags(raw).split())
            if 2 <= len(text) <= 60 and text not in out:
                out.append(text)
    return out


def _tags(html: str) -> list[str]:
    out: list[str] = []
    for pat in _TAG_PATTERNS:
        for block in re.findall(pat, html):
            for t in re.findall(r"#\s*([^<#\s][^<#]{0,38})", strip_tags(block)):
                t = t.strip()
                if t and t not in out:
                    out.append(t)
    if not out:  # 모바일 뷰는 JSON으로 실어 보내기도 한다
        m = re.search(r'(?i)"tagList"\s*:\s*\[(.*?)\]', html, re.S)
        if m:
            out = [unescape(x) for x in re.findall(r'"([^"]{1,40})"', m.group(1))]
    return out


def _links(body_html: str, blog_id: str) -> tuple[int, int]:
    inner = outer = 0
    for href in re.findall(r'(?i)<a[^>]+href="([^"]+)"', body_html):
        if href.startswith("#") or href.startswith("javascript"):
            continue
        if blog_id and blog_id in href:
            inner += 1
        elif "blog.naver.com" in href or href.startswith("/"):
            inner += 1
        else:
            outer += 1
    return inner, outer


def body_html(html: str) -> str:
    for pat in _BODY_PATTERNS:
        m = re.search(pat, html)
        if m and len(m.group(1)) > 200:
            return m.group(1)
    return html


def parse_post(html: str, blog_id: str = "", log_no: str = "", url: str = "") -> Post:
    inner_html = body_html(html)
    text = strip_tags(inner_html)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    inner, outer = _links(inner_html, blog_id)
    return Post(
        log_no=log_no,
        url=url or (f"https://blog.naver.com/{blog_id}/{log_no}" if log_no else ""),
        title=_title(html, inner_html),
        body=text,
        published_at=_published_at(html),
        images=_count(inner_html, _IMG_PATTERNS),
        videos=_count(inner_html, _VIDEO_PATTERNS),
        maps=_count(inner_html, _MAP_PATTERNS),
        headings=_headings(inner_html),
        tags=_tags(html),
        internal_links=inner,
        external_links=outer,
    )
