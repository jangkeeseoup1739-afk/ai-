/**
 * ═══════════════════════════════════════════════════════════════
 *  오피스텔형 기숙사 타입 안내 설정 파일
 * ═══════════════════════════════════════════════════════════════
 *
 *  공식 타입 평면도(아이소) 자료에 적힌 값만 입력했습니다.
 *  - 면적은 ㎡ 숫자로 입력하면 화면에 평(㎡ ÷ 3.3058) 환산값이 함께 표시됩니다.
 *  - 타입 이미지: public/images/types/ 에 넣고 image 경로를 지정하세요.
 *  - 새 타입 자료가 생기면 unitTypes 배열에 항목을 추가하면 됩니다.
 *  - floors.ts 의 unitTypeIds 에 타입 id 를 적으면 해당 층 안내에 "타입 보기" 버튼이 생깁니다.
 */

export interface UnitTypeVariant {
  /** 세부 타입 이름 (예: 'A type') */
  name: string;
  /** 세대(실) 수 */
  count: number;
}

export interface UnitType {
  /** 고유 ID – 화면 주소(#type-a 등)와 층별 연결에 사용 */
  id: string;
  /** 카드 제목 */
  title: string;
  /** 적용 층 (도면 기준) */
  floorsLabel: string;
  /** 평면도(아이소) 이미지 – 아직 없으면 null ("평면도 준비 중" 표시) */
  image: string | null;
  imageAlt: string;
  /** 세부 타입과 실 수 */
  variants: UnitTypeVariant[];
  /** 면적표 (단위: ㎡) – 세부 타입 모두 같은 면적일 때 한 번만 입력 */
  areas: { label: string; sqm: number }[];
  /** 짧은 참고 문구 (공식 자료로 확인된 내용만) */
  notes: string[];
}

export const unitTypes: UnitType[] = [
  {
    id: 'type-a',
    title: 'A · A1 타입',
    floorsLabel: '8~9층',
    image: '/images/types/a-a1.webp',
    imageAlt: '오피스텔형 기숙사 A·A1 타입 아이소 평면도',
    variants: [
      { name: 'A type', count: 12 },
      { name: 'A1 type', count: 54 },
    ],
    areas: [
      { label: '전용면적', sqm: 25.1391 },
      { label: '공유면적', sqm: 16.0778 },
      { label: '공급면적', sqm: 41.2169 },
      { label: '기타공유면적', sqm: 12.0607 },
      { label: '계약면적', sqm: 53.2776 },
    ],
    notes: ['A·A1 타입 면적 동일', '8층은 테라스가 있는 평면 (8층 도면 기준)'],
  },
  {
    id: 'type-b',
    title: 'B 타입',
    floorsLabel: '8~9층',
    image: '/images/types/b.webp',
    imageAlt: '오피스텔형 기숙사 B 타입 아이소 평면도',
    variants: [{ name: 'B type', count: 6 }],
    areas: [
      { label: '전용면적', sqm: 26.566 },
      { label: '공유면적', sqm: 16.8653 },
      { label: '공급면적', sqm: 43.4313 },
      { label: '기타공유면적', sqm: 12.7453 },
      { label: '계약면적', sqm: 56.1765 },
    ],
    notes: ['8층은 테라스가 있는 평면 (8층 도면 기준)'],
  },
  {
    id: 'type-c',
    title: 'C · C1 타입 (복층)',
    floorsLabel: '10층',
    image: '/images/types/c-c1.webp',
    imageAlt: '오피스텔형 기숙사 C·C1 복층 타입 아이소 평면도',
    variants: [
      { name: 'C type', count: 6 },
      { name: 'C1 type', count: 27 },
    ],
    areas: [
      { label: '전용면적', sqm: 25.1391 },
      { label: '공유면적', sqm: 16.0778 },
      { label: '공급면적', sqm: 41.2169 },
      { label: '기타공유면적', sqm: 12.0607 },
      { label: '계약면적', sqm: 53.2776 },
    ],
    notes: ['C·C1 타입 면적 동일', '복층 구조 (10층 도면 기준)'],
  },
  {
    id: 'type-d',
    title: 'D 타입 (복층)',
    floorsLabel: '10층',
    image: '/images/types/d.webp',
    imageAlt: '오피스텔형 기숙사 D 복층 타입 아이소 평면도',
    variants: [{ name: 'D type', count: 4 }],
    areas: [
      { label: '전용면적', sqm: 26.566 },
      { label: '공유면적', sqm: 16.8653 },
      { label: '공급면적', sqm: 43.4313 },
      { label: '기타공유면적', sqm: 12.7453 },
      { label: '계약면적', sqm: 56.1765 },
    ],
    notes: ['복층 구조 (10층 도면 기준)'],
  },
  {
    id: 'type-e',
    title: 'E 타입',
    floorsLabel: '9층',
    image: '/images/types/e.webp',
    imageAlt: '오피스텔형 기숙사 E 타입 아이소 평면도',
    variants: [{ name: 'E type', count: 2 }],
    areas: [
      { label: '전용면적', sqm: 26.5717 },
      { label: '공유면적', sqm: 16.8626 },
      { label: '공급면적', sqm: 43.4343 },
      { label: '기타공유면적', sqm: 12.748 },
      { label: '계약면적', sqm: 56.1823 },
    ],
    notes: [],
  },
];

/** 오피스텔형 기숙사 무상 제공 품목 (타입 평면도 자료 기준) */
export const unitAmenities = ['빌트인 냉장고', '빌트인 세탁기', '시스템 에어컨', '인덕션 (준공 후 설치)', '전자레인지'];

/** ㎡ → 평 환산 (소수 둘째 자리) */
export function toPyeong(sqm: number): string {
  return (sqm / 3.305785).toFixed(2);
}
