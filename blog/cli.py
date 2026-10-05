"""네이버 블로그 노출·유입 진단.

    python -m blog diagnose --id 내아이디 --out 진단.md
    python -m blog plan --id 내아이디 --out 발행계획.md
    python -m blog post --url https://blog.naver.com/아이디/123456
    python -m blog repurpose --url https://blog.naver.com/아이디/123456

아이디는 한 번 주면 기억한다(`python -m blog config --show` 로 확인).
Tab 자동완성은 `eval "$(python -m blog completion bash)"` 한 줄이면 된다.

네트워크가 막힌 곳에서는 글 페이지를 저장해 두고 --html-dir 로 넣으면 된다.
조회수·유입 검색어는 공개되지 않으므로, 블로그 통계에서 내려받은 표를
CSV로 저장해 --stats 로 넣으면 리포트에 함께 들어간다.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from . import (completion, config, fetch, keywords as kw, plan as plan_mod,
               report, repurpose, score, stats)
from .parse import parse_post


def _blog_id_and_log_no(url: str) -> tuple[str, str]:
    m = re.search(r"blogId=([\w-]+)", url)
    blog_id = m.group(1) if m else ""
    m = re.search(r"blog\.naver\.com/([\w-]+)/(\d+)", url)
    if m:
        return m.group(1), m.group(2)
    log_no = (re.search(r"logNo=(\d+)", url) or re.search(r"/(\d{6,})", url))
    return blog_id, log_no.group(1) if log_no else ""


def _out(text: str, path: str | None) -> None:
    if path:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"저장했습니다: {p}", file=sys.stderr)
    else:
        print(text)


def _load_from_dir(d: str, blog_id: str):
    files = sorted(Path(d).expanduser().glob("*.htm*"))
    if not files:
        raise SystemExit(f"{d} 안에 html 파일이 없습니다.")
    posts = []
    for f in files:
        log_no = re.sub(r"\D", "", f.stem)
        posts.append(parse_post(f.read_text(encoding="utf-8", errors="replace"),
                                blog_id, log_no))
    return posts


def _load_posts(args):
    if getattr(args, "html_dir", None):
        return _load_from_dir(args.html_dir, args.id or "")
    if not args.id:
        raise SystemExit(
            "--id (블로그 주소의 아이디) 또는 --html-dir 가 필요합니다.\n"
            "한 번 저장해 두면 다음부터 생략됩니다:  python -m blog config --id 내아이디")
    try:
        refs = fetch.post_list(args.id, args.limit)
    except fetch.FetchError as e:
        raise SystemExit(
            f"{e}\n\n네이버에 닿지 못했습니다. 이 컴퓨터에서 "
            f"https://blog.naver.com/{args.id} 가 열리는지 확인하고, "
            "막혀 있으면 글 페이지를 저장한 뒤 --html-dir 로 넣어 주세요.")
    print(f"글 목록 {len(refs)}편을 받았습니다. 본문을 읽습니다...", file=sys.stderr)

    save = Path(args.save_dir).expanduser() if getattr(args, "save_dir", None) else None
    if save:
        save.mkdir(parents=True, exist_ok=True)

    posts = []
    for i, r in enumerate(refs, 1):
        try:
            html = fetch.post_html(args.id, r.log_no)
        except fetch.FetchError as e:
            print(f"  [{i}/{len(refs)}] 건너뜀 ({r.title}): {e}", file=sys.stderr)
            continue
        if save:
            (save / f"{r.log_no}.html").write_text(html, encoding="utf-8")
        p = parse_post(html, args.id, r.log_no, r.url)
        if not p.title:
            p.title = r.title
        if not p.published_at:
            p.published_at = r.published_at
        if not p.tags:
            p.tags = r.tags
        posts.append(p)
        print(f"  [{i}/{len(refs)}] {p.title} ({p.char_count}자)", file=sys.stderr)
    if not posts:
        raise SystemExit("본문을 하나도 읽지 못했습니다.")
    return posts


def cmd_diagnose(args) -> int:
    config.resolve(args)
    posts = _load_posts(args)
    bd = score.score_blog(args.id or "블로그", posts)
    inflow = stats.load(args.stats) if args.stats else None
    _out(report.render(bd, inflow, detail_posts=args.detail), args.out)
    print(f"\n글 평균 {bd.avg_score}/100 · 가장 많이 깎인 항목: "
          + ", ".join(n for n, _, _ in bd.weakest[:3]), file=sys.stderr)
    return 0


def cmd_post(args) -> int:
    config.resolve(args)
    if args.html:
        html = Path(args.html).expanduser().read_text(encoding="utf-8",
                                                      errors="replace")
        blog_id, log_no = args.id or "", ""
    else:
        if not args.url:
            raise SystemExit("--url 또는 --html 이 필요합니다.")
        blog_id, log_no = _blog_id_and_log_no(args.url)
        if not (blog_id and log_no):
            raise SystemExit("주소에서 아이디와 글 번호를 못 찾았습니다.")
        try:
            html = fetch.post_html(blog_id, log_no)
        except fetch.FetchError as e:
            raise SystemExit(str(e))
    p = parse_post(html, blog_id, log_no, args.url or "")
    d = score.score_post(p, args.keyword)
    _out(f"# 글 점검\n\n{report.post_section(d)}", args.out)
    return 0


def cmd_keywords(args) -> int:
    config.resolve(args)
    if args.text:
        text = Path(args.text).expanduser().read_text(encoding="utf-8",
                                                      errors="replace")
        lines = [f"# 키워드 - {args.text}", ""]
        for w, c in kw.top_keywords(text, args.top):
            lines.append(f"- {w} {c}회 (밀도 {kw.density(text, w)}%)")
        main = kw.top_keywords(text, 1)
        if main:
            lines += ["", f"## `{main[0][0]}` 롱테일 후보", ""]
            lines += [f"- {t}" for t in kw.longtail(main[0][0], date.today().year,
                                                    args.place, args.preset)]
        _out("\n".join(lines), args.out)
        return 0

    posts = _load_posts(args)
    clusters = kw.cluster([(p.title, p.body) for p in posts])
    lines = [f"# {args.id} 키워드 지도", "",
             f"글 {len(posts)}편에서 반복되는 주제어", "",
             "| 주제어 | 걸친 글 | 비중 |", "|---|---|---|"]
    n = max(1, len(posts))
    for w, c in clusters[:args.top]:
        lines.append(f"| {w} | {c}편 | {int(c / n * 100)}% |")
    if clusters:
        main = clusters[0][0]
        lines += ["", f"## 주력 `{main}` 롱테일 후보", ""]
        lines += [f"- {t}" for t in kw.longtail(main, date.today().year, args.place,
                                                args.preset)]
    _out("\n".join(lines), args.out)
    return 0


def cmd_plan(args) -> int:
    config.resolve(args)
    keyword, existing = args.keyword, []
    if not keyword:
        posts = _load_posts(args)
        clusters = kw.cluster([(p.title, p.body) for p in posts])
        if not clusters:
            raise SystemExit("주력 주제를 못 찾았습니다. --keyword 로 직접 넣어 주세요.")
        keyword = clusters[0][0]
        existing = [p.title for p in posts]
        print(f"주력 주제를 `{keyword}` 로 잡았습니다.", file=sys.stderr)
    slots = plan_mod.build(keyword, weeks=args.weeks, per_week=args.per_week,
                           place=args.place, existing_titles=existing,
                           preset=args.preset)
    _out(plan_mod.render(keyword, slots, args.place), args.out)
    return 0


def cmd_repurpose(args) -> int:
    config.resolve(args)
    if args.html:
        html = Path(args.html).expanduser().read_text(encoding="utf-8",
                                                      errors="replace")
        blog_id, log_no = args.id or "", ""
    else:
        if not args.url:
            raise SystemExit("--url 또는 --html 이 필요합니다.")
        blog_id, log_no = _blog_id_and_log_no(args.url)
        try:
            html = fetch.post_html(blog_id, log_no)
        except fetch.FetchError as e:
            raise SystemExit(str(e))
    p = parse_post(html, blog_id, log_no, args.url or "")
    _out(repurpose.script(p, args.keyword, args.seconds), args.out)
    return 0


def _add_source(p: argparse.ArgumentParser) -> None:
    p.add_argument("--id", help="블로그 아이디 (blog.naver.com/<아이디>). "
                               "한 번 주면 기억해서 다음부터 생략 가능")
    p.add_argument("--limit", type=int, default=20, help="최근 몇 편까지 볼지")
    p.add_argument("--html-dir", default=None,
                   help="미리 저장해 둔 글 html 폴더 (네트워크가 막힌 경우)")
    p.add_argument("--save-dir", default=None, help="받은 html을 여기에 저장")
    p.add_argument("--out", "-o", default=None, help="결과를 쓸 파일 (.md)")


def cmd_config(args) -> int:
    if args.clear:
        config.clear()
        print("저장된 설정을 지웠습니다.")
        return 0
    if args.id or args.place or args.limit:
        p = config.save(id=args.id, place=args.place, limit=args.limit)
        print(f"저장했습니다: {p}")
    saved = config.load()
    if not saved:
        print("저장된 설정이 없습니다.  python -m blog config --id 내아이디")
        return 0
    print("현재 설정 (" + str(config.path()) + ")")
    for k in config.KEYS:
        if k in saved:
            print(f"  {k} = {saved[k]}")
    return 0


def cmd_completion(args) -> int:
    print(completion.script(build_parser(), args.shell, args.name), end="")
    if sys.stdout.isatty():   # 눈으로 볼 때만 설치법을 덧붙인다
        print(f"\n# 설치: 위 줄을 ~/.{args.shell}rc 에 넣거나\n"
              f'#   eval "$(python3 -m blog completion {args.shell})"',
              file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m blog",
                                 description="네이버 블로그 노출·유입 진단")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("diagnose", help="블로그 전체 진단 리포트")
    _add_source(d)
    d.add_argument("--stats", default=None,
                   help="블로그 통계 > 유입분석에서 내려받은 CSV")
    d.add_argument("--detail", type=int, default=5,
                   help="항목 전체를 보여줄 하위 글 수")
    d.set_defaults(func=cmd_diagnose)

    p = sub.add_parser("post", help="글 하나 점검")
    p.add_argument("--url", default=None)
    p.add_argument("--html", default=None, help="저장해 둔 글 html")
    p.add_argument("--id", default=None)
    p.add_argument("--keyword", default=None, help="노리는 키워드 (기본: 자동 추정)")
    p.add_argument("--out", "-o", default=None)
    p.set_defaults(func=cmd_post)

    k = sub.add_parser("keywords", help="키워드 지도와 롱테일 후보")
    _add_source(k)
    k.add_argument("--text", default=None, help="글 텍스트 파일 하나만 볼 때")
    k.add_argument("--top", type=int, default=20)
    k.add_argument("--place", default="", help="지역 키워드를 붙일 때 (예: 인천 주안)")
    k.add_argument("--preset", default="기본", choices=list(kw.PRESETS),
                   help="롱테일 수식어 묶음 (부동산 = 시세·공실·분양가 등)")
    k.set_defaults(func=cmd_keywords)

    pl = sub.add_parser("plan", help="4주 발행 계획")
    _add_source(pl)
    pl.add_argument("--keyword", default=None, help="주력 주제 (기본: 블로그에서 추정)")
    pl.add_argument("--weeks", type=int, default=4)
    pl.add_argument("--per-week", type=int, default=3)
    pl.add_argument("--place", default="")
    pl.add_argument("--preset", default="기본", choices=list(plan_mod.PRESETS),
                    help="글 유형·키워드 묶음 (부동산 = 중개·분양·임대용)")
    pl.set_defaults(func=cmd_plan)

    r = sub.add_parser("repurpose", help="글을 릴스 대본으로")
    r.add_argument("--url", default=None)
    r.add_argument("--html", default=None)
    r.add_argument("--id", default=None)
    r.add_argument("--keyword", default=None)
    r.add_argument("--seconds", type=int, default=30)
    r.add_argument("--out", "-o", default=None)
    r.set_defaults(func=cmd_repurpose)

    c = sub.add_parser("config", help="자주 쓰는 값 저장 (--id 생략용)")
    c.add_argument("--id", default=None, help="기억해 둘 블로그 아이디")
    c.add_argument("--place", default=None, help="기억해 둘 지역 키워드")
    c.add_argument("--limit", type=int, default=None, help="기본으로 볼 글 수")
    c.add_argument("--show", action="store_true", help="저장된 값 보기 (기본 동작)")
    c.add_argument("--clear", action="store_true", help="저장된 값 지우기")
    c.set_defaults(func=cmd_config)

    cp = sub.add_parser("completion", help="Tab 자동완성 스크립트 출력")
    cp.add_argument("shell", choices=["bash", "zsh"])
    cp.add_argument("--name", default="blog", help="만들 명령 이름 (기본: blog)")
    cp.set_defaults(func=cmd_completion)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
