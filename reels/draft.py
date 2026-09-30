"""4단계: pycapcut으로 캡컷 초안 생성 (원본 재인코딩 없이 컷만 반영)."""
from __future__ import annotations

from pathlib import Path

from .util import SEC_US

DEFAULT_DRAFT_ROOT = Path(
    "~/Movies/CapCut/User Data/Projects/com.lveditor.draft").expanduser()


def _fill_scale(mat_w: int, mat_h: int, canvas_w: int, canvas_h: int) -> float:
    """캔버스를 꽉 채우도록(cover) 필요한 배율. 캡컷 기본은 contain이라 키워줘야 한다."""
    if not mat_w or not mat_h:
        return 1.0
    mat_aspect = mat_w / mat_h
    canvas_aspect = canvas_w / canvas_h
    if mat_aspect >= canvas_aspect:
        return mat_aspect / canvas_aspect
    return canvas_aspect / mat_aspect


def build_draft(source: Path, timeline: list[dict], srt_path: Path, *,
                draft_name: str = "릴스_러프컷",
                draft_root: Path = DEFAULT_DRAFT_ROOT,
                width: int = 1080, height: int = 1920, fps: int = 30,
                fill: bool = True, subtitle_y: float = -0.62,
                font_size: float = 8.0,
                allow_replace: bool = True) -> Path:
    """유지 구간을 영상 트랙에 순서대로 얹고, SRT를 자막 트랙으로 불러온다."""
    import pycapcut as cc

    source = Path(source).expanduser().resolve()
    draft_root = Path(draft_root).expanduser()
    if not draft_root.exists():
        raise SystemExit(
            f"캡컷 초안 폴더가 없습니다: {draft_root}\n"
            "캡컷을 한 번 실행해 프로젝트를 하나 만든 뒤 다시 시도하세요."
        )
    if not timeline:
        raise SystemExit("남은 구간이 없습니다. decisions.json을 확인하세요.")

    folder = cc.DraftFolder(str(draft_root))
    script = folder.create_draft(draft_name, width, height, fps,
                                 allow_replace=allow_replace)

    material = cc.VideoMaterial(str(source))
    script.add_material(material)
    script.add_track(cc.TrackType.video, "영상")

    scale = _fill_scale(material.width, material.height, width, height) if fill else 1.0
    clip = cc.ClipSettings(scale_x=scale, scale_y=scale)

    for seg in timeline:
        src_start = int(round(seg["src_start"] * SEC_US))
        dur = int(round(seg["duration"] * SEC_US))
        if dur <= 0:
            continue
        # 소재 끝을 넘지 않도록 잘라준다 (whisper 타임스탬프가 조금 넘칠 수 있음)
        dur = min(dur, material.duration - src_start)
        if dur <= 0:
            continue
        script.add_segment(
            cc.VideoSegment(
                material,
                target_timerange=cc.trange(int(round(seg["new_start"] * SEC_US)), dur),
                source_timerange=cc.trange(src_start, dur),
                clip_settings=clip,
            ),
            "영상",
        )

    style_ref = cc.TextSegment(
        "style", cc.trange(0, SEC_US),
        style=cc.TextStyle(size=font_size, align=1, bold=True,
                           auto_wrapping=True, max_line_width=0.82),
        border=cc.TextBorder(color=(0.0, 0.0, 0.0), width=40.0),
    )
    script.import_srt(str(srt_path), "자막", style_reference=style_ref,
                      clip_settings=cc.ClipSettings(transform_y=subtitle_y))

    script.save()
    return draft_root / draft_name
