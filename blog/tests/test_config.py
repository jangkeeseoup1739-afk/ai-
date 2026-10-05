"""저장된 기본값(--id 생략)과 Tab 자동완성 스크립트."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

TMP = Path(__file__).parent / "_tmp_cfg"
os.environ["BLOG_CONFIG"] = str(TMP / "config.json")

from blog import cli, completion, config          # noqa: E402
from blog.tests import _fixtures as fx            # noqa: E402


def test_save_load_clear() -> None:
    config.clear()
    assert config.load() == {}
    p = config.save(id="ks506l", place="수원", limit=None)
    assert p.exists()
    assert config.load() == {"id": "ks506l", "place": "수원"}   # 빈 값은 안 들어간다
    config.save(id="다른아이디")
    assert config.load()["id"] == "다른아이디" and config.load()["place"] == "수원"
    config.clear()
    assert config.load() == {}
    print("  저장·읽기·지우기 OK")


def test_broken_file_is_ignored() -> None:
    Path(os.environ["BLOG_CONFIG"]).parent.mkdir(parents=True, exist_ok=True)
    Path(os.environ["BLOG_CONFIG"]).write_text("깨진 내용", encoding="utf-8")
    assert config.load() == {}        # 터지지 않고 빈 설정으로 본다
    config.clear()
    print("  망가진 설정 파일 무시 OK")


def test_resolve_fills_id_and_place() -> None:
    config.save(id="ks506l", place="수원")

    class Args:
        id = None
        place = ""
        html_dir = None

    a = Args()
    config.resolve(a)
    assert a.id == "ks506l" and a.place == "수원"

    # 직접 준 값이 우선이고, 그 값이 기억된다
    b = Args()
    b.id = "newid"
    config.resolve(b)
    assert b.id == "newid"
    assert config.load()["id"] == "newid"
    config.clear()
    print("  --id 자동 채움 OK")


def test_cli_without_id_uses_saved() -> None:
    html_dir = TMP / "posts"
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "1.html").write_text(fx.long_post(), encoding="utf-8")

    assert cli.main(["config", "--id", "ks506l"]) == 0
    out = TMP / "진단.md"
    # --id 없이 돌아가야 한다
    assert cli.main(["diagnose", "--html-dir", str(html_dir), "--out", str(out)]) == 0
    assert "ks506l" in out.read_text(encoding="utf-8").splitlines()[0]
    config.clear()
    print("  --id 없이 실행 OK")


def test_completion_covers_every_command() -> None:
    parser = cli.build_parser()
    commands, options = completion.spec(parser)
    names = [n for n, _ in commands]
    for must in ("diagnose", "post", "keywords", "plan", "repurpose",
                 "config", "completion"):
        assert must in names, names
    assert "--stats" in options["diagnose"] and "--weeks" in options["plan"]
    assert all(h for _, h in commands)        # 설명 없는 명령이 있으면 zsh 목록이 빈다

    bash = completion.script(parser, "bash")
    assert "complete -F _blog_complete blog" in bash
    assert "blog() {" in bash                 # alias 가 아니라 함수여야 한다
    assert "--html-dir|--save-dir" in bash
    for n in names:
        assert f"    {n}) opts=" in bash, n

    zsh = completion.script(parser, "zsh")
    assert "compdef _blog_complete blog" in zsh
    assert "_describe" in zsh and "_files -/" in zsh

    custom = completion.script(parser, "bash", name="블로그진단")
    assert "complete -F _블로그진단_complete 블로그진단" in custom
    try:
        completion.script(parser, "fish")
    except SystemExit as e:
        assert "bash" in str(e)
    else:
        raise AssertionError("fish 를 받아 주면 안 된다")
    print(f"  자동완성 목록 OK (명령 {len(names)}개)")


def test_bash_script_runs() -> None:
    bash = shutil.which("bash")
    if not bash:
        print("  bash 없음 - 실행 검사 생략")
        return
    script = TMP / "c.bash"
    script.write_text(completion.script(cli.build_parser(), "bash"), encoding="utf-8")
    subprocess.run([bash, "-n", str(script)], check=True)

    probe = f'''
source "{script}"
COMP_WORDS=(blog ""); COMP_CWORD=1; _blog_complete; echo "${{COMPREPLY[@]}}"
COMP_WORDS=(blog plan --w); COMP_CWORD=2; _blog_complete; echo "${{COMPREPLY[@]}}"
'''
    r = subprocess.run([bash, "-c", probe], capture_output=True, text=True, check=True)
    first, second = r.stdout.strip().splitlines()
    assert "diagnose" in first and "completion" in first, first
    assert second.strip() == "--weeks", second
    print("  bash 자동완성 실제 동작 OK")


def main() -> int:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    try:
        test_save_load_clear()
        test_broken_file_is_ignored()
        test_resolve_fills_id_and_place()
        test_cli_without_id_uses_saved()
        test_completion_covers_every_command()
        test_bash_script_runs()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
