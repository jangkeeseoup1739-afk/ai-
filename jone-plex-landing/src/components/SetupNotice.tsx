/**
 * "설정 필요" 안내창
 *
 * 카카오톡 채널 주소 등이 site.ts 에 아직 입력되지 않았을 때
 * 가짜 링크로 이동시키는 대신 이 안내창을 띄웁니다. (방문자용 문구만 표시)
 * 설정 위치: 카카오톡 → site.ts 의 contact.kakaoChannelUrl, 전화 → contact.phone
 *
 * 사용법:
 *   const showNotice = useSetupNotice();
 *   showNotice('kakao');
 */
import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';
import { Modal } from './Modal';
import { phoneDisplay, phoneHref } from '../lib/links';

/** 안내 종류별 문구 – 새 항목이 필요하면 여기에 추가하세요. */
const NOTICES = {
  kakao: {
    title: '카카오톡 상담 준비 중',
    body: '카카오톡 채널 주소가 아직 연결되지 않았습니다.',
    setting: 'src/config/site.ts → contact.kakaoChannelUrl',
  },
  phone: {
    title: '전화 상담 준비 중',
    body: '상담 전화번호가 아직 입력되지 않았습니다.',
    setting: 'src/config/site.ts → contact.phone',
  },
} as const;

export type NoticeKey = keyof typeof NOTICES;

const SetupNoticeContext = createContext<(key: NoticeKey) => void>(() => {});

export function SetupNoticeProvider({ children }: { children: ReactNode }) {
  const [current, setCurrent] = useState<NoticeKey | null>(null);
  const close = useCallback(() => setCurrent(null), []);
  const notice = current ? NOTICES[current] : null;

  return (
    <SetupNoticeContext.Provider value={setCurrent}>
      {children}
      <Modal open={!!notice} title={notice?.title ?? ''} onClose={close}>
        <p>{notice?.body}</p>
        {current !== 'phone' && phoneHref && (
          <p className="mt-3">
            지금 바로 상담이 필요하시면{' '}
            <a href={phoneHref} className="font-semibold text-gold-700 underline underline-offset-2">
              {phoneDisplay}
            </a>
            로 전화 주세요.
          </p>
        )}
      </Modal>
    </SetupNoticeContext.Provider>
  );
}

export function useSetupNotice() {
  return useContext(SetupNoticeContext);
}
