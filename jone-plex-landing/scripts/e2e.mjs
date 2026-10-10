/**
 * 브라우저 통합 테스트 (실제 Chromium 으로 빌드 결과물을 열어 확인)
 *
 *   npm run build && npm run test:e2e
 *
 * 확인 항목
 *  1. PC(1440px)·태블릿(820px)·모바일(390px) 화면 로드, 콘솔 오류/하이드레이션 경고 없음
 *  2. 페이지 안 모든 #링크의 이동 대상이 실제로 존재
 *  3. 전화 링크(tel:)가 설정된 번호로 연결, 외부 링크는 새 창 + noopener
 *  4. 모바일에서 가로 스크롤(화면 넘침) 없음, 하단 고정 바 표시 / PC 플로팅 버튼 표시
 *  5. 층 탭 클릭 시 내용 변경, 층 상담 문의 → 폼 관심 층 자동 선택
 *  6. 미설정 카카오톡·지도 버튼 → 설정 안내창
 *  7. 상담 폼 검증 / 테스트 모드에서 "접수 완료"로 표시되지 않음
 *  8. 화면 캡처 저장: test-results/*.png
 */
import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { chromium } from 'playwright-core';

const PORT = 4179;
const BASE = `http://localhost:${PORT}/`;
// 브라우저 경로: CHROMIUM_PATH 환경변수 → 이 개발환경의 기본 경로 → Playwright 가 설치한 기본 브라우저 순
const DEFAULT_CHROMIUM = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const executablePath = process.env.CHROMIUM_PATH || (existsSync(DEFAULT_CHROMIUM) ? DEFAULT_CHROMIUM : undefined);
const EXPECTED_TEL = 'tel:01088737258';

let failures = 0;
const check = (ok, label) => {
  console.log(`${ok ? '  ✓' : '  ✗'} ${label}`);
  if (!ok) failures++;
};

// 1) 빌드 결과물 미리보기 서버 실행
const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js', 'preview', '--port', String(PORT), '--strictPort'], { stdio: 'pipe' });
await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error('preview 서버 시작 시간 초과')), 20000);
  server.stdout.on('data', (d) => {
    if (String(d).includes(String(PORT))) {
      clearTimeout(timer);
      resolve();
    }
  });
  server.on('exit', (code) => reject(new Error(`preview 서버 종료 (code ${code}) – 먼저 npm run build 를 실행하세요`)));
});

await mkdir('test-results', { recursive: true });
const browser = await chromium.launch({ executablePath });

async function openPage(name, viewport, isMobile = false) {
  const context = await browser.newContext({ viewport, isMobile, hasTouch: isMobile, locale: 'ko-KR', deviceScaleFactor: isMobile ? 2 : 1 });
  const page = await context.newPage();
  const errors = [];
  page.on('console', (m) => {
    if (m.type() === 'error' || /hydrat/i.test(m.text())) errors.push(m.text());
  });
  page.on('pageerror', (e) => errors.push(String(e)));
  // 외부 웹폰트(CDN)는 테스트 환경(사내망·CI)에 따라 막힐 수 있으므로 빈 응답으로 대체 →
  // 우리 코드의 오류만 검사합니다. (폰트가 없으면 시스템 한글 글꼴로 표시됨)
  await page.route((url) => url.hostname !== 'localhost', (route) =>
    route.fulfill({ status: 200, contentType: 'text/css', body: '' }),
  );
  await page.goto(BASE, { waitUntil: 'networkidle' });
  console.log(`\n[${name}] ${viewport.width}×${viewport.height}`);
  return { page, context, errors };
}

