/**
 * 공유 미리보기 이미지(public/og-image.png, 1200×630) 생성 스크립트
 * 문구를 바꾸고 싶다면 아래 HTML 을 수정한 뒤 `node scripts/make-og-image.mjs` 실행
 * (직접 만든 이미지가 있다면 public/og-image.png 파일을 덮어쓰기만 하면 됩니다)
 */
import { existsSync } from 'node:fs';
import { chromium } from 'playwright-core';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const out = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../public/og-image.png');
// 브라우저 경로: CHROMIUM_PATH 환경변수 → 이 개발환경의 기본 경로 → Playwright 가 설치한 기본 브라우저 순
const DEFAULT_CHROMIUM = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const executablePath = process.env.CHROMIUM_PATH || (existsSync(DEFAULT_CHROMIUM) ? DEFAULT_CHROMIUM : undefined);

const html = `<!doctype html><html><head><meta charset="utf-8">
<style>
  body{margin:0;width:1200px;height:630px;font-family:'Noto Sans CJK KR','Noto Sans KR','Apple SD Gothic Neo',sans-serif;
    background:radial-gradient(ellipse at top right,#1D345E 0%,#0F1F3D 45%,#0A1529 100%);color:#fff;display:flex;flex-direction:column;justify-content:center;padding:0 90px;box-sizing:border-box}
  .tag{display:inline-block;border:2px solid #D4B06A;color:#EEDDB6;border-radius:999px;padding:8px 22px;font-size:26px;font-weight:700;width:fit-content}
  h1{margin:28px 0 0;font-size:78px;line-height:1.18;font-weight:900;letter-spacing:-2px}
  h1 span{color:#E2C78C}
  p{margin:26px 0 0;font-size:30px;color:#C3CFE3}
  .bar{position:absolute;left:0;bottom:0;height:14px;width:100%;background:#C29A4E}
</style></head><body>
  <div class="tag">지식산업센터 분양 안내</div>
  <h1><span>주안국가산단역</span><br>제이원플렉스 지식산업센터</h1>
  <p>층별 공급 정보 · 입지 · 교통 환경 확인 및 분양 상담</p>
  <div class="bar"></div>
</body></html>`;

const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
await page.setContent(html);
await page.screenshot({ path: out, type: 'png' });
await browser.close();
console.log('✓ OG 이미지 생성:', out);
