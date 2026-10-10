/**
 * ═══════════════════════════════════════════════════════════════
 *  층별 공급 정보 설정 파일
 * ═══════════════════════════════════════════════════════════════
 *
 *  ★ 공식 분양 자료로 확인된 값만 입력하세요. ★
 *  - 값이 null 이면 화면에 "상담 문의" 로 표시됩니다.
 *  - features 가 빈 배열([])이면 "공식 자료 확인 후 안내" 로 표시됩니다.
 *  - 샘플 가격·가짜 도면은 넣지 마세요.
 *
 *  도면 이미지 넣는 법
 *   1) 도면 파일을 public/images/floors/ 폴더에 넣습니다. (예: b1.webp)
 *   2) 아래 해당 층의 planImage 를 '/images/floors/b1.webp' 로 바꿉니다.
 *   3) 가로 1600px 이하, WebP 또는 JPG 로 저장하면 모바일 로딩이 빨라집니다.
 *
 *  층을 추가·삭제하려면 floors 배열에 항목을 추가하거나 지우면 됩니다.
 *  (탭, 상담 폼의 "관심 층" 선택지가 자동으로 함께 바뀝니다.)
 */

export interface FloorInfo {
  /** 고유 ID (영문/숫자, 중복 금지) – 주소창 #floor-xx, 폼 값 등에 사용 */
  id: string;
  /** 탭에 표시되는 이름 */
  label: string;
  /** 도면 이미지 경로 (public 기준). 없으면 null */
  planImage: string | null;
  /** 도면 이미지 대체 텍스트 (시각장애인용 스크린리더가 읽어줌) */
  planImageAlt: string;
  /** 공급 면적 (예: '약 120.5㎡ (36.4평) ~ 245.3㎡ (74.2평)') */
  supplyArea: string | null;
  /** 전용 면적 */
  exclusiveArea: string | null;
  /** 분양가 (예: '평당 ○○○만원대') */
  price: string | null;
  /** 주요 특징 – 공식 자료로 확인된 내용만 (예: '드라이브인 적용', '층고 ○.○m') */
  features: string[];
}

export const floors: FloorInfo[] = [
  {
    id: 'b1',
    label: '지하 1층',
    planImage: '/images/floors/b1.webp',
    planImageAlt: '제이원플렉스 지하 1층 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: [],
  },
  {
    id: '1f',
    label: '지상 1층',
    planImage: '/images/floors/1f.webp',
    planImageAlt: '제이원플렉스 지상 1층 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: [],
  },
  {
    id: '2f',
    label: '지상 2층',
    planImage: '/images/floors/2f.webp',
    planImageAlt: '제이원플렉스 지상 2층 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: [],
  },
  {
    id: '3f',
    label: '지상 3층',
    planImage: '/images/floors/3f.webp',
    planImageAlt: '제이원플렉스 지상 3층 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: [],
  },
  {
    id: '4f',
    label: '지상 4층',
    planImage: '/images/floors/4f.webp',
    planImageAlt: '제이원플렉스 지상 4층 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: [],
  },
  {
    id: '5f',
    label: '지상 5층',
    planImage: '/images/floors/5f.webp',
    planImageAlt: '제이원플렉스 지상 5층 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: [],
  },
  {
    id: '6f',
    label: '지상 6층',
    planImage: '/images/floors/6f.webp',
    planImageAlt: '제이원플렉스 지상 6층 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: [],
  },
  {
    id: '7f',
    label: '지상 7층',
    planImage: '/images/floors/7f.webp',
    planImageAlt: '제이원플렉스 지상 7층 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: [],
  },
  {
    id: '8f',
    label: '지상 8층 (테라스)',
    planImage: '/images/floors/8f.webp',
    planImageAlt: '제이원플렉스 지상 8층 테라스 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: ['테라스형 호실 구성 (8층 도면 기준)'],
  },
  {
    id: '9-10f',
    label: '지상 9~10층',
    planImage: null,
    planImageAlt: '제이원플렉스 지상 9~10층 평면도',
    supplyArea: null,
    exclusiveArea: null,
    price: null,
    features: [],
  },
];

/** 값이 없을 때 표시할 문구 (한 곳에서 바꾸기 위해 상수로 분리) */
export const EMPTY_VALUE_TEXT = '상담 문의';
export const EMPTY_FEATURES_TEXT = '공식 자료 확인 후 안내';
