import { formatPhone, isValidMobile, toTelHref, validateConsultForm } from '../lib/validation';

describe('휴대전화 번호', () => {
  it('하이픈 자동 입력', () => {
    expect(formatPhone('01088737258')).toBe('010-8873-7258');
    expect(formatPhone('0101234567')).toBe('010-123-4567');
    expect(formatPhone('010')).toBe('010');
    expect(formatPhone('010-12')).toBe('010-12');
    expect(formatPhone('010123456789999')).toBe('010-1234-5678');
  });
  it('형식 검사', () => {
    expect(isValidMobile('010-8873-7258')).toBe(true);
    expect(isValidMobile('011-123-4567')).toBe(true);
    expect(isValidMobile('010-123-4567')).toBe(false); // 010 은 11자리
    expect(isValidMobile('02-123-4567')).toBe(false);
    expect(isValidMobile('')).toBe(false);
  });
  it('tel 링크 변환', () => {
    expect(toTelHref('010-8873-7258')).toBe('tel:01088737258');
    expect(toTelHref('')).toBeNull();
  });
});

describe('폼 전체 검증', () => {
  const ok = { name: '홍길동', phone: '010-1234-5678', floor: '', purpose: '실사용', message: '', agree: true };
  it('정상 입력은 오류 없음', () => {
    expect(validateConsultForm(ok)).toEqual({});
  });
  it('필수값 누락 시 각각 오류', () => {
    const e = validateConsultForm({ ...ok, name: ' ', phone: '', purpose: '', agree: false });
    expect(Object.keys(e).sort()).toEqual(['agree', 'name', 'phone', 'purpose']);
  });
  it('잘못된 번호', () => {
    expect(validateConsultForm({ ...ok, phone: '1234' }).phone).toMatch(/정확히/);
  });
});
