/**
 * ═══════════════════════════════════════════════════════════════
 *  화면 문구 설정 파일 (핵심 정보 카드 · 주요 장점 · 교통 안내)
 * ═══════════════════════════════════════════════════════════════
 *
 *  문구만 바꾸고 싶다면 이 파일의 글자만 수정하면 됩니다.
 *  ※ 확인되지 않은 수익률·임대수익·시세차익·투자 보장 표현은 쓰지 마세요.
 *  ※ 거리·시간·층별 시설은 공식 자료/현장 기준으로 확인한 뒤 입력하세요.
 *
 *  icon 에 쓸 수 있는 이름: src/components/Icons.tsx 의 paths 목록 참고
 *  (phone, chat, train, road, building, document, pin, truck, layers, user ...)
 */
import type { IconName } from '../components/Icons';
import { siteConfig } from './site';

const loc = siteConfig.location;

/** 역 → 현장 거리 안내 문구 (값이 없으면 "확인 후 안내") */
const walkText =
  loc.stationDistance || loc.stationWalkTime
    ? `역에서 현장까지 ${[loc.stationDistance, loc.stationWalkTime].filter(Boolean).join(' · ')}`
    : '역~현장 거리·도보 시간: 현장 기준 확인 후 안내';

export interface CoreInfoCard {
  icon: IconName;
  label: string;
  title: string;
  items: string[];
  /** 카드를 눌렀을 때 이동할 섹션 ID */
  target: string;
  cta: string;
}

/** 첫 화면 아래 4개 핵심 정보 카드 */
export const coreInfoCards: CoreInfoCard[] = [
  {
    icon: 'train',
    label: '01',
    title: '역세권 입지',
    items: ['인천2호선 주안국가산단역 인근', walkText],
    target: 'location',
    cta: '위치 확인',
  },
  {
    icon: 'road',
    label: '02',
    title: '교통 접근성',
    items: [
      '주안역(1호선 환승)까지 인천2호선 1정거장',
      '가좌IC·도화IC, 경인고속도로 인접',
      '서인천IC까지 차량 약 10분 (교통 상황에 따라 다름)',
    ],
    target: 'location',
    cta: '교통 안내 보기',
  },
  {
    icon: 'building',
    label: '03',
    title: '건물 및 시설',
    items: [
      '지하 1층 ~ 지상 10층 층별 구성',
      '드라이브인 · 도어투도어 구조 안내',
      '8~10층 오피스텔형 기숙사 (테라스·복층 타입)',
      '적용 층과 시설은 공식 자료 기준으로 안내',
    ],
    target: 'floors',
    cta: '층별 정보 보기',
  },
  {
    icon: 'document',
    label: '04',
    title: '분양 정보',
    items: ['층별 분양 정보', '공급 면적 · 전용 면적', '분양가 · 계약 조건: 상담 문의', '방문 상담 예약 가능'],
    target: 'consult',
    cta: '상담 예약하기',
  },
];

export interface Merit {
  icon: IconName;
  title: string;
  description: string;
}

/** "제이원플렉스를 확인해야 하는 이유" 카드 */
export const merits: Merit[] = [
  {
    icon: 'pin',
    title: '주안국가산업단지 내 입지',
    description: '인천 미추홀구 주안국가산업단지 안에 자리해 산업단지 내 기업·협력사와의 업무 동선을 고려할 수 있습니다.',
  },
  {
    icon: 'train',
    title: '주안국가산단역 접근성',
    description: '인천2호선 주안국가산단역 2번 출구에서 약 100m, 도보 약 2분 거리입니다. 주안역(1호선)에서도 1정거장입니다.',
  },
  {
    icon: 'truck',
    title: '업무·물류 동선을 고려한 구조',
    description: '드라이브인·도어투도어 등 차량 동선과 화물 이동을 고려한 구조를 안내합니다. 적용 층은 공식 자료로 확인해 드립니다.',
  },
  {
    icon: 'layers',
    title: '층별 공간 · 공급 정보 확인',
    description: '지하 1층부터 지상 10층까지 층별 공급 면적, 전용 면적, 도면을 업종과 규모에 맞게 비교해 볼 수 있습니다.',
  },
  {
    icon: 'user',
    title: '담당자 직접 상담',
    description: '분양가, 계약 조건, 잔여 호실 등 최신 정보는 담당자가 공식 자료를 바탕으로 직접 안내해 드립니다.',
  },
];

/** 위치·교통 섹션의 교통 안내 목록 */
export const transportInfo: { icon: IconName; title: string; body: string }[] = [
  {
    icon: 'train',
    title: '주안국가산단역 (인천2호선)',
    body:
      loc.stationDistance || loc.stationWalkTime || loc.stationExit
        ? [loc.stationExit, loc.stationDistance, loc.stationWalkTime].filter(Boolean).join(' · ')
        : '현장까지의 거리와 도보 시간은 현장 기준으로 확인 후 안내해 드립니다.',
  },
  {
    icon: 'train',
    title: '주안역 환승 (1호선 · 인천2호선)',
    body: '주안역에서 인천2호선으로 1정거장이면 주안국가산단역에 도착합니다.',
  },
  {
    icon: 'road',
    title: '가좌IC · 도화IC',
    body: '경인고속도로에 인접해 있으며, 서인천IC까지 차량으로 약 10분 거리입니다.',
  },
  {
    icon: 'road',
    title: '광역 도로망',
    body: '수도권제1·2순환고속도로, 제2경인고속도로(안양·시흥 등 남부권 방면)로 이어집니다.',
  },
];
