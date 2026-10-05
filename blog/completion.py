"""Tab 자동완성 스크립트를 파서에서 바로 만들어 낸다.

명령이나 옵션을 cli.py 에 추가하면 완성 목록도 같이 늘어난다(따로 손댈 것 없음).
설치는 한 줄이다.

    eval "$(python3 -m blog completion bash)"   # ~/.bashrc 에 넣으면 영구
    eval "$(python3 -m blog completion zsh)"    # ~/.zshrc
"""
from __future__ import annotations

import argparse
import sys

# 값으로 파일/폴더를 받는 옵션. 완성할 때 경로를 보여준다.
FILE_OPTS = ("--out", "-o", "--stats", "--html", "--text")
DIR_OPTS = ("--html-dir", "--save-dir")


def spec(parser: argparse.ArgumentParser) -> tuple[list[tuple[str, str]], dict[str, list[str]]]:
    """(명령 이름, 설명) 목록과 명령별 옵션 목록을 뽑는다."""
    subs = next((a for a in parser._actions
                 if isinstance(a, argparse._SubParsersAction)), None)
    if subs is None:
        return [], {}
    helps = {c.dest: (c.help or "") for c in subs._choices_actions}
    commands = [(name, helps.get(name, "")) for name in subs.choices]
    options = {
        name: sorted({o for a in sub._actions for o in a.option_strings})
        for name, sub in subs.choices.items()
    }
    return commands, options


def _runner() -> str:
    return f"{sys.executable} -m blog"


def bash_script(parser: argparse.ArgumentParser, name: str = "blog") -> str:
    commands, options = spec(parser)
    cmd_names = " ".join(n for n, _ in commands)
    cases = "\n".join(
        f'    {n}) opts="{" ".join(opts)}" ;;' for n, opts in options.items())
    return f"""# {name} 자동완성 (bash). 설치: eval "$({_runner()} completion bash)"
{name}() {{ {_runner()} "$@"; }}

_{name}_complete() {{
  local cur prev cmd opts i
  COMPREPLY=()
  cur="${{COMP_WORDS[COMP_CWORD]}}"
  prev="${{COMP_WORDS[COMP_CWORD-1]}}"

  case "$prev" in
    {"|".join(FILE_OPTS)})
      COMPREPLY=( $(compgen -f -- "$cur") ); return ;;
    {"|".join(DIR_OPTS)})
      COMPREPLY=( $(compgen -d -- "$cur") ); return ;;
  esac

  cmd=""
  for ((i=1; i<COMP_CWORD; i++)); do
    case "${{COMP_WORDS[i]}}" in
      -*) ;;
      *) cmd="${{COMP_WORDS[i]}}"; break ;;
    esac
  done

  if [ -z "$cmd" ]; then
    COMPREPLY=( $(compgen -W "{cmd_names}" -- "$cur") ); return
  fi

  case "$cmd" in
{cases}
    *) opts="" ;;
  esac
  COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
}}
complete -F _{name}_complete {name}
"""


def zsh_script(parser: argparse.ArgumentParser, name: str = "blog") -> str:
    commands, options = spec(parser)
    # 설명에 콜론이 들어가면 _describe 가 잘라 먹는다
    described = " \\\n    ".join(
        f"'{n}:{h.replace(':', ' -')}'" for n, h in commands)
    cases = "\n".join(
        f"      {n}) opts=({' '.join(opts)}) ;;" for n, opts in options.items())
    return f"""# {name} 자동완성 (zsh). 설치: eval "$({_runner()} completion zsh)"
{name}() {{ {_runner()} "$@"; }}

_{name}_complete() {{
  local -a cmds opts
  cmds=(
    {described}
  )
  if (( CURRENT == 2 )); then
    _describe '명령' cmds
    return
  fi
  case "${{words[CURRENT-1]}}" in
    {"|".join(FILE_OPTS)}) _files; return ;;
    {"|".join(DIR_OPTS)}) _files -/; return ;;
  esac
  case "${{words[2]}}" in
{cases}
      *) opts=() ;;
  esac
  compadd -- $opts
}}
(( $+functions[compdef] )) && compdef _{name}_complete {name}
"""


def script(parser: argparse.ArgumentParser, shell: str, name: str = "blog") -> str:
    if shell == "bash":
        return bash_script(parser, name)
    if shell == "zsh":
        return zsh_script(parser, name)
    raise SystemExit(f"bash 또는 zsh 만 됩니다 (받은 값: {shell})")
