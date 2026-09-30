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


def main() -> int:
    tmp = Path(__file__).parent / "_tmp"
    tmp.mkdir(exist_ok=True)
    decisions = test_decisions()
    timeline, _ = test_subtitles(decisions)
    test_draft(tmp, timeline)
    print("\n" + clean.report(decisions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
