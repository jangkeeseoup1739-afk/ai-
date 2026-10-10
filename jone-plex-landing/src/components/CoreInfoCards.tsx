/**
 * 핵심 정보 카드 4개 (역세권 입지 / 교통 접근성 / 건물 및 시설 / 분양 정보)
 * 문구는 src/config/content.ts 의 coreInfoCards 에서 수정합니다.
 * 카드 하단 버튼을 누르면 관련 섹션으로 이동합니다.
 */
import { coreInfoCards } from '../config/content';
import { SECTION } from '../lib/links';
import { Icon } from './Icons';

export function CoreInfoCards() {
  return (
    <section id={SECTION.info} aria-labelledby="info-title" className="relative z-10 scroll-mt-20 bg-navy-50 pb-16 pt-12 sm:pb-20 sm:pt-16">
      <div className="mx-auto max-w-content px-4 sm:px-6">
        <h2 id="info-title" className="mb-6 text-[26px] font-bold text-navy-900 sm:mb-8 sm:text-3xl">
          한눈에 보는 핵심 정보
        </h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-5">
          {coreInfoCards.map((card) => (
            <li key={card.title} className="flex flex-col rounded-3xl bg-white p-6 shadow-card transition-shadow hover:shadow-card-hover">
              <div className="mb-5 flex items-center justify-between">
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-navy-900 text-gold-300">
                  <Icon name={card.icon} className="h-6 w-6" />
                </span>
                <span className="text-sm font-bold text-gold-500" aria-hidden="true">
                  {card.label}
                </span>
              </div>
              <h3 className="text-xl font-bold text-navy-900">{card.title}</h3>
              <ul className="mt-3 flex-1 space-y-2">
                {card.items.map((item) => (
                  <li key={item} className="flex gap-2 text-[15px] leading-snug text-navy-700">
                    <Icon name="check" className="mt-0.5 h-4 w-4 shrink-0 text-gold-500" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <a
                href={`#${card.target}`}
                className="mt-6 inline-flex items-center justify-between rounded-xl border border-navy-100 px-4 py-3 text-[15px] font-semibold text-navy-800 hover:border-gold-400 hover:text-gold-700"
              >
                {card.cta}
                <Icon name="arrowRight" className="h-4 w-4" />
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
