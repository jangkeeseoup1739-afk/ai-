/**
 * 분양 정보 상담 신청 폼
 *
 *  - 필수: 이름, 연락처(휴대전화 형식), 상담 목적, 개인정보 동의
 *  - 전송 주소(endpoint)가 없으면 "테스트 모드"로 동작하며, 접수 완료라고 표시하지 않습니다.
 *  - 전송 주소 설정: src/config/site.ts → form.endpoint (README "상담 신청 폼 연결 방법" 참고)
 */
import { useCallback, useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { floors } from '../config/floors';
import { SECTION, getFormEndpoint, phoneDisplay, phoneHref } from '../lib/links';
import { submitConsult, type SubmitResult } from '../lib/submit';
import { formatPhone, validateConsultForm, type ConsultFormErrors, type ConsultFormValues } from '../lib/validation';
import { Icon } from './Icons';
import { PrivacyModal } from './PrivacyModal';
import { Section } from './Section';

/** 상담 목적 선택지 – 바꾸려면 여기만 수정 */
export const PURPOSES = ['실사용', '임대', '투자 검토', '기타'] as const;
/** 관심 층 "미정" 선택지 값 */
const FLOOR_UNDECIDED = '';

const INITIAL: ConsultFormValues = { name: '', phone: '', floor: FLOOR_UNDECIDED, purpose: '', message: '', agree: false };

interface ConsultFormProps {
  /** 층별 정보에서 "상담 문의"를 누르면 들어오는 층 ID. token 이 바뀔 때마다 다시 적용됩니다. */
  preset?: { floorId: string; token: number } | null;
  /** 테스트용으로 전송 주소를 바꿔 끼울 수 있게 열어 둔 값 (기본: 설정 파일) */
  endpoint?: string;
}

export function ConsultForm({ preset, endpoint = getFormEndpoint() }: ConsultFormProps) {
  const uid = useId();
  const [values, setValues] = useState<ConsultFormValues>(INITIAL);
  const [errors, setErrors] = useState<ConsultFormErrors>({});
  const [honeypot, setHoneypot] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [privacyOpen, setPrivacyOpen] = useState(false);
  const nameRef = useRef<HTMLInputElement>(null);
  const closePrivacy = useCallback(() => setPrivacyOpen(false), []);
  const isTestMode = !endpoint;

  // 층별 정보에서 넘어온 관심 층을 자동 선택
  useEffect(() => {
    if (!preset) return;
    setValues((v) => ({ ...v, floor: preset.floorId }));
    setResult(null);
    nameRef.current?.focus({ preventScroll: true });
  }, [preset]);

  const set = <K extends keyof ConsultFormValues>(key: K, value: ConsultFormValues[K]) => {
    setValues((v) => ({ ...v, [key]: value }));
    // 사용자가 고치면 해당 항목 오류 메시지는 바로 지움
    if (errors[key]) setErrors((e) => ({ ...e, [key]: undefined }));
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const found = validateConsultForm(values);
    setErrors(found);
    setResult(null);
    const firstError = (Object.keys(found) as (keyof ConsultFormValues)[])[0];
    if (firstError) {
      // 첫 번째 오류 항목으로 커서 이동
      document.getElementById(`${uid}-${firstError}`)?.focus();
      return;
    }

    setSubmitting(true);
    const floorLabel = floors.find((f) => f.id === values.floor)?.label ?? '미정';
    const res = await submitConsult(endpoint, {
      name: values.name.trim(),
      phone: formatPhone(values.phone),
      floor: floorLabel,
      purpose: values.purpose,
      message: values.message.trim(),
      agreedAt: new Date().toISOString(),
      pageUrl: window.location.href,
      _gotcha: honeypot,
    });
    setSubmitting(false);
    setResult(res);
    if (res.status === 'success') {
      setValues(INITIAL);
    }
  };

  const fieldId = (k: keyof ConsultFormValues) => `${uid}-${k}`;
  const errorId = (k: keyof ConsultFormValues) => `${uid}-${k}-error`;
  const errProps = (k: keyof ConsultFormValues) =>
    errors[k] ? { 'aria-invalid': true as const, 'aria-describedby': errorId(k) } : {};
  const inputClass = (k: keyof ConsultFormValues) =>
    `mt-2 block w-full rounded-xl border bg-white px-4 py-3.5 text-base text-navy-900 placeholder:text-navy-300 focus:outline-none focus:ring-2 focus:ring-gold-400 ${
      errors[k] ? 'border-red-500' : 'border-navy-200'
    }`;
  const ErrorText = ({ k }: { k: keyof ConsultFormValues }) =>
    errors[k] ? (
      <p id={errorId(k)} role="alert" className="mt-1.5 text-sm font-medium text-red-600">
        {errors[k]}
      </p>
    ) : null;

  return (
    <Section
      id={SECTION.consult}
      eyebrow="CONSULTING"
      title="분양 정보 상담받기"
      description="남겨주신 연락처로 담당자가 층별 공급 정보와 분양 조건을 안내해 드립니다."
      tone="white"
    >
      <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr] lg:gap-10">
        {/* ── 왼쪽: 바로 상담 안내 ── */}
        <aside className="rounded-3xl bg-navy-900 p-6 text-white sm:p-8">
          <p className="text-sm font-semibold text-gold-300">빠른 전화 상담</p>
          {phoneHref ? (
            <a href={phoneHref} className="mt-2 block text-3xl font-extrabold tracking-tight text-white hover:text-gold-200 sm:text-4xl">
              {phoneDisplay}
            </a>
          ) : (
            <p className="mt-2 text-lg font-bold">전화번호 설정 필요</p>
          )}
          <ul className="mt-6 space-y-3 text-[15px] text-navy-100">
            {['층별 공급 면적 · 전용 면적 안내', '분양가 · 계약 조건 안내', '방문 상담 일정 예약'].map((t) => (
              <li key={t} className="flex gap-2">
                <Icon name="check" className="mt-0.5 h-5 w-5 shrink-0 text-gold-400" />
                {t}
              </li>
            ))}
          </ul>
        </aside>

        {/* ── 오른쪽: 신청 폼 ── */}
        <div className="rounded-3xl border border-navy-100 bg-navy-50/60 p-5 sm:p-8">
          {isTestMode && (
            <div role="note" className="mb-6 flex gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-[15px] text-amber-900">
              <Icon name="alert" className="mt-0.5 h-5 w-5 shrink-0" />
              <div>
                <p className="font-bold">테스트 모드 – 온라인 신청이 아직 전송되지 않습니다</p>
                <p className="mt-1">
                  운영자: <code className="rounded bg-amber-100 px-1">src/config/site.ts</code>의 <code className="rounded bg-amber-100 px-1">form.endpoint</code>를 설정해야 실제 접수됩니다.
                  {phoneHref && <> 지금 상담이 필요하시면 <a href={phoneHref} className="font-bold underline">{phoneDisplay}</a>로 전화 주세요.</>}
                </p>
              </div>
            </div>
          )}

          {result?.status === 'success' ? (
            <div role="status" className="py-8 text-center">
              <span className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-gold-500 text-navy-950">
                <Icon name="check" className="h-8 w-8" />
              </span>
              <p className="mt-5 text-2xl font-bold text-navy-900">상담 신청이 접수되었습니다</p>
              <p className="mt-2 text-base text-navy-700">담당자가 확인 후 남겨주신 연락처로 연락드리겠습니다.</p>
              <button
                type="button"
                onClick={() => setResult(null)}
                className="mt-6 rounded-xl border border-navy-200 px-5 py-3 text-base font-semibold text-navy-800 hover:bg-white"
              >
                새 상담 신청하기
              </button>
            </div>
          ) : (
            <form onSubmit={onSubmit} noValidate aria-label="분양 상담 신청서" className="grid gap-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div>
                  <label htmlFor={fieldId('name')} className="text-[15px] font-semibold text-navy-900">
                    이름 <span className="text-red-600" aria-hidden="true">*</span>
                    <span className="sr-only">(필수)</span>
                  </label>
                  <input
                    ref={nameRef}
                    id={fieldId('name')}
                    name="name"
                    type="text"
                    autoComplete="name"
                    maxLength={30}
                    placeholder="홍길동"
                    value={values.name}
                    onChange={(e) => set('name', e.target.value)}
                    className={inputClass('name')}
                    required
                    {...errProps('name')}
                  />
                  <ErrorText k="name" />
                </div>
                <div>
                  <label htmlFor={fieldId('phone')} className="text-[15px] font-semibold text-navy-900">
                    연락처 <span className="text-red-600" aria-hidden="true">*</span>
                    <span className="sr-only">(필수)</span>
                  </label>
                  <input
                    id={fieldId('phone')}
                    name="phone"
                    type="tel"
                    inputMode="numeric"
                    autoComplete="tel"
                    placeholder="010-1234-5678"
                    value={values.phone}
                    onChange={(e) => set('phone', formatPhone(e.target.value))}
                    className={inputClass('phone')}
                    required
                    {...errProps('phone')}
                  />
                  <ErrorText k="phone" />
                </div>
              </div>

              <div>
                <label htmlFor={fieldId('floor')} className="text-[15px] font-semibold text-navy-900">
                  관심 층
                </label>
                <select
                  id={fieldId('floor')}
                  name="floor"
                  value={values.floor}
                  onChange={(e) => set('floor', e.target.value)}
                  className={inputClass('floor')}
                >
                  <option value={FLOOR_UNDECIDED}>미정 / 상담 후 결정</option>
                  {floors.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.label}
                    </option>
                  ))}
                </select>
              </div>

              <fieldset {...(errors.purpose ? { 'aria-describedby': errorId('purpose') } : {})}>
                <legend className="text-[15px] font-semibold text-navy-900">
                  상담 목적 <span className="text-red-600" aria-hidden="true">*</span>
                  <span className="sr-only">(필수)</span>
                </legend>
                <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {PURPOSES.map((p, i) => (
                    <label
                      key={p}
                      className={`flex cursor-pointer items-center justify-center rounded-xl border px-3 py-3.5 text-base font-semibold transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-gold-400 ${
                        values.purpose === p ? 'border-navy-900 bg-navy-900 text-white' : 'border-navy-200 bg-white text-navy-800 hover:border-gold-400'
                      }`}
                    >
                      <input
                        type="radio"
                        name="purpose"
                        value={p}
                        id={i === 0 ? fieldId('purpose') : undefined}
                        checked={values.purpose === p}
                        onChange={() => set('purpose', p)}
                        className="sr-only"
                      />
                      {p}
                    </label>
                  ))}
                </div>
                <ErrorText k="purpose" />
              </fieldset>

              <div>
                <label htmlFor={fieldId('message')} className="text-[15px] font-semibold text-navy-900">
                  문의 내용 <span className="text-sm font-normal text-navy-500">(선택)</span>
                </label>
                <textarea
                  id={fieldId('message')}
                  name="message"
                  rows={4}
                  maxLength={1000}
                  placeholder="필요한 면적, 업종, 방문 희망 일정 등을 적어 주세요."
                  value={values.message}
                  onChange={(e) => set('message', e.target.value)}
                  className={inputClass('message')}
                  {...errProps('message')}
                />
                <ErrorText k="message" />
              </div>

              {/* 스팸 방지용 숨은 칸 – 화면·스크린리더에 보이지 않음 */}
              <div aria-hidden="true" className="absolute -left-[9999px] h-0 w-0 overflow-hidden">
                <label>
                  비워 두세요
                  <input type="text" name="_gotcha" tabIndex={-1} autoComplete="off" value={honeypot} onChange={(e) => setHoneypot(e.target.value)} />
                </label>
              </div>

              <div className={`rounded-xl border bg-white p-4 ${errors.agree ? 'border-red-500' : 'border-navy-200'}`}>
                <div className="flex items-start justify-between gap-3">
                  <label htmlFor={fieldId('agree')} className="flex cursor-pointer items-start gap-3 text-[15px] text-navy-900">
                    <input
                      id={fieldId('agree')}
                      name="agree"
                      type="checkbox"
                      checked={values.agree}
                      onChange={(e) => set('agree', e.target.checked)}
                      className="mt-0.5 h-5 w-5 shrink-0 accent-navy-900"
                      {...errProps('agree')}
                    />
                    <span>
                      <span className="font-semibold">[필수]</span> 개인정보 수집 및 이용에 동의합니다.
                    </span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setPrivacyOpen(true)}
                    className="shrink-0 text-sm font-semibold text-gold-700 underline underline-offset-2 hover:text-gold-600"
                  >
                    전문 보기
                  </button>
                </div>
                <ErrorText k="agree" />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gold-500 px-6 py-4 text-lg font-bold text-navy-950 hover:bg-gold-400 disabled:cursor-wait disabled:opacity-70"
              >
                {submitting ? '전송 중…' : '상담 신청하기'}
              </button>

              {result?.status === 'test-mode' && (
                <div role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-[15px] text-amber-900">
                  <p className="font-bold">테스트 모드: 입력값 검증은 통과했지만 신청서는 전송되지 않았습니다.</p>
                  <p className="mt-1">
                    전송 서비스가 연결되지 않아 접수되지 않았습니다.
                    {phoneHref && <> 상담은 <a href={phoneHref} className="font-bold underline">{phoneDisplay}</a>로 전화 주세요.</>}
                  </p>
                </div>
              )}
              {result?.status === 'error' && (
                <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-[15px] font-medium text-red-800">
                  {result.message}
                </div>
              )}
            </form>
          )}
        </div>
      </div>

      <PrivacyModal open={privacyOpen} onClose={closePrivacy} />
    </Section>
  );
}
