# 이미지 폴더

- `hero.webp` 처럼 첫 화면 배경 이미지를 이 폴더에 넣고 `src/config/site.ts` → `images.hero.src` 에 `'/images/hero.webp'` 를 입력하세요.
- 층별 도면은 `floors/` 폴더에 넣고 `src/config/floors.ts` 의 `planImage` 에 경로를 입력하세요.
- 권장: WebP 형식, 가로 1600~1920px 이하, 300KB 이하.
- 실제 현장 사진이 아니라면 `isActualPhoto: false` 로 두어 "참고 이미지" 문구가 표시되게 하세요.
