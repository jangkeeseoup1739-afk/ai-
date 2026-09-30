#!/bin/bash
# 릴스 편집 도구 설치 (macOS)
# 사전 조건: Homebrew가 설치되어 있어야 함 (없으면 아래 주석 명령을 먼저 실행 — 맥 비밀번호 필요)
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
set -euo pipefail

# brew PATH 보정 (Apple Silicon / Intel)
if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)"
else
  echo "Homebrew가 없습니다. 먼저 Homebrew를 설치하세요 (맥 비밀번호 필요):"
  echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  exit 1
fi

echo "== 1/3 brew 패키지 설치 =="
brew update
brew install yt-dlp ffmpeg whisper-cpp

echo "== 2/3 whisper 모델 다운로드 (~574MB) =="
MODEL_DIR="$HOME/.cache/whisper"
MODEL="$MODEL_DIR/ggml-large-v3-turbo-q5_0.bin"
mkdir -p "$MODEL_DIR"
curl -L -C - --progress-bar -o "$MODEL" \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin

echo "== 3/3 파이썬 가상환경 + pycapcut =="
python3 -m venv "$HOME/.pycapcut"
"$HOME/.pycapcut/bin/python" -m pip install --upgrade pip
"$HOME/.pycapcut/bin/pip" install pycapcut

echo
echo "== 설치 확인 =="
brew --version | head -1
echo "yt-dlp:   $(yt-dlp --version)"
echo "ffmpeg:   $(ffmpeg -version | head -1)"
echo "whisper:  $(brew list --versions whisper-cpp)"
command -v whisper-cli >/dev/null && echo "whisper-cli: $(command -v whisper-cli)"
ls -lh "$MODEL"
"$HOME/.pycapcut/bin/pip" show pycapcut | sed -n '1,2p'
echo
echo "설치 끝!"
