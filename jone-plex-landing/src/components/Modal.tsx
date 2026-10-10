/**
 * 공용 팝업(모달) 컴포넌트
 * - ESC 키 또는 바깥 영역 클릭으로 닫힘
 * - 열려 있는 동안 뒤쪽 페이지 스크롤 잠금
 * - 스크린리더용 role="dialog", aria-modal 적용
 */
import { useEffect, useId, useRef, type ReactNode } from 'react';
import { Icon } from './Icons';

interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

export function Modal({ open, title, onClose, children }: ModalProps) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousFocus = document.activeElement as HTMLElement | null;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
      previousFocus?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-end justify-center bg-navy-950/60 p-0 sm:items-center sm:p-6"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="max-h-[88vh] w-full overflow-y-auto rounded-t-3xl bg-white p-6 shadow-card-hover sm:max-w-lg sm:rounded-3xl sm:p-8"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 id={titleId} className="text-xl font-bold text-navy-900">
            {title}
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="-mr-2 -mt-1 rounded-full p-2 text-navy-600 hover:bg-navy-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-gold-500"
          >
            <Icon name="close" className="h-6 w-6" />
          </button>
        </div>
        <div className="text-[15px] leading-relaxed text-navy-800">{children}</div>
        <button
          type="button"
          onClick={onClose}
          className="mt-6 w-full rounded-xl bg-navy-900 py-3.5 text-base font-semibold text-white hover:bg-navy-800"
        >
          확인
        </button>
      </div>
    </div>
  );
}
