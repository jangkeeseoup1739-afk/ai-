/**
 * 하단 고정 상담 버튼
 *  - 모바일(768px 미만): 화면 맨 아래 3칸 버튼 바 (전화 / 카카오톡 / 상담 신청)
 *  - PC·태블릿: 오른쪽 아래 떠 있는 상담 버튼 묶음
 */
import { SECTION } from '../lib/links';
import { KakaoButton, PhoneButton } from './ContactButtons';
import { Icon } from './Icons';

export function FixedContactBar() {
  return (
    <>
      {/* 모바일 하단 바 */}
      <nav
        aria-label="빠른 상담"
        className="fixed inset-x-0 bottom-0 z-50 grid grid-cols-3 border-t border-white/10 bg-navy-950 pb-[env(safe-area-inset-bottom)] text-white md:hidden"
      >
        <PhoneButton className="flex flex-col items-center justify-center gap-1 py-2.5 text-[13px] font-semibold active:bg-white/10">
          <Icon name="phone" className="h-6 w-6 text-gold-300" />
          전화 상담
        </PhoneButton>
        <KakaoButton className="flex flex-col items-center justify-center gap-1 border-x border-white/10 py-2.5 text-[13px] font-semibold active:bg-white/10">
          <Icon name="chat" className="h-6 w-6 text-[#FEE500]" />
          카카오톡 상담
        </KakaoButton>
        <a href={`#${SECTION.consult}`} className="flex flex-col items-center justify-center gap-1 bg-gold-500 py-2.5 text-[13px] font-bold text-navy-950 active:bg-gold-400">
          <Icon name="edit" className="h-6 w-6" />
          상담 신청
        </a>
      </nav>

      {/* PC 오른쪽 아래 플로팅 버튼 – 본문 옆 여백에 들어가도록 작은 세로 타일 형태 */}
      <nav
        aria-label="빠른 상담"
        className="fixed bottom-6 right-4 z-50 hidden w-[84px] flex-col overflow-hidden rounded-2xl shadow-card-hover md:flex xl:right-6"
      >
        <a
          href={`#${SECTION.consult}`}
          className="flex flex-col items-center gap-1 bg-gold-500 px-2 py-3.5 text-[13px] font-bold text-navy-950 hover:bg-gold-400"
        >
          <Icon name="edit" className="h-6 w-6" />
          상담 신청
        </a>
        <PhoneButton className="flex flex-col items-center gap-1 bg-navy-900 px-2 py-3.5 text-[13px] font-bold text-white hover:bg-navy-800">
          <Icon name="phone" className="h-6 w-6 text-gold-300" />
          전화 상담
        </PhoneButton>
        <KakaoButton className="flex flex-col items-center gap-1 bg-[#FEE500] px-2 py-3.5 text-[13px] font-bold leading-tight text-[#191919] hover:brightness-95">
          <Icon name="chat" className="h-6 w-6" />
          카카오톡
          <br />
          상담
        </KakaoButton>
      </nav>
    </>
  );
}
