/**
 * 전화 / 카카오톡 상담 버튼
 *
 * site.ts 에 값이 있으면 실제 링크(<a>)로, 없으면 "설정 필요" 안내창을 여는 버튼으로 동작합니다.
 * 여러 곳(첫 화면, 하단 고정바, 헤더 등)에서 모양만 바꿔 재사용합니다.
 */
import type { ReactNode } from 'react';
import { kakaoHref, phoneDisplay, phoneHref } from '../lib/links';
import { useSetupNotice } from './SetupNotice';

interface ContactButtonProps {
  className?: string;
  children: ReactNode;
}

export function PhoneButton({ className, children }: ContactButtonProps) {
  const showNotice = useSetupNotice();
  if (phoneHref) {
    return (
      <a href={phoneHref} className={className} aria-label={`전화 상담 ${phoneDisplay}`}>
        {children}
      </a>
    );
  }
  return (
    <button type="button" className={className} onClick={() => showNotice('phone')}>
      {children}
    </button>
  );
}

export function KakaoButton({ className, children }: ContactButtonProps) {
  const showNotice = useSetupNotice();
  if (kakaoHref) {
    return (
      <a
        href={kakaoHref}
        target="_blank"
        rel="noopener noreferrer"
        className={className}
        aria-label="카카오톡 상담 (새 창)"
      >
        {children}
      </a>
    );
  }
  return (
    <button type="button" className={className} onClick={() => showNotice('kakao')} aria-label="카카오톡 상담">
      {children}
    </button>
  );
}
