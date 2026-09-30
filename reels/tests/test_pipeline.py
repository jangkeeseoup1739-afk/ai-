"""판정/자막/초안 생성 전 구간 테스트. whisper 없이 가짜 받아쓰기로 돈다."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from reels import clean, draft, subtitles  # noqa: E402
from reels.util import ffmpeg_bin  # noqa: E402

FAKE = [
    (0.0, 0.6, "음"),
    (0.8, 3.0, "안녕하세요 오늘은 릴스 편집 툴을"),
    (3.2, 6.5, "안녕하세요 오늘은 릴스 편집 툴을 소개할게요"),
    (6.8, 9.5, "먼저 유튜브 영상을 받아야 되는데요"),
    (9.7, 10.2, "다시"),
    (10.4, 13.0, "먼저 유튜브 영상을 받아야 됩니다"),
    (13.2, 13.7, "그"),
    (13.9, 17.5, "자막은 위스퍼가 알아서 만들어 줍니다"),
    (17.7, 18.4, "그리고..."),
]


def fake_segments() -> list[dict]:
    return [{"id": i, "start": s, "end": e, "text": t}
            for i, (s, e, t) in enumerate(FAKE)]


def make_video(path: Path, seconds: int = 20) -> Path:
    subprocess.run([
        ffmpeg_bin(), "-y", "-v", "error",
        "-f", "lavfi", "-i", f"testsrc=size=1920x1080:rate=30:duration={seconds}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
        str(path),
    ], check=True)
    return path


def test_decisions() -> list[dict]:
    d = clean.decide(fake_segments())
    by_id = {x["id"]: x for x in d}
    dropped = {x["id"] for x in d if not x["keep"]}
    assert dropped == {0, 1, 3, 4, 6, 8}, f"예상과 다른 제거 목록: {sorted(dropped)}"
    assert "군말" in by_id[0]["reason"]
    assert "끊긴" in by_id[1]["reason"]
    assert "NG" in by_id[3]["reason"]
    assert "끊김" in by_id[8]["reason"]
    print("판정 OK — 유지:", [x["id"] for x in d if x["keep"]])
    return d


def test_subtitles(decisions: list[dict]) -> tuple[list[dict], list[dict]]:
    timeline = subtitles.build_timeline(decisions)
    assert [t["id"] for t in timeline] == [2, 5, 7]
    assert abs(timeline[0]["new_start"]) < 1e-9
    assert abs(timeline[1]["new_start"] - timeline[0]["duration"]) < 1e-9
    cues = subtitles.to_cues(timeline, max_chars=12)
    over = [c["text"] for c in cues if len(c["text"]) > 12]
    assert not over, f"12자를 넘는 줄: {over}"
    for a, b in zip(cues, cues[1:]):
        assert a["end"] <= b["start"] + 1e-6, "자막이 겹칩니다"
    print("자막 OK —", [c["text"] for c in cues])
    return timeline, cues


def test_draft(tmp: Path, timeline: list[dict]) -> Path:
    video = make_video(tmp / "촬영본.mp4")
    srt = subtitles.write_srt(timeline, tmp / "subtitle.srt", 12)
    root = tmp / "com.lveditor.draft"
    root.mkdir(parents=True, exist_ok=True)
    out = draft.build_draft(video, timeline, srt, draft_name="릴스_러프컷",
                            draft_root=root, width=1080, height=1920)
    content = json.loads((out / "draft_content.json").read_text(encoding="utf-8"))
    assert (out / "draft_meta_info.json").exists()
    assert content["canvas_config"]["width"] == 1080
    assert content["canvas_config"]["height"] == 1920
    tracks = {t["type"]: t for t in content["tracks"]}
    assert "video" in tracks and "text" in tracks, list(tracks)
    assert len(tracks["video"]["segments"]) == len(timeline)
    n_cues = len(subtitles.to_cues(timeline, 12))
    assert len(tracks["text"]["segments"]) == n_cues
    # 세로 꽉 채우기 배율 (1920x1080 -> 1080x1920 이면 (16/9)/(9/16) = 3.16)
    scale = tracks["video"]["segments"][0]["clip"]["scale"]["x"]
    assert abs(scale - (16 / 9) / (9 / 16)) < 0.01, scale
    print(f"초안 OK — 영상 {len(tracks['video']['segments'])}컷 / "
          f"자막 {len(tracks['text']['segments'])}줄 / 배율 {scale:.2f}")
    return out


def test_silence() -> None:
    """짧은 침묵은 남기고, 0.4초 넘는 침묵과 들어낸 자리는 붙인다."""
    decisions = [
        {"id": 0, "start": 0.0, "end": 2.0, "text": "첫 문장입니다", "keep": True},
        # 0.25초 간격 -> 그대로 남는다
        {"id": 1, "start": 2.25, "end": 4.0, "text": "둘째 문장입니다", "keep": True},
        # 2.0초 간격 -> 0.4초만 남는다
        {"id": 2, "start": 6.0, "end": 8.0, "text": "셋째 문장입니다", "keep": True},
        {"id": 3, "start": 8.1, "end": 8.6, "text": "음", "keep": False},
        # 사이에서 군말을 들어냈으니 하드컷
        {"id": 4, "start": 9.5, "end": 11.0, "text": "넷째 문장입니다", "keep": True},
    ]
    tl = subtitles.build_timeline(decisions, max_silence=0.4)
    assert [t["id"] for t in tl] == [0, 1, 2, 4]

    # 타임라인은 끊김 없이 이어져야 한다 (검은 구멍 금지)
    for a, b in zip(tl, tl[1:]):
        assert abs(a["new_end"] - b["new_start"]) < 1e-9, "타임라인에 구멍"

    # 0.25초 침묵은 앞뒤가 절반씩 나눠 가져 전부 보존
    assert abs(tl[0]["src_end"] - 2.125) < 1e-9, tl[0]
    assert abs(tl[1]["src_start"] - 2.125) < 1e-9, tl[1]
    # 2.0초 침묵은 0.4초만 (앞 0.2 + 뒤 0.2), 1.6초는 삭제
    assert abs(tl[1]["src_end"] - 4.2) < 1e-9, tl[1]
    assert abs(tl[2]["src_start"] - 5.8) < 1e-9, tl[2]
    # 군말을 들어낸 자리는 침묵 없이 붙는다
    assert abs(tl[2]["src_end"] - 8.0) < 1e-9, tl[2]
    assert abs(tl[3]["src_start"] - 9.5) < 1e-9, tl[3]
    # 소재 시작 이전으로는 내려가지 않는다
    assert tl[0]["src_start"] == 0.0

    total = tl[-1]["new_end"]
    raw = 11.0
    print(f"침묵 처리 OK — 원본 {raw:.1f}초 -> {total:.2f}초 "
          f"(0.25초 침묵 보존, 2.0초 침묵은 0.4초만 남김)")


def main() -> int:
    tmp = Path(__file__).parent / "_tmp"
    tmp.mkdir(exist_ok=True)
    test_silence()
    decisions = test_decisions()
    timeline, _ = test_subtitles(decisions)
    test_draft(tmp, timeline)
    print("\n" + clean.report(decisions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
