/**
 * 첫 화면 안내 팝업 (분양·임대 / 특별 프로모션)
 * - 문구·이미지·사용 여부: src/config/site.ts → promoPopup
 * - "오늘 하루 보지 않기"를 누르면 그 기기에서 오늘 자정까지 다시 뜨지 않습니다.
 * - 미리 그려 둔 HTML(프리렌더)과 어긋나지 않도록, 페이지가 열린 뒤에만 표시합니다.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { siteConfig } from '../config/site';
import { SECTION, phoneDisplay, scrollToId } from '../lib/links';
import { PhoneButton } from './ContactButtons';
import { Icon } from './Icons';

/** "오늘 하루 보지 않기" 기록 이름 (브라우저 저장소) */
export const PROMO_HIDE_KEY = 'j1plex-promo-hide-until';

function isHiddenToday(): boolean {
  try {
    return Number(window.localStorage.getItem(PROMO_HIDE_KEY) || 0) > Date.now();
  } catch {
    return false; // 저장소를 쓸 수 없는 환경(사생활 보호 모드 등)에서는 그냥 표시
  }
}

function hideUntilMidnight() {
  try {
    const midnight = new Date();
    midnight.setHours(24, 0, 0, 0);
    window.localStorage.setItem(PROMO_HIDE_KEY, String(midnight.getTime()));
  } catch {
    /* 저장 실패해도 이번에는 닫힘 */
  }
}

export function PromoPopup() {
  const promo = siteConfig.promoPopup;
  const [open, setOpen] = useState(false);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (promo.enabled && !isHiddenToday()) setOpen(true);
  }, [promo.enabled]);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && close();
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, close]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[65] flex items-center justify-center bg-navy-950/70 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="promo-title"
        aria-describedby="promo-desc"
        className="relative w-full max-w-[400px] overflow-hidden rounded-3xl bg-navy-900 text-white shadow-card-hover"
      >
        <button
          ref={closeRef}
          type="button"
          onClick={close}
          aria-label="팝업 닫기"
          className="absolute right-3 top-3 z-10 rounded-full bg-navy-950/60 p-2 text-white hover:bg-navy-950/80"
        >
          <Icon name="close" className="h-5 w-5" />
        </button>

        {promo.image && (
          <div className="relative">
            <img src={promo.image} alt="" className="aspect-[16/9] w-full object-cover" decoding="async" />
            <div className="absolute inset-0 bg-gradient-to-t from-navy-900 via-navy-900/20 to-transparent" />
          </div>
        )}

        <div className={`px-6 pb-6 text-center ${promo.image ? '-mt-6 relative' : 'pt-10'}`}>
          <p className="inline-flex items-center gap-1.5 rounded-full bg-gold-500 px-4 py-1.5 text-sm font-extrabold text-navy-950">
            <span className="h-1.5 w-1.5 rounded-full bg-navy-950" aria-hidden="true" />
            {promo.badge}
          </p>
          <p className="mt-4 text-sm font-semibold tracking-wide text-gold-300">{siteConfig.fullName}</p>
          <h2 id="promo-title" className="mt-1 text-[34px] font-extrabold leading-tight tracking-tight">
            {promo.title}
          </h2>
          <p id="promo-desc" className="mt-3 text-[15px] leading-relaxed text-navy-200">
            {promo.description}
          </p>

          <div className="mt-6 grid gap-2.5">
            <button
              type="button"
              onClick={() => {
                close();
                scrollToId(SECTION.consult);
              }}
              className="flex items-center justify-center gap-2 rounded-2xl bg-gold-500 px-5 py-4 text-lg font-bold text-navy-950 hover:bg-gold-400"
            >
              <Icon name="edit" className="h-5 w-5" />
              프로모션 상담 신청
            </button>
            <PhoneButton className="flex items-center justify-center gap-2 rounded-2xl border border-white/20 px-5 py-3.5 text-base font-bold text-white hover:bg-white/10">
              <Icon name="phone" className="h-5 w-5 text-gold-300" />
              전화 문의 {phoneDisplay}
            </PhoneButton>
          </div>
        </div>

        <div className="grid grid-cols-2 border-t border-white/10 text-[15px] text-navy-200">
          <button
            type="button"
            onClick={() => {
              hideUntilMidnight();
              close();
            }}
            className="py-3.5 hover:bg-white/5 hover:text-white"
          >
            오늘 하루 보지 않기
          </button>
          <button type="button" onClick={close} className="border-l border-white/10 py-3.5 font-semibold hover:bg-white/5 hover:text-white">
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}
