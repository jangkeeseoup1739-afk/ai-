/**
 * 오피스텔형 기숙사 타입 안내 (8~10층)
 * - 타입별 평면도 이미지, 실 수, 면적표(㎡·평), 무상 제공 품목
 * - 데이터는 src/config/unitTypes.ts 에서 수정합니다.
 */
import { toPyeong, unitAmenities, unitTypes, type UnitType } from '../config/unitTypes';
import { SECTION } from '../lib/links';
import { Icon } from './Icons';
import { Section } from './Section';

export function UnitTypesSection() {
  if (unitTypes.length === 0) return null;

  return (
    <Section
      id={SECTION.units}
      eyebrow="UNIT TYPE"
      title="오피스텔형 기숙사 타입 안내"
      description={`8~10층 기숙사 ${unitTypes.reduce((n, t) => n + t.variants.reduce((m, v) => m + v.count, 0), 0)}실의 타입별 평면과 면적입니다. 잔여 호실과 분양 조건은 상담 시 안내해 드립니다.`}
      tone="soft"
    >
      {/* 타입 카드 + 마지막 칸에 무상 제공 품목 (PC 2열, 넓은 화면 3열) */}
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {unitTypes.map((t) => (
          <UnitTypeCard key={t.id} type={t} />
        ))}

        <aside className="flex flex-col rounded-3xl bg-navy-900 p-6 text-white sm:p-7">
          <p className="text-sm font-semibold text-gold-300">오피스텔형 기숙사 전 타입</p>
          <h3 className="mt-1 text-2xl font-bold">무상 제공 품목</h3>
          <ul className="mb-6 mt-5 grid gap-2.5">
            {unitAmenities.map((a) => (
              <li key={a} className="flex items-center gap-2.5 rounded-xl bg-white/5 px-4 py-3 text-base font-medium text-navy-50">
                <Icon name="check" className="h-5 w-5 shrink-0 text-gold-400" />
                {a}
              </li>
            ))}
          </ul>
          <a
            href={`#${SECTION.consult}`}
            className="mt-auto inline-flex items-center justify-center gap-2 rounded-xl bg-gold-500 px-5 py-3.5 text-base font-bold text-navy-950 hover:bg-gold-400"
          >
            기숙사 호실 상담 신청
            <Icon name="arrowRight" className="h-4 w-4" />
          </a>
        </aside>
      </div>
    </Section>
  );
}

function UnitTypeCard({ type }: { type: UnitType }) {
  const totalCount = type.variants.reduce((sum, v) => sum + v.count, 0);

  return (
    <article id={type.id} className="scroll-mt-20 overflow-hidden rounded-3xl bg-white shadow-card">
      {type.image ? (
        <a href={type.image} target="_blank" rel="noopener noreferrer" aria-label={`${type.imageAlt} 크게 보기 (새 창)`} className="block border-b border-navy-100">
          <img
            src={type.image}
            alt={type.imageAlt}
            loading="lazy"
            decoding="async"
            width={1010}
            height={640}
            className="aspect-[1010/640] h-auto w-full bg-white object-contain"
          />
        </a>
      ) : (
        <div className="flex aspect-[1010/640] flex-col items-center justify-center gap-2 border-b border-navy-100 bg-navy-50/60 text-center">
          <Icon name="image" className="h-10 w-10 text-navy-300" />
          <p className="text-base font-bold text-navy-700">{type.title} 평면도 준비 중</p>
        </div>
      )}

      <div className="p-5 sm:p-7">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-2xl font-bold text-navy-900">{type.title}</h3>
          <span className="rounded-full bg-gold-100 px-3 py-1 text-sm font-semibold text-gold-700">{type.floorsLabel}</span>
        </div>
        <p className="mt-2 text-[15px] text-navy-700">
          {type.variants.map((v) => `${v.name} ${v.count}실`).join(' · ')} <span className="text-navy-500">(총 {totalCount}실)</span>
        </p>

        <table className="mt-4 w-full overflow-hidden rounded-2xl text-[15px]">
          <caption className="sr-only">{type.title} 면적표</caption>
          <thead>
            <tr className="bg-navy-50 text-left text-navy-600">
              <th scope="col" className="px-4 py-2.5 font-medium">
                구분
              </th>
              <th scope="col" className="px-4 py-2.5 text-right font-medium">
                ㎡
              </th>
              <th scope="col" className="px-4 py-2.5 text-right font-medium">
                평
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-100 tabular-nums">
            {type.areas.map((a) => {
              const strong = a.label === '전용면적' || a.label === '계약면적';
              return (
                <tr key={a.label} className={strong ? 'font-bold text-navy-900' : 'text-navy-800'}>
                  <th scope="row" className="px-4 py-2.5 text-left font-[inherit]">
                    {a.label}
                  </th>
                  <td className="px-4 py-2.5 text-right">{a.sqm.toFixed(4)}</td>
                  <td className="px-4 py-2.5 text-right">{toPyeong(a.sqm)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {type.notes.length > 0 && (
          <ul className="mt-4 space-y-1.5">
            {type.notes.map((n) => (
              <li key={n} className="flex gap-2 text-[15px] text-navy-700">
                <Icon name="check" className="mt-0.5 h-4 w-4 shrink-0 text-gold-500" />
                {n}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-4 text-xs text-navy-500">※ 평 = ㎡ ÷ 3.3058 환산값. 평면도는 이해를 돕기 위한 이미지로 실제와 다를 수 있습니다.</p>
      </div>
    </article>
  );
}
