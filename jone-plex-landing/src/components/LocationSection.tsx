/**
 * 현장 위치와 교통 환경
 * - 주소(복사 버튼), 교통 안내, 지도 보기 버튼
 * - 주소·지도 링크는 src/config/site.ts 의 location 에서 설정합니다.
 * - 지도 링크가 하나도 없으면 "지도 링크 준비 중" 안내창이 뜹니다. (가짜 지도 금지)
 */
import { useState } from 'react';
import { transportInfo } from '../config/content';
import { siteConfig } from '../config/site';
import { SECTION, mapLinks } from '../lib/links';
import { Icon } from './Icons';
import { Section } from './Section';
import { useSetupNotice } from './SetupNotice';

export function LocationSection() {
  const { address, areaLabel, mapImages } = siteConfig.location;
  const showNotice = useSetupNotice();
  const [copyState, setCopyState] = useState<'idle' | 'done' | 'fail'>('idle');

  const copyAddress = async () => {
    try {
      await navigator.clipboard.writeText(address);
      setCopyState('done');
    } catch {
      setCopyState('fail');
    }
    window.setTimeout(() => setCopyState('idle'), 2500);
  };

  return (
    <Section
      id={SECTION.location}
      eyebrow="LOCATION"
      title="현장 위치와 교통 환경"
      description="정확한 위치와 이동 경로는 방문 상담 예약 시 함께 안내해 드립니다."
      tone="soft"
    >
      <div className="grid gap-5 lg:grid-cols-[1fr_1.2fr]">
        {/* ── 주소 카드 ── */}
        <div className="flex flex-col rounded-3xl bg-navy-900 p-6 text-white shadow-card sm:p-8">
          <span className="grid h-12 w-12 place-items-center rounded-2xl bg-gold-500 text-navy-950">
            <Icon name="pin" className="h-6 w-6" />
          </span>
          <p className="mt-5 text-sm font-semibold text-gold-300">현장 주소</p>
          {address ? (
            <>
              <p className="mt-1 text-xl font-bold leading-snug">{address}</p>
              <button
                type="button"
                onClick={copyAddress}
                className="mt-3 inline-flex w-fit items-center gap-1.5 rounded-lg border border-white/20 px-3 py-2 text-sm font-medium hover:bg-white/10"
              >
                <Icon name="copy" className="h-4 w-4" />
                {copyState === 'done' ? '복사되었습니다' : copyState === 'fail' ? '복사 실패 – 직접 선택해 주세요' : '주소 복사'}
              </button>
            </>
          ) : (
            <>
              <p className="mt-1 text-xl font-bold leading-snug">{areaLabel}</p>
              <p className="mt-2 text-[15px] text-navy-200">상세 주소는 확인 후 안내해 드립니다.</p>
            </>
          )}

          <div className="mt-auto pt-8">
            <p className="mb-3 text-sm font-semibold text-gold-300">지도 보기</p>
            {mapLinks.length > 0 ? (
              <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                {mapLinks.map((m) => (
                  <a
                    key={m.key}
                    href={m.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`${m.label}에서 현장 위치 보기 (새 창)`}
                    className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-white px-4 py-3 text-[15px] font-bold text-navy-900 hover:bg-gold-100"
                  >
                    {m.label}
                    <Icon name="external" className="h-4 w-4" />
                  </a>
                ))}
              </div>
            ) : (
              <button
                type="button"
                onClick={() => showNotice('map')}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3.5 text-base font-bold text-navy-900 hover:bg-gold-100"
              >
                <Icon name="pin" className="h-5 w-5" />
                지도 보기
              </button>
            )}
          </div>
        </div>

        {/* ── 교통 안내 ── */}
        <ul className="grid gap-4">
          {transportInfo.map((t) => (
            <li key={t.title} className="flex gap-4 rounded-3xl bg-white p-5 shadow-card sm:p-6">
              <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-navy-50 text-navy-800">
                <Icon name={t.icon} className="h-6 w-6" />
              </span>
              <div>
                <h3 className="text-lg font-bold text-navy-900">{t.title}</h3>
                <p className="mt-1 text-[15px] leading-relaxed text-navy-700">{t.body}</p>
              </div>
            </li>
          ))}
          <li className="flex items-start gap-2 px-1 text-sm text-navy-600">
            <Icon name="info" className="mt-0.5 h-4 w-4 shrink-0" />
            교통 정보는 공개된 노선 기준이며, 실제 거리·소요 시간은 현장 위치와 교통 상황에 따라 달라질 수 있습니다.
          </li>
        </ul>
      </div>

      {/* ── 지도 이미지 (site.ts → location.mapImages) – 누르면 크게 보기 ── */}
      {mapImages.length > 0 && (
        <div className="mt-6 grid gap-5 md:grid-cols-2">
          {mapImages.map((m) => (
            <figure key={m.src} className="overflow-hidden rounded-3xl bg-white shadow-card">
              <a href={m.src} target="_blank" rel="noopener noreferrer" aria-label={`${m.alt} 크게 보기 (새 창)`} className="block">
                <img src={m.src} alt={m.alt} loading="lazy" decoding="async" width={600} height={660} className="aspect-[600/660] h-auto w-full bg-white object-contain" />
              </a>
              <figcaption className="border-t border-navy-100 px-5 py-3.5 text-[15px] font-semibold text-navy-800">{m.caption}</figcaption>
            </figure>
          ))}
        </div>
      )}
    </Section>
  );
}
