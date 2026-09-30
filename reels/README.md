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

침묵은 구간 사이 간격이 **0.4초를 넘을 때만** 넘는 만큼 덜어낸다(`--max-silence`).
남길 침묵은 빈자리로 두지 않고 앞뒤 컷의 소재 범위를 절반씩 넓혀 채우므로,
영상에 검은 구멍이 생기지 않고 말끝이 잘리지도 않는다.
NG나 군말을 들어낸 자리는 침묵을 남기지 않고 바로 붙인다.

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
| `--max-silence` | `0.4` | 구간 사이에 남길 침묵의 최대 길이(초) |
| `--no-fill` | — | 세로 꽉 채우기 배율을 적용하지 않음(원본 비율 유지) |
| `--subtitle-y` | `-0.62` | 자막 세로 위치(-1이 맨 아래) |
| `--model` | `~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin` | whisper 모델 |

가로 촬영본은 기본적으로 세로 화면을 꽉 채우도록 확대된다(16:9 → 9:16이면 3.16배).
좌우가 잘리는 게 싫으면 `--no-fill`로 두고 캡컷에서 직접 맞추면 된다.

## 효과음 넣기

이미 만든 초안에 효과음 트랙을 덧붙인다. **캡컷에서 해당 프로젝트를 닫아두고** 실행할 것.

```bash
python -m reels sfx --name 릴스_러프컷 --dry-run   # 어디에 뭘 넣을지만 확인
python -m reels sfx --name 릴스_러프컷             # 실제로 넣고 저장
```

문장 경계는 초안의 **영상 컷**에서, 문장 내용은 **자막 트랙**에서 읽는다.
각 소리는 문장 시작 **0.05초 전**에, 볼륨 **50%**로 `효과음` 오디오 트랙에 들어간다.
저장 전에 `draft_content.json.bak`으로 원본을 백업한다.

### 어떤 소리를 어디에

| 자리 | 소리 | 판정 근거 |
|------|------|-----------|
| 첫 문장 | whoosh | 무조건 |
| 반전 | pop | `근데 / 하지만 / 사실 / 알고 보니 / 반전 / 의외로 / 문제는` |
| 숫자 강조 | pop | 숫자, `%`, `배 / 개 / 초 / 분 / 원 / 명 / 번` |
| 목록 시작 | click | `첫째 / 첫 번째 / 먼저 / 우선 / 일단` |
| 주제 전환 | swoosh | `그리고 / 다음은 / 이제 / 마지막으로 / 두 번째` |
| 마지막 문장 | ding | 무조건 (`댓글 / 구독 / 저장`이 있으면 댓글 유도로 표시) |

개수는 **30초당 4~8개**로 제한하고(기본 6개), 효과음끼리 2초 이상 띄운다.
첫 문장과 마지막 문장이 먼저 확보되고, 남는 자리를 반전·숫자 → 목록 → 주제 전환 순으로 채운다.
`--per-30s / --min-per-30s / --max-per-30s / --spacing`으로 조정한다.

### 소리를 어디서 구하나

1. `~/릴스효과음` 폴더를 먼저 뒤진다. 파일명에 종류 이름이 들어 있으면 쓴다
   (`whoosh.wav`, `딩-bell.wav`, `클릭.mp3` 등 — 별칭은 `sfx.py`의 `KIND_ALIASES`).
2. 없으면 Openverse에서 `license=cc0,by`로 검색해 **4초 이하 첫 결과**를 받는다.
   가입이나 키가 필요 없다. 받은 파일은 `~/.cache/reels-sfx`에 둔다.
   실제로 열리는 오디오인지 확인하고, 아니면 다음 후보로 넘어간다.
3. `--no-download`를 주면 로컬 파일만 쓴다.

CC BY 소리를 썼으면 캡션에 붙일 출처 문구를 마지막에 출력한다. CC0만 썼으면 표기가 필요 없다.

### 효과음 옵션

| 옵션 | 기본값 |
|------|--------|
| `--sfx-dir` | `~/릴스효과음` |
| `--cache` | `~/.cache/reels-sfx` |
| `--track-name` | `효과음` |
| `--volume` | `0.5` |
| `--dry-run` | 초안을 건드리지 않고 배치안만 출력 |

같은 이름의 트랙이 이미 있으면 덮어쓰지 않고 멈춘다.

## 장면 전환

```bash
python -m reels transitions --name 릴스_러프컷 --dry-run
python -m reels transitions --name 릴스_러프컷
```

이야기가 바뀌는 컷 경계에 **30초당 2~4곳**(기본 3곳), 길이 **0.3초** 전환을 넣는다.
전환은 pycapcut 규약대로 **앞쪽 컷**에 붙는다. 마지막 컷에는 붙일 수 없다.

