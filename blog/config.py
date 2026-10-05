"""자주 쓰는 값(블로그 아이디 등)을 한 번만 치고 기억해 둔다.

파일 위치
  윈도우: %APPDATA%\\blog\\config.json
  맥/리눅스: ~/.config/blog/config.json  (XDG_CONFIG_HOME 를 따른다)
  BLOG_CONFIG 환경변수가 있으면 그 경로를 쓴다 (테스트·여러 블로그 운영용).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

KEYS = ("id", "place", "limit")


def path() -> Path:
    override = os.environ.get("BLOG_CONFIG")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", "~")).expanduser()
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    return base / "blog" / "config.json"


def load() -> dict:
    p = path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save(**values) -> Path:
    """빈 값은 무시하고, 기존 설정 위에 덮어쓴다."""
    data = load()
    data.update({k: v for k, v in values.items() if k in KEYS and v not in (None, "")})
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")
    return p


def clear() -> None:
    p = path()
    if p.exists():
        p.unlink()


def resolve(args, remember: bool = True) -> None:
    """--id 를 안 줬으면 저장된 값을 쓰고, 줬으면 그 값을 기억한다."""
    saved = load()
    given = getattr(args, "id", None)
    if given:
        if remember and saved.get("id") != given:
            save(id=given, place=getattr(args, "place", "") or None)
            print(f"블로그 아이디 '{given}' 를 기억했습니다. 다음부터 --id 를 빼도 됩니다. "
                  f"({path()})", file=sys.stderr)
        return
    if saved.get("id"):
        args.id = saved["id"]
    if not getattr(args, "place", "") and saved.get("place"):
        args.place = saved["place"]
