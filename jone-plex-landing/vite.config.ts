/// <reference types="vitest" />
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { siteConfig } from './src/config/site';

/**
 * index.html 안의 %SEO_xxx% 자리표시자를 src/config/site.ts 값으로 바꿔 넣습니다.
 * → 검색엔진(네이버·구글)과 카카오톡/페이스북 미리보기는 JS 실행 전 HTML을 읽기 때문에
 *   메타태그를 빌드 시점에 HTML에 직접 박아 둡니다.
 */
function seoHtmlPlugin(): Plugin {
  const { seo } = siteConfig;
  const siteUrl = seo.siteUrl.replace(/\/$/, '');
  // OG 이미지는 절대 주소가 권장됩니다. siteUrl이 비어 있으면 상대 경로를 그대로 씁니다.
  const ogImage = siteUrl && seo.ogImage.startsWith('/') ? siteUrl + seo.ogImage : seo.ogImage;

  const escape = (v: string) =>
    v.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  const values: Record<string, string> = {
    SEO_TITLE: seo.title,
    SEO_DESCRIPTION: seo.description,
    SEO_KEYWORDS: seo.keywords.join(', '),
    SEO_SITE_NAME: siteConfig.fullName,
    SEO_OG_IMAGE: ogImage,
  };

  return {
    name: 'seo-html',
    transformIndexHtml(html) {
      let out = html;
      for (const [key, value] of Object.entries(values)) {
        out = out.split(`%${key}%`).join(escape(value));
      }
      // 사이트 주소가 정해진 경우에만 canonical / og:url 을 넣습니다. (가짜 주소 금지)
      const urlTags = siteUrl
        ? `<link rel="canonical" href="${escape(siteUrl)}/" />\n    <meta property="og:url" content="${escape(siteUrl)}/" />`
        : '<!-- site.ts 의 seo.siteUrl 을 입력하면 canonical / og:url 태그가 자동으로 추가됩니다. -->';
      out = out.replace('<!--%SEO_URL_TAGS%-->', urlTags);
      // 네이버 서치어드바이저 사이트 소유확인 코드
      const naverTag = seo.naverSiteVerification
        ? `<meta name="naver-site-verification" content="${escape(seo.naverSiteVerification)}" />`
        : '<!-- 네이버 서치어드바이저 소유확인 코드는 site.ts 의 seo.naverSiteVerification 에 입력하세요. -->';
      out = out.replace('<!--%NAVER_VERIFICATION%-->', naverTag);
      return out;
    },
  };
}

/**
 * 빌드 결과(dist)에 sitemap.xml 을 만들고, robots.txt 끝에 그 위치를 적어 둡니다.
 * → 네이버 서치어드바이저·구글 서치콘솔에 사이트맵으로 제출할 수 있습니다.
 * site.ts 의 seo.siteUrl 이 비어 있으면 아무것도 만들지 않습니다. (가짜 주소 금지)
 */
function sitemapPlugin(): Plugin {
  const siteUrl = siteConfig.seo.siteUrl.replace(/\/$/, '');
  let outDir = 'dist';
  let isSsr = false;

  return {
    name: 'seo-sitemap',
    apply: 'build',
    configResolved(config) {
      outDir = config.build.outDir;
      // SSR 빌드(dist-ssr)는 중간 산출물이라 건너뜁니다.
      isSsr = Boolean(config.build.ssr);
    },
    async closeBundle() {
      if (isSsr || !siteUrl) return;
      const { readFile, writeFile } = await import('node:fs/promises');
      const { join } = await import('node:path');

      // 한 장짜리 페이지라 주소는 메인 하나입니다.
      const lastmod = new Date().toISOString().slice(0, 10);
      const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${siteUrl}/</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
`;
      await writeFile(join(outDir, 'sitemap.xml'), sitemap, 'utf8');

      const robotsPath = join(outDir, 'robots.txt');
      const robots = await readFile(robotsPath, 'utf8');
      if (!robots.includes('Sitemap:')) {
        await writeFile(robotsPath, `${robots.trimEnd()}\n\nSitemap: ${siteUrl}/sitemap.xml\n`, 'utf8');
      }
      console.log(`\u2713 sitemap.xml 생성: ${siteUrl}/sitemap.xml`);
    },
  };
}

export default defineConfig({
  plugins: [react(), seoHtmlPlugin(), sitemapPlugin()],
  build: {
    // 이미지가 4KB 이하면 인라인 처리 → 요청 수 감소
    assetsInlineLimit: 4096,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
  },
});
