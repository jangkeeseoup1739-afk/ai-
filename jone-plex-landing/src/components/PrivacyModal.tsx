/**
 * 개인정보 수집 및 이용 동의 전문 (팝업)
 * 운영자 정보·보유 기간은 src/config/site.ts 의 privacy 항목에서 입력합니다.
 * 입력되지 않은 항목은 [운영자 입력 필요] 로 눈에 띄게 표시됩니다.
 */
import { siteConfig } from '../config/site';
import { isHttpUrl } from '../lib/links';
import { Modal } from './Modal';

const MISSING = '[운영자 입력 필요]';

interface PrivacyModalProps {
  open: boolean;
  onClose: () => void;
}

export function PrivacyModal({ open, onClose }: PrivacyModalProps) {
  const p = siteConfig.privacy;
  const val = (v: string) => (v.trim() ? v : <span className="font-semibold text-red-600">{MISSING}</span>);

  return (
    <Modal open={open} title="개인정보 수집 및 이용 안내" onClose={onClose}>
      <dl className="space-y-4">
        <div>
          <dt className="font-bold text-navy-900">1. 수집·이용 목적</dt>
          <dd className="mt-1">{siteConfig.fullName} 분양 상담 및 상담 결과 안내</dd>
        </div>
        <div>
          <dt className="font-bold text-navy-900">2. 수집 항목</dt>
          <dd className="mt-1">(필수) 이름, 연락처, 상담 목적 / (선택) 관심 층, 문의 내용</dd>
        </div>
        <div>
          <dt className="font-bold text-navy-900">3. 보유·이용 기간</dt>
          <dd className="mt-1">{val(p.retentionPeriod)}</dd>
        </div>
        <div>
          <dt className="font-bold text-navy-900">4. 개인정보 처리자</dt>
          <dd className="mt-1 space-y-0.5">
            <p>상호: {val(p.operatorName)}</p>
            <p>대표자: {val(p.representative)}</p>
            <p>개인정보 보호책임자: {val(p.officerName)}</p>
            <p>문의: {val(p.officerContact)}</p>
          </dd>
        </div>
        <div>
          <dt className="font-bold text-navy-900">5. 동의 거부 권리</dt>
          <dd className="mt-1">
            개인정보 수집·이용에 동의하지 않을 수 있습니다. 다만 동의하지 않으면 온라인 상담 신청이 제한되며, 전화로 상담받으실 수 있습니다.
          </dd>
        </div>
      </dl>
      {isHttpUrl(p.policyUrl) && (
        <a href={p.policyUrl} target="_blank" rel="noopener noreferrer" className="mt-4 inline-block font-semibold text-gold-700 underline underline-offset-2">
          개인정보 처리방침 전문 보기 (새 창)
        </a>
      )}
    </Modal>
  );
}
