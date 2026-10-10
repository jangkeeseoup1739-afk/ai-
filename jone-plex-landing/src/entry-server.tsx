/**
 * 빌드 시 페이지를 HTML 문자열로 미리 그리는 진입점 (scripts/prerender.mjs 에서 사용)
 * → 검색엔진이 JS 실행 없이도 본문을 읽을 수 있습니다.
 */
import { StrictMode } from 'react';
import { renderToString } from 'react-dom/server';
import App from './App';

export function render(): string {
  return renderToString(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
