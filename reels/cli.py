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

from . import broll, clean, draft, sfx, subtitles, transcribe, transitions
from .util import ensure_dir


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--input", "-i", required=True, help="촬영본 영상 경로")
    p.add_argument("--work", default=None, help="작업 폴더 (기본: 영상 옆 .reels_work)")
    p.add_argument("--model", default=str(transcribe.DEFAULT_MODEL), help="whisper 모델 경로")
    p.add_argument("--lang", default="ko")
    p.add_argument("--threads", type=int, default=0)
    p.add_argument("--beam", type=int, default=5)
    p.add_argument("--max-chars", type=int, default=12, help="자막 한 줄 글자 수")
    p.add_argument("--max-silence", type=float, default=subtitles.MAX_SILENCE,
                   help="구간 사이에 남길 침묵의 최대 길이(초)")
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
    timeline = subtitles.build_timeline(decisions, args.max_silence)
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


def cmd_sfx(args) -> int:
    content = sfx.draft_content_path(Path(args.draft_root), args.name)
    sentences = sfx.read_sentences(content)
    if not sentences:
        raise SystemExit("초안에서 문장을 읽지 못했습니다.")
    total = max(s["end"] for s in sentences)
    print(f"문장 {len(sentences)}개 / {total:.1f}초", file=sys.stderr)

    picks = sfx.choose(sentences, per_30s=args.per_30s,
                       min_per_30s=args.min_per_30s, max_per_30s=args.max_per_30s,
                       spacing=args.spacing)
    if not picks:
        raise SystemExit("넣을 자리를 찾지 못했습니다.")
    print(f"효과음 {len(picks)}개 배치 예정", file=sys.stderr)

    picks = sfx.resolve(picks, sfx_dir=Path(args.sfx_dir).expanduser(),
                        cache=Path(args.cache).expanduser(),
                        allow_download=not args.no_download)

    print("\n## 넣은 효과음\n")
    print(sfx.table(picks))

    if args.dry_run:
        print("\n--dry-run 이라 초안은 건드리지 않았습니다.", file=sys.stderr)
        return 0

    added = sfx.attach(content, picks, volume=args.volume,
                       track_name=args.track_name)
    credit = sfx.attribution(picks)
    print(f"\n'{args.track_name}' 트랙에 {added}개를 볼륨 "
          f"{int(args.volume * 100)}%로 넣고 저장했습니다.")
    print(f"원본 백업: {content.with_suffix('.json.bak')}")
    if credit:
        print("\n## 캡션에 붙일 출처 문구 (CC BY)\n")
        print(credit)
    else:
        print("\nCC BY 소리는 없어서 출처 표기는 필요 없습니다.")
    print("\n캡컷을 다시 열면 효과음 트랙이 보입니다.")
    return 0


def cmd_transitions(args) -> int:
    content = sfx.draft_content_path(Path(args.draft_root), args.name)
    sentences = sfx.read_sentences(content)
    points = transitions.find_points(
        sentences, per_30s=args.per_30s, min_per_30s=args.min_per_30s,
        max_per_30s=args.max_per_30s, spacing=args.spacing)
    if not points:
        raise SystemExit("이야기가 바뀌는 지점을 찾지 못했습니다. "
                         "--per-30s 를 올리거나 직접 넣으세요.")
    total = max(s["end"] for s in sentences)
    print(f"문장 {len(sentences)}개 / {total:.1f}초 "
          f"-> 전환 {len(points)}곳 (30초당 {len(points) / (total / 30):.1f}곳)",
          file=sys.stderr)

    if args.dry_run:
        print("\n## 넣을 장면 전환\n")
        print(transitions.table(points))
        print("\n--dry-run 이라 초안은 건드리지 않았습니다.", file=sys.stderr)
        return 0

    added = transitions.apply(content, points, duration=args.duration,
                              force=args.force)
    print("\n## 넣은 장면 전환\n")
    print(transitions.table(points))
    print(f"\n{added}곳에 전환을 넣고 저장했습니다.")
    print(f"원본 백업: {content.with_suffix('.json.bak')}")
    print("\n캡컷을 다시 열어서 컷 경계와 자막 싱크를 한 번 확인해 주세요.")
    return 0


