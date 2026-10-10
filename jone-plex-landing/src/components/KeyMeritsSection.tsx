/**
 * "제이원플렉스를 확인해야 하는 이유" – 주요 장점 카드 5개
 * 문구는 src/config/content.ts 의 merits 에서 수정합니다.
 */
import { merits } from '../config/content';
import { SECTION } from '../lib/links';
import { Icon } from './Icons';
import { Section } from './Section';

export function KeyMeritsSection() {
  return (
    <Section
      id={SECTION.merits}
      eyebrow="WHY J1 PLEX"
      title="제이원플렉스를 확인해야 하는 이유"
      description="입지, 동선, 공간 구성까지 — 상담 전에 먼저 확인해 보세요."
      tone="navy"
    >
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 lg:gap-5">
        {merits.map((m, i) => (
          <li key={m.title} className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 sm:p-7">
            <div className="mb-4 flex items-center gap-3">
              <span className="grid h-12 w-12 place-items-center rounded-2xl bg-gold-500 text-navy-950">
                <Icon name={m.icon} className="h-6 w-6" />
              </span>
              <span className="text-sm font-semibold text-gold-300" aria-hidden="true">
                POINT {String(i + 1).padStart(2, '0')}
              </span>
            </div>
            <h3 className="text-xl font-bold text-white">{m.title}</h3>
            <p className="mt-2 text-[15px] leading-relaxed text-navy-200">{m.description}</p>
          </li>
        ))}
        {/* 마지막 칸: 상담 유도 카드 */}
        <li className="flex flex-col justify-between rounded-3xl bg-gradient-to-br from-gold-400 to-gold-600 p-6 text-navy-950 sm:p-7">
          <div>
            <p className="text-sm font-bold">분양가 · 잔여 호실 · 계약 조건</p>
            <p className="mt-2 text-xl font-extrabold leading-snug">최신 공식 자료로 담당자가 직접 안내해 드립니다.</p>
          </div>
          <a
            href={`#${SECTION.consult}`}
            className="mt-6 inline-flex items-center justify-center gap-2 rounded-xl bg-navy-950 px-5 py-3.5 text-base font-bold text-white hover:bg-navy-900"
          >
            상담 신청하기
            <Icon name="arrowRight" className="h-4 w-4" />
          </a>
        </li>
      </ul>
    </Section>
  );
}