try {
  // ───────── PC ─────────
  {
    const { page, context, errors } = await openPage('PC', { width: 1440, height: 900 });

    // SEO 메타
    check((await page.title()).includes('제이원플렉스'), '문서 제목(title)');
    check((await page.locator('meta[property="og:image"]').getAttribute('content')) === '/og-image.png', 'og:image 메타태그');
    check((await page.locator('meta[name="description"]').getAttribute('content'))?.length > 40, 'description 메타태그');
    check((await page.locator('h1').count()) === 1, 'h1 은 1개');
    const ogRes = await page.request.get(BASE + 'og-image.png');
    check(ogRes.ok(), 'OG 이미지 파일 접근 가능');
    check((await page.request.get(BASE + 'favicon.svg')).ok(), '파비콘 접근 가능');
    check((await page.request.get(BASE + 'robots.txt')).ok(), 'robots.txt 접근 가능');
    const heroLoaded = await page.locator('#top img').first().evaluate((img) => img.complete && img.naturalWidth > 0);
    check(heroLoaded, '첫 화면 조감도 이미지 로드');

    // 프리렌더 확인: JS 없이 받은 HTML 에 본문이 들어있는지
    const rawHtml = await (await page.request.get(BASE)).text();
    check(rawHtml.includes('층별 공급 정보 확인하기') && !rawHtml.includes('<!--app-html-->'), '프리렌더 HTML 에 본문 포함');

    // 모든 내부 # 링크 대상 존재
    const hashTargets = await page.$$eval('a[href^="#"]', (as) => [...new Set(as.map((a) => a.getAttribute('href')))]);
    for (const href of hashTargets) {
      const exists = await page.locator(href).count();
      check(exists === 1, `내부 링크 ${href} 대상 존재`);
    }

    // 전화 링크
    const tels = await page.$$eval('a[href^="tel:"]', (as) => as.map((a) => a.getAttribute('href')));
    check(tels.length > 0 && tels.every((t) => t === EXPECTED_TEL), `전화 링크 ${tels.length}개 모두 ${EXPECTED_TEL}`);

    // 외부 링크는 새 창 + noopener, 빈 href / javascript: 링크 없음
    const badLinks = await page.$$eval('a', (as) =>
      as
        .filter((a) => {
          const h = a.getAttribute('href') ?? '';
          if (!h || h === '#' || h.startsWith('javascript:')) return true;
          if (/^https?:/.test(h)) return a.target !== '_blank' || !(a.rel || '').includes('noopener');
          return false;
        })
        .map((a) => a.outerHTML.slice(0, 80)),
    );
    check(badLinks.length === 0, `잘못된/빈 링크 없음 ${badLinks.join(' ')}`);

    // 모든 버튼에 접근 가능한 이름이 있는지
    const unnamed = await page.$$eval('button', (bs) => bs.filter((b) => !(b.getAttribute('aria-label') || b.textContent?.trim())).length);
    check(unnamed === 0, '모든 버튼에 이름(텍스트/aria-label) 있음');

    // 메뉴 링크 클릭 → 해당 섹션으로 스크롤
    await page.getByRole('navigation', { name: '주요 메뉴' }).getByRole('link', { name: '층별 정보' }).click();
    await page.waitForTimeout(900);
    const floorsTop = await page.locator('#floors').evaluate((el) => el.getBoundingClientRect().top);
    check(Math.abs(floorsTop) < 120, '메뉴 "층별 정보" 클릭 → 섹션 이동');

    // 핵심 정보 카드 버튼 → 이동
    await page.locator('#info').getByRole('link', { name: '위치 확인' }).click();
    await page.waitForTimeout(900);
    const locTop = await page.locator('#location').evaluate((el) => el.getBoundingClientRect().top);
    check(Math.abs(locTop) < 120, '카드 "위치 확인" 클릭 → 위치 섹션 이동');

    // 층 탭 전환
    const tabs = page.getByRole('tab');
    const tabCount = await tabs.count();
    for (let i = 0; i < tabCount; i++) {
      const tab = tabs.nth(i);
      const label = (await tab.textContent()).trim();
      await tab.click();
      const heading = (await page.locator('#floor-panel h3').textContent()).trim();
      check(heading === label && (await tab.getAttribute('aria-selected')) === 'true', `층 탭 "${label}" → 안내 영역 변경`);
      const plan = page.locator('#floor-panel figure img');
      if (await plan.count()) {
        await plan.scrollIntoViewIfNeeded();
        const loaded = await plan.evaluate((img) => img.decode().then(() => img.naturalWidth > 0).catch(() => false));
        check(loaded, `층 탭 "${label}" 도면 이미지 로드`);
      }
    }

    // 층 상담 문의 → 폼 관심 층
    await tabs.filter({ hasText: '지상 2층' }).click();
    await page.getByRole('button', { name: '지상 2층 상담 문의' }).click();
    await page.waitForTimeout(900);
    check((await page.getByLabel('관심 층').inputValue()) === '2f', '층 상담 문의 → 관심 층 자동 선택');

    // 미설정 카카오톡 → 안내창
    await page.locator('nav[aria-label="빠른 상담"]').last().getByRole('button', { name: '카카오톡 상담' }).click();
    check(await page.getByRole('dialog').isVisible(), 'PC 플로팅 카카오톡(미설정) → 설정 안내창');
    await page.keyboard.press('Escape');
    check((await page.getByRole('dialog').count()) === 0, 'ESC 로 안내창 닫힘');

    // 지도 링크: 주소 검색 링크 3개, 새 창
    const mapHrefs = await page.locator('#location a[href^="https://map"], #location a[href^="https://www.google.com/maps"]').evaluateAll((as) => as.map((a) => a.getAttribute('href')));
    check(mapHrefs.length === 3 && mapHrefs.every((h) => h.includes(encodeURIComponent('주염로73번길 54'))), '지도 보기 링크 3개 (현장 주소 검색)');

    // 상담 폼 검증
    const form = page.getByRole('form', { name: '분양 상담 신청서' });
    await form.getByRole('button', { name: '상담 신청하기' }).click();
    check((await form.getByRole('alert').count()) >= 4, '빈 폼 제출 → 필수 항목 오류 표시');

    await form.getByLabel(/이름/).fill('테스트');
    await form.getByLabel(/연락처/).pressSequentially('01012345678');
    check((await form.getByLabel(/연락처/).inputValue()) === '010-1234-5678', '연락처 자동 하이픈');
    await form.getByText('실사용', { exact: true }).click();
    await form.getByRole('button', { name: '전문 보기' }).click();
    check((await page.getByRole('dialog').textContent()).includes('개인정보 수집 및 이용 안내'), '개인정보 전문 보기 팝업');
    await page.getByRole('dialog').getByRole('button', { name: '확인' }).click();
    await form.getByLabel(/개인정보 수집 및 이용에 동의/).check();
    await form.getByRole('button', { name: '상담 신청하기' }).click();
    await page.waitForTimeout(300);
    const formText = await page.locator('#consult').textContent();
    check(formText.includes('신청서는 전송되지 않았습니다') && !formText.includes('상담 신청이 접수되었습니다'), '테스트 모드: 접수 완료로 표시하지 않음');

    check(await page.locator('nav[aria-label="빠른 상담"]').last().isVisible(), 'PC 플로팅 상담 버튼 표시');

    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/pc-first-view.png' });
    await page.screenshot({ path: 'test-results/pc-full.png', fullPage: true });
    check(errors.length === 0, `콘솔 오류 없음 ${errors.join(' | ')}`);
    await context.close();
  }

  // ───────── 태블릿 ─────────
  {
    const { page, context, errors } = await openPage('태블릿', { width: 820, height: 1180 }, true);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    check(overflow <= 0, `가로 넘침 없음 (${overflow}px)`);
    await page.screenshot({ path: 'test-results/tablet-first-view.png' });
    check(errors.length === 0, `콘솔 오류 없음 ${errors.join(' | ')}`);
    await context.close();
  }

  // ───────── 모바일 ─────────
  {
    const { page, context, errors } = await openPage('모바일', { width: 390, height: 844 }, true);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    check(overflow <= 0, `가로 넘침 없음 (${overflow}px)`);

    const bar = page.locator('nav[aria-label="빠른 상담"]').first();
    check(await bar.isVisible(), '하단 고정 상담 바 표시');
    check((await bar.locator('a[href="tel:01088737258"]').count()) === 1, '하단 바 전화 상담 → tel 링크');
    const barBox = await bar.boundingBox();
    check(barBox && Math.abs(barBox.y + barBox.height - 844) < 2, '하단 바가 화면 맨 아래 고정');
    check(!(await page.locator('nav[aria-label="빠른 상담"]').last().isVisible()), 'PC 플로팅 버튼은 모바일에서 숨김');

    // 첫 화면 안에 제목·상담 버튼이 보이는지
    const ctaBox = await page.locator('#top').getByRole('link', { name: /분양 상담 신청/ }).boundingBox();
    check(ctaBox && ctaBox.y + ctaBox.height < 844, '첫 화면에서 상담 신청 버튼이 보임');

    // 터치 영역 크기 (44px 이상 권장)
    const small = await page.$$eval('nav[aria-label="빠른 상담"] a, nav[aria-label="빠른 상담"] button, #top a, #top button', (els) =>
      els.filter((e) => e.offsetParent && e.getBoundingClientRect().height < 44).length,
    );
    check(small === 0, '주요 버튼 터치 높이 44px 이상');

    // 햄버거 메뉴
    await page.getByRole('button', { name: '메뉴 열기' }).click();
    await page.locator('#mobile-menu').getByRole('link', { name: '분양 상담 신청' }).click();
    await page.waitForTimeout(900);
    check((await page.locator('#mobile-menu').count()) === 0, '모바일 메뉴 링크 클릭 후 메뉴 닫힘');
    const consultTop = await page.locator('#consult').evaluate((el) => el.getBoundingClientRect().top);
    check(Math.abs(consultTop) < 120, '모바일 메뉴 → 상담 섹션 이동');

    // 하단 바 카카오톡 → 안내
    await bar.getByRole('button', { name: '카카오톡 상담' }).click();
    check(await page.getByRole('dialog').isVisible(), '하단 바 카카오톡(미설정) → 설정 안내창');
    await page.getByRole('dialog').getByRole('button', { name: '닫기' }).click();

    // 하단 바 상담 신청 → 폼으로 이동
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await page.waitForTimeout(300);
    await bar.getByRole('link', { name: '상담 신청' }).click();
    await page.waitForTimeout(900);
    const consultTop2 = await page.locator('#consult').evaluate((el) => el.getBoundingClientRect().top);
    check(Math.abs(consultTop2) < 120, '하단 바 상담 신청 → 상담 섹션 이동');

    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/mobile-first-view.png' });
    await page.screenshot({ path: 'test-results/mobile-full.png', fullPage: true });
    check(errors.length === 0, `콘솔 오류 없음 ${errors.join(' | ')}`);
    await context.close();
  }
} finally {
  await browser.close();
  server.kill();
}

console.log(failures === 0 ? '\n모든 E2E 검사 통과 ✓' : `\n실패 ${failures}건 ✗`);
process.exit(failures === 0 ? 0 : 1);