def cmd_broll(args) -> int:
    content = sfx.draft_content_path(Path(args.draft_root), args.name)
    out_dir = Path(args.dir).expanduser()

    if args.stage == "plan":
        sentences = sfx.read_sentences(content)
        shots = broll.plan(sentences, max_picks=args.max_picks,
                           min_picks=args.min_picks)
        if not shots:
            raise SystemExit("자료 화면이 필요한 문장을 찾지 못했습니다.")
        path = broll.save_plan(shots, out_dir)
        live = [s for s in shots if not s.blocked]
        print("\n## 보여줄 화면 목록\n")
        print(broll.table(shots))
        blank = [s for s in live if not s.url]
        print(f"\n{len(live)}곳을 골랐습니다. 목록: {path}")
        if blank:
            print(f"주소가 빈 곳이 {len(blank)}개 있습니다. "
                  "plan.json 의 url 을 채워주세요.")
        print("\n이대로 진행해도 될까요? 괜찮으면:")
        print(f"  python -m reels broll record --name {args.name}")
        return 0

    shots = broll.load_plan(out_dir / "plan.json")

    if args.stage == "record":
        print(f"{out_dir} 에 녹화합니다. "
              "화면 기록 권한이 필요하고, 스크롤에는 손쉬운 사용 권한이 필요합니다.")
        done = broll.record(shots, out_dir, settle=args.settle, rect=args.rect,
                            scroll=not args.no_scroll, dry_run=args.dry_run)
        if args.dry_run:
            return 0
        print(f"\n{len(done)}개를 녹화했습니다. 다음:")
        print(f"  python -m reels broll place --name {args.name}")
        return 0

    if args.stage == "place":
        added = broll.place(content, shots, out_dir, crop_mode=args.crop_mode,
                            crop_x=args.crop_x)
        print("\n## 올린 자료 화면\n")
        print(broll.table([s for s in shots if not s.blocked]))
        print(f"\n'{broll.TRACK_NAME}' 트랙에 {added}개를 올렸습니다 (화면 위쪽 절반).")
        print(f"원본 백업: {content.with_suffix('.json.bak')}")
        print("\n캡컷을 다시 열어주세요.")
        return 0

    raise SystemExit(f"알 수 없는 단계: {args.stage}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reels", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_all = sub.add_parser("all", help="전체 파이프라인 실행")
    _add_common(p_all)
    p_all.set_defaults(func=cmd_all)
    p_sfx = sub.add_parser("sfx", help="기존 초안에 효과음 트랙 추가")
    p_sfx.add_argument("--name", default="릴스_러프컷", help="캡컷 초안 이름")
    p_sfx.add_argument("--draft-root", default=str(draft.DEFAULT_DRAFT_ROOT))
    p_sfx.add_argument("--sfx-dir", default=str(sfx.DEFAULT_SFX_DIR),
                       help="내 효과음 폴더 (여기를 먼저 뒤진다)")
    p_sfx.add_argument("--cache", default=str(sfx.DEFAULT_CACHE),
                       help="내려받은 소리를 두는 곳")
    p_sfx.add_argument("--track-name", default="효과음")
    p_sfx.add_argument("--volume", type=float, default=0.5)
    p_sfx.add_argument("--per-30s", type=float, default=6.0)
    p_sfx.add_argument("--min-per-30s", type=float, default=4.0)
    p_sfx.add_argument("--max-per-30s", type=float, default=8.0)
    p_sfx.add_argument("--spacing", type=float, default=sfx.MIN_SPACING_SEC,
                       help="효과음 사이 최소 간격(초)")
    p_sfx.add_argument("--no-download", action="store_true",
                       help="Openverse에서 받지 않고 로컬 파일만 쓴다")
    p_sfx.add_argument("--dry-run", action="store_true",
                       help="초안을 고치지 않고 배치안만 보여준다")
    p_sfx.set_defaults(func=cmd_sfx)
    p_tr = sub.add_parser("transitions", help="기존 초안에 장면 전환 추가")
    p_tr.add_argument("--name", default="릴스_러프컷", help="캡컷 초안 이름")
    p_tr.add_argument("--draft-root", default=str(draft.DEFAULT_DRAFT_ROOT))
    p_tr.add_argument("--duration", type=float,
                      default=transitions.DEFAULT_DURATION, help="전환 길이(초)")
    p_tr.add_argument("--per-30s", type=float, default=3.0)
    p_tr.add_argument("--min-per-30s", type=float, default=2.0)
    p_tr.add_argument("--max-per-30s", type=float, default=4.0)
    p_tr.add_argument("--spacing", type=float, default=transitions.MIN_SPACING_SEC,
                      help="전환 사이 최소 간격(초)")
    p_tr.add_argument("--force", action="store_true",
                      help="이미 전환이 있어도 덧붙인다")
    p_tr.add_argument("--dry-run", action="store_true")
    p_tr.set_defaults(func=cmd_transitions)
    p_br = sub.add_parser("broll", help="배경 자료 화면 (plan / record / place)")
    p_br.add_argument("stage", choices=["plan", "record", "place"])
    p_br.add_argument("--name", default="릴스_러프컷", help="캡컷 초안 이름")
    p_br.add_argument("--draft-root", default=str(draft.DEFAULT_DRAFT_ROOT))
    p_br.add_argument("--dir", default=str(broll.DEFAULT_DIR),
                      help="녹화분을 두는 폴더")
    p_br.add_argument("--max-picks", type=int, default=broll.MAX_PICKS)
    p_br.add_argument("--min-picks", type=int, default=broll.MIN_PICKS)
    p_br.add_argument("--settle", type=float, default=2.5,
                      help="페이지가 뜨고 녹화까지 기다릴 시간(초)")
    p_br.add_argument("--rect", default="", help="녹화 영역 x,y,w,h (기본: 전체 화면)")
    p_br.add_argument("--no-scroll", action="store_true",
                      help="녹화 중 스크롤하지 않음")
    p_br.add_argument("--crop-mode", default="cover", choices=["cover", "fit"])
    p_br.add_argument("--crop-x", type=float, default=0.5,
                      help="cover로 자를 때 가로 위치 (0=왼쪽, 1=오른쪽)")
    p_br.add_argument("--dry-run", action="store_true",
                      help="record: 실행할 명령만 출력")
    p_br.set_defaults(func=cmd_broll)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
