/**
 * 섹션 공통 틀 – 제목(eyebrow + h2) + 설명 + 내용
 * 모든 섹션의 여백·제목 스타일을 한 곳에서 맞추기 위해 사용합니다.
 */
import type { ReactNode } from 'react';

interface SectionProps {
  id: string;
  /** 제목 위 작은 영문/분류 글씨 */
  eyebrow?: string;
  title: string;
  description?: ReactNode;
  /** 배경 톤: white(기본) | soft(연한 회청색) | navy(진한 남색) */
  tone?: 'white' | 'soft' | 'navy';
  children: ReactNode;
}

const toneClass = {
  white: 'bg-white',
  soft: 'bg-navy-50',
  navy: 'bg-navy-900 text-white',
};

export function Section({ id, eyebrow, title, description, tone = 'white', children }: SectionProps) {
  const isNavy = tone === 'navy';
  return (
    <section id={id} aria-labelledby={`${id}-title`} className={`scroll-mt-20 py-16 sm:py-20 lg:py-24 ${toneClass[tone]}`}>
      <div className="mx-auto max-w-content px-4 sm:px-6">
        <header className="mb-8 sm:mb-12">
          {eyebrow && (
            <p className={`mb-2 text-sm font-semibold tracking-[0.18em] ${isNavy ? 'text-gold-300' : 'text-gold-600'}`}>
              {eyebrow}
            </p>
          )}
          <h2 id={`${id}-title`} className={`text-[26px] font-bold leading-tight sm:text-4xl ${isNavy ? 'text-white' : 'text-navy-900'}`}>
            {title}
          </h2>
          {description && (
            <p className={`mt-3 max-w-2xl text-base leading-relaxed sm:text-lg ${isNavy ? 'text-navy-200' : 'text-navy-700'}`}>
              {description}
            </p>
          )}
        </header>
        {children}
      </div>
    </section>
  );
}
