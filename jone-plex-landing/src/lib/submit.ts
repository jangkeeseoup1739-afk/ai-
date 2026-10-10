/**
 * 상담 신청서 전송 로직
 *
 *  endpoint 가 비어 있으면 → 'test-mode' (어디에도 보내지 않음, 접수 완료라고 표시하지 않음)
 *  endpoint 가 있으면      → JSON 으로 POST, 서버가 성공(2xx) 응답을 줄 때만 'success'
 *
 *  Formspree(https://formspree.io), 이 프로젝트의 /api/consult(Vercel 함수),
 *  Google Apps Script 웹앱 등 "JSON POST 를 받는 주소"라면 어디든 연결할 수 있습니다.
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

export async function submitConsult(
  endpoint: string,
  payload: ConsultPayload,
  fetchImpl: typeof fetch = fetch,
): Promise<SubmitResult> {
  if (!endpoint) return { status: 'test-mode' };

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000); // 15초 이상 응답이 없으면 실패 처리
    const res = await fetchImpl(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    clearTimeout(timer);

    if (res.ok) return { status: 'success' };
    if (res.status === 503) {
      return { status: 'error', message: '상담 접수 서버 설정이 완료되지 않았습니다. 전화로 문의해 주세요.' };
    }
    return { status: 'error', message: `전송에 실패했습니다. (오류 코드 ${res.status}) 잠시 후 다시 시도하거나 전화로 문의해 주세요.` };
  } catch {
    return { status: 'error', message: '네트워크 오류로 전송하지 못했습니다. 인터넷 연결을 확인하거나 전화로 문의해 주세요.' };
  }
}
