/**
 * ═══════════════════════════════════════════════════════════════
 *  제이원플렉스 상담 신청 → 구글 시트 저장 스크립트 (Google Apps Script)
 * ═══════════════════════════════════════════════════════════════
 *
 *  설치 방법 (한 번만)
 *   1) "제이원플렉스 관심고객" 구글 시트를 엽니다.
 *   2) 메뉴 [확장 프로그램] → [Apps Script] 를 누릅니다.
 *   3) 편집기에 있던 내용을 모두 지우고, 이 파일 내용을 통째로 붙여넣은 뒤 저장(💾)합니다.
 *   4) 오른쪽 위 [배포] → [새 배포] → 톱니바퀴(유형 선택)에서 [웹 앱] 선택
 *        - 설명: 상담 신청 접수
 *        - 다음 사용자 인증 정보로 실행: 나
 *        - 액세스 권한이 있는 사용자: 모든 사용자
 *      → [배포] → 권한 승인(내 구글 계정 선택 → 고급 → 이동 → 허용)
 *   5) 나오는 "웹 앱 URL"(https://script.google.com/macros/s/..../exec)을 복사해
 *      랜딩페이지 src/config/site.ts 의 form.endpoint 에 붙여넣습니다.
 *
 *  저장 위치: 아래 SHEET_ID 의 시트(탭). 시트 주소의 #gid= 뒤 숫자입니다.
 *  첫 줄이 비어 있으면 제목 줄을 자동으로 만들고, 이미 제목이 있으면 같은 이름의 열에 맞춰 넣습니다.
 *  (없는 제목은 오른쪽 끝에 새 열로 추가)
 *
 *  스크립트를 고친 뒤에는 [배포] → [배포 관리] → 연필 → 버전 "새 버전" → [배포] 해야 반영됩니다.
 */

/** 저장할 시트 탭 번호 (시트 주소 #gid=1946917195) – 다른 탭에 쌓으려면 숫자만 바꾸세요. */
const SHEET_ID = 1946917195;

/** 시트 제목 줄 이름 ← 랜딩페이지가 보내는 값 */
const COLUMNS = [
  ['접수일시', (d) => Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm:ss')],
  ['이름', (d) => d.name],
  ['연락처', (d) => d.phone],
  ['관심 층', (d) => d.floor],
  ['상담 목적', (d) => d.purpose],
  ['문의 내용', (d) => d.message],
  ['개인정보 동의', (d) => (d.agreedAt ? '동의 (' + d.agreedAt + ')' : '')],
  ['접수 페이지', (d) => d.pageUrl],
];

function doPost(e) {
  try {
    const d = JSON.parse((e && e.postData && e.postData.contents) || '{}');

    // 스팸 로봇이 숨은 칸을 채운 경우: 저장하지 않고 성공처럼 응답
    if (d._gotcha) return reply({ ok: true });

    // 최소 검증 (화면 검증을 우회한 요청 차단)
    const digits = String(d.phone || '').replace(/\D/g, '');
    if (String(d.name || '').trim().length < 2 || !/^01[016789]\d{7,8}$/.test(digits) || !d.agreedAt) {
      return reply({ ok: false, error: 'validation' });
    }

    const lock = LockService.getScriptLock();
    lock.waitLock(10000); // 동시에 여러 건이 들어와도 줄이 겹치지 않게
    try {
      const sheet = getSheet();
      const headers = ensureHeaders(sheet);
      const row = headers.map((h) => {
        const col = COLUMNS.find((c) => c[0] === h);
        // 수식으로 해석되지 않도록 = + - @ 로 시작하는 값 앞에 ' 를 붙임
        const v = col ? String(col[1](d) ?? '').slice(0, 1000) : '';
        return /^[=+\-@]/.test(v) && h !== '연락처' ? "'" + v : v;
      });
      sheet.appendRow(row);
    } finally {
      lock.releaseLock();
    }
    return reply({ ok: true });
  } catch (err) {
    console.error(err);
    return reply({ ok: false, error: 'server' });
  }
}

/** 브라우저에서 주소를 열었을 때 동작 확인용 */
function doGet() {
  return reply({ ok: true, message: '제이원플렉스 상담 신청 접수 스크립트가 동작 중입니다.' });
}

function getSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  return ss.getSheets().find((s) => s.getSheetId() === SHEET_ID) || ss.getSheets()[0];
}

/** 첫 줄 제목을 확인하고, 없는 제목은 추가한 뒤 최종 제목 목록을 돌려줌 */
function ensureHeaders(sheet) {
  const lastCol = sheet.getLastColumn();
  let headers = lastCol > 0 ? sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(String) : [];
  if (headers.every((h) => !h.trim())) headers = [];
  const missing = COLUMNS.map((c) => c[0]).filter((name) => !headers.includes(name));
  if (missing.length) {
    sheet.getRange(1, headers.length + 1, 1, missing.length).setValues([missing]).setFontWeight('bold');
    headers = headers.concat(missing);
    sheet.setFrozenRows(1);
  }
  return headers;
}

function reply(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

/** (선택) 편집기에서 ▶실행 으로 테스트 줄 1개 넣어보기 – 확인 후 시트에서 지우세요 */
function 테스트_한줄_넣기() {
  doPost({
    postData: {
      contents: JSON.stringify({
        name: '테스트',
        phone: '010-0000-0000',
        floor: '지상 3층',
        purpose: '실사용',
        message: '스크립트 동작 확인',
        agreedAt: new Date().toISOString(),
        pageUrl: 'test',
      }),
    },
  });
}
