# 릴스 분석 도구 세팅

macOS에서 인스타 릴스/쇼츠를 내려받고 음성을 텍스트로 옮기기 위한 도구 모음입니다.

| 도구 | 역할 |
|---|---|
| Homebrew | 맥용 패키지 관리자 |
| yt-dlp | 영상 다운로드 |
| ffmpeg | 영상 → 오디오 변환 |
| whisper-cpp | 음성 → 텍스트 (STT) |
| ggml-large-v3-turbo-q5_0.bin | whisper 모델 파일 (~574MB, `~/.cache/whisper`) |

## 설치

터미널에 붙여넣으세요.

```bash
curl -fsSL https://raw.githubusercontent.com/jangkeeseoup1739-afk/ai-/claude/happy-clarke-dlgd9d/scripts/setup-reels-tools.sh | bash
```

Homebrew가 아직 없다면 설치 중 **맥 로그인 비밀번호**를 한 번 물어봅니다.
(입력해도 화면에 글자가 보이지 않는 것이 정상입니다.)

## 사용 예시

```bash
# 1. 릴스 다운로드
yt-dlp -f 'bv*+ba/b' -o reel.mp4 '<릴스 URL>'

# 2. whisper가 쓰는 형식(16kHz 모노 wav)으로 변환
ffmpeg -i reel.mp4 -ar 16000 -ac 1 -c:a pcm_s16le reel.wav

# 3. 자막 뽑기 (한국어)
whisper-cli -m ~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin -f reel.wav -l ko -otxt
```
