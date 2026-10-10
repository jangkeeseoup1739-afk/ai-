/**
 * 층별 공급 정보 (탭 UI)
 * - 층 탭을 누르면 아래 안내 영역(도면·면적·분양가·특징)이 바뀝니다.
 * - 데이터는 src/config/floors.ts 에서 수정합니다.
 * - 값이 없으면 "상담 문의", 도면이 없으면 "도면 준비 중" 으로 표시합니다. (가짜 자료 금지)
 * - [이 층 상담 문의] 버튼 → 상담 폼의 "관심 층"이 자동 선택되고 폼으로 이동합니다.
 */
import { useRef, useState, type KeyboardEvent } from 'react';
import { EMPTY_FEATURES_TEXT, EMPTY_VALUE_TEXT, floors, type FloorInfo } from '../config/floors';
import { SECTION } from '../lib/links';
import { Icon } from './Icons';
import { Section } from './Section';

interface FloorGuideSectionProps {
  /** 층 상담 버튼을 눌렀을 때 호출 (App 에서 상담 폼으로 전달) */
  onConsultFloor: (floorId: string) => void;
}

export function FloorGuideSection({ onConsultFloor }: FloorGuideSectionProps) {
  const [activeId, setActiveId] = useState(floors[0]?.id ?? '');
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const active = floors.find((f) => f.id === activeId) ?? floors[0];

  // 키보드 ←/→ 로 탭 이동 (접근성)
  const onTabKeyDown = (e: KeyboardEvent<HTMLButtonElement>, index: number) => {
    let next = -1;
    if (e.key === 'ArrowRight') next = (index + 1) % floors.length;
    if (e.key === 'ArrowLeft') next = (index - 1 + floors.length) % floors.length;
    if (e.key === 'Home') next = 0;
    if (e.key === 'End') next = floors.length - 1;
    if (next < 0) return;
    e.preventDefault();
    setActiveId(floors[next].id);
    tabRefs.current[next]?.focus();
  };

  if (!active) return null;

  return (
    <Section
      id={SECTION.floors}
      eyebrow="FLOOR GUIDE"
      title="층별 공급 정보 확인하기"
      description="층을 선택하면 해당 층의 도면과 공급 정보를 확인할 수 있습니다."
      tone="white"
    >
      {/* ── 층 선택 탭 ── */}
      <div
        role="tablist"
        aria-label="층 선택"
        className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-2 sm:mx-0 sm:grid sm:grid-cols-5 sm:overflow-visible sm:px-0"
      >
        {floors.map((floor, i) => {
          const selected = floor.id === active.id;
          return (
            <button
              key={floor.id}
              ref={(el) => {
                tabRefs.current[i] = el;
              }}
              id={`floor-tab-${floor.id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls="floor-panel"
              tabIndex={selected ? 0 : -1}
              onClick={(e) => {
                setActiveId(floor.id);
                // 모바일 가로 스크롤 탭에서 누른 탭이 화면 안에 보이도록
                e.currentTarget.scrollIntoView?.({ block: 'nearest', inline: 'nearest' });
              }}
              onKeyDown={(e) => onTabKeyDown(e, i)}
              className={`shrink-0 whitespace-nowrap rounded-2xl border px-4 py-3.5 text-base font-bold transition-colors ${
                selected
                  ? 'border-navy-900 bg-navy-900 text-white shadow-card'
                  : 'border-navy-100 bg-white text-navy-700 hover:border-gold-400 hover:text-navy-900'
              }`}
            >
              {floor.label}
            </button>
          );
        })}
      </div>

      {/* ── 선택된 층 안내 ── */}
      <div
        id="floor-panel"
        role="tabpanel"
        aria-labelledby={`floor-tab-${active.id}`}
        className="mt-6 grid gap-6 rounded-3xl bg-navy-50 p-4 sm:p-6 lg:grid-cols-[1.15fr_1fr] lg:gap-8 lg:p-8"
      >
        <FloorPlan floor={active} />
        <FloorDetail floor={active} onConsult={() => onConsultFloor(active.id)} />
      </div>
    </Section>
  );
}

/** 층별 도면 이미지 (없으면 "도면 준비 중" 안내) */
function FloorPlan({ floor }: { floor: FloorInfo }) {
  if (floor.planImage) {
    return (
      <figure className="overflow-hidden rounded-2xl bg-white shadow-card">
        {/* 휴대폰에서 도면 글씨가 작으므로, 누르면 원본 크기로 새 창에서 열림 (두 손가락으로 확대 가능) */}
        <a href={floor.planImage} target="_blank" rel="noopener noreferrer" aria-label={`${floor.planImageAlt} 크게 보기 (새 창)`}>
          <img
            key={floor.planImage}
            src={floor.planImage}
            alt={floor.planImageAlt}
            loading="lazy"
            decoding="async"
            // 이미지가 늦게 로드되어도 화면이 밀리지 않도록 도면 비율(약 16:9)만큼 자리를 미리 잡아 둠
            width={1240}
            height={710}
            className="aspect-[1240/710] h-auto w-full bg-white object-contain"
          />
        </a>
        <figcaption className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 text-xs text-navy-600">
          <span>※ 도면은 이해를 돕기 위한 것으로 실제 시공 시 일부 변경될 수 있습니다. 분양 현황은 상담 시 최신 기준으로 안내합니다.</span>
          <a
            href={floor.planImage}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 rounded-lg border border-navy-200 px-3 py-2 text-sm font-semibold text-navy-800 hover:border-gold-400"
          >
            도면 크게 보기
            <Icon name="external" className="h-4 w-4" />
          </a>
        </figcaption>
      </figure>
    );
  }
  return (
    <div className="flex min-h-[240px] flex-col items-center justify-center rounded-2xl border-2 border-dashed border-navy-200 bg-white p-8 text-center sm:min-h-[320px]">
      <Icon name="image" className="h-12 w-12 text-navy-300" />
      <p className="mt-4 text-lg font-bold text-navy-800">{floor.label} 도면 준비 중</p>
      <p className="mt-1 text-[15px] text-navy-600">공식 도면 자료는 상담 시 안내해 드립니다.</p>
    </div>
  );
}

/** 층별 면적·분양가·특징 + 상담 버튼 */
function FloorDetail({ floor, onConsult }: { floor: FloorInfo; onConsult: () => void }) {
  const rows = [
    { label: '공급 면적', value: floor.supplyArea },
    { label: '전용 면적', value: floor.exclusiveArea },
    { label: '분양가', value: floor.price },
  ];

  return (
    <div className="flex flex-col">
      <h3 className="text-2xl font-bold text-navy-900" aria-live="polite">
        {floor.label}
      </h3>

      <dl className="mt-4 divide-y divide-navy-100 overflow-hidden rounded-2xl bg-white shadow-card">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between gap-4 px-5 py-4">
            <dt className="text-[15px] font-medium text-navy-600">{r.label}</dt>
            <dd className={`text-right text-base font-bold ${r.value ? 'text-navy-900' : 'text-gold-700'}`}>
              {r.value ?? EMPTY_VALUE_TEXT}
            </dd>
          </div>
        ))}
      </dl>

      <div className="mt-4 rounded-2xl bg-white p-5 shadow-card">
        <p className="text-[15px] font-medium text-navy-600">주요 특징</p>
        {floor.features.length > 0 ? (
          <ul className="mt-2 space-y-1.5">
            {floor.features.map((f) => (
              <li key={f} className="flex gap-2 text-base text-navy-900">
                <Icon name="check" className="mt-1 h-4 w-4 shrink-0 text-gold-500" />
                {f}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-1 text-base font-semibold text-gold-700">{EMPTY_FEATURES_TEXT}</p>
        )}
      </div>

      <button
        type="button"
        onClick={onConsult}
        className="mt-5 inline-flex items-center justify-center gap-2 rounded-2xl bg-navy-900 px-6 py-4 text-lg font-bold text-white hover:bg-navy-800"
      >
        <Icon name="edit" className="h-5 w-5" />
        {floor.label} 상담 문의
      </button>
    </div>
  );
}
