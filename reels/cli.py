"""촬영본 -> 캡컷 러프컷 초안 파이프라인.

    python -m reels all --input ~/Desktop/촬영본.mp4 --name 릴스_러프컷

받아쓰기 -> NG/군말/끊김 정리 -> 12자 자막 -> 캡컷 초안 순으로 돈다.
판정을 직접 손보려면 --review 로 멈춘 뒤 work/decisions.json 을 고치고
--from-decisions 로 이어서 돌리면 된다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import clean, draft, subtitles, transcribe
from .util import ensure_dir


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--input", "-i", required=True, help="촬영본 영상 경로")
    p.add_argument("--work", default=None, help="작업 폴더 (기본: 영상 옆 .reels_work)")
    p.add_argument("--model", default=str(transcribe.DEFAULT_MODEL), help="whisper 모델 경로")
    p.add_argument("--lang", default="ko")
    p.add_argument("--threads", type=int, default=0)
    p.add_argument("--beam", type=int, default=5)
    p.add_argument("--max-chars", type=int, default=12, help="자막 한 줄 글자 수")
    p.add_argument("--name", default="릴스_러프컷", help="캡컷 초안 이름")
    p.add_argument("--draft-root", default=str(draft.DEFAULT_DRAFT_ROOT))
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--height", type=int, default=1920)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--no-fill", action="store_true", help="세로 꽉 채우기 배율 적용 안 함")
    p.add_argument("--subtitle-y", type=float, default=-0.62)
    p.add_argument("--font-size", type=float, default=8.0)
    p.add_argument("--typo-map", default=None, help='오타 교정 JSON ({"틀린말":"고칠말"})')
    p.add_argument("--llm", action="store_true",
                   help="ANTHROPIC_API_KEY로 문맥 판정/오타 교정 (선택)")
    p.add_argument("--review", action="store_true",
                   help="판정 리포트만 만들고 멈춤 (초안 생성 안 함)")
    p.add_argument("--from-decisions", default=None,
                   help="기존 decisions.json으로 이어서 실행 (받아쓰기 건너뜀)")


def _workdir(args) -> Path:
    if args.work:
        return ensure_dir(args.work)
    return ensure_dir(Path(args.input).expanduser().parent / ".reels_work")


def _load_typo_map(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def cmd_all(args) -> int:
    src = Path(args.input).expanduser()
    work = _workdir(args)

    if args.from_decisions:
        decisions = json.loads(
            Path(args.from_decisions).expanduser().read_text(encoding="utf-8"))
        print(f"판정 파일을 그대로 사용합니다: {args.from_decisions}", file=sys.stderr)
    else:
        print("[1/4] 받아쓰기...", file=sys.stderr)
        segments = transcribe.transcribe(src, work, Path(args.model), args.lang,
                                         args.threads, args.beam)
        if not segments:
            raise SystemExit("받아쓴 내용이 없습니다. 오디오를 확인하세요.")
        print(f"[2/4] NG/군말/끊김 판정... ({len(segments)}구간)", file=sys.stderr)
        decisions = clean.decide(segments, typo_map=_load_typo_map(args.typo_map))
        if args.llm:
            decisions = clean.apply_llm(decisions)
        dj, rp = clean.save(decisions, work)
        print(f"      판정: {dj}\n      리포트: {rp}", file=sys.stderr)

    print(clean.report(decisions))

    if args.review:
        print("\n--review 모드라 여기서 멈춥니다. "
              "decisions.json을 고친 뒤 --from-decisions 로 이어서 돌리세요.",
              file=sys.stderr)
        return 0

    print("[3/4] 자막 만드는 중...", file=sys.stderr)
    timeline = subtitles.build_timeline(decisions)
    if not timeline:
        raise SystemExit("남은 구간이 없습니다. 판정 기준을 완화해 보세요.")
    srt_path = subtitles.write_srt(timeline, work / "subtitle.srt", args.max_chars)
    total = timeline[-1]["new_end"]
    print(f"      {len(timeline)}구간 / {total:.1f}초 -> {srt_path}", file=sys.stderr)

    print("[4/4] 캡컷 초안 만드는 중...", file=sys.stderr)
    out = draft.build_draft(
        src, timeline, srt_path,
        draft_name=args.name, draft_root=Path(args.draft_root),
        width=args.width, height=args.height, fps=args.fps,
        fill=not args.no_fill, subtitle_y=args.subtitle_y,
        font_size=args.font_size,
    )
    print(f"\n초안 생성 완료: {out}")
    print(f"길이 {total:.1f}초 / {args.width}x{args.height} / 영상 + 자막 트랙")
    print("\n캡컷을 완전히 종료했다가 다시 열어주세요. "
          "초안 목록에 새로고침된 프로젝트가 보입니다.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reels", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_all = sub.add_parser("all", help="전체 파이프라인 실행")
    _add_common(p_all)
    p_all.set_defaults(func=cmd_all)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
