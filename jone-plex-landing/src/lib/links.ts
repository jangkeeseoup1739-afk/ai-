/**
 * 설정 파일(site.ts)의 연락처를 실제 링크로 바꿔 주는 함수 모음.
 * 값이 비어 있으면 null 을 돌려주고, 화면에서는 "설정 필요" 안내를 띄웁니다.
 */
import { siteConfig } from '../config/site';
import { toTelHref } from './validation';

/** http(s) 로 시작하는 정상 주소인지 확인 (잘못 입력된 값으로 가짜 링크가 생기지 않게) */
export function isHttpUrl(value: string | undefined | null): value is string {
  if (!value) return false;
  try {
    const u = new URL(value);
    return u.protocol === 'https:' || u.protocol === 'http:';
  } catch {
    return false;
  }
}

export const phoneHref = toTelHref(siteConfig.contact.phone);
export const phoneDisplay = siteConfig.contact.phone.trim();
export const kakaoHref = isHttpUrl(siteConfig.contact.kakaoChannelUrl) ? siteConfig.contact.kakaoChannelUrl : null;
export const blogHref = isHttpUrl(siteConfig.contact.naverBlogUrl) ? siteConfig.contact.naverBlogUrl : null;

/**
 * 지도 링크 – site.ts 에 직접 넣은 링크가 있으면 그것을, 없으면 현장 주소로 검색하는 링크를 씁니다.
 * 주소도 없으면 버튼을 만들지 않습니다.
 */
const addressQuery = encodeURIComponent(siteConfig.location.address.trim());
const mapUrl = (custom: string, searchBase: string) =>
  isHttpUrl(custom) ? custom : addressQuery ? searchBase + addressQuery : '';

export const mapLinks = [
  { key: 'naver', label: '네이버 지도', href: mapUrl(siteConfig.location.maps.naver, 'https://map.naver.com/p/search/') },
  { key: 'kakao', label: '카카오맵', href: mapUrl(siteConfig.location.maps.kakao, 'https://map.kakao.com/link/search/') },
  { key: 'google', label: '구글 지도', href: mapUrl(siteConfig.location.maps.google, 'https://www.google.com/maps/search/?api=1&query=') },
].filter((m) => isHttpUrl(m.href));

/** 상담 폼 전송 주소 (Vercel 환경변수 VITE_CONSULT_ENDPOINT 가 있으면 우선) */
export function getFormEndpoint(): string {
  const fromEnv = (import.meta.env?.VITE_CONSULT_ENDPOINT as string | undefined) ?? '';
  return (fromEnv || siteConfig.form.endpoint).trim();
}

/** 페이지 안의 특정 섹션으로 부드럽게 스크롤 */
export function scrollToId(id: string) {
  const el = document.getElementById(id);
  if (!el) return;
  const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
}

/** 섹션 ID – 메뉴, 버튼, 테스트에서 같은 값을 쓰도록 한 곳에 모아 둡니다. */
export const SECTION = {
  top: 'top',
  info: 'info',
  merits: 'merits',
  floors: 'floors',
  units: 'units',
  location: 'location',
  consult: 'consult',
} as const;
