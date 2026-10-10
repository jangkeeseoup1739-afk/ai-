/**
 * 상담 신청서 전송 로직
 *
 *  endpoint 가 비어 있으면 → 'test-mode' (어디에도 보내지 않음, 접수 완료라고 표시하지 않음)
 *
 *  endpoint 가 구글 Apps Script 웹앱(https://script.google.com/...)이면
 *   → 기존 홈페이지(joneflex.homefixweb.com)의 관심고객 등록과 "같은 형식"으로 보냅니다.
 *     기존 스크립트(lead-webhook.gs)가 그대로 받아 '관심고객' 시트에 한 줄 쌓고 이메일 알림을 보냅니다.
 *     기존 스크립트·시트는 전혀 수정하지 않습니다.
 *
 *  그 밖의 주소(Formspree, 이 프로젝트의 /api/consult 등)
 *   → ConsultPayload 를 JSON 으로 POST, 서버가 성공 응답을 줄 때만 'success'
 */

export interface ConsultPayload {
  name: string;
  phone: string;
  floor: string;
  purpose: string;
  message: string;
  /** 개인정보 동의 시각 (ISO 문자열) */
  agreedAt: string;
  /** 신청이 들어온 페이지 주소 */
  pageUrl: string;
  /** 스팸 방지용 숨은 칸 – 사람은 비워 둡니다 (Formspree 규칙과 같은 이름) */
  _gotcha: string;
}

export type SubmitResult =
  | { status: 'test-mode' }
  | { status: 'success' }
  | { status: 'error'; message: string };

/**
 * 기존 홈페이지가 보내는 관심고객 형식 (기존 저장소 src/types.ts 의 CustomerLead 와 동일)
 * 시트 열: 접수시각 | 접수번호 | 성함 | 연락처 | 관심 상품 | 관심 타입 | 상담 희망 시간 | 문의 내용 | 개인정보 동의
 */
export interface HomepageLead {
  id: string;
  name: string;
  phone: string;
  interestCategory: string;
  preferredType: string;
  preferredTime: string;
  message: string;
  createdAt: string;
  privacyAgreed: boolean;
}

/** 이 랜딩페이지에서 들어온 접수는 접수번호가 'LP-' 로 시작합니다. (기존 홈페이지는 'LEAD-') */
export const LANDING_LEAD_PREFIX = 'LP-';

/** 상담 폼 값 → 기존 홈페이지 관심고객 형식 */
export function toHomepageLead(p: ConsultPayload, now: Date = new Date()): HomepageLead {
  return {
    id: `${LANDING_LEAD_PREFIX}${now.getTime().toString().slice(-6)}`,
    name: p.name,
    phone: p.phone,
    interestCategory: `관심 층: ${p.floor}`, // 시트 '관심 상품' 열
    preferredType: `상담 목적: ${p.purpose}`, // 시트 '관심 타입' 열
    preferredTime: '', // 이 폼에는 상담 희망 시간 항목이 없음
    message: p.message,
    createdAt: now.toLocaleString('ko-KR'),
    privacyAgreed: true,
  };
}

const ERROR_GENERIC = '전송에 실패했습니다. 잠시 후 다시 시도하거나 전화로 문의해 주세요.';
const ERROR_NETWORK = '네트워크 오류로 전송하지 못했습니다. 인터넷 연결을 확인하거나 전화로 문의해 주세요.';

function withTimeout(ms: number) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  return { signal: controller.signal, done: () => clearTimeout(timer) };
}

export async function submitConsult(
  endpoint: string,
  payload: ConsultPayload,
  fetchImpl: typeof fetch = fetch,
): Promise<SubmitResult> {
  if (!endpoint) return { status: 'test-mode' };
  if (/^https:\/\/script\.google\.com\//.test(endpoint)) return submitToAppsScript(endpoint, payload, fetchImpl);
  return submitJson(endpoint, payload, fetchImpl);
}

/**
 * 구글 Apps Script 웹앱으로 전송 (기존 홈페이지 sendLead.ts 와 같은 방식)
 * - Content-Type 을 text/plain 으로 보내 CORS 사전 요청 없이 전달
 * - 응답을 읽지 못하면(CORS 등) no-cors 로 한 번 더 보냄. 같은 접수번호+연락처는
 *   기존 스크립트가 중복으로 걸러 주므로 두 줄로 쌓이지 않습니다.
 */
async function submitToAppsScript(endpoint: string, payload: ConsultPayload, fetchImpl: typeof fetch): Promise<SubmitResult> {
  // 스팸 로봇이 숨은 칸을 채운 경우: 보내지 않고 완료처럼 처리 (기존 홈페이지와 동일)
  if (payload._gotcha.trim()) return { status: 'success' };

  const body = JSON.stringify(toHomepageLead(payload));
  const headers = { 'Content-Type': 'text/plain;charset=utf-8' };

  const first = withTimeout(10000);
  try {
    const res = await fetchImpl(endpoint, { method: 'POST', headers, body, redirect: 'follow', signal: first.signal });
    if (res.ok) {
      const data = (await res.json().catch(() => null)) as { ok?: unknown } | null;
      if (data && data.ok === false) {
        return { status: 'error', message: '접수가 처리되지 않았습니다. 입력 내용을 확인하거나 전화로 문의해 주세요.' };
      }
      return { status: 'success' };
    }
    return { status: 'error', message: `${ERROR_GENERIC} (오류 코드 ${res.status})` };
  } catch {
    // 아래 no-cors 재전송으로 넘어감
  } finally {
    first.done();
  }

  const second = withTimeout(10000);
  try {
    await fetchImpl(endpoint, { method: 'POST', mode: 'no-cors', headers, body, signal: second.signal });
    return { status: 'success' };
  } catch {
    return { status: 'error', message: ERROR_NETWORK };
  } finally {
    second.done();
  }
}

/** 일반 JSON 접수 주소로 전송 (Formspree, /api/consult 등) */
async function submitJson(endpoint: string, payload: ConsultPayload, fetchImpl: typeof fetch): Promise<SubmitResult> {
  const t = withTimeout(15000);
  try {
    const res = await fetchImpl(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload),
      signal: t.signal,
    });
    if (res.ok) {
      const data = (await res.json().catch(() => null)) as { ok?: unknown } | null;
      if (data && data.ok === false) {
        return { status: 'error', message: '접수가 처리되지 않았습니다. 입력 내용을 확인하거나 전화로 문의해 주세요.' };
      }
      return { status: 'success' };
    }
    if (res.status === 503) {
      return { status: 'error', message: '상담 접수 서버 설정이 완료되지 않았습니다. 전화로 문의해 주세요.' };
    }
    return { status: 'error', message: `${ERROR_GENERIC} (오류 코드 ${res.status})` };
  } catch {
    return { status: 'error', message: ERROR_NETWORK };
  } finally {
    t.done();
  }
}
