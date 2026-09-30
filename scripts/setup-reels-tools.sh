#!/bin/bash
# 릴스 분석 도구 설치 스크립트 (macOS)
#   - Homebrew (없으면 설치)
#   - yt-dlp, ffmpeg, whisper-cpp
#   - whisper 모델 ggml-large-v3-turbo-q5_0.bin -> ~/.cache/whisper
#
# 사용법:  bash scripts/setup-reels-tools.sh
# 중간에 맥 로그인 비밀번호를 물어볼 수 있습니다(Homebrew 설치 시).

set -u

MODEL_DIR="$HOME/.cache/whisper"
MODEL_NAME="ggml-large-v3-turbo-q5_0.bin"
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/${MODEL_NAME}"
MODEL_PATH="${MODEL_DIR}/${MODEL_NAME}"

blue()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
green() { printf '\033[1;32m%s\033[0m\n' "$*"; }
red()   { printf '\033[1;31m%s\033[0m\n' "$*"; }

if [ "$(uname -s)" != "Darwin" ]; then
  red "이 스크립트는 macOS 전용입니다. (현재: $(uname -s))"
  exit 1
fi

# ---------------------------------------------------------------- 1. Homebrew
blue "1/4  Homebrew 확인"

if ! command -v brew >/dev/null 2>&1; then
  # 이미 설치돼 있는데 PATH만 안 잡힌 경우를 먼저 확인
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [ -x "$candidate" ]; then
      eval "$("$candidate" shellenv)"
      break
    fi
  done
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew가 없습니다. 지금 설치합니다."
  echo "→ 설치 중 맥 로그인 비밀번호를 물어봅니다. 입력해도 화면에 안 보이는 게 정상입니다."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || {
    red "Homebrew 설치 실패. 위 메시지를 확인해 주세요."
    exit 1
  }

  # 설치 직후 PATH 등록 (Apple Silicon: /opt/homebrew, Intel: /usr/local)
  if [ -x /opt/homebrew/bin/brew ]; then
    BREW_BIN=/opt/homebrew/bin/brew
  else
    BREW_BIN=/usr/local/bin/brew
  fi
  eval "$("$BREW_BIN" shellenv)"

  SHELL_PROFILE="$HOME/.zprofile"
  [ "$(basename "${SHELL:-/bin/zsh}")" = "bash" ] && SHELL_PROFILE="$HOME/.bash_profile"
  if ! grep -q 'brew shellenv' "$SHELL_PROFILE" 2>/dev/null; then
    echo "eval \"\$(${BREW_BIN} shellenv)\"" >> "$SHELL_PROFILE"
    echo "PATH 설정을 $SHELL_PROFILE 에 추가했습니다."
  fi
else
  green "Homebrew 이미 설치됨: $(command -v brew)"
fi

# ------------------------------------------------------------------ 2. 패키지
blue "2/4  yt-dlp, ffmpeg, whisper-cpp 설치"

for pkg in yt-dlp ffmpeg whisper-cpp; do
  if brew list --formula "$pkg" >/dev/null 2>&1; then
    echo "$pkg : 이미 설치됨 → 업그레이드 확인"
    brew upgrade "$pkg" 2>/dev/null || true
  else
    echo "$pkg : 설치 중..."
    brew install "$pkg" || { red "$pkg 설치 실패"; exit 1; }
  fi
done

# -------------------------------------------------------------------- 3. 모델
blue "3/4  whisper 모델 내려받기 (약 574MB)"

mkdir -p "$MODEL_DIR"

if [ -s "$MODEL_PATH" ] && [ "$(stat -f%z "$MODEL_PATH")" -gt 400000000 ]; then
  green "모델 이미 있음: $MODEL_PATH ($(du -h "$MODEL_PATH" | cut -f1))"
else
  echo "받는 중: $MODEL_URL"
  # -C - : 중간에 끊겨도 이어받기
  curl -L --fail --progress-bar -C - -o "$MODEL_PATH" "$MODEL_URL" || {
    red "모델 다운로드 실패. 네트워크 확인 후 다시 실행하면 이어받습니다."
    exit 1
  }
  green "받기 완료: $MODEL_PATH ($(du -h "$MODEL_PATH" | cut -f1))"
fi

# ------------------------------------------------------------------ 4. 버전확인
blue "4/4  설치된 버전 확인"

printf '  %-12s %s\n' "brew"   "$(brew --version | head -1)"
printf '  %-12s %s\n' "yt-dlp" "$(yt-dlp --version 2>/dev/null || echo '확인 실패')"
printf '  %-12s %s\n' "ffmpeg" "$(ffmpeg -version 2>/dev/null | head -1 || echo '확인 실패')"

# whisper.cpp 실행파일 이름은 버전에 따라 whisper-cli / whisper-cpp / main
WHISPER_BIN=""
for b in whisper-cli whisper-cpp main; do
  if command -v "$b" >/dev/null 2>&1; then WHISPER_BIN="$b"; break; fi
done
if [ -n "$WHISPER_BIN" ]; then
  printf '  %-12s %s (%s)\n' "whisper" "$(brew list --versions whisper-cpp | head -1)" "실행: $WHISPER_BIN"
else
  printf '  %-12s %s\n' "whisper" "$(brew list --versions whisper-cpp 2>/dev/null || echo '확인 실패')"
fi
printf '  %-12s %s\n' "model" "$MODEL_PATH ($(du -h "$MODEL_PATH" 2>/dev/null | cut -f1))"

echo
green "설치 끝!"
echo
echo "사용 예시:"
echo "  yt-dlp -f 'bv*+ba/b' -o reel.mp4 '<릴스 URL>'"
echo "  ffmpeg -i reel.mp4 -ar 16000 -ac 1 -c:a pcm_s16le reel.wav"
echo "  ${WHISPER_BIN:-whisper-cli} -m \"$MODEL_PATH\" -f reel.wav -l ko -otxt"
