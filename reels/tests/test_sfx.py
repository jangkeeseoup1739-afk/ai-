"""효과음 배치 테스트. 네트워크 없이 로컬 효과음 폴더만으로 돈다."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from reels import draft, sfx, subtitles  # noqa: E402
from reels.util import SEC_US, ffmpeg_bin  # noqa: E402
from reels.tests.test_pipeline import make_video  # noqa: E402

SENTENCES = [
    "안녕하세요 오늘은 릴스 편집 툴을 소개할게요",
    "먼저 유튜브 영상을 받아야 됩니다",
    "근데 여기서 문제가 하나 있어요",
    "자막은 위스퍼가 알아서 만들어 줍니다",
    "그리고 캡컷 초안으로 바로 넘어갑니다",
    "3분이면 편집이 끝납니다",
    "궁금한 점은 댓글로 남겨주세요",
]


def make_sfx_dir(tmp: Path) -> Path:
    """이름만 맞춰둔 짧은 소리 파일들을 만든다."""
    d = tmp / "릴스효과음"
    d.mkdir(parents=True, exist_ok=True)
    recipes = {
        "whoosh.wav": "anoisesrc=color=brown:duration=0.6",
        "pop.wav": "sine=frequency=900:duration=0.2",
        "딩-bell.wav": "sine=frequency=1200:duration=0.8",
        "클릭.wav": "sine=frequency=1800:duration=0.1",
    }
    for name, src in recipes.items():
        out = d / name
        if not out.exists():
            subprocess.run([ffmpeg_bin(), "-y", "-v", "error", "-f", "lavfi",
                            "-i", src, "-c:a", "pcm_s16le", str(out)], check=True)
    return d


def build_base_draft(tmp: Path) -> tuple[Path, Path]:
    video = make_video(tmp / "촬영본.mp4", seconds=40)
    timeline, cursor = [], 0.0
    for i, text in enumerate(SENTENCES):
        dur = 3.0 + (i % 3) * 0.5
        timeline.append({"id": i, "src_start": cursor, "src_end": cursor + dur,
                         "duration": dur, "new_start": cursor,
                         "new_end": cursor + dur, "text": text})
        cursor += dur
    srt = subtitles.write_srt(timeline, tmp / "subtitle.srt", 12)
    root = tmp / "com.lveditor.draft"
    root.mkdir(parents=True, exist_ok=True)
    out = draft.build_draft(video, timeline, srt, draft_name="릴스_러프컷",
                            draft_root=root, width=1080, height=1920)
    return root, out / "draft_content.json"


def test_openverse_offline(tmp: Path) -> None:
    """Openverse 응답을 흉내 내어 파싱·길이필터·출처문구를 확인한다."""
    src = make_sfx_dir(tmp) / "pop.wav"
    long_src = tmp / "too_long.wav"
    subprocess.run([ffmpeg_bin(), "-y", "-v", "error", "-f", "lavfi",
                    "-i", "sine=frequency=440:duration=6", "-c:a", "pcm_s16le",
                    str(long_src)], check=True)

    fixture = [
        {"id": "aaa", "title": "Long Boom", "duration": 6000,        # 4초 초과
         "url": "https://example.test/long.wav", "license": "cc0"},
        {"id": "bbb", "title": "No URL", "duration": 900,            # url 없음
         "url": None, "license": "cc0"},
        {"id": "ccc", "title": "Nice Pop", "duration": 200,
         "url": "https://example.test/pop.wav",
         "creator": "Jane Doe", "license": "by", "license_version": "4.0",
         "license_url": "https://creativecommons.org/licenses/by/4.0/",
         "foreign_landing_url": "https://example.test/item/ccc",
         "provider": "freesound"},
    ]

    def fake_search(query, **kw):
        return fixture

    def fake_download(url, dest, timeout=30.0):
        shutil.copy(long_src if "long" in url else src, dest)
        return dest

    real_search, real_download = sfx.search_openverse, sfx.download
    sfx.search_openverse, sfx.download = fake_search, fake_download
    try:
        path, meta = sfx.fetch_openverse("pop", tmp / "cache")
    finally:
        sfx.search_openverse, sfx.download = real_search, real_download

    assert meta["title"] == "Nice Pop", meta          # 6초짜리와 url 없는 건 걸러짐
    assert meta["license"] == "by" and meta["creator"] == "Jane Doe"
    assert meta["duration"] < 4.0
    assert Path(path).exists()
    print(f"Openverse 파싱 OK — {meta['title']} / {meta['duration']:.2f}초 / CC {meta['license'].upper()}")

    picks = [sfx.Pick(0, "pop", "숫자 강조", 1.0, 1.05, "3분이면 끝")]
    picks[0].path, picks[0].source, picks[0].meta = path, "openverse", meta
    credit = sfx.attribution(picks)
    assert "CC BY 4.0" in credit and "Jane Doe" in credit and "Nice Pop" in credit
    print("출처 문구 OK —\n" + credit)

    cc0 = [sfx.Pick(0, "pop", "x", 1.0, 1.05, "y")]
    cc0[0].path, cc0[0].source, cc0[0].meta = path, "openverse", {"license": "cc0"}
    assert sfx.attribution(cc0) == "", "CC0만 쓰면 출처 문구가 없어야 함"


def main() -> int:
    tmp = Path(__file__).parent / "_tmp_sfx"
    tmp.mkdir(exist_ok=True)
    sfx_dir = make_sfx_dir(tmp)
    root, content = build_base_draft(tmp)

    before = json.loads(content.read_text(encoding="utf-8"))
    n_video = len([t for t in before["tracks"] if t["type"] == "video"][0]["segments"])
    n_text = len([t for t in before["tracks"] if t["type"] == "text"][0]["segments"])

    sentences = sfx.read_sentences(content)
    assert len(sentences) == len(SENTENCES), len(sentences)
    for s, want in zip(sentences, SENTENCES):
        got = s["text"].replace(" ", "")
        assert got == want.replace(" ", ""), f"{got!r} != {want!r}"
    print(f"문장 읽기 OK — {len(sentences)}개 / {sentences[-1]['end']:.1f}초")

    picks = sfx.choose(sentences)
    total = sentences[-1]["end"]
    per30 = len(picks) / (total / 30.0)
    assert 4 <= per30 <= 8.5, f"30초당 {per30:.1f}개는 범위를 벗어남"
    assert picks[0].kind == "whoosh" and picks[0].sentence_index == 0
    assert picks[-1].kind == "ding" and picks[-1].sentence_index == len(SENTENCES) - 1
    assert "댓글" in picks[-1].reason
    for p in picks:
        assert abs((p.sentence_start - p.at_sec) - 0.05) < 1e-9 or p.at_sec == 0.0
    print(f"배치 OK — {len(picks)}개 (30초당 {per30:.1f}개): "
          + ", ".join(f"{p.at_sec:.2f}s {p.kind}" for p in picks))

    picks = sfx.resolve(picks, sfx_dir=sfx_dir, allow_download=False)
    assert all(p.path for p in picks), [p.kind for p in picks if not p.path]
    assert all(p.source == "local" for p in picks)
    print("소리 찾기 OK —", {p.kind: Path(p.path).name for p in picks})

    added = sfx.attach(content, picks, volume=0.5)
    after = json.loads(content.read_text(encoding="utf-8"))
    tracks = {t["type"]: t for t in after["tracks"]}
    assert added == len(picks)
    assert len(tracks["video"]["segments"]) == n_video, "영상 트랙이 훼손됨"
    assert len(tracks["text"]["segments"]) == n_text, "자막 트랙이 훼손됨"
    assert "audio" in tracks, "오디오 트랙이 없음"
    audio = tracks["audio"]["segments"]
    assert len(audio) == len(picks)
    for seg, p in zip(sorted(audio, key=lambda s: s["target_timerange"]["start"]), picks):
        assert abs(seg["target_timerange"]["start"] / SEC_US - p.at_sec) < 1e-6
        assert abs(seg["volume"] - 0.5) < 1e-9, seg["volume"]
    assert content.with_suffix(".json.bak").exists(), "백업이 없음"
    print(f"초안 반영 OK — 영상 {n_video}컷 / 자막 {n_text}줄 유지, "
          f"효과음 {len(audio)}개 볼륨 {audio[0]['volume']}")

    print()
    test_openverse_offline(tmp)

    print("\n" + sfx.table(picks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
