# 릴스 러프컷 파이프라인

촬영본 하나를 넣으면 **받아쓰기 → NG/군말/끊김 정리 → 12자 자막 → 캡컷 초안**까지 만든다.
영상을 다시 인코딩하지 않는다. 컷은 캡컷 타임라인의 구간 정보로만 들어가므로
초안을 열어서 마음대로 다시 늘리고 줄일 수 있다.

## 설치 (macOS)

```bash
# Homebrew가 없다면 먼저 (맥 비밀번호 필요)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

bash reels/setup-mac.sh
```

`setup-mac.sh`가 하는 일: `yt-dlp`/`ffmpeg`/`whisper-cpp` 설치, whisper 모델
`ggml-large-v3-turbo-q5_0.bin`을 `~/.cache/whisper`에 내려받기, `~/.pycapcut`에
가상환경을 만들고 `pycapcut` 설치.

## 실행

```bash
source ~/.pycapcut/bin/activate
python -m reels all --input ~/Desktop/촬영본.mp4 --name 릴스_러프컷
```

끝나면 **캡컷을 완전히 종료했다가 다시 열어야** 초안 목록에 나타난다.

### 판정을 직접 손보기

자동 판정을 그대로 쓰지 않고 검토하려면:

```bash
python -m reels all -i ~/Desktop/촬영본.mp4 --review     # 리포트만 만들고 멈춤
$EDITOR ~/Desktop/.reels_work/decisions.json             # keep / text_final 수정
python -m reels all -i ~/Desktop/촬영본.mp4 \
    --from-decisions ~/Desktop/.reels_work/decisions.json
```

`decisions.json`의 각 항목은 `keep`(남길지)과 `text_final`(자막에 쓸 문장)만
고치면 된다. 나머지 필드는 건드리지 않아도 된다.

### 문맥 기반 판정/오타 교정 (선택)

규칙만으로는 "문맥 보고 오타 고치기"가 안 된다. API 키가 있으면 `--llm`을 붙인다.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
python -m reels all -i ~/Desktop/촬영본.mp4 --llm
```

## 뭘 빼는가

| 규칙 | 판정 근거 |
|------|-----------|
| 군말/구령 | 구간 전체가 `음 / 어 / 그 / 저 / 다시 / 컷 / 잠깐` 류 토큰만으로 되어 있을 때 |
| 말하다 끊김 | 다음 구간이 같은 말을 더 길게 이어서 다시 할 때(도입부 재촬영), `...`로 끝날 때, 어미 없이 3자 이하일 때 |
| 같은 말 반복(NG) | 20초 안쪽 4구간 이내에 75% 이상 겹치는 말이 또 나오면 **앞의 것을 버리고 마지막 테이크만** 남김 |

살아남은 대사는 앞에 붙은 군말만 떼어낸다(뒤쪽 내용은 손대지 않음).
제거된 구간은 전부 이유와 함께 `report.md`에 표로 남는다.

임계값은 `reels/clean.py`의 `decide()` 인자로 조정한다.
군말 목록은 같은 파일 `FILLERS`에 있다.

## 만들어지는 파일

작업 폴더는 기본적으로 영상 옆 `.reels_work/`:

| 파일 | 내용 |
|------|------|
| `audio.wav` | whisper용 16kHz mono |
| `whisper.json` | 받아쓰기 원본 |
| `segments.json` | 정규화한 구간 목록 |
| `decisions.json` | 구간별 keep/이유/최종 문장 — **손으로 고치는 파일** |
| `report.md` | 뺀 부분·남긴 부분 리포트 |
| `subtitle.srt` | 컷 이후 타임라인 기준 12자 자막 |

## 주요 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--name` | `릴스_러프컷` | 캡컷 초안 이름 |
| `--draft-root` | `~/Movies/CapCut/User Data/Projects/com.lveditor.draft` | 캡컷 초안 폴더 |
| `--width/--height` | `1080` / `1920` | 캔버스 크기 |
| `--max-chars` | `12` | 자막 한 줄 글자 수 |
| `--no-fill` | — | 세로 꽉 채우기 배율을 적용하지 않음(원본 비율 유지) |
| `--subtitle-y` | `-0.62` | 자막 세로 위치(-1이 맨 아래) |
| `--model` | `~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin` | whisper 모델 |

가로 촬영본은 기본적으로 세로 화면을 꽉 채우도록 확대된다(16:9 → 9:16이면 3.16배).
좌우가 잘리는 게 싫으면 `--no-fill`로 두고 캡컷에서 직접 맞추면 된다.

## 테스트

whisper 없이 가짜 받아쓰기로 판정·자막·초안 생성까지 전부 돈다.

```bash
python reels/tests/test_pipeline.py
```
