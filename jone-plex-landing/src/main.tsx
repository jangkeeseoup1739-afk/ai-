/**
 * 브라우저 진입점
 * 빌드된 HTML에는 페이지가 미리 그려져(프리렌더링) 있으므로 hydrateRoot 로 이어 붙이고,
 * 개발 서버(npm run dev)처럼 비어 있으면 createRoot 로 새로 그립니다.
 */
import { StrictMode } from 'react';
import { createRoot, hydrateRoot } from 'react-dom/client';
import App from './App';
import './index.css';

const container = document.getElementById('root')!;
const app = (
  <StrictMode>
    <App />
  </StrictMode>
);

if (container.firstElementChild) {
  hydrateRoot(container, app);
} else {
  createRoot(container).render(app);
}
