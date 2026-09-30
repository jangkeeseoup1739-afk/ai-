"""자료 화면 테스트. 녹화(macOS)만 빼고 전부 돈다."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from reels import broll, draft, sfx, subtitles  # noqa: E402
from reels.util import SEC_US, ffmpeg_bin  # noqa: E402
from reels.tests.test_pipeline import make_video  # noqa: E402

SENTENCES = [
    "안녕하세요 오늘은 릴스 편집 툴을 소개할게요",
    "먼저 유튜브에서 영상을 받습니다",
    "효과음은 openverse 에서 가져옵니다",
    "편집 시간이 30분에서 3분으로 줄었어요",
    "여기 보시면 결과물이 이렇게 나옵니다",
    "로그인 화면에서 비밀번호를 넣으면 됩니다",
    "궁금한 점은 댓글로 남겨주세요",
]


def build(tmp: Path) -> Path:
    video = make_video(tmp / "촬영본.mp4", seconds=40)
    timeline, cursor = [], 0.0
    for i, text in enumerate(SENTENCES):
        dur = 4.0
        timeline.append({"id": i, "src_start": cursor, "src_end": cursor + dur,
                         "duration": dur, "new_start": cursor,
                         "new_end": cursor + dur, "text": text})
        cursor += dur
    srt = subtitles.write_srt(timeline, tmp / "subtitle.srt", 12)
    root = tmp / "com.lveditor.draft"
    root.mkdir(parents=True, exist_ok=True)
    out = draft.build_draft(video, timeline, srt, draft_name="릴스_러프컷",
                            draft_root=root, width=1080, height=1920)
    return out / "draft_content.json"


def fake_recordings(shots: list[broll.Shot], d: Path) -> None:
    """가로 화면 녹화분을 흉내 낸다 (2560x1600)."""
    d.mkdir(parents=True, exist_ok=True)
    for s in shots:
        if s.blocked:
            continue
        out = d / s.file
        subprocess.run([
            ffmpeg_bin(), "-y", "-v", "error", "-f", "lavfi",
            "-i", f"testsrc=size=2560x1600:rate=30:duration={s.duration:.0f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)], check=True)


def main() -> int:
    tmp = Path(__file__).parent / "_tmp_broll"
    tmp.mkdir(exist_ok=True)
    content = build(tmp)
    work = tmp / "릴스자료"

    before = json.loads(content.read_text(encoding="utf-8"))
    n_video = len([t for t in before["tracks"] if t["type"] == "video"][0]["segments"])
    n_text = len([t for t in before["tracks"] if t["type"] == "text"][0]["segments"])

    sentences = sfx.read_sentences(content)
    shots = broll.plan(sentences)
    live = [s for s in shots if not s.blocked]
    blocked = [s for s in shots if s.blocked]

    assert 1 <= len(live) <= broll.MAX_PICKS, len(live)
    assert blocked, "로그인·비밀번호 문장이 걸러지지 않음"
    assert blocked[0].sentence_index == 5, blocked[0]
    assert "개인정보" in blocked[0].block_reason
    kinds = {s.kind for s in live}
    assert "site" in kinds, kinds          # 유튜브 / openverse
    urls = {s.url for s in live if s.url}
    assert "https://www.youtube.com" in urls and "https://openverse.org" in urls, urls
    for s in live:
        assert broll.MIN_CLIP <= s.duration <= broll.MAX_CLIP, s.duration
    print(f"후보 선정 OK — {len(live)}곳 채택, {len(blocked)}곳 차단: "
          + ", ".join(f"{s.at_sec:.0f}s {s.kind}" for s in live))
    print("  차단:", blocked[0].text, "->", blocked[0].block_reason)

    # 로그인 주소도 막히는지
    guard = broll.plan([{"index": 0, "start": 0.0, "end": 4.0,
                         "text": "github.com/login 에서 시작합니다"}])
    assert guard and guard[0].blocked and "로그인" in guard[0].block_reason, guard
    print("  주소 차단 OK —", guard[0].url, "->", guard[0].block_reason)

    path = broll.save_plan(shots, work)
    assert broll.load_plan(path)[0].file == shots[0].file
    print(f"계획 저장/복원 OK — {path.name}")

    cmds = broll.record_commands(live[0], work)
    assert cmds[0][:3] == ["open", "-a", "Google Chrome"]
    assert cmds[1][0] == "screencapture" and "-v" in cmds[1] and "-V" in cmds[1]
    print("  녹화 명령:", " ".join(cmds[1]))

    fake_recordings(shots, work)
    added = broll.place(content, shots, work)
    after = json.loads(content.read_text(encoding="utf-8"))
    tracks = [t for t in after["tracks"]]
    video_tracks = [t for t in tracks if t["type"] == "video"]
    text_track = [t for t in tracks if t["type"] == "text"][0]

    assert added == len(live)
    assert len(video_tracks) == 2, f"영상 트랙이 {len(video_tracks)}개"
    main_tr = min(video_tracks, key=lambda t: len(t["segments"]) * 0 + t["segments"][0]["render_index"])
    broll_tr = max(video_tracks, key=lambda t: t["segments"][0]["render_index"])
    assert len(main_tr["segments"]) == n_video, "본 영상 트랙 훼손"
    assert len(broll_tr["segments"]) == added
    assert len(text_track["segments"]) == n_text, "자막 트랙 훼손"
    # 자료 화면은 본 영상 위, 자막 아래
    assert (main_tr["segments"][0]["render_index"]
            < broll_tr["segments"][0]["render_index"]
            < text_track["segments"][0]["render_index"]), "레이어 순서가 틀림"
    for seg, s in zip(sorted(broll_tr["segments"],
                             key=lambda x: x["target_timerange"]["start"]), live):
        assert abs(seg["target_timerange"]["start"] / SEC_US - s.at_sec) < 1e-6
        assert abs(seg["clip"]["transform"]["y"] - broll.UPPER_HALF_Y) < 1e-9
    print(f"배치 OK — 자료 화면 {added}개가 본 영상({main_tr['segments'][0]['render_index']}) "
          f"위, 자막({text_track['segments'][0]['render_index']}) 아래 "
          f"레이어 {broll_tr['segments'][0]['render_index']}, 위쪽 절반(y={broll.UPPER_HALF_Y})")

    # 세로 변환 결과 확인
    vert = next(work.glob("*_vert.mp4"))
    probe = subprocess.run([ffmpeg_bin(), "-v", "error", "-i", str(vert), "-f", "null", "-"],
                           capture_output=True, text=True)
    assert probe.returncode == 0, probe.stderr
    import pymediainfo
    t = pymediainfo.MediaInfo.parse(str(vert)).video_tracks[0]
    assert (t.width, t.height) == (broll.HALF_W, broll.HALF_H), (t.width, t.height)
    print(f"세로 변환 OK — 2560x1600 -> {t.width}x{t.height}")

    print("\n" + broll.table(shots))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
