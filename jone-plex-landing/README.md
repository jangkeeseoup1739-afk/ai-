# 주안국가산단역 제이원플렉스 · 분양 홍보 랜딩페이지

인천 미추홀구 주안동 **제이원플렉스 지식산업센터** 분양 상담을 받기 위한 모바일 우선 카드형 랜딩페이지입니다.

- React 18 + TypeScript + Vite + Tailwind CSS
- 빌드할 때 HTML을 미리 그려 둠(프리렌더링) → 네이버·구글 검색 로봇이 본문을 바로 읽음
- Vercel 배포용 설정과 상담 접수 서버 함수(`api/consult.ts`) 포함
- 기존 홈페이지·도메인과 상관없는 **새 프로젝트**입니다. 따로 테스트하고 배포할 수 있습니다.

> **확인되지 않은 정보는 넣지 않았습니다.** 면적·분양가·도면·현장 주소·역에서의 거리는 모두 비워 두었고, 화면에는 "상담 문의" 또는 "확인 후 안내"로 나옵니다. 공식 자료를 받으면 아래 설정 파일에 입력하세요.

---

## 1. 바로 실행하기

Node.js 20 이상이 필요합니다. (`node -v` 로 확인)

```bash
cd jone-plex-landing
npm install        # 처음 한 번만
npm run dev        # 개발 서버 → 터미널에 나오는 http://localhost:5173 접속
```

| 명령 | 하는 일 |
|---|---|
| `npm run dev` | 개발 서버. 파일을 저장하면 화면이 바로 바뀝니다 |
| `npm run build` | 타입 검사 → 배포용 빌드(`dist/`) → 프리렌더링 |
| `npm run preview` | 빌드 결과물을 http://localhost:4173 에서 확인 |
| `npm test` | 단위 테스트 (검증, 층 탭, 상담 폼, 서버 함수) |
| `npm run test:e2e` | 실제 브라우저로 전체 링크·버튼·폼·PC/모바일 화면 검사 (`npm run build` 먼저) |
| `npm run check` | 위 빌드 + 단위 테스트 + 브라우저 테스트를 한 번에 |

---

## 2. 무엇을 어디서 고치나요?

**코드를 몰라도 `src/config/` 폴더의 세 파일만 고치면 됩니다.**

| 파일 | 내용 |
|---|---|
| `src/config/site.ts` | 전화번호, 카카오톡 채널, 네이버 블로그, 주소, 지도 링크, 상담 폼 전송 주소, 개인정보 처리 운영자 정보, 검색 노출(SEO) 문구, 첫 화면 이미지 |
| `src/config/floors.ts` | 층별 도면 이미지, 공급/전용 면적, 분양가, 주요 특징 |
| `src/config/content.ts` | 핵심 정보 카드 4개, "확인해야 하는 이유" 카드 5개, 교통 안내 문구 |

### 프로젝트 구조

```
jone-plex-landing/
├─ api/consult.ts              # Vercel 서버 함수: 상담 신청 접수(웹훅/이메일 전달)
├─ public/                     # 그대로 배포되는 파일 (이미지, 파비콘, robots.txt, OG 이미지)
│  └─ images/floors/           # ← 층별 도면 이미지 넣는 곳
├─ scripts/
│  ├─ prerender.mjs            # 빌드 후 HTML 미리 그리기
│  ├─ e2e.mjs                  # 브라우저 통합 테스트
│  └─ make-og-image.mjs        # 공유 미리보기 이미지 생성
├─ src/
│  ├─ config/                  # ★ 운영자가 고치는 설정 파일
│  ├─ components/              # 화면 조각(섹션별 컴포넌트)
│  │  ├─ Header.tsx            #   상단 메뉴
│  │  ├─ HeroSection.tsx       #   첫 화면
│  │  ├─ CoreInfoCards.tsx     #   핵심 정보 카드 4개
│  │  ├─ KeyMeritsSection.tsx  #   확인해야 하는 이유
│  │  ├─ FloorGuideSection.tsx #   층별 공급 정보 탭
│  │  ├─ LocationSection.tsx   #   위치·교통
│  │  ├─ ConsultForm.tsx       #   상담 신청 폼
│  │  ├─ PrivacyModal.tsx      #   개인정보 동의 전문
│  │  ├─ FixedContactBar.tsx   #   하단 고정(모바일)/플로팅(PC) 상담 버튼
│  │  ├─ ContactButtons.tsx    #   전화·카카오톡 버튼(미설정 시 안내창)
│  │  ├─ SetupNotice.tsx       #   "설정 필요" 안내창
│  │  └─ Footer.tsx, Modal.tsx, Section.tsx, Icons.tsx, BuildingIllustration.tsx
│  ├─ lib/                     # 검증·링크·전송 로직
│  ├─ __tests__/               # 단위 테스트
│  └─ App.tsx                  # 섹션 순서 조립
├─ index.html                  # SEO 메타태그 틀 (값은 site.ts 에서 자동 주입)
├─ tailwind.config.js          # 브랜드 색상(네이비·골드)
└─ vercel.json                 # Vercel 배포 설정
```

