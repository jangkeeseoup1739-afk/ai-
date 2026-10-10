/**
 * 빌드 후처리: React 화면을 HTML 로 미리 그려 dist/index.html 에 넣습니다.
 * (네이버·구글 검색 로봇과 카카오톡 미리보기가 본문을 바로 읽을 수 있게 함)
 */
import { readFile, rm, writeFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const indexPath = path.join(root, 'dist', 'index.html');
const ssrDir = path.join(root, 'dist-ssr');

const { render } = await import(pathToFileURL(path.join(ssrDir, 'entry-server.js')).href);
const template = await readFile(indexPath, 'utf8');
if (!template.includes('<!--app-html-->')) {
  throw new Error('dist/index.html 에서 <!--app-html--> 자리표시자를 찾지 못했습니다.');
}
const html = template.replace('<!--app-html-->', render());
await writeFile(indexPath, html);
await rm(ssrDir, { recursive: true, force: true });
console.log('✓ prerender 완료: dist/index.html');
