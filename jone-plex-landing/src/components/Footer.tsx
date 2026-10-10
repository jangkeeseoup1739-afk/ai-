/**
 * 하단 정보(푸터) – 운영자 정보, 고지 문구, 블로그 링크
 * 운영자 정보는 src/config/site.ts 의 privacy 항목을 사용합니다. (비어 있는 항목은 표시하지 않음)
 */
import { siteConfig } from '../config/site';
import { blogHref, phoneDisplay } from '../lib/links';

export function Footer() {
  const p = siteConfig.privacy;
  const infoRows = [
    { label: '상호', value: p.operatorName },
    { label: '대표', value: p.representative },
    { label: '사업자등록번호', value: p.businessNumber },
    { label: '현장 주소', value: siteConfig.location.address },
    { label: '상담 전화', value: phoneDisplay },
    { label: '상담 시간', value: siteConfig.contact.businessHours },
    { label: '담당', value: siteConfig.contact.managerName },
  ].filter((r) => r.value.trim());

  return (
    // 모바일에서는 하단 고정 바(약 64px)에 내용이 가리지 않도록 아래 여백을 더 줍니다.
    <footer className="bg-navy-950 pb-28 pt-12 text-navy-300 md:pb-12">
      <div className="mx-auto max-w-content px-4 sm:px-6">
        <p className="text-lg font-bold text-white">{siteConfig.fullName}</p>
        {infoRows.length > 0 && (
          <ul className="mt-4 flex flex-wrap gap-x-5 gap-y-1.5 text-sm">
            {infoRows.map((r) => (
              <li key={r.label}>
                <span className="text-navy-400">{r.label}</span> {r.value}
              </li>
            ))}
          </ul>
        )}
        {blogHref && (
          <a href={blogHref} target="_blank" rel="noopener noreferrer" className="mt-4 inline-block rounded-lg bg-[#03C75A] px-4 py-2 text-sm font-bold text-white hover:brightness-95">
            네이버 블로그 (새 창)
          </a>
        )}
        <div className="mt-8 space-y-1.5 border-t border-white/10 pt-6 text-xs leading-relaxed text-navy-400">
          <p>※ 본 페이지의 이미지·일러스트는 이해를 돕기 위한 것으로 실제와 다를 수 있습니다.</p>
          <p>※ 면적·분양가·계약 조건 등 분양 정보는 공식 분양 자료 및 계약서를 기준으로 하며, 상담 시 최신 내용을 확인해 주시기 바랍니다.</p>
          <p>※ 교통 정보의 거리·소요 시간은 현장 위치와 교통 상황에 따라 달라질 수 있습니다.</p>
          <p className="pt-3">© {siteConfig.projectName}. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