섹션 순서를 바꾸거나 빼려면 `src/App.tsx` 의 `<main>` 안 순서만 바꾸면 됩니다.
브랜드 색상은 `tailwind.config.js` 의 `navy`, `gold` 값을 바꾸면 전체에 반영됩니다.

---

## 3. 연락처와 상담 링크 설정

`src/config/site.ts` 의 `contact` 부분:

```ts
contact: {
  phone: '010-8873-7258',                          // 전화 상담 (설정됨)
  kakaoChannelUrl: 'https://pf.kakao.com/_abcdE/chat', // 카카오톡 채널 1:1 채팅 주소
  naverBlogUrl: 'https://blog.naver.com/아이디',     // 푸터에 블로그 버튼 표시
  managerName: '분양 담당 ○○○',
  businessHours: '평일 09:00~18:00',
},
```

- **카카오톡 채널 주소 얻는 법**: [카카오톡 채널 관리자센터](https://center-pf.kakao.com) → 채널 선택 → 채널 URL 복사 → 끝에 `/chat` 붙이기
- 값을 비워 두면 가짜 링크를 만들지 않고, 버튼을 눌렀을 때 **"카카오톡 상담 준비 중"** 안내창과 전화번호를 보여줍니다. (방문자에게는 설정 파일 경로 같은 개발용 문구가 보이지 않습니다)
- 전화번호는 첫 화면, 헤더, 하단 고정 바, PC 플로팅 버튼, 상담 섹션, 푸터에 한 번에 반영됩니다.

### 주소와 지도

```ts
location: {
  address: '인천광역시 미추홀구 ○○로 ○○',  // 실제 현장 주소
  stationDistance: '약 ○○m',               // 현장 기준으로 직접 확인한 값만
  stationWalkTime: '도보 약 ○분',
  stationExit: '○번 출구',
  maps: {
    naver: 'https://naver.me/xxxx',        // 네이버 지도에서 주소 검색 → 공유 → 링크 복사
    kakao: 'https://kko.to/xxxx',          // 카카오맵에서 주소 검색 → 공유 → 링크 복사
    google: '',                            // 비워 두면 해당 버튼은 숨김
  },
},
```

`maps` 를 비워 두면 `address` 로 네이버·카카오·구글 지도의 **주소 검색 링크가 자동으로** 만들어집니다. 특정 장소 페이지로 보내고 싶을 때만 `maps` 에 공유 링크를 넣으세요.

---

## 4. 이미지 교체 방법

### 첫 화면 배경

1. 이미지를 `public/images/hero.webp` 로 저장 (가로 1920px 이하, 300KB 안팎 권장)
2. `src/config/site.ts`:
   ```ts
   images: { hero: { src: '/images/hero.webp', alt: '제이원플렉스 외관 투시도', isActualPhoto: false } }
   ```
3. **실제 현장 사진일 때만** `isActualPhoto: true`. 투시도·CG·참고 사진이면 `false` 로 두세요. 화면 아래에 "참고 이미지" 문구가 자동으로 붙습니다.

이미지가 없으면 코드로 그린 건물 일러스트가 나오고, "실제 건물 외관과 다르다"는 문구가 함께 표시됩니다.

### 층별 도면

1. 도면 파일을 `public/images/floors/` 에 넣기 (예: `b1.webp`, `1f.webp`)
2. `src/config/floors.ts` 에서 해당 층 `planImage: '/images/floors/b1.webp'`
3. 면적·분양가·특징도 같은 곳에 입력. `null` 이면 "상담 문의", `features: []` 이면 "공식 자료 확인 후 안내"

```ts
{
  id: '1f',
  label: '지상 1층',
  planImage: '/images/floors/1f.webp',
  planImageAlt: '제이원플렉스 지상 1층 평면도',
  supplyArea: '○○㎡ ~ ○○㎡',
  exclusiveArea: '○○㎡ ~ ○○㎡',
  price: null,                       // 공개하지 않으면 null → "상담 문의"
  features: ['드라이브인 적용', '층고 ○.○m'],   // 공식 자료로 확인된 내용만
},
```

### 용량 줄이기 (모바일 속도)

- [Squoosh](https://squoosh.app) 에서 WebP, 품질 75~80으로 변환하면 보통 원본의 1/5 이하가 됩니다.
- 도면은 `loading="lazy"` 가 적용되어 있어 화면에 보일 때만 내려받습니다.

### 공유 미리보기 이미지 (카카오톡·네이버 공유 시)

`public/og-image.png` (1200×630)를 원하는 이미지로 덮어쓰면 됩니다.
문구만 바꾸려면 `scripts/make-og-image.mjs` 를 수정하고 `node scripts/make-og-image.mjs` 를 실행하세요.

---

## 5. 상담 신청 폼 연결 방법

`src/config/site.ts` → `form.endpoint` 가 비어 있으면 **테스트 모드**입니다.

- 폼 위에 "테스트 모드 – 온라인 신청이 아직 전송되지 않습니다" 경고가 보입니다.
- 입력값 검증은 동작하지만 **어디에도 전송되지 않고, "접수되었습니다"라고 표시하지 않습니다.**
- 실제 운영 전에 아래 방법 중 하나로 반드시 연결하세요.

### 방법 1: Formspree (가장 쉬움, 서버 설정 없음)

1. [formspree.io](https://formspree.io) 가입 → New Form → 받을 이메일 입력
2. 발급된 주소(`https://formspree.io/f/abcdwxyz`)를 붙여넣기:
   ```ts
   form: { endpoint: 'https://formspree.io/f/abcdwxyz' },
   ```
3. 첫 신청은 Formspree 가 보낸 확인 메일에서 승인해야 이후부터 메일로 들어옵니다.

### 방법 2: 포함된 Vercel 서버 함수 (`/api/consult`)

1. `form: { endpoint: '/api/consult' }`
2. Vercel → 프로젝트 → **Settings → Environment Variables** 에 아래 중 하나 이상 설정 후 재배포
   - **웹훅으로 받기**: `CONSULT_WEBHOOK_URL` – Google Apps Script 웹앱(구글 시트 저장), Make, Zapier, Slack Incoming Webhook 등
   - **이메일로 받기 ([Resend](https://resend.com))**: `RESEND_API_KEY`, `CONSULT_TO_EMAIL`(받는 주소), `CONSULT_FROM_EMAIL`(Resend 에서 인증한 보내는 주소)
3. 아무것도 설정하지 않으면 서버가 `503` 을 돌려주고, 화면에는 "상담 접수 서버 설정이 완료되지 않았습니다" 오류가 나옵니다. 접수 완료로 잘못 보이지 않습니다.

서버 함수는 이름·휴대전화 형식·상담 목적·동의 여부를 다시 검사하고, 스팸 로봇용 숨은 칸(`_gotcha`)이 채워진 요청은 버립니다.

<details>
<summary>구글 시트에 쌓기 (Google Apps Script 예시)</summary>

구글 시트 → 확장 프로그램 → Apps Script 에 붙여넣고 **배포 → 웹 앱(액세스: 모든 사용자)** 으로 배포한 주소를 `CONSULT_WEBHOOK_URL` 에 넣으세요.

```js
function doPost(e) {
  const d = JSON.parse(e.postData.contents);
  SpreadsheetApp.getActiveSheet().appendRow([
    d.receivedAt, d.name, d.phone, d.floor, d.purpose, d.message, d.agreedAt, d.pageUrl,
  ]);
  return ContentService.createTextOutput('ok');
}
```
</details>

`site.ts` 를 고치지 않고 Vercel 환경변수 `VITE_CONSULT_ENDPOINT` 로 전송 주소를 지정할 수도 있습니다. (이 값이 우선, 변경 후 재배포 필요)

### 개인정보 처리 안내

`src/config/site.ts` → `privacy` 에 **실제 운영자 정보**를 입력하세요. 비어 있는 항목은 동의 전문 팝업에 빨간색 **[운영자 입력 필요]** 로 표시됩니다.

```ts
privacy: {
  operatorName: '○○분양대행(주)',
  representative: '○○○',
  businessNumber: '000-00-00000',
  officerName: '○○○',
  officerContact: '010-0000-0000 / privacy@example.com',
  retentionPeriod: '상담 완료 후 1년, 이후 지체 없이 파기',
  policyUrl: '',   // 별도 개인정보 처리방침 페이지가 있으면 주소 입력
},
```

---

## 6. Vercel 배포 방법

이 프로젝트는 저장소 안의 `jone-plex-landing/` 폴더에 있습니다. 배포할 때 **Root Directory** 를 반드시 이 폴더로 지정하세요.

### 웹 화면에서 배포 (추천)

1. [vercel.com](https://vercel.com) 로그인 → **Add New → Project**
2. GitHub 저장소 `ai-` 선택 → Import
3. **Root Directory** → `Edit` → `jone-plex-landing` 선택
4. Framework Preset 은 `Vite` 로 자동 인식됩니다. (Build: `npm run build`, Output: `dist` — `vercel.json` 에 설정되어 있음)
5. 필요하면 Environment Variables 입력 (5번 항목 참고) → **Deploy**
6. 배포 후 나오는 `https://프로젝트명.vercel.app` 주소에서 확인

새 Vercel 프로젝트로 만들기 때문에 기존에 운영 중인 사이트나 도메인에는 영향이 없습니다. 도메인 연결은 테스트를 마친 뒤 **Settings → Domains** 에서 직접 추가하세요.

### 명령어로 배포

```bash
npm i -g vercel
cd jone-plex-landing
vercel          # 미리보기 배포 (처음엔 로그인·프로젝트 생성 질문)
vercel --prod   # 운영 배포
```

### 배포 후 할 일

- [ ] `site.ts` → `seo.siteUrl` 에 실제 주소 입력 (canonical·og:url·OG 이미지 절대주소 자동 생성) 후 재배포
- [ ] [네이버 서치어드바이저](https://searchadvisor.naver.com) → 사이트 등록 → HTML 태그 소유확인 코드를 `seo.naverSiteVerification` 에 입력 후 재배포
- [ ] 휴대폰으로 접속해 전화·카카오톡·상담 신청 버튼 직접 눌러 보기
- [ ] 상담 폼으로 실제 테스트 신청 1건 보내고 메일/시트에 들어오는지 확인

---

## 7. 테스트

### 자동 테스트

```bash
npm run check   # 빌드 + 단위 테스트 26개 + 브라우저 테스트 51개 항목
```

**단위 테스트** (`src/__tests__/`)
- 휴대전화 자동 하이픈·형식 검사, 필수값 검증
- 첫 화면 제목·상담 버튼 3개, 전화 링크(`tel:01088737258`)
- 카카오톡 미설정 시 가짜 링크 대신 안내창, 지도 링크는 현장 주소 검색으로 연결
- 층 탭 6개 모두 클릭 시 내용 변경, 키보드(←/→) 이동, 층 상담 → 폼 관심 층 자동 선택
- 폼: 빈 값 오류, 테스트 모드에서 전송·접수완료 표시 안 함, 서버 성공일 때만 접수 완료, 서버 오류/네트워크 오류 처리
- 서버 함수: 잘못된 요청 400, 미설정 503, 웹훅/이메일 전달, HTML 이스케이프, 전달 실패 502, 스팸 차단

**브라우저 테스트** (`scripts/e2e.mjs`, 실제 Chromium)
- PC 1440px / 태블릿 820px / 모바일 390px
- 모든 `#` 내부 링크의 이동 대상 존재, 메뉴·카드·하단 바 클릭 시 실제 섹션 이동
- 모든 전화 링크 번호 일치, 외부 링크 새 창 + `noopener`, 빈 링크·`javascript:` 링크 없음
- 모바일 가로 넘침 없음, 하단 고정 바 위치, 주요 버튼 터치 높이 44px 이상
- 프리렌더 HTML 에 본문 포함, OG 이미지·파비콘·robots.txt 접근
- 콘솔 오류·하이드레이션 경고 없음
- 화면 캡처 저장: `test-results/pc-*.png`, `tablet-*.png`, `mobile-*.png`

GitHub 에 올리면 `.github/workflows/landing.yml` 이 같은 검사를 자동으로 실행하고 화면 캡처를 첨부합니다.

### 브라우저 테스트용 Chromium

`npm run test:e2e` 는 `playwright-core` 를 씁니다. 처음 한 번 `npx playwright-core install chromium` 으로 브라우저를 설치하거나, 이미 있는 Chrome 경로를 `CHROMIUM_PATH` 환경변수로 지정하세요.

---

## 8. 광고·표시 관련 주의

- 확인되지 않은 수익률, 임대수익, 시세차익, 투자 보장 표현은 쓰지 않았습니다. 문구를 추가할 때도 같은 기준을 지켜 주세요.
- "초역세권" 등 입지 표현은 실제 거리 확인 후 사용하고, 거리·시간은 현장 기준 값만 입력하세요.
- 분양 광고 관련 법규(표시·광고의 공정화에 관한 법률 등)와 분양 대행 계약상 광고 지침을 함께 확인하세요.
