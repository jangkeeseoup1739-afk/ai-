/**
 * 상단 고정 헤더 – 로고 + 메뉴 + 전화/상담 버튼
 * 모바일에서는 햄버거 버튼으로 메뉴를 펼칩니다.
 */
import { useState } from 'react';
import { siteConfig } from '../config/site';
import { SECTION, phoneDisplay } from '../lib/links';
import { PhoneButton } from './ContactButtons';
import { Icon } from './Icons';

/** 메뉴 항목 – 순서를 바꾸거나 추가하려면 여기만 수정하세요. */
const NAV_ITEMS = [
  { href: `#${SECTION.info}`, label: '핵심 정보' },
  { href: `#${SECTION.merits}`, label: '주요 장점' },
  { href: `#${SECTION.floors}`, label: '층별 정보' },
  { href: `#${SECTION.units}`, label: '타입 안내' },
  { href: `#${SECTION.location}`, label: '위치·교통' },
];

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const close = () => setMenuOpen(false);

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-navy-950/95 text-white backdrop-blur supports-[backdrop-filter]:bg-navy-950/85">
      <div className="mx-auto flex h-16 max-w-content items-center justify-between gap-4 px-4 sm:px-6">
        <a href={`#${SECTION.top}`} className="flex items-center gap-2.5" onClick={close} aria-label={`${siteConfig.projectName} 맨 위로`}>
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-gold-500 text-[15px] font-black text-navy-950" aria-hidden="true">
            J1
          </span>
          <span className="leading-tight">
            <span className="block text-[11px] font-medium tracking-wide text-gold-300">주안국가산단역</span>
            <span className="block text-base font-bold">{siteConfig.projectName}</span>
          </span>
        </a>

        {/* PC 메뉴 */}
        <nav aria-label="주요 메뉴" className="hidden lg:block">
          <ul className="flex items-center gap-8 text-[15px] font-medium text-navy-100">
            {NAV_ITEMS.map((item) => (
              <li key={item.href}>
                <a href={item.href} className="transition-colors hover:text-gold-300">
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center gap-2">
          <PhoneButton className="hidden items-center gap-2 rounded-full border border-gold-400/60 px-4 py-2 text-sm font-semibold text-gold-200 hover:bg-gold-500/10 md:inline-flex">
            <Icon name="phone" className="h-4 w-4" />
            {phoneDisplay || '전화 상담'}
          </PhoneButton>
          <a
            href={`#${SECTION.consult}`}
            className="hidden rounded-full bg-gold-500 px-4 py-2 text-sm font-bold text-navy-950 hover:bg-gold-400 sm:inline-flex"
          >
            상담 신청
          </a>
          <button
            type="button"
            className="rounded-lg p-2 text-white hover:bg-white/10 lg:hidden"
            aria-label={menuOpen ? '메뉴 닫기' : '메뉴 열기'}
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
            onClick={() => setMenuOpen((v) => !v)}
          >
            <Icon name={menuOpen ? 'close' : 'menu'} className="h-6 w-6" />
          </button>
        </div>
      </div>

      {/* 모바일 펼침 메뉴 */}
      {menuOpen && (
        <nav id="mobile-menu" aria-label="모바일 메뉴" className="border-t border-white/10 bg-navy-950 lg:hidden">
          <ul className="mx-auto max-w-content px-4 py-2">
            {[...NAV_ITEMS, { href: `#${SECTION.consult}`, label: '분양 상담 신청' }].map((item) => (
              <li key={item.href}>
                <a href={item.href} onClick={close} className="block border-b border-white/5 py-3.5 text-base font-medium text-navy-100 last:border-0 hover:text-gold-300">
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  );
}
