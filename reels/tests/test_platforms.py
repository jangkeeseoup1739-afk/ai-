"""플랫폼 분기 테스트. 실제 윈도우 없이 sys.platform을 갈아끼워 확인한다."""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class as_platform:
    """sys.platform(과 환경변수)을 바꾼 채로 platforms 모듈을 쓰게 한다.

    경로 후보는 호출 시점에 계산되므로 블록 안에서 불러야 한다.
    """

    def __init__(self, platform: str, env: dict | None = None):
        self.platform = platform
        self.env = env or {}

    def __enter__(self):
        self._real_platform = sys.platform
        self._real_env = dict(os.environ)
        sys.platform = self.platform
        os.environ.update(self.env)
        import reels.platforms as mod
        self.mod = importlib.reload(mod)
        return self.mod

    def __exit__(self, *exc):
        sys.platform = self._real_platform
        os.environ.clear()
        os.environ.update(self._real_env)
        importlib.reload(self.mod)   # 원래 플랫폼으로 되돌린다
        return False


def test_windows() -> None:
  with as_platform("win32", {"LOCALAPPDATA": r"C:\Users\나\AppData\Local"}) as p:
    assert p.IS_WIN and not p.IS_MAC
    assert p.RECORD_EXT == ".mp4"

    roots = [str(r) for r in p.draft_root_candidates()]
    # 첫 후보는 LOCALAPPDATA 를 그대로 따라야 한다
    assert roots[0].startswith(r"C:\Users\나\AppData\Local"), roots[0]
    assert roots[0].endswith("com.lveditor.draft"), roots[0]
    assert any("CapCut Drafts" in r for r in roots), roots   # 초안 위치를 옮긴 경우
    print("  윈도우 초안 후보:", roots[0])

    cmd = p.open_browser_cmd("https://example.com")
    assert cmd[:3] == ["cmd", "/c", "start"] and cmd[3] == "", cmd
    assert cmd[-1] == "https://example.com"
    print("  브라우저:", " ".join(cmd))

    rec = p.record_cmd(Path("out.mp4"), 4.0, ffmpeg="ffmpeg")
    assert "gdigrab" in rec and "desktop" in rec, rec
    assert "-t" in rec and rec[rec.index("-t") + 1] == "4.00"
    print("  녹화:", " ".join(rec))

    rect = p.record_cmd(Path("out.mp4"), 3.0, rect="10,20,1280,720", ffmpeg="ffmpeg")
    assert rect[rect.index("-offset_x") + 1] == "10"
    assert rect[rect.index("-video_size") + 1] == "1280x720"
    print("  영역 녹화 인자 OK")

    sc = p.scroll_cmd()
    assert sc[0] == "powershell" and "SendKeys" in sc[-1], sc
    assert "AppActivate" in sc[-1]
    assert p.can_record()
    print("  스크롤:", sc[-1][:60] + "...")


def test_mac() -> None:
  with as_platform("darwin") as p:
    assert p.IS_MAC and not p.IS_WIN
    assert p.RECORD_EXT == ".mov"
    assert "Movies" in str(p.draft_root_candidates()[0])
    assert p.open_browser_cmd("u")[:3] == ["open", "-a", "Google Chrome"]
    rec = p.record_cmd(Path("o.mov"), 4.0)
    assert rec[0] == "screencapture" and "-v" in rec
    assert p.scroll_cmd()[0] == "osascript"
    assert p.can_record()
    print("  맥 분기 OK —", p.draft_root_candidates()[0])


def test_find_recording(tmp: Path) -> None:
    import reels.platforms as p
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "03-site.mkv").write_bytes(b"x")     # 직접 녹화해 확장자가 다른 경우
    found = p.find_recording(tmp, "03-site")
    assert found is not None and found.suffix == ".mkv", found
    assert p.find_recording(tmp, "없는파일") is None
    print("  확장자 무관 탐색 OK —", found.name)


def main() -> int:
    print("윈도우:")
    test_windows()
    print("맥:")
    test_mac()
    print("공통:")
    test_find_recording(Path(__file__).parent / "_tmp_plat")
    import shutil
    shutil.rmtree(Path(__file__).parent / "_tmp_plat", ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
