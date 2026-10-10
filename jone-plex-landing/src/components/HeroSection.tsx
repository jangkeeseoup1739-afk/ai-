/**
 * 첫 화면(메인 비주얼)
 * - 메인 제목, 보조 문구, 상담 버튼 3개, 핵심 요약 배지
 * - 배경 이미지는 site.ts → images.hero.src 로 교체
 *   (비어 있으면 네이비 그라데이션 + 건물 일러스트 표시, 실제 사진처럼 표시하지 않음)
 */
import { siteConfig } from '../config/site';
import { SECTION } from '../lib/links';
import { KakaoButton, PhoneButton } from './ContactButtons';
import { Icon } from './Icons';
import { BuildingIllustration } from './BuildingIllustration';

/** 첫 화면 하단 요약 배지 – 확인된 사실만 짧게 */
const HIGHLIGHTS = [
  { icon: 'train', text: '주안국가산단역 2번 출구 도보 약 2분' },
  { icon: 'building', text: '지하 1층 ~ 지상 10층 층별 공급' },
  { icon: 'pin', text: '인천 미추홀구 주안국가산업단지' },
] as const;

export function HeroSection() {
  const { hero } = siteConfig.images;
  const hasImage = hero.src.trim() !== '';

  return (
    <section id={SECTION.top} aria-labelledby="hero-title" className="relative isolate overflow-hidden bg-navy-950 text-white">
      {/* ── 배경 ── */}
      {hasImage ? (
        <>
          <img
            src={hero.src}
            alt={hero.alt}
            className="absolute inset-0 -z-20 h-full w-full object-cover object-[70%_center]"
            // 첫 화면 이미지는 가장 먼저 내려받도록 우선순위를 높임 (React 18 은 소문자 속성으로 전달)
            {...{ fetchpriority: 'high' }}
            decoding="async"
          />
          {/* 글씨가 잘 보이도록 어둡게 덮는 층 – 모바일은 전체, PC는 왼쪽(글씨 쪽)만 진하게 */}
          <div className="absolute inset-0 -z-10 bg-gradient-to-b from-navy-950/85 via-navy-950/75 to-navy-950/95 lg:bg-gradient-to-r lg:from-navy-950/95 lg:via-navy-950/70 lg:to-navy-950/10" />
        </>
      ) : (
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top_right,_#1D345E_0%,_#0F1F3D_45%,_#0A1529_100%)]">
          <BuildingIllustration className="absolute bottom-0 right-[-20%] h-[45%] w-auto opacity-20 sm:right-0 sm:h-[70%] sm:opacity-50 lg:h-[88%] lg:opacity-60" />
        </div>
      )}

      <div className="mx-auto max-w-content px-4 pb-14 pt-14 sm:px-6 sm:pb-20 sm:pt-24 lg:pb-24 lg:pt-28">
        <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-gold-400/50 bg-navy-900/60 px-4 py-1.5 text-sm font-semibold text-gold-200">
          <span className="h-1.5 w-1.5 rounded-full bg-gold-400" aria-hidden="true" />
          지식산업센터 분양 안내
        </p>

        <h1 id="hero-title" className="text-[34px] font-extrabold leading-[1.22] tracking-tight sm:text-5xl lg:text-6xl">
          <span className="block text-gold-300">주안국가산단역 초역세권</span>
          <span className="mt-1 block">제이원플렉스</span>
          <span className="block">지식산업센터</span>
        </h1>

        <p className="mt-5 max-w-xl text-[17px] leading-relaxed text-navy-100 sm:text-xl">
          인천 주안국가산업단지의 입지와 업무 환경을 확인하고, 분양 정보를 상담받아 보세요.
        </p>

        {/* ── 상담 버튼 3개 ── */}
        <div className="mt-8 grid gap-3 sm:flex sm:flex-wrap">
          <a
            href={`#${SECTION.consult}`}
            className="flex items-center justify-center gap-2 rounded-2xl bg-gold-500 px-7 py-4 text-lg font-bold text-navy-950 shadow-lg shadow-gold-500/20 hover:bg-gold-400"
          >
            <Icon name="edit" className="h-5 w-5" />
            분양 상담 신청
          </a>
          <div className="grid grid-cols-2 gap-3 sm:flex">
            <PhoneButton className="flex items-center justify-center gap-2 whitespace-nowrap rounded-2xl bg-white px-4 py-4 text-[17px] sm:px-6 sm:text-lg font-bold text-navy-900 hover:bg-navy-50">
              <Icon name="phone" className="h-5 w-5" />
              전화 상담
            </PhoneButton>
            <KakaoButton className="flex items-center justify-center gap-2 whitespace-nowrap rounded-2xl bg-[#FEE500] px-4 py-4 text-[17px] sm:px-6 sm:text-lg font-bold text-[#191919] hover:brightness-95">
              <Icon name="chat" className="h-5 w-5" />
              카카오톡 상담
            </KakaoButton>
          </div>
        </div>

        {/* ── 핵심 요약 배지 ── */}
        <ul className="mt-10 grid gap-2.5 sm:grid-cols-3 sm:gap-4">
          {HIGHLIGHTS.map((h) => (
            <li key={h.text} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3.5 backdrop-blur-sm">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-gold-500/15 text-gold-300">
                <Icon name={h.icon} className="h-5 w-5" />
              </span>
              <span className="text-[15px] font-semibold text-navy-50">{h.text}</span>
            </li>
          ))}
        </ul>

        {/* ── 모바일·태블릿: 배경에 가려지는 건물을 카드로 한 번 더 또렷하게 보여줌 ── */}
        {hasImage && (
          <figure className="mt-8 overflow-hidden rounded-2xl border border-white/10 lg:hidden">
            <img src={hero.src} alt="" loading="lazy" decoding="async" className="h-auto w-full" />
          </figure>
        )}

        {/* ── 이미지 고지 문구 (허위 표시 방지) ── */}
        <p className="mt-6 text-xs text-navy-300">
          {hasImage && hero.isActualPhoto
            ? '※ 배경 이미지는 현장 사진입니다.'
            : hasImage
              ? `※ ${hero.caption || '배경 이미지는 이해를 돕기 위한 참고 이미지'}로 실제와 다를 수 있습니다.`
              : '※ 배경 그림은 이해를 돕기 위한 일러스트이며 실제 건물 외관과 다릅니다.'}
        </p>
      </div>
    </section>
  );
}
