/**
 * 상담 신청 폼 입력값 검증 함수 모음
 * (화면 폼과 테스트에서 함께 사용합니다)
 */

/** 숫자만 남기기: '010-1234-5678' → '01012345678' */
export function digitsOnly(value: string): string {
  return value.replace(/\D/g, '');
}

/**
 * 입력 중인 휴대전화 번호에 하이픈을 자동으로 넣어 줍니다.
 * '01012345678' → '010-1234-5678', '0101234567' → '010-123-4567'
 */
export function formatPhone(value: string): string {
  const d = digitsOnly(value).slice(0, 11);
  if (d.length < 4) return d;
  if (d.length < 8) return `${d.slice(0, 3)}-${d.slice(3)}`;
  if (d.length === 10) return `${d.slice(0, 3)}-${d.slice(3, 6)}-${d.slice(6)}`;
  return `${d.slice(0, 3)}-${d.slice(3, 7)}-${d.slice(7)}`;
}

/**
 * 휴대전화 번호 형식 확인
 * 010은 11자리, 011·016·017·018·019는 10~11자리 허용
 */
export function isValidMobile(value: string): boolean {
  const d = digitsOnly(value);
  if (/^010\d{8}$/.test(d)) return true;
  return /^01[16789]\d{7,8}$/.test(d);
}

/** 전화번호를 tel: 링크용 숫자로 변환. 빈 값이면 null */
export function toTelHref(phone: string): string | null {
  const d = digitsOnly(phone);
  return d.length >= 8 ? `tel:${d}` : null;
}

export interface ConsultFormValues {
  name: string;
  phone: string;
  floor: string;
  purpose: string;
  message: string;
  agree: boolean;
}

export type ConsultFormErrors = Partial<Record<keyof ConsultFormValues, string>>;

/** 폼 전체 검증 – 오류가 있는 항목만 메시지를 담아 돌려줍니다. */
export function validateConsultForm(v: ConsultFormValues): ConsultFormErrors {
  const errors: ConsultFormErrors = {};
  const name = v.name.trim();
  if (!name) errors.name = '이름을 입력해 주세요.';
  else if (name.length < 2) errors.name = '이름을 2자 이상 입력해 주세요.';

  if (!digitsOnly(v.phone)) errors.phone = '연락처를 입력해 주세요.';
  else if (!isValidMobile(v.phone)) errors.phone = '휴대전화 번호를 정확히 입력해 주세요. (예: 010-1234-5678)';

  if (!v.purpose) errors.purpose = '상담 목적을 선택해 주세요.';
  if (v.message.length > 1000) errors.message = '문의 내용은 1000자 이내로 입력해 주세요.';
  if (!v.agree) errors.agree = '개인정보 수집 및 이용에 동의해 주세요.';
  return errors;
}
