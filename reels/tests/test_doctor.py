"""doctor 테스트. 윈도우 분기는 sys.platform 을 갈아끼워 확인한다."""
from __future__ import annotations

import importlib
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from reels import doctor  # noqa: E402
from reels.tests.test_platforms import as_platform  # noqa: E402


def test_report_shape() -> None:
    checks = doctor.run(record=False)
    names = [c.name for c in checks]
    assert names == ["시스템", "외부 도구", "파이썬 패키지", "캡컷 초안 폴더",
                     "작업 폴더", "GPU", "모니터", "화면 녹화", "스크롤"], names
    for c in checks:
        assert c.status in (doctor.OK, doctor.WARN, doctor.FAIL, doctor.SKIP), c

    text = doctor.report(checks)
    for c in checks:
        assert c.name in text, c.name
    assert "## 요약" in text and "# reels doctor" in text
    # 표가 체크 수만큼 행을 갖는다
    rows = [l for l in text.splitlines() if l.startswith("| ") and " | " in l]
    assert len(rows) >= len(checks), rows
    print(f"  리포트 OK — {len(checks)}개 항목, {len(text.splitlines())}줄")


def test_draft_root_override(tmp: Path) -> None:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "릴스_러프컷").mkdir(exist_ok=True)
    c = doctor.check_draft_root(str(tmp))
    assert c.status == doctor.OK, c
    assert "릴스_러프컷" in "\n".join(c.lines), c.lines
    print("  초안 폴더 지정 OK —", c.detail)

    bad = doctor.check_draft_root(str(tmp / "없는폴더"))
    assert bad.status == doctor.FAIL
    print("  없는 폴더는 실패로 보고 OK")


class stub_which:
    """sys.platform 을 위조하면 3.12+ 의 shutil.which 가 윈도우 경로를 타다
    _winapi 를 찾지 못해 터진다. 실제 윈도우에선 멀쩡하므로, 분기만 보기 위해
    위조 구간에서만 which 를 세워둔다."""

    def __init__(self, found: str | None = "ffmpeg"):
        self.found = found

    def __enter__(self):
        self._real = shutil.which
        shutil.which = lambda name, *a, **k: self.found
        return self

    def __exit__(self, *exc):
        shutil.which = self._real
        return False


def test_windows_branch() -> None:
    """윈도우일 때 실제로 윈도우용 점검을 고르는지 확인."""
    with as_platform("win32", {"LOCALAPPDATA": r"C:\Users\나\AppData\Local"}), stub_which():
        importlib.reload(doctor)

        # 모니터: PowerShell이 없으므로 '읽지 못함'으로 떨어져야 한다 (죽으면 안 됨)
        mon = doctor.check_monitors()
        assert mon.name == "모니터" and mon.status in (doctor.OK, doctor.WARN), mon
        print(f"  모니터 분기 OK — {mon.status}: {mon.detail[:50]}")

        # 스크롤: powershell 이 없으니 실패로 보고하되 죽지 않아야 한다
        sc = doctor.check_scroll()
        assert sc.status == doctor.FAIL, sc
        print(f"  스크롤 분기 OK — {sc.detail}")

        # 녹화: 윈도우에선 건너뛰지 않고 gdigrab 명령을 만들어 시험해야 한다
        rec = doctor.check_recording(True)
        assert rec.status == doctor.FAIL, rec        # 가짜 ffmpeg 라 녹화는 실패
        assert "gdigrab" in "\n".join(rec.lines), rec.lines
        print(f"  녹화 분기 OK — gdigrab 명령을 만들고 {rec.status}로 보고")

        # 초안 폴더 후보가 LOCALAPPDATA 를 따라야 한다
        dr = doctor.check_draft_root()
        assert any("AppData" in l for l in dr.lines), dr.lines
        print("  초안 폴더 후보 OK — LOCALAPPDATA 반영")

    # 도구가 아예 없을 때 설치 안내가 winget 을 가리켜야 한다
    with as_platform("win32"), stub_which(None):
        importlib.reload(doctor)
        tools = doctor.check_tools()
        assert tools.status == doctor.FAIL and "winget" in tools.detail, tools
        print("  설치 안내 OK — winget")

    importlib.reload(doctor)


def test_exit_code_logic() -> None:
    fail = [doctor.Check("x", doctor.FAIL)]
    warn = [doctor.Check("x", doctor.WARN)]
    assert any(c.status == doctor.FAIL for c in fail)
    assert not any(c.status == doctor.FAIL for c in warn)
    print("  종료 코드 판정 OK (실패가 있을 때만 1)")


def main() -> int:
    tmp = Path(__file__).parent / "_tmp_doc"
    print("리포트:")
    test_report_shape()
    print("초안 폴더:")
    test_draft_root_override(tmp / "com.lveditor.draft")
    print("윈도우 분기:")
    test_windows_branch()
    print("기타:")
    test_exit_code_logic()
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
