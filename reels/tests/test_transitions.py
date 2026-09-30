"""장면 전환 주입 테스트."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from reels import draft, sfx, subtitles, transitions  # noqa: E402
from reels.util import SEC_US  # noqa: E402
from reels.tests.test_pipeline import make_video  # noqa: E402

SENTENCES = [
    "안녕하세요 오늘은 릴스 편집 툴을 소개할게요",
    "먼저 유튜브 영상을 받아야 됩니다",
    "그런데 여기서 문제가 하나 있어요",
    "이제 자막을 만들어 볼게요",
    "자막은 위스퍼가 알아서 만들어 줍니다",
    "두 번째로 효과음을 넣습니다",
    "다음은 장면 전환입니다",
    "마지막으로 궁금한 점은 댓글로 남겨주세요",
]


def build(tmp: Path) -> Path:
    video = make_video(tmp / "촬영본.mp4", seconds=60)
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


def main() -> int:
    tmp = Path(__file__).parent / "_tmp_tr"
    tmp.mkdir(exist_ok=True)
    content = build(tmp)

    before = json.loads(content.read_text(encoding="utf-8"))
    n_video = len([t for t in before["tracks"] if t["type"] == "video"][0]["segments"])
    n_text = len([t for t in before["tracks"] if t["type"] == "text"][0]["segments"])

    sentences = sfx.read_sentences(content)
    total = max(s["end"] for s in sentences)
    points = transitions.find_points(sentences)
    per30 = len(points) / (total / 30.0)
    assert 2 <= per30 <= 4.2, f"30초당 {per30:.1f}곳은 범위를 벗어남"
    # 마지막 컷에는 붙일 수 없다
    assert all(p.sentence_index < len(SENTENCES) - 1 for p in points)
    # 같은 전환이 연달아 나오면 안 된다
    kinds = [p.transition for p in points]
    assert all(a != b for a, b in zip(kinds, kinds[1:])), kinds
    assert len(set(kinds)) == len(kinds), f"전환이 겹침: {kinds}"
    print(f"지점 선정 OK — {len(points)}곳 (30초당 {per30:.1f}곳): "
          + ", ".join(f"{p.at_sec:.0f}s {p.transition}" for p in points))

    added = transitions.apply(content, points, duration=0.3)
    after = json.loads(content.read_text(encoding="utf-8"))
    tracks = {t["type"]: t for t in after["tracks"]}
    assert added == len(points)
    assert len(tracks["video"]["segments"]) == n_video, "영상 트랙 훼손"
    assert len(tracks["text"]["segments"]) == n_text, "자막 트랙 훼손"

    mats = after["materials"]["transitions"]
    assert len(mats) == added, f"전환 소재 {len(mats)}개 != {added}"
    ids = {m["id"] for m in mats}
    segs = sorted(tracks["video"]["segments"],
                  key=lambda s: s["target_timerange"]["start"])
    linked = {}
    for idx, seg in enumerate(segs):
        hit = ids & set(seg.get("extra_material_refs", []))
        if hit:
            linked[idx] = hit
    assert len(linked) == added, f"연결된 컷 {len(linked)}개 != {added}"
    assert set(linked) == {p.sentence_index for p in points}, linked
    for refs in linked.values():
        assert len(refs) == 1, "한 컷에 전환이 둘"
    for m in mats:
        assert m["type"] == "transition"
        assert abs(m["duration"] / SEC_US - 0.3) < 1e-6, m["duration"]
    print(f"주입 OK — 전환 소재 {len(mats)}개가 컷 {sorted(linked)}에 연결, "
          f"길이 {mats[0]['duration'] / SEC_US:.2f}초")

    # 다시 실행하면 중복 방지가 걸려야 한다
    try:
        transitions.apply(content, points, duration=0.3)
    except SystemExit as exc:
        assert "이미 전환" in str(exc), exc
        print("중복 방지 OK —", str(exc).split(".")[0])
    else:
        raise AssertionError("이미 전환이 있는데도 또 넣었다")

    print("\n" + transitions.table(points))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