| 뒤 문장이 이렇게 시작하면 | 판정 | 우선순위 |
|---|---|---|
| `자 그럼 / 그러면 / 이제 / 이번엔` | 화제를 넘김 | 높음 |
| `다음은 / 다음으로 / 그다음` | 다음 순서 | 높음 |
| `마지막으로 / 정리하면 / 결론적으로` | 마무리 | 높음 |
| `두 번째 / 세 번째` | 목록의 다음 항목 | 중간 |
| `그런데 / 근데 / 하지만 / 반면 / 한편` | 이야기가 꺾임 | 중간 |
| `그리고 / 또 / 게다가` | 이어지며 바뀜 | 낮음 |

전환은 `White_Flash → Snap_Zoom → Whip_Tear → Lumin_Flash → Zoom_to_Change →
Signal_Glitch_2` 순서로 돌려 쓰므로 같은 전환이 연달아 나오지 않는다
(`transitions.py`의 `DEFAULT_POOL`). 전환 사이는 3초 이상 띄우고,
앞뒤 컷의 절반보다 길어지지 않도록 줄인다.

이미 전환이 있는 초안은 덮어쓰지 않고 멈춘다(`--force`로 무시).
저장 전에 `draft_content.json.bak`으로 백업한다.

> **확인이 필요한 점**: CapCut의 전환은 대부분 overlap 방식이라,
> 캡컷이 전환을 넣으면서 뒤 클립을 당겨 붙이는지 여부에 따라 자막·효과음
> 싱크가 조금 밀릴 수 있다. 초안을 열어 컷 경계를 한 번 확인할 것.
> 문제가 있으면 `.bak`을 되돌리면 된다.

## 배경 자료 화면

세 단계로 나뉜다. 가운데 `record`만 macOS에서 돌아간다.

```bash
python -m reels broll plan   --name 릴스_러프컷   # 보여줄 화면 목록 (확인용)
$EDITOR ~/릴스자료/plan.json                      # 빈 url 채우기
python -m reels broll record --name 릴스_러프컷   # 크롬으로 열고 녹화
python -m reels broll place  --name 릴스_러프컷   # 세로로 잘라 트랙에 올림
```

### plan

사이트·앱·숫자·결과물을 말하는 문장에서 **3~5곳**을 고른다. 우선순위는
주소를 직접 말한 곳 → 아는 서비스 이름 → 숫자 → 결과물 순이다.
아는 서비스는 주소를 자동으로 채운다(`KNOWN_SITES`). 숫자·결과물은 보여줄
화면을 알 수 없으므로 `plan.json`의 `url`을 직접 채워야 한다.
길이는 문장 길이에 맞춰 3~5초.

**로그인·결제·개인정보 화면은 여기서 막는다.** 주소에 `/login`, `/checkout`,
`/billing`, `/account`, `mail.` 등이 들어가거나, 문장에 `로그인 / 결제 /
비밀번호 / 계좌 / 주민등록`이 나오면 후보에서 빼고 표에 이유를 적는다.
`record`에서도 한 번 더 막는다.

### record

`open -a "Google Chrome" --new <url>` 로 열고, 페이지가 뜰 때까지 기다린 뒤
`screencapture -v -V <초> -x` 로 녹화하며 아래 화살표를 눌러 천천히 스크롤한다.
`~/릴스자료`에 저장.

- **화면 기록 권한**이 필요하다 (시스템 설정 → 개인정보 보호 및 보안 → 화면 기록).
- 스크롤에는 **손쉬운 사용 권한**이 필요하다. 없으면 스크롤만 조용히 포기하고 녹화는 계속한다.
- `--dry-run`으로 실행할 명령만 볼 수 있다. `--no-scroll`, `--rect x,y,w,h`, `--settle 초` 지원.
- 녹화 전에 비밀번호 관리자·메일·알림을 닫아둘 것.

### place

녹화분을 `1080x960`(세로 캔버스의 위쪽 절반)으로 잘라 `자료 화면` 영상 트랙에
올린다. 레이어는 **본 영상 위, 자막 아래**. 위치는 `transform_y=0.5`.

`--crop-mode cover`(기본, 가운데를 채워 자름) / `fit`(전체를 넣고 위아래 여백).
`--crop-x 0`이면 왼쪽 기준으로 자른다(웹 내용이 왼쪽에 몰린 경우).

## 테스트

whisper 없이 가짜 받아쓰기로 판정·자막·초안 생성까지 전부 돈다.

```bash
python reels/tests/test_pipeline.py   # 판정·자막·초안 생성
python reels/tests/test_sfx.py        # 효과음 배치·Openverse 파싱·출처 문구
python reels/tests/test_transitions.py # 전환 지점 선정·주입·중복 방지
python reels/tests/test_broll.py       # 자료 화면 선정·차단·세로 변환·배치
```
