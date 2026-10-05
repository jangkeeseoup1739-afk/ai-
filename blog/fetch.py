"""네이버 블로그에서 글 목록과 본문 HTML을 받아온다.

로그인 없이 공개 페이지만 쓴다. 조회수·유입 키워드는 공개되지 않으므로
그 수치는 블로그 통계에서 내려받은 CSV로 따로 넣는다(`--stats`).

표준 라이브러리만 쓴다. 네트워크가 막힌 곳에서는 미리 저장해 둔 HTML을
`--html-dir` 로 읽을 수 있게 되어 있다(cli 참고).
"""
from __future__ import annotations

import gzip
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

RSS = "https://rss.blog.naver.com/{blog_id}.xml"
TITLE_LIST = ("https://blog.naver.com/PostTitleListAsync.naver"
              "?blogId={blog_id}&currentPage={page}&countPerPage={count}"
              "&categoryNo=&parentCategoryNo=&viewdate=&range=&cpage=")
POST_VIEW = "https://m.blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"


class FetchError(RuntimeError):
    pass


@dataclass
class PostRef:
    """글 목록 한 줄. 본문은 아직 안 받은 상태."""
    log_no: str
    title: str
    published_at: datetime | None = None
    url: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)


def get(url: str, timeout: float = 20.0) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Accept-Encoding": "gzip",
        "Referer": "https://m.blog.naver.com/",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            charset = r.headers.get_content_charset()
    except urllib.error.HTTPError as e:
        raise FetchError(f"{url} -> HTTP {e.code}") from e
    except OSError as e:  # 타임아웃, DNS, 프록시 차단 등
        raise FetchError(f"{url} -> {e}") from e
    for enc in filter(None, [charset, "utf-8", "cp949"]):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def _parse_rfc822(s: str) -> datetime | None:
    s = s.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s, fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _log_no_from_url(url: str) -> str:
    m = re.search(r"logNo=(\d+)", url) or re.search(r"/(\d+)(?:[/?#]|$)", url)
    return m.group(1) if m else ""


def parse_rss(xml: str) -> list[PostRef]:
    """RSS(rss.blog.naver.com/아이디.xml)에서 최근 글을 뽑는다."""
    out: list[PostRef] = []
    for item in re.findall(r"<item>(.*?)</item>", xml, re.S):
        def tag(name: str) -> str:
            m = re.search(rf"<{name}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{name}>",
                          item, re.S)
            return unescape(m.group(1)).strip() if m else ""

        link = tag("link")
        out.append(PostRef(
            log_no=_log_no_from_url(link),
            title=tag("title"),
            published_at=_parse_rfc822(tag("pubDate")),
            url=link,
            summary=strip_tags(tag("description"))[:400],
            tags=[t for t in re.findall(r"<category>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</category>",
                                        item, re.S)],
        ))
    return out


def parse_title_list(payload: str) -> list[PostRef]:
    """PostTitleListAsync 응답(JSON 비슷한 문자열)에서 글 목록을 뽑는다."""
    payload = payload.strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        # 키가 작은따옴표로 오는 경우가 있어 한 번 고쳐서 다시 시도한다.
        fixed = re.sub(r"([{,])\s*'([^']+)'\s*:", r'\1"\2":', payload)
        fixed = fixed.replace("':'", '":"').replace("','", '","')
        fixed = re.sub(r"'", '"', fixed)
        try:
            data = json.loads(fixed)
        except json.JSONDecodeError as e:
            raise FetchError("글 목록 응답을 읽지 못했습니다.") from e

    out: list[PostRef] = []
    for row in data.get("postList", []):
        title = urllib.parse.unquote(str(row.get("title", ""))).replace("+", " ")
        out.append(PostRef(
            log_no=str(row.get("logNo", "")),
            title=unescape(title).strip(),
            published_at=_parse_rfc822(str(row.get("addDate", ""))),
        ))
    return out


def post_list(blog_id: str, limit: int = 30, getter=get) -> list[PostRef]:
    """최근 글 목록. RSS를 먼저 쓰고, 막히면 글 제목 목록 API로 넘어간다."""
    refs: list[PostRef] = []
    errors: list[str] = []
    try:
        refs = parse_rss(getter(RSS.format(blog_id=blog_id)))
    except FetchError as e:
        errors.append(str(e))

    if len(refs) < limit:
        page, seen = 1, {r.log_no for r in refs}
        while len(refs) < limit and page <= 10:
            url = TITLE_LIST.format(blog_id=blog_id, page=page,
                                    count=min(30, limit))
            try:
                more = parse_title_list(getter(url))
            except FetchError as e:
                errors.append(str(e))
                break
            if not more:
                break
            for r in more:
                if r.log_no and r.log_no not in seen:
                    seen.add(r.log_no)
                    refs.append(r)
            page += 1

    if not refs:
        raise FetchError("글 목록을 못 받았습니다. " + " / ".join(errors or ["원인 불명"]))
    for r in refs:
        if not r.url and r.log_no:
            r.url = f"https://blog.naver.com/{blog_id}/{r.log_no}"
    return refs[:limit]


def post_html(blog_id: str, log_no: str, getter=get) -> str:
    return getter(POST_VIEW.format(blog_id=blog_id, log_no=log_no))


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</(p|div|h\d|li|tr|blockquote)>", "\n", html)
    return unescape(re.sub(r"<[^>]+>", " ", html))


def unescape(s: str) -> str:
    import html as _html

    return _html.unescape(s)
